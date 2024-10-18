import os
import argparse
import navigate
import json
import requests

from model import MetroMap

file_path = "metro_data.json"
tmp_file_path = "stationstmp.json"
metro_data_url = "https://gitee.com/brokenclouds03/dhwinf-metro-stations/raw/master/metro_data.json"
print_header = "[INF Metro Navigation] "
version = 0

# 测试一下新的文件结构


def load_metro_data(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        version = data.get("version")
        stations = data['stations']
        lines = data['lines']
        return version, stations, lines
    except FileNotFoundError:
        print(f"文件未找到: {file_path}")
        return 0, None, None
    except json.JSONDecodeError:
        print(f"文件格式错误: {file_path}")
        return 0, None, None


# 新格式文件的更新
def update_metro_data(url=metro_data_url):
    global version, stations, lines
    try:
        print(print_header + "正在检查更新地铁数据")
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
        version, *_ = load_metro_data(file_path)
        if version_tmp > version:
            old_version = version
            # 更新本地数据
            with open(file_path, 'w', encoding='utf-8') as file:
                json.dump(data, file, ensure_ascii=False, indent=4)
            print(print_header +
                  f"无本地文件，已下载版本为 {version_tmp} 的数据") if version == 0 else None
            version, stations, lines = load_metro_data(file_path)
            return f"完成版本更新：{old_version} -> {version}。"
        else:
            return f"当前版本与远程仓库版本一致，版本均为：{version_tmp}。"

    except requests.RequestException as e:
        print(f"请求出错: {e}")
        return "更新失败：请求出错"
    except json.JSONDecodeError:
        print("解析 JSON 出错")
        return "更新失败：解析 JSON 出错"


def list_stations(metro_map: MetroMap):
    print("All stations:")
    print("已启用的地铁站如下:", ' '.join([
        str(station.name)
        for station in metro_map.stations.values()
        if station.status == "enabled"
    ]))
    print("未启用的地铁站:", ' '.join([
        str(station.name)
        for station in metro_map.stations.values()
        if station.status == "disabled"
    ]))


if not os.path.exists(file_path):
    update_metro_data(metro_data_url)
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
        const=metro_data_url,
        type=str,
        help="更新地铁站数据，可选 URL"
    )

    # metro_map = MetroMap.from_dict(json.load(f))

    # Try loading from local data
    try:
        with open(file_path, 'r') as f:
            metro_map = MetroMap.from_dict(json.load(f))
    except FileNotFoundError:
        print("File not found")
        metro_map = None
    except Exception as e:
        print(f"An error occurred: {e}")
        metro_map = None

    args = parser.parse_args()
    # 解析 metro 可变参数
    if args.metro:
        print(Navigate.navigate_metro(*args.metro, file_path))
        return
    if args.liststation:
        if metro_map:
            list_stations(metro_map)
        else:
            print("No metro map loaded")
        return
    if args.update:
        update_url = args.update
        print(update_metro_data(update_url))
        return


if __name__ == "__main__":
    print_header = ""
    main()
