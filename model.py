from __future__ import annotations

from dataclasses import dataclass
from logging import warning
from typing import Any, Callable, List, Literal, Dict, Tuple

L10N_LANG = "zh"


DistanceMode = Literal["euclidean", "manhattan"]


class L10nDict(dict):
    """
    本地化字典
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for lang, value in kwargs.items():
            self[lang] = value

    def __str__(self) -> str:
        if L10N_LANG in self:
            return self[L10N_LANG]
        warning(f"Missing l10n for {L10N_LANG}, trying random fallback...")
        if len(self) > 0:
            return next(iter(self.values()))
        raise ValueError("No l10n data available")

    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> L10nDict:
        return cls(**data)


@dataclass
class Coord2D:
    """
    二维坐标
    """

    x: int
    z: int

    def __str__(self) -> str:
        return f"({self.x}, {self.z})"

    @property
    def distance(self) -> float:
        """Euclidean distance"""
        return (self.x ** 2 + self.z ** 2) ** 0.5

    def distance_to(
            self,
            other: Coord2D,
            mode: DistanceMode = "manhattan"
    ) -> float:
        if mode == "euclidean":
            return ((self.x - other.x) ** 2 + (self.z - other.z) ** 2) ** 0.5
        elif mode == "manhattan":
            return abs(self.x - other.x) + abs(self.z - other.z)
        else:
            raise ValueError(f"Invalid mode `{mode}`")

    def __sub__(self, other: Coord2D) -> Coord2D:
        return Coord2D(self.x - other.x, self.z - other.z)

    @classmethod
    def deserialize(cls, data: Tuple[int, int]) -> Coord2D:
        return cls(*data)


@dataclass
class Station:
    """
    地铁站
    """
    id: str
    location: Coord2D
    name: L10nDict
    status: Literal["enabled", "disabled"] = "enabled"
    platforms = []
    """还没写捏"""
    exits = []
    """还没写捏"""

    def __hash__(self) -> int:
        return hash(self.id)

    def __eq__(self, other: Station) -> bool:
        return self.id == other.id

    def __str__(self) -> str:
        return f"{self.name} {self.location}"

    def distance_to(self, other: Station) -> float:
        """用 Manhattan 距离"""
        return self.location.distance_to(other.location, mode="manhattan")

    @classmethod
    def deserialize(cls, data: Any, format_version: int) -> Station:
        if format_version == 1:
            raise NotImplementedError("Format version 1 is not supported")
        elif format_version == 2:
            # data is `(id, station)`
            id, station = data
            status = station.get("status", "enabled")
            status = "enabled" if status == "enable" else status
            return cls(
                id=id,
                location=Coord2D.deserialize(station["coordinates"]),
                status=status,
                name=L10nDict.from_dict(station["name"]),
            )


StationBank = Dict[str, Station]
"""id as key, station as value"""


@dataclass
class Line:
    """
    地铁线
    """
    id: str
    stations: StationBank
    """Subset of the global station bank"""
    routes: Dict[Tuple[str, str], bool]
    """
    key: `(station_id_1, station_id_2)`

    `True` for enabled, `False` for disabled
    """
    name: L10nDict

    @property
    def navi_graph(self) -> NaviGraph:
        routes = {}
        for r, available in self.routes.items():
            if not available:
                continue
            id1, id2 = r
            if id1 not in routes:
                routes[id1] = {id2: 1}
            else:
                routes[id1][id2] = 1
            if id2 not in routes:
                routes[id2] = {id1: 1}
            else:
                routes[id2][id1] = 1
        return NaviGraph(
            routes=routes,
            nodes=self.stations
        )

    def find_dir(
        self,
        *stations,
    ) -> str:
        graph = self.navi_graph
        if graph.routes.get(stations[0].id, {}).get(stations[-1].id, 0) == 1:
            if len(stations) == 1:
                return "Unknown"
            # 环线
            # +--> +x
            # |
            # v
            # +z

            def cross_prod(a: Coord2D, b: Coord2D):
                """x cross z = -y"""
                return a.z * b.x - a.x * b.z
            area = 0
            for i in range(len(stations) - 1):
                area += cross_prod(
                    self.stations[stations[i].id].location,
                    self.stations[stations[i + 1].id].location
                )
            if area > 0:
                return "外环"
            return "内环"
        new_nodes = [
            station
            for station in map(
                self.stations.get, graph.routes[stations[-1].id])
            if station not in stations
        ]
        if len(new_nodes) == 0:
            return str(stations[-1].name)
        return '/'.join(map(
            lambda x: self.find_dir(*stations, x),
            new_nodes
        ))

    @classmethod
    def deserialize(
        cls,
        data: Any,
        format_version: int,
        all_stations: StationBank,
    ) -> Line:
        if format_version == 1:
            raise NotImplementedError("Format version 1 is not supported")
        elif format_version == 2:
            id, line = data
            for id in line["stations"]:
                if id not in all_stations:
                    warning(f"Station `{id}` not found in global bank")
            stations = {
                id: all_stations[id]
                for id in line["stations"]
                if id in all_stations
            }
            routes = {}
            station_ids = [
                id
                for id in line["stations"]
                if id in stations
            ]
            circular = line.get("circle", False)
            if type(circular) is str:
                circular = circular.lower() in ["true", "yes", "1"]
            routes = cls.routes_from_list(
                station_ids=station_ids,
                circular=circular,
            )
            routes = {
                (id1, id2): available
                for (id1, id2), available in routes.items()
                if id1 in stations and id2 in stations
            }
            return cls(
                id=id,
                stations=stations,
                routes=routes,
                name=L10nDict.from_dict(line["name"])
            )

    @classmethod
    def routes_from_list(
        cls,
        station_ids: list[str],
        circular: bool = False
    ) -> Dict[Tuple[str, str], bool]:
        """
        Notice: no station bank check
        """
        routes = {}
        for i in range(len(station_ids) - 1):
            station1 = station_ids[i]
            station2 = station_ids[i + 1]
            routes[(station1, station2)] = True
        if circular:
            station1 = station_ids[0]
            station2 = station_ids[-1]
            routes[(station1, station2)] = True
        return routes


@dataclass
class MapVersion:
    """
    地图版本
    """
    format_ver: int
    data_ver: int
    suffix: str

    @classmethod
    def from_str(cls, data: str | float) -> MapVersion:
        if type(data) is float:
            data = str(data)
        format_ver, data = data.split(".", maxsplit=1)
        format_ver = int(format_ver)
        data_ver, *data_suffix = data.split("-", maxsplit=1)
        data_suffix = data_suffix[0] if len(data_suffix) > 0 else ""
        data_ver = int(data_ver)
        return cls(
            format_ver=format_ver,
            data_ver=data_ver,
            suffix=data_suffix
        )

    def __str__(self) -> str:
        return f"{self.format_ver}.{self.data_ver}-{self.suffix}"


@dataclass
class NaviGraph:
    routes: Dict[str, Dict[str, float]]
    """`table[id1][id2]` 为 1 到 2 的 weight"""
    nodes: StationBank

    def find_route(
        self,
        start: Station,
        end: Station,
        heuristic_weight: float = 1.0
    ) -> Tuple[List[Station], float]:
        """
        寻找最短路径, 既然是地铁站那用 astar 吧

        启发函数: 两点间的曼哈顿距离
        """
        res = []
        if start == end:
            return res, 0
        open_set = {start}
        closed_set = set()
        g_score = {id: float("inf") for id in self.nodes}
        g_score[start.id] = 0
        f_score = {id: float("inf") for id in self.nodes}
        f_score[start.id] = start.location.distance_to(end.location)
        # Copilot generated A* algorithm, modified
        # TODO: more tests
        while len(open_set) > 0:
            current = min(
                open_set,
                key=lambda x: f_score[x.id]
            )
            res.append(current)
            open_set.remove(current)
            closed_set.add(current)
            if current == end:
                while current in res:
                    res.remove(current)
                res.append(current)
                return res, g_score[end.id]
            no_avail_neighbors = True
            for neighbor_id in self.routes[current.id]:
                neighbor = self.nodes[neighbor_id]
                if neighbor in closed_set:
                    continue
                no_avail_neighbors = False
                tentative_g_score = g_score[current.id] + \
                    self.routes[current.id][neighbor_id]
                if neighbor not in open_set:
                    open_set.add(neighbor)
                elif tentative_g_score >= g_score[neighbor_id]:
                    continue
                g_score[neighbor_id] = tentative_g_score
                f_score[neighbor_id] = g_score[neighbor_id] + \
                    heuristic_weight * \
                    neighbor.location.distance_to(end.location)
            if no_avail_neighbors:
                res.remove(current)
        return res, g_score[end.id]


@dataclass
class MetroMap:
    """
    地铁图
    """
    version: MapVersion
    stations: StationBank
    lines: Dict[str, Line]

    @property
    def navi_graph(self):
        """
        导航图
        """
        nodes = self.stations
        routes = {}
        for line in self.lines.values():
            for r, available in line.routes.items():
                if not available:
                    continue
                id1, id2 = r
                if id1 not in routes:
                    routes[id1] = {
                        id2: nodes[id1].distance_to(nodes[id2])
                    }
                else:
                    routes[id1][id2] = nodes[id1].distance_to(nodes[id2])
                if id2 not in routes:
                    routes[id2] = {
                        id1: nodes[id2].distance_to(nodes[id1])
                    }
                else:
                    routes[id2][id1] = nodes[id2].distance_to(nodes[id1])
        return NaviGraph(routes=routes, nodes=nodes)

    def find_nearest_station(
        self,
        location: Coord2D,
        distance_mode: DistanceMode = "manhattan",
        filter: Callable[[Station], bool] = lambda _: True
    ) -> Tuple[Station | None, float]:
        """
        `filter` 留给之后筛选非匿名站点用的
        """
        nearest = None
        nearest_distance = float("inf")
        for station in self.stations.values():
            if not filter(station):
                continue
            distance = location.distance_to(
                station.location,
                mode=distance_mode,
            )
            if distance < nearest_distance:
                nearest = station
                nearest_distance = distance
        return nearest, nearest_distance

    @classmethod
    def from_dict(cls, data: dict) -> MetroMap:
        if "version" not in data:
            raise ValueError("Missing version in data")
        version = data["version"]
        version = MapVersion.from_str(version)
        format_ver = version.format_ver
        if format_ver == 1:
            stations = data["stations"]
            stations = {
                id: Station(id, Coord2D(*coord), name=L10nDict(zh=id))
                for id, coord in stations.items()
            }
            raw_lines = data["lines"]
            line_ids = data["linesCode"]
            lines = {
                id: Line(
                    id=id,
                    stations=stations,
                    routes=Line.routes_from_list([
                        station
                        for station in raw_lines[id]
                        if station in stations
                    ]),
                    name=L10nDict(zh=line_ids[id][0], en=line_ids[id][1])
                )
                for id in line_ids
            }
            return cls(
                version=version,
                stations=stations,
                lines=lines
            )
        elif format_ver == 2:
            stations = data["stations"]
            stations = {
                id: Station.deserialize((id, station), format_ver)
                for id, station in stations.items()
            }
            lines = data["lines"]
            lines = {
                id: Line.deserialize((id, line), format_ver, stations)
                for id, line in lines.items()
            }
            return cls(
                version=version,
                stations=stations,
                lines=lines
            )


if __name__ == "__main__":
    # Tests
    import json
    with open("test.json", 'r') as f:
        metro_map = MetroMap.from_dict(json.load(f))
