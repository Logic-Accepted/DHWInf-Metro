import DataFileProcess

# 列出车站
def liststations():
    _, stations, *_ = DataFileProcess.load_station_data(DataFileProcess.file_path)
    stationlist = [station_name for station_name in stations.keys()]
    return f"所有地铁站名称如下：{' '.join(stationlist)}"