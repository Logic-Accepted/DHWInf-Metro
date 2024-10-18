from __future__ import annotations

from dataclasses import dataclass
from logging import warning
from typing import Any, Literal, Dict, Tuple

L10N_LANG = "zh"


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
    y: int

    @property
    def distance(self) -> float:
        """Euclidean distance"""
        return (self.x ** 2 + self.y ** 2) ** 0.5

    def distance_to(
            self,
            other: Coord2D,
            mode: Literal["euclidean", "manhattan"] = "mahanattan"
    ) -> float:
        if mode == "euclidean":
            return ((self.x - other.x) ** 2 + (self.y - other.y) ** 2) ** 0.5
        elif mode == "manhattan":
            return abs(self.x - other.x) + abs(self.y - other.y)
        else:
            raise ValueError(f"Invalid mode `{mode}`")

    def __sub__(self, other: Coord2D) -> Coord2D:
        return Coord2D(self.x - other.x, self.y - other.y)

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
            if len(stations) == 0:
                raise ValueError(f"No stations in line `{id}`")
            for i in range(len(stations) - 1):
                station1 = station_ids[i]
                station2 = station_ids[i + 1]
                routes[(station1, station2)] = True
            if line.get("circle", False):
                station1 = station_ids[0]
                station2 = station_ids[-1]
                routes[(station1, station2)] = True
            return cls(
                id=id,
                stations=stations,
                routes=routes,
                name=L10nDict.from_dict(line["name"])
            )


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


@dataclass
class MetroMap:
    """
    地铁图
    """
    version: MapVersion
    stations: StationBank
    lines: Dict[str, Line]
    """Deprecated"""

    @classmethod
    def from_dict(cls, data: dict) -> MetroMap:
        if "version" not in data:
            raise ValueError("Missing version in data")
        version = data["version"]
        version = MapVersion.from_str(version)
        format_ver = version.format_ver
        if format_ver == 1:
            # 没找到捏
            raise NotImplementedError("Format version 1 is not supported")
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
