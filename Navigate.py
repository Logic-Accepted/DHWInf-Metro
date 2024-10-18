import metro, math, heapq

# 计算两个坐标之间的欧氏距离,用于粗略计算步行距离
def calculate_distance_coords(coord1, coord2):
    x1, z1 = coord1
    x2, z2 = coord2
    distance = math.sqrt((x1 - x2) ** 2 + (z1 - z2) ** 2)
    return distance

# 计算两个坐标之间的曼哈顿距离，用于粗略计算站间距离
def calculate_manhattan_distance(coord1, coord2):
    x1, z1 = coord1
    x2, z2 = coord2
    distance = abs(x1 - x2) + abs(z1 - z2)
    return distance

# 计算站点间的距离
def calculate_distance(stations, station1, station2):
    return calculate_manhattan_distance(stations[station1], stations[station2])

# 根据坐标找到最近的地铁站
def find_nearest_station(coord, stations):
    nearest_station = None
    min_distance = float('inf')
    for station, station_coord in stations.items():
        distance = calculate_distance_coords(coord, station_coord)
        if distance < min_distance:
            min_distance = distance
            nearest_station = station
    return nearest_station, min_distance

# 构建带路线信息的图
def build_graph(stations, lines):
    graph = {station: [] for station in stations}
    for line_name, line in lines.items():  # 加入线路名称
        for i in range(len(line) - 1):
            station1 = line[i]
            station2 = line[i + 1]
            distance = calculate_distance(stations, station1, station2)
            # 除了距离外，还要记录该段的线路名称
            graph[station1].append((distance, station2, line_name))
            graph[station2].append((distance, station1, line_name))
    return graph

# Dijkstra最短路,增加路线跟踪
def dijkstra(graph, start, end):
    pq = [(0, start, [], [])]  # (cost, current_station, path, line_path)
    visited = set()

    while pq:
        cost, current_station, path, line_path = heapq.heappop(pq)
        if current_station in visited:
            continue
        visited.add(current_station)

        path = path + [current_station]

        if current_station == end:
            return path, line_path, cost

        for distance, neighbor, line_name in graph[current_station]:
            if neighbor not in visited:
                heapq.heappush(pq, (cost + distance, neighbor, path, line_path + [line_name]))

    return None, None, float('inf')

# 判断乘车方向
def determine_direction(current_station, next_station, line, lines):
    try:
        current_index = lines[line].index(current_station)
        next_index = lines[line].index(next_station)
    except ValueError:
        return "parameter error: station not on line"

    if next_index > current_index:
        return lines[line][-1]  # 终点站方向
    elif next_index < current_index:
        return lines[line][0]  # 起点站方向
    else:
        return "parameter error: not move"

# 把坐标试着转化成 int
def soft_int_assert(value):
    try:
        return int(value)
    except (ValueError, TypeError):
        return value

# 导航逻辑实现
def navigate_metro(*args):
    # 通过本地文件读入信息
    _, stations, lines, linesCode = Metro.load_station_data(Metro.file_path)
    args = tuple(map(soft_int_assert, args[:-1]))
    # 传入四个参数，处理为四个坐标
    if len(args) == 4:
        x_start, z_start, x_des, z_des = args
        current_coords = (x_start, z_start)
        destination_coords = (x_des, z_des)
        start_station, start_distance = find_nearest_station(current_coords, stations)
        end_station, end_distance = find_nearest_station(destination_coords, stations)

    # 传入两个参数，处理为两个站名
    elif len(args) == 2 and isinstance(args[0], str) and isinstance(args[1], str):
        start_station, end_station = args
        start_distance = 0
        end_distance = 0

    # 传入三个参数，站名+2坐标
    elif len(args) == 3 and isinstance(args[0], str):
        start_station = args[0]
        x_des, z_des = args[1], args[2]
        destination_coords = (x_des, z_des)
        start_distance = 0
        end_station, end_distance = find_nearest_station(destination_coords, stations)

    # 传入三个参数，2坐标+站名
    elif len(args) == 3 and isinstance(args[2], str):
        x_start, z_start = args[0], args[1]
        end_station = args[2]
        current_coords = (x_start, z_start)
        end_distance = 0
        start_station, start_distance = find_nearest_station(current_coords, stations)

    else:
        return "不支持的参数格式"
    
    #构建图
    graph = build_graph(stations, lines)
    
    # 找离当前坐标和目的地最近的地铁站
    if(start_station != end_station):
        # 计算最短路径
        route, lineList, total_distance = dijkstra(graph, start_station, end_station)
        # 格式化输出
        formatted_output = format_route_output(route, lineList, start_distance, end_distance, total_distance, linesCode, lines)
        return formatted_output
    elif(start_distance <= 50):
        return "当前位置距离目的地距离极近，暂无乘车方案。"
    elif(start_distance >= 20000):
        return "当前位置距离地铁系统极远，暂无乘车方案。"
    else:
        return "暂无乘车方案。"
    
# 格式化输出
def format_route_output(route, lineList, start_distance = 0, end_distance = 0, total_distance = None, linesCode = None, lines = None):
    output = []
    output.append(f"路线为：")
    current_line = lineList[0]
    first_station = route[0]
    if start_distance != 0:
        output.append(f"当前位置\n↓步行{start_distance:.2f}米\n{route[0]}地铁站 进站\n")
    else:
        output.append(f"{first_station}地铁站 进站\n")

    stationsum = 0

    for i in range(1, len(route)):
        if lineList[i - 1] == current_line:
            stationsum += 1
        else:
            direction = determine_direction(route[i-2], route[i-1], current_line, lines)
            output.append(f"{first_station}地铁站 \n↓{linesCode[current_line][0]}{direction}方向 乘坐{stationsum}站\n{route[i-1]}地铁站 换乘{linesCode[lineList[i-1]][0]}\n ")
            current_line = lineList[i-1]
            first_station = route[i-1]
            stationsum = 1

    # 最后一段
    direction = determine_direction(route[-1-1], route[-1], lineList[-1], lines)
    output.append(f"{first_station}地铁站 \n↓{linesCode[current_line][0]}{direction}方向 乘坐{stationsum}站\n{route[-1]}地铁站\n")
    if end_distance != 0:
        output.append(f"由{route[-1]}地铁站出站\n↓步行{end_distance:.2f}米\n目的地")
    else: 
        output.append(f"由{route[-1]}地铁站出站")
    total_walk_distance = start_distance + end_distance
    if total_walk_distance != 0:
        output.append(f"总计步行距离约{total_walk_distance:.2f}米，乘车约{total_distance:.0f}米。")
    else:
        output.append(f"总计乘车约{total_distance:.0f}米。")
    return "\n".join(output)