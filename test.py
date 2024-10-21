import os
import subprocess
import random
from lib.metro import load_metro_data, MAP

error_log = []


def get_random_station():
    """用于产生随机站名"""
    if MAP is None:
        load_metro_data()
    data = MAP
    random_station = random.choice(list(data.stations.values())).name["zh"]
    return random_station


def get_random_coords():
    """用于随机抽选出某站的(x, z)坐标"""
    if MAP is None:
        load_metro_data()
    data = MAP
    random_coords = random.choice(list(data.stations.values())).location
    return random_coords


def get_random_coords_value():
    """用于随机选择坐标数值"""
    xandz = get_random_coords()
    return random.choice([xandz.x, xandz.z])


def generate_random_coords_as_str(num):
    """用于产生指定数量个随机坐标"""
    for _ in range(num):
        return str(get_random_coords_value())


def run_commands():
    """运行命令并且捕获异常"""
    for command in commands:
        try:
            print(f"Running command: {' '.join(command)}")
            result = subprocess.run(command, check=True)
            print(f"Command succeeded: {result}")
        except subprocess.CalledProcessError as e:
            error_log.append(f"Error running command: - {e}")
        except Exception as e:
            error_log.append(f"Unexpected error: {e}")


def delete_metro_data():
    """删除数据文件"""
    if os.path.exists("metro_data.json"):
        os.remove("metro_data.json")


# 构建 commands


commands = [
    ["python", "cli.py", "--metro"] + generate_random_coords_as_str(4),
    ["python", "cli.py", "--metro"]
    + generate_random_coords_as_str(2)
    + [get_random_station()],
    ["python", "cli.py", "--metro", get_random_station()]
    + generate_random_coords_as_str(2),
    ["python", "cli.py", "--metro", get_random_station(), get_random_station()],
    ["python", "cli.py", "--liststation"],
    ["python", "cli.py", "--update"],
]

run_commands()  # 测试直接运行

for command in commands:
    try:
        # 测试在没有数据文件的情况下运行
        delete_metro_data()
        print(f"Running command: {' '.join(command)}")
        result = subprocess.run(command, check=True)
        print(f"Command succeeded: {result}")
    except subprocess.CalledProcessError as e:
        error_log.append(f"Error running command: - {e}")
    except Exception as e:
        error_log.append(f"Unexpected error: {e}")

if error_log:
    print("\nErrors encountered:")
    for error in error_log:
        print(error)
else:
    print("All commands succeeded.")

input("Press Enter to continue...")
