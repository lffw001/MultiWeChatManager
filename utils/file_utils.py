import hashlib
import os
import platform
import re
import datetime as dt
# from datetime import datetime

import win32api


def get_recent_folders_from_dir(directory, minutes=360):
    now = dt.datetime.now()
    some_minutes_ago = now - dt.timedelta(minutes=minutes)
    recent_folders = []
    for item in os.listdir(directory):
        item_path = os.path.join(directory, item)
        if os.path.isdir(item_path):
            modification_time = dt.datetime.fromtimestamp(os.path.getmtime(item_path))
            if modification_time >= some_minutes_ago:
                recent_folders.append(item_path)
    return recent_folders


def calculate_md5(file_path, chunk_size=4096):
    """计算文件的 MD5 哈希值"""
    md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            md5.update(chunk)
    return md5.hexdigest()


def is_latest_file(file_path):
    # 获取文件的修改时间（时间戳）
    modification_time = os.path.getmtime(file_path)
    # 转换为日期格式
    modification_date = dt.datetime.fromtimestamp(modification_time).date()
    # 获取今天的日期
    today = dt.datetime.now().date()

    return modification_date >= today


def find_dir(start_dir, dirname):
    """递归查找指定文件"""
    for root, dirs, files in os.walk(start_dir):
        if dirname in dirs:
            return os.path.join(root, dirname)
    return None


def find_file(start_dir, filename):
    """递归查找指定文件"""
    for root, dirs, files in os.walk(start_dir):
        if filename in files:
            return os.path.join(root, filename)
    return None


def get_file_version(file_path):
    version_info = win32api.GetFileVersionInfo(file_path, '\\')  # type: ignore
    version = (
        f"{win32api.HIWORD(version_info['FileVersionMS'])}."  # type: ignore
        f"{win32api.LOWORD(version_info['FileVersionMS'])}."  # type: ignore
        f"{win32api.HIWORD(version_info['FileVersionLS'])}."  # type: ignore
        f"{win32api.LOWORD(version_info['FileVersionLS'])}"  # type: ignore
    )
    return version


def extract_version(folder):
    matches = re.compile(r'(\d+(?:\.\d+){0,4})').findall(folder)  # 找到所有匹配的版本号
    if matches:
        # 取最右边的版本号
        version_str = matches[-1]
        version_parts = list(map(int, version_str.split(".")))

        # 如果版本号不足 4 位，补足 0；如果超过 4 位，只取前 4 位
        while len(version_parts) < 4:
            version_parts.append(0)
        key = version_parts[:4]  # 使用 4 个数字的版本号作为key
        # print(key)
        return key
    return [0, 0, 0, 0]  # 如果没有匹配到版本号，默认返回0.0.0.0


def get_newest_full_version_dir(versions):
    # 找到最大版本号的文件夹
    max_version_dir = max(versions, key=extract_version).replace('\\', '/')
    print(max_version_dir)
    return max_version_dir


def get_newest_full_version(versions):
    # 找到最大版本号的文件夹
    # print(versions)
    max_full_version = max(versions, key=extract_version)
    # print(max_full_version)
    return max_full_version


def get_sorted_full_versions(versions):
    # 按版本号排序
    sorted_versions = sorted(versions, key=extract_version, reverse=True)
    # 返回按版本号排序的文件夹列表
    return sorted_versions


def get_sys_major_version_name():
    major_version = platform.release()
    if major_version == "7":
        print("当前系统是 Windows 7")
        return "win7"
    elif major_version == "10":
        print("当前系统是 Windows 10")
        return "win10"
    elif major_version == "11":
        print("当前系统是 Windows 11")
        return "win11"
    else:
        print("当前不是 Windows 7、10 或 11")
        return "default"


if __name__ == '__main__':
    md5 = calculate_md5(r'E:\Now\Desktop\MultiWeChatManager_win7_x64_v2.8.7.668-Alpha.zip')
    print(md5)
