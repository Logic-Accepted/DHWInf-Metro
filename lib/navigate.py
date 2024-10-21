import logging
from typing import List, Tuple
from .metro import load_metro_data, MAP
from .model import Coord2D, Line, MetroMap, Station


logger = logging.getLogger(__name__)


def soft_float_assert(value):
    """把坐标试着转化成 float"""
    try:
        return float(value)
    except (ValueError, TypeError):
        return value

# 导航逻辑实现


def navigate_metro(*args):
    if MAP is None:
        load_metro_data()
    data = MAP
    args = list(map(soft_float_assert, args[:]))

    def take_pos(args) -> Tuple[Station | Coord2D, list]:
        if len(args) == 0:
            raise ValueError("参数不足")
        if type(args[0]) is str:
            return data.stations[args[0]], args[1:]
        if len(args) < 2:
            raise ValueError("参数不足")
        return Coord2D(*args[:2]), args[2:]

    start, args = take_pos(args)
    dest, _ = take_pos(args)

    if isinstance(start, Station):
        start_station = start
        start_distance = 0
    else:
        start_station, start_distance = data.find_nearest_station(start)

    if isinstance(dest, Station):
        end_station = dest
        end_distance = 0
    else:
        end_station, end_distance = data.find_nearest_station(dest)

    if start_station is None:
        return "无法找到起始站点"

    if end_station is None:
        return "无法找到目的站点"

    if start_station == end_station:
        total_distance = start_distance + end_distance
        if total_distance <= 50:
            return "当前位置距离目的地过近"
        elif total_distance >= 200000:
            return "位置距离地铁系统过远"
        else:
            return "暂无地铁乘坐方案"
    else:
        nodes, distance = data.navi_graph.find_route(
            start_station, end_station)

        formatted_output = format_route_output(
            nodes,
            data,
            start_distance,
            end_distance,
            distance
        )
        return formatted_output

# 格式化输出


def format_route_output(
    route,
    metro_map: MetroMap,
    start_distance,
    end_distance,
    distance,
):
    output = []
    dest = route[-1]
    output.append("路线为：")
    first_station = route[0]
    if start_distance != 0:
        output.append(f"当前位置\n↓步行{start_distance:.2f}米\n{route[0]}地铁站 进站\n")
    else:
        output.append(f"{first_station.name} 地铁站 进站\n")

    route_lines: List[Tuple[Line, str, int, Station, Station]] = []
    """line, direction, station_count, start, end"""

    while len(route) > 1:
        stataion_count = len(route) - 1
        while True:
            for line in metro_map.lines.values():
                if line.include(*route[:stataion_count + 1]):
                    direction = line.find_dir(*route[:stataion_count + 1])
                    route_lines.append(
                        (line, direction, stataion_count,
                         route[0], route[stataion_count]))
                    logger.debug(
                        f"{line.name}:{direction} {stataion_count} "
                        f"{route[0].name}->{route[stataion_count].name}"
                    )
                    route = route[stataion_count:]
                    break
            else:
                stataion_count -= 1
                continue
            break

    for i in range(len(route_lines) - 1):
        l, d, c, s, e = route_lines[i]
        next_l = route_lines[i + 1][0]
        output.append(
            f"{s.name} 地铁站 \n↓ {l.name} {d} 方向 乘坐 {c} 站\n"
            f"{e.name} 地铁站 换乘 {next_l.name}\n"
        )

    l, d, c, s, e = route_lines[-1]
    output.append(
        f"{s.name} 地铁站 \n↓ {l.name} {d} 方向 乘坐 {c} 站\n"
        f"{dest.name} 地铁站\n"
    )

    if end_distance != 0:
        output.append(f"由 {dest.name} 地铁站出站\n↓步行 {end_distance:.2f} 米\n目的地")
    else:
        output.append(f"由 {dest.name} 地铁站出站")

    total_walk_distance = start_distance + end_distance
    if total_walk_distance != 0:
        output.append(
            f"总计步行距离约 {total_walk_distance:.2f} 米，乘车约 {distance:.0f} 米。")
    else:
        output.append(f"总计乘车约 {distance:.0f} 米。")
    return "\n".join(output)
