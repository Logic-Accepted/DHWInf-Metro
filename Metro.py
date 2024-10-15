import heapq, math, json, requests, os, shutil, argparse
file_path = "stations.json"  
tmp_file_path = "stationstmp.json" 
default_url = "https://gitee.com/brokenclouds03/dhwinf-metro-stations/raw/master/stations.json" 
print_header = "[INF Metro Navigation] "
version = 0

# 从本地 JSON 文件读取站点和线路数据
def load_station_data(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        
        # 读 version
        version = data.get("version")
        
        # stations数据要给坐标列表转换为元组
        for station, coord in data['stations'].items():
            data['stations'][station] = tuple(coord)
            stations = data['stations']  # 站点坐标
            lines = data['lines'] # 线路连接性信息
            linesCode = data['linesCode']  # 线路代号
        
        return version, stations, lines, linesCode
    except FileNotFoundError:
        print(print_header + f"文件未找到: {file_path}")
        return 0, None, None, None
    except json.JSONDecodeError:
        print(print_header + f"文件格式错误: {file_path}")
        return 0, None, None, None

# 站点信息远程更新逻辑实现
def update_station_data(url=default_url):
    global version, stations, lines, linesCode
    try:
        print(print_header + "正在检查更新")
        # 下载 JSON 文件
        response = requests.get(url)
        response.raise_for_status()  # 检查请求是否成功

        # 解析 JSON 数据
        data = response.json()

        # 读取 version 字段
        version_tmp = data.get('version')
        if version_tmp is None:
            print("未找到 version 字段")
            return "更新失败：未找到 version 字段"

        # 比较版本号
        if version_tmp > version:
            old_version = version
            # 更新本地数据
            with open(file_path, 'w', encoding='utf-8') as file:
                json.dump(data, file, ensure_ascii=False, indent=4)
            print(print_header + f"无本地文件，已下载版本为 {version_tmp} 的数据") if version == 0 else None
            version, stations, lines, linesCode = load_station_data(file_path)
            return f"完成版本更新：{old_version} -> {version}。"
        else:
            return f"当前版本与远程仓库版本一致，版本均为：{version_tmp}。"

    except requests.RequestException as e:
        print(f"请求出错: {e}")
        return "更新失败：请求出错"
    except json.JSONDecodeError:
        print("解析 JSON 出错")
        return "更新失败：解析 JSON 出错"

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
def calculate_distance(station1, station2):
    return calculate_manhattan_distance(stations[station1], stations[station2])

# 根据坐标找到最近的地铁站
def find_nearest_station(coord):
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
            distance = calculate_distance(station1, station2)
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
def determine_direction(current_station, next_station, line):
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

# 格式化输出
def format_route_output(route, lineList, start_distance = 0, end_distance = 0, total_distance = None, linesCode = None):
    output = []
    output.append(f"路线为：")
    if start_distance != 0:
        output.append(f"当前位置\n↓步行{start_distance:.2f}米\n{route[0]}地铁站 进站\n")
    else:
        output.append(f"{route[0]}地铁站 进站\n")

    stationsum = 0
    current_line = lineList[0]
    first_station = route[0]

    for i in range(1, len(route)):
        if lineList[i - 1] == current_line:
            stationsum += 1
        else:
            direction = determine_direction(route[i-2], route[i-1], current_line)
            output.append(f"{first_station}地铁站 \n↓{direction}方向 乘坐{stationsum}站\n{route[i-1]}地铁站 换乘{linesCode[lineList[i-1]][0]}\n ")
            current_line = lineList[i-1]
            first_station = route[i-1]
            stationsum = 1

    # 最后一段
    direction = determine_direction(route[-1-1], route[-1], lineList[-1])
    output.append(f"{first_station}地铁站 \n↓{direction}方向 乘坐{stationsum}站\n{route[-1]}地铁站\n")
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

# 导航逻辑实现
def navigate_metro(*args):
    args = tuple(map(soft_int_assert, args))
    # 传入四个参数，处理为四个坐标
    if len(args) == 4:
        x_start, z_start, x_des, z_des = args
        current_coords = (x_start, z_start)
        destination_coords = (x_des, z_des)
        start_station, start_distance = find_nearest_station(current_coords)
        end_station, end_distance = find_nearest_station(destination_coords)

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
        end_station, end_distance = find_nearest_station(destination_coords)

    # 传入三个参数，2坐标+站名
    elif len(args) == 3 and isinstance(args[2], str):
        x_start, z_start = args[0], args[1]
        end_station = args[2]
        current_coords = (x_start, z_start)
        end_distance = 0
        start_station, start_distance = find_nearest_station(current_coords)

    else:
        return "不支持的参数格式"
    
    #构建图
    graph = build_graph(stations, lines)
    
    # 找离当前坐标和目的地最近的地铁站
    if(start_station != end_station):
        # 计算最短路径
        route, lineList, total_distance = dijkstra(graph, start_station, end_station)
        # 格式化输出
        formatted_output = format_route_output(route, lineList, start_distance, end_distance, total_distance, linesCode)
        return formatted_output
    elif(start_distance <= 50):
        return "当前位置距离目的地距离极近，暂无乘车方案。"
    elif(start_distance >= 20000):
        return "当前位置距离地铁系统极远，暂无乘车方案。"
    else:
        return "暂无乘车方案。"
    
def soft_int_assert(value):
    try:
        return int(value)
    except (ValueError, TypeError):
        return value

def liststations():
    stationlist = [station_name for station_name in stations.keys()]
    return f"所有地铁站名称如下：{' '.join(stationlist)}"
 
###################################################################################

if not os.path.exists(file_path):
    update_station_data(default_url)
    if os.path.exists(tmp_file_path):
            os.remove(tmp_file_path)

version, stations, lines, linesCode = load_station_data(file_path)

def main():
    parser = argparse.ArgumentParser(description="DHW Inf地铁导航工具。")

    parser.add_argument(
        "--metro",
        nargs='+',
        metavar='METRO_ARGS',
        help="输入起点和终点坐标: 可以是两组坐标，也可以用站名代替任意一组坐标。"
    )

    parser.add_argument(
        "--liststation",
        action="store_true",
        help="列出所有地铁站名称"
    )

    parser.add_argument(
        "--update",
        nargs='?',
        const=default_url,
        type=str,
        help="更新地铁站数据，可选 URL"
    )
    
    args = parser.parse_args()
    # 解析 metro 可变参数
    if args.metro:
        print(navigate_metro(*args.metro))
        return
    if args.liststation:
        print(liststations(stations))
        return
    if args.update:
        update_url = args.update
        print(update_station_data(update_url))
        return

if __name__ == "__main__":
    print_header = ""
    main()
