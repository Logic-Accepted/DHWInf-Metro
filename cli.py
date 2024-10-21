import argparse
import logging

from lib.metro import (list_stations, load_metro_data,
                       metro_data_url, navigate, update_metro_data)


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
        # print(navigate.navigate_metro(*args.metro))
        print(navigate(*args.metro))
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
