import os
import subprocess

commands = [
    ["python", "metro.py", "--metro", "100", "200", "300", "400"],
    ["python", "metro.py", "--metro", "100", "200", "喵喵神社"],
    ["python", "metro.py", "--metro", "喵喵神社", "100", "200"],
    ["python", "metro.py", "--metro", "喵喵神社", "主城"],
    ["python", "metro.py", "--liststation"],
    ["python", "metro.py", "--update"]
]

error_log = []

def run_commands():
    '''运行命令并且捕获异常'''
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
    '''删除数据文件'''
    if os.path.exists("metro_data.json"):
        os.remove("metro_data.json")


run_commands() #测试直接运行

for command in commands:
    try:
        #测试在没有数据文件的情况下运行
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
