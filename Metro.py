import heapq, math, json, requests, os, shutil, argparse

# 检查文件是否存在，如果不存在则创建默认文件
def check_and_create_file(file_path):
    if not os.path.exists(file_path):
        # 创建文件并写入默认内容
        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump({}, file, ensure_ascii=False, indent=4)
        #print(f"创建文件: {file_path}")
        return 0
    else:
        return 1

# 从指定 URL 下载 JSON 并读取 version 信息
def update_station_data_from_remote(url, local_file, tmp_file_path):
    try:
        # 下载 JSON 文件
        response = requests.get(url)
        response.raise_for_status()  # 检查请求是否成功
        
        # 解析 JSON 数据
        data = response.json()
        
        # 读取 version 字段
        version = data.get("version")
        if version is not None:
            print("正在检查更新")
            check_and_create_file(tmp_file_path)
            # 保存到本地文件
            with open(local_file, 'w', encoding='utf-8') as file:
                json.dump(data, file, ensure_ascii=False, indent=4)
                # print(f"数据已保存到本地文件: {local_file}")
                return version
        else:
            # print("未找到 version 字段")
            return float('inf')*-1
        
    except requests.RequestException as e:
        print(f"请求出错: {e}")
    except json.JSONDecodeError:
        print("解析 JSON 出错")

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
        print(f"文件未找到: {file_path}")
        return None
    except json.JSONDecodeError:
        print(f"文件格式错误: {file_path}")
        return None

# 比较两个版本号，并决定是否覆盖文件
def update_if_newer(version, version_tmp, local_file, tmp_file):
    if version_tmp > version:
        # 用 stationstmp.json 覆盖 stations.json
        shutil.move(tmp_file, local_file)  # shutil.move 同时完成文件移动和覆盖
        return 1
    else:
        # 删除临时文件
        if os.path.exists(tmp_file):
            os.remove(tmp_file)
            return 0
        else:
            return 0

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
def calculate_distance(station1, station2, stations):
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
    return nearest_station,min_distance

# 构建带路线信息的图
def build_graph(stations, lines):
    graph = {station: [] for station in stations}
    for line_name, line in lines.items():  # 加入线路名称
        for i in range(len(line) - 1):
            station1 = line[i]
            station2 = line[i + 1]
            distance = calculate_distance(station1, station2, stations)
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

# 格式化输出
def format_route_output(route, lineList, start_distance, end_distance, total_distance, lines, linesCode):
    output = []
    output.append(f"路线为：")
    output.append(f"当前位置\n↓步行{start_distance:.2f}米\n{route[0]}地铁站 进站\n")

    stationsum = 0
    current_line = lineList[0]
    first_station = route[0]

    for i in range(1, len(route)):
        if lineList[i - 1] == current_line:
            stationsum += 1
        else:
            direction = determine_direction(route[i-2], route[i-1], current_line, lines)
            output.append(f"{first_station}地铁站 \n↓{direction}方向 乘坐{stationsum}站\n{route[i-1]}地铁站 换乘{linesCode[lineList[i-1]][0]}\n ")
            current_line = lineList[i-1]
            first_station = route[i-1]
            stationsum = 1

    # 最后一段
    direction = determine_direction(route[-1-1], route[-1], lineList[-1], lines)
    output.append(f"{first_station}地铁站 \n↓{direction}方向 乘坐{stationsum}站\n{route[-1]}地铁站\n")
    output.append(f"由{route[-1]}地铁站出站\n↓步行{end_distance:.2f}米\n目的地")
    total_walk_distance = start_distance + end_distance
    output.append(f"总计步行距离约{total_walk_distance:.2f}米，乘车约{total_distance:.0f}米。")
    return "\n".join(output)

# 导航逻辑实现
def navigate_metro(x_start, z_start, x_des, z_des, graph, lines, linesCode, stations):
    try:
        current_coords = (x_start, z_start)
        destination_coords = (x_des, z_des)
    except Exception as e:
        print("请检查输入数据。")

    # 找离当前坐标和目的地最近的地铁站
    start_station, start_distance = find_nearest_station(current_coords, stations)
    end_station, end_distance = find_nearest_station(destination_coords, stations)
  
    if(start_station != end_station):
        # 计算最短路径
        route, lineList, total_distance = dijkstra(graph, start_station, end_station)
        # 格式化输出
        formatted_output = format_route_output(route, lineList, start_distance, end_distance, total_distance, lines, linesCode)
        print(formatted_output)
    elif(start_distance <= 50):
        print("当前位置距离目的地距离极近，暂无乘车方案。")
    elif(start_distance >= 20000):
        print("当前位置距离地铁系统极远，暂无乘车方案。")
    else:
        print("暂无乘车方案。")

# 站点信息远程更新逻辑实现
def update_station_data(url, file_path, tmp_file_path, version):
    version_tmp = update_station_data_from_remote(url, file_path, tmp_file_path)
    update = update_if_newer(version, version_tmp, file_path, tmp_file_path)
    if update == 1:
        print(f"完成版本更新：{version} -> {version_tmp}。")
        version = version_tmp
    else: 
        print(f"当前版本与远程仓库版本一致，版本均为：{version_tmp}。")    

def first_load(file_path, url, tmp_file_path): 
    update_station_data_from_remote(url, file_path, tmp_file_path)
    if os.path.exists(tmp_file_path):
            os.remove(tmp_file_path)
    return 0

###################################################################################

def main():
    parser = argparse.ArgumentParser(description="DHW Inf地铁导航工具。")
    version, stations, lines, linesCode = load_station_data(file_path)

    parser.add_argument(
        "--metro",
        nargs=4,
        type=int,
        metavar=('X_START', 'Z_START', 'X_DES', 'Z_DES'),
        help="输入起点和终点坐标: X_START Z_START X_DES Z_DES"
    )

    parser.add_argument(
        "--update",
        nargs='?',
        const=url,
        type=str,
        help="更新地铁站数据，可选 URL"
    )
    
    args = parser.parse_args()
    if args.metro:
        x_start, z_start, x_des, z_des = args.metro
        navigate_metro(x_start, z_start, x_des, z_des, build_graph(stations, lines), lines, linesCode, stations)
        return
    if args.update:
        update_url = args.update
        update_station_data(update_url, file_path, tmp_file_path, version)
        return
    while True:
        # 如果没有传入 --metro 参数，则手动输入坐标
        print("请输入起点和终点坐标 (X_START Z_START X_DES Z_DES)，每个坐标用回车隔开：")
        x_start = int(input("X_START: "))
        z_start = int(input("Z_START: "))
        x_des = int(input("X_DES: "))
        z_des = int(input("Z_DES: "))
        # 执行地铁导航
        navigate_metro(x_start, z_start, x_des, z_des, build_graph(stations, lines), lines, linesCode, stations)
if __name__ == "__main__":
    file_path = "stations.json"  
    tmp_file_path = "stationstmp.json" 
    url = "https://gitee.com/brokenclouds03/dhwinf-metro-stations/raw/master/stations.json" 
    if not os.path.exists(file_path):    
            first_load(file_path, url, tmp_file_path)
    main()
