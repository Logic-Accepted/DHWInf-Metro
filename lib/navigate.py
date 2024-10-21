import logging
from typing import List, Tuple
from .model import (Coord2D, MetroMap, MetroNaviRecord,
                    NaviRecord, Station, TransferRecord, WalkNaviRecord)


logger = logging.getLogger(__name__)


def soft_float_assert(value):
    """把坐标试着转化成 float"""
    try:
        return float(value)
    except (ValueError, TypeError):
        return value

# 导航逻辑实现


def navigate_metro(metro_map: MetroMap, *args) -> List[NaviRecord]:

    args = list(map(soft_float_assert, args[:]))

    def take_pos(args) -> Tuple[Station | Coord2D, list]:
        if len(args) == 0:
            raise ValueError("参数不足")
        if type(args[0]) is str:
            return metro_map.stations[args[0]], args[1:]
        if len(args) < 2:
            raise ValueError("参数不足")
        return Coord2D(*args[:2]), args[2:]

    start, args = take_pos(args)
    dest, _ = take_pos(args)

    if isinstance(start, Station):
        start_station = start
        start_distance = 0
    else:
        start_station, start_distance = metro_map.find_nearest_station(start)

    if isinstance(dest, Station):
        end_station = dest
        end_distance = 0
    else:
        end_station, end_distance = metro_map.find_nearest_station(dest)

    if start_station is None:
        raise ValueError("无法找到起始站点")

    if end_station is None:
        raise ValueError("无法找到目的站点")

    if start_station == end_station:
        total_distance = start_distance + end_distance
        if total_distance <= 50:
            raise ValueError("当前位置距离目的地过近")
        if total_distance >= 200000:
            raise ValueError("位置距离地铁系统过远")
        raise ValueError("起始站点与目的站点相同")

    nodes, distance = metro_map.navi_graph.find_route(
        start_station, end_station)

    res: List[NaviRecord] = []

    if start_distance != 0:
        res.append(WalkNaviRecord(
            start=start, end=start_station, distance=start_distance))

    last_line = None
    while len(nodes) > 1:
        stataion_count = len(nodes) - 1
        while True:
            for line in metro_map.lines.values():
                if line.include(*nodes[:stataion_count + 1]):
                    direction = line.find_dir(*nodes[:stataion_count + 1])
                    if last_line is not None and last_line != line:
                        res.append(TransferRecord(
                            line_from=last_line, line_to=line,
                            station=nodes[0]
                        ))
                    last_line = line
                    res.append(
                        MetroNaviRecord(
                            start=nodes[0], end=nodes[stataion_count],
                            line=line, direction=direction,
                            station_count=stataion_count,
                            time_cost=0  # TODO: add this
                        )
                    )
                    logger.debug(
                        f"{line.name}:{direction} {stataion_count} "
                        f"{nodes[0].name}->{nodes[stataion_count].name}"
                    )
                    nodes = nodes[stataion_count:]
                    break
            else:
                stataion_count -= 1
                continue
            break

    if end_distance != 0:
        res.append(WalkNaviRecord(
            start=end_station, end=dest, distance=end_distance))
    return res
