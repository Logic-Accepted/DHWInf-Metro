import logging
from typing import List, Tuple
from .metro import load_metro_data, MAP
from .model import Line, MetroMap, Station


logger = logging.getLogger(__name__)


def soft_int_assert(value):
    """把坐标试着转化成 int"""
    try:
        return int(value)
    except (ValueError, TypeError):
        return value

# 导航逻辑实现


def navigate_metro(*args):
    if MAP is None:
        load_metro_data()
    data = MAP
    args = tuple(map(soft_int_assert, args[:]))
    try:
        # 传入四个参数，处理为四个坐标
        if len(args) == 4:
            x_start, z_start, x_des, z_des = args
            current_coords = (x_start, z_start)
            destination_coords = (x_des, z_des)
            start_station, start_distance = data.find_nearest_station(
                current_coords)
            end_station, end_distance = data.find_nearest_station(
                destination_coords)

        # 传入两个参数，处理为两个站名
        elif len(args) == 2:
            start_station, end_station = args
            if type(start_station) is str and type(end_station) is str:
                start_station = data.stations[start_station]
                end_station = data.stations[end_station]
                start_distance = 0
                end_distance = 0
            else:
                return "不支持的参数格式"

        # 传入三个参数，站名+2坐标
        elif len(args) == 3 and isinstance(args[0], str):
            start_station = args[0]
            start_station = data.stations[start_station]
            x_des, z_des = args[1], args[2]
            destination_coords = (x_des, z_des)
            start_distance = 0
            end_station, end_distance = data.find_nearest_station(
                destination_coords)

        # 传入三个参数，2坐标+站名
        elif len(args) == 3 and isinstance(args[2], str):
            x_start, z_start = args[0], args[1]
            end_station = args[2]
            end_station = data.stations[end_station]
            current_coords = (x_start, z_start)
            end_distance = 0
            start_station, start_distance = data.find_nearest_station(
                current_coords)

        else:
            return "不支持的参数格式"
    except KeyError as e:
        return f"未知的车站: {str(e)}"

    nodes, distance = data.navi_graph.find_route(start_station, end_station)

    # TODO: 判断过近过远

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
