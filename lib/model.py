from __future__ import annotations

from dataclasses import dataclass
import heapq
from logging import getLogger
from typing import Any, Callable, List, Literal, Dict, Tuple

L10N_LANG = "zh"


DistanceMode = Literal["euclidean", "manhattan"]
Number = int | float

logger = getLogger(__name__)


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
        logger.warning(
            f"Missing l10n for {L10N_LANG}, trying random fallback...")
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

    x: Number
    z: Number

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
    def deserialize(cls, data: Tuple[Number, Number]) -> Coord2D:
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
        raise ValueError(f"Invalid format version `{format_version}`")


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
    routes: NaviGraph
    """
    路线
    """
    name: L10nDict

    def find_dir(
        self,
        *stations,
    ) -> str:
        assert self.include(*stations), "Algo error..."
        graph = self.routes

        def peek(*stations) -> List[str]:
            if stations[0] == stations[-1]:
                if len(stations) == 1:
                    return ["Unknown"]
                if len(stations) == 2:
                    return [str(stations[1].name)]
                logger.debug(
                    f"Loop: {'->'.join(map(lambda x: str(x.name), stations))}"
                )
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
                    return ["外环"]
                return ["内环"]
            new_nodes = [
                station
                for station in map(
                    self.stations.get, graph.routes[stations[-1].id])
                if station not in stations
            ]
            res = []
            for node in new_nodes:
                res.extend(peek(*stations, node))
            if len(res) == 0:
                return [str(stations[-1].name)]
            return res

        res = peek(*stations)
        if len(res) == 0:
            return str(stations[-1].name)
        return '/'.join(res)

    def include(
        self,
        *stations: Station,
    ) -> bool:
        """
        判断 `stations` (按顺序) 是否在这条线上
        """

        last = None
        for station in stations:
            if station.id not in self.stations:
                return False
            if last is not None:
                if self.routes.get_weight(last, station) is None:
                    return False
            last = station
        return True

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
                    logger.warning(f"Station `{id}` not found in global bank")
            stations = {
                id: all_stations[id]
                for id in line["stations"]
                if id in all_stations
            }

            circular = line.get("circle", False)
            if type(circular) is str:
                circular = circular.lower() in ["true", "yes", "1"]
            routes = cls.routes_from_list(
                stations=[
                    stations[id]
                    for id in line["stations"]
                    if id in stations
                ],
                circular=circular,
            )
            return cls(
                id=id,
                stations=stations,
                routes=routes,
                name=L10nDict.from_dict(line["name"])
            )
        raise ValueError(f"Invalid format version `{format_version}`")

    @classmethod
    def routes_from_list(
        cls,
        stations: list[Station],
        circular: bool = False
    ) -> NaviGraph:
        """
        Notice: no station bank check (TODO: better impl?)
        TODO: Future time cost support
        """

        routes = NaviGraph(
            routes={},
            nodes={s.id: s for s in stations}
        )
        for i in range(len(stations) - 1):
            station1 = stations[i]
            station2 = stations[i + 1]
            routes.add_route(station1, station2,
                             station1.distance_to(station2))
        if circular:
            station1 = stations[0]
            station2 = stations[-1]
            routes.add_route(station1, station2,
                             station1.distance_to(station2))

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
        if self.suffix == "":
            return f"{self.format_ver}.{self.data_ver}"
        return f"{self.format_ver}.{self.data_ver}-{self.suffix}"


@dataclass
class NaviGraph:
    """
    导航图, 图结构的抽象
    """
    routes: Dict[str, Dict[str, float]]
    """`table[id1][id2]` 为 1 到 2 的 weight"""
    nodes: StationBank
    """`id`: `station`"""

    def __add__(self, other: NaviGraph) -> NaviGraph:
        """
        Merge two graphs, the latter one will overwrite the former one
        TODO: min weight
        """
        nodes = {**self.nodes, **other.nodes}
        routes = {**self.routes}
        for id1, table in other.routes.items():
            if id1 not in routes:
                routes[id1] = {}
            for id2, weight in table.items():
                if id2 not in routes[id1]:
                    routes[id1][id2] = weight
        return NaviGraph(routes=routes, nodes=nodes)

    def add_route(
        self,
        start: Station,
        end: Station,
        weight: float,
        reverse: bool = True,
    ):
        """
        添加路径
        """
        if start.id not in self.routes:
            self.routes[start.id] = {}
        self.routes[start.id][end.id] = weight
        if reverse:
            self.add_route(end, start, weight, reverse=False)

    def get_weight(
        self,
        start: Station,
        end: Station
    ) -> float | None:
        """
        `None` for no direct route
        """
        return self.routes[start.id].get(end.id, None)

    def find_route(
        self,
        start: Station,
        end: Station,
        heuristic_weight: float = 1.0,
        h_func: Callable[[Station, Station],
                         float] = lambda x, y: x.distance_to(y)
    ) -> Tuple[List[Station], float]:
        """
        寻找最短路径, 既然是地铁站那用 astar 吧

        启发函数: 两点间的曼哈顿距离
        """
        came_from: Dict[Station, Station] = {}

        def construct_path(last: Station) -> List[Station]:
            res = []
            current = last
            while current != start:
                res.append(current)
                current = came_from[current]
            res.append(start)
            return res[::-1]

        g_score: Dict[Station, float] = {
            station: float("inf")
            for station in self.nodes.values()
        }
        g_score[start] = 0
        f_score: Dict[Station, float] = {
            station: float("inf")
            for station in self.nodes.values()
        }
        f_score[start] = h_func(start, end)
        open_set = [(f_score[start], start)]
        while len(open_set) > 0:
            current = heapq.heappop(open_set)
            if current[1] == end:
                return construct_path(current[1]), g_score[end]

            for neighbor_id in self.routes[current[1].id]:
                neighbor = self.nodes[neighbor_id]
                tentative_g_score = g_score[current[1]] + \
                    self.get_weight(current[1], neighbor)  # type: ignore
                if tentative_g_score < g_score[neighbor]:
                    came_from[neighbor] = current[1]
                    g_score[neighbor] = tentative_g_score
                    f_score[neighbor] = g_score[neighbor] + \
                        heuristic_weight * h_func(neighbor, end)
                    heapq.heappush(open_set, (f_score[neighbor], neighbor))

        logger.warning("No route found")
        return [], float("inf")


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
        graph = NaviGraph(routes={}, nodes=nodes)
        for line in self.lines.values():
            graph = graph + line.routes
        return graph

    def find_nearest_station(
        self,
        location: Coord2D | Tuple[Number, Number],
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
            if isinstance(location, tuple):
                location = Coord2D(*location)
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
        raise ValueError(f"Invalid format version `{format_ver}`")


if __name__ == "__main__":
    # Tests
    import json
    with open("test.json", 'r') as f:
        metro_map = MetroMap.from_dict(json.load(f))
