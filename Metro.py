import os, argparse, Navigate, json, requests

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
        version, *_ = load_station_data(file_path)
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
    

# 列出车站
def liststations():
    _, stations, *_ = load_station_data(file_path)
    stationlist = [station_name for station_name in stations.keys()]
    return f"所有地铁站名称如下：{' '.join(stationlist)}"

if not os.path.exists(file_path):
        update_station_data(default_url)
        if os.path.exists(tmp_file_path):
                os.remove(tmp_file_path)

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
        print(Navigate.navigate_metro(*args.metro, file_path))
        return
    if args.liststation:
        print(liststations())
        return
    if args.update:
        update_url = args.update
        print(update_station_data(update_url))
        return

if __name__ == "__main__":
    print_header = ""
    main()
