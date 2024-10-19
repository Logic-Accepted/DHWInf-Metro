import argparse
import json
import logging
import navigate
import os
import requests


from model import MetroMap

file_path = "metro_data.json"
tmp_file_path = "stationstmp.json"
metro_data_url = ("https://gitee.com/brokenclouds03/dhwinf-metro-stations"
                  "/raw/master/metro_data.json")
print_header = "[INF Metro Navigation] "
version = 0
MAP = None
LOG_LEVEL = logging.WARNING


def load_metro_data(file_path=file_path) -> MetroMap:
    """
    Will raise exceptions, set global `MAP` and return it.
    """

    global MAP

    with open(file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
        MAP = MetroMap.from_dict(data)
        return MAP


def update_metro_data(url=metro_data_url):
    """新格式文件的更新"""

    global MAP
    try:
        print(print_header + "正在检查更新地铁数据")
        # 下载 JSON 文件
        response = requests.get(url)
        response.raise_for_status()  # 检查请求是否成功

        # 解析 JSON 数据
        remote_data = response.json()
        remote_data_raw = json.loads(response.text)
        remote_data = MetroMap.from_dict(remote_data_raw)

        # 比较版本号
        try:
            local_data = load_metro_data()
        except Exception as e:
            print(f"An error occurred: {e}")
            local_data = None

        if local_data is None:
            print(print_header +
                  f"无本地文件，已下载版本为 {remote_data.version} 的数据")
            with open(file_path, 'w', encoding='utf-8') as file:
                json.dump(remote_data_raw, file, ensure_ascii=False, indent=4)
            MAP = remote_data
            return "无本地文件，已下载最新数据。"
        if remote_data.version.data_ver > local_data.version.data_ver:
            # 更新本地数据
            with open(file_path, 'w', encoding='utf-8') as file:
                json.dump(remote_data_raw, file, ensure_ascii=False, indent=4)
            MAP = remote_data
            return (f"完成版本更新：{local_data.version.data_ver}"
                    " -> {remote_data.version.data_ver}。")
        else:
            return ("当前版本与远程仓库版本一致，"
                    f"版本均为：{remote_data.version.data_ver}。")

    except requests.RequestException as e:
        print(f"请求出错: {e}")
        return "更新失败：请求出错"
    except json.JSONDecodeError:
        print("解析 JSON 出错")
        return "更新失败：解析 JSON 出错"


def list_stations(metro_map: MetroMap | None = MAP) -> str:
    if metro_map is None:
        return "No metro map loaded"
    res: str = ""
    res += "已启用的地铁站如下:" + ' '.join([
        str(station.name)
        for station in metro_map.stations.values()
        if station.status == "enabled"
    ])
    res += "未启用的地铁站:" + ' '.join([
        str(station.name)
        for station in metro_map.stations.values()
        if station.status == "disabled"
    ])
    return res


update_metro_data(metro_data_url)
if os.path.exists(tmp_file_path):
    os.remove(tmp_file_path)


logger = logging.getLogger(__name__)


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

    parser.add_argument(
        "--debug",
        action="store_true",
        help="开启调试模式"
    )

    # metro_map = MetroMap.from_dict(json.load(f))

    # Try loading from local data
    try:
        load_metro_data()
    except FileNotFoundError:
        print("File not found")
    except Exception as e:
        print(f"An error occurred: {e}")

    args = parser.parse_args()
    # 解析 metro 可变参数
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    if args.metro:
        print(navigate.navigate_metro(*args.metro))
        return
    if args.liststation:
        print(list_stations())
        return
    if args.update:
        update_url = args.update
        print(update_metro_data(update_url))
        return


if __name__ == "__main__":
    print_header = ""
    main()
