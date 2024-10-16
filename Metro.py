import os, argparse, DataFileProcess, Navigate, ListStation

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
        const=DataFileProcess.default_url,
        type=str,
        help="更新地铁站数据，可选 URL"
    )
    
    args = parser.parse_args()
    # 解析 metro 可变参数
    if args.metro:
        print(Navigate.navigate_metro(*args.metro, DataFileProcess.file_path))
        return
    if args.liststation:
        print(ListStation.liststations())
        return
    if args.update:
        update_url = args.update
        print(DataFileProcess.update_station_data(update_url))
        return

if __name__ == "__main__":
    print_header = ""
    if not os.path.exists(DataFileProcess.file_path):
        DataFileProcess.update_station_data(DataFileProcess.default_url)
        if os.path.exists(DataFileProcess.tmp_file_path):
                os.remove(DataFileProcess.tmp_file_path)
    main()
