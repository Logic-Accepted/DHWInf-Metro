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
    def from_tuple(cls, data: Tuple[int, int]) -> Coord2D:
        return cls(*data)


@dataclass
class Station:
    """
    地铁站
    """
    id: str
    location: Coord2D
    status: Literal["enabled", "disabled"] = "enabled"
    name: L10nDict

    @classmethod
    def from_dict(cls, data: Any, version: str) -> Station:
        ...


@dataclass
class Line:
    """
    地铁线
    """
    id: str
    stations: Dict[str, Station]
    """id as key, station as value"""
    routes: Dict[Tuple[str, str], bool]
    """`True` for enabled, `False` for disabled"""
    name: L10nDict

    @classmethod
    def from_dict(cls, data: Any, version: str) -> Line:
        ...


@dataclass
class MetroMap:
    """
    地铁图
    """
    stations: Dict[str, Station]
    lines: Dict[str, Line]
    """Deprecated"""

    @classmethod
    def from_dict(cls, data: Any) -> MetroMap:
        ...
