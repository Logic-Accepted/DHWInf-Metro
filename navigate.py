import metro
from model import Line


def soft_int_assert(value):
    """把坐标试着转化成 int"""
    try:
        return int(value)
    except (ValueError, TypeError):
        return value

# 导航逻辑实现


def navigate_metro(*args):
    if metro.MAP is None:
        metro.load_metro_data()
    data = metro.MAP
    args = tuple(map(soft_int_assert, args[:]))
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

    if start_station is None:
        return f"未知的起点站 {start_station}"
    if end_station is None:
        return f"未知的终点站 {end_station}"

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
    metro_map,
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

    route_lines = []

    def on_line(line: Line, *stations):
        last = None
        for station in stations:
            if station.id not in line.stations:
                return False
            if last is not None:
                if (station.id, last.id) not in line.routes and \
                        (last.id, station.id) not in line.routes:
                    return False
            last = station
        return True

    while len(route) > 1:
        stataion_count = len(route) - 1
        while True:
            for line in metro_map.lines.values():
                if on_line(line, *route[:stataion_count + 1]):
                    direction = line.find_dir(*route[:stataion_count + 1])
                    route_lines.append((line, direction, stataion_count))
                    route = route[stataion_count + 1:]
                    break
            else:
                stataion_count -= 1
                continue
            break

    for i in range(len(route_lines) - 1):
        l, d, c = route_lines[i]
        next_l = route_lines[i + 1][0]
        output.append(
            f"{first_station.name} 地铁站 \n↓ {l.name} {d} 方向 乘坐 {c} 站\n"
            f"{route[i-1]} 地铁站 换乘 {next_l.name}\n"
        )

    l, d, c = route_lines[-1]
    output.append(
        f"{first_station.name} 地铁站 \n↓ {l.name} {d} 方向 乘坐 {c} 站\n"
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
