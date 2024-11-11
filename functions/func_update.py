# 获取最新版本号
import json
import os
import shutil
import subprocess
import sys
from tkinter import messagebox

import requests

from functions import subfunc_file
from resources import Config
from utils import file_utils


def split_vers_by_cur_from_local(current_ver):
    try:
        with open(Config.VER_ADAPTATION_JSON_PATH, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        if not config_data:
            print("没有数据")
            return "错误：没有数据"
        else:
            # 获取 update 节点的所有版本
            all_versions = list(config_data["update"].keys())
            # 对版本号进行排序
            sorted_versions = file_utils.get_sorted_full_versions(all_versions)
            if len(sorted_versions) == 0:
                return [], []
            # 遍历 sorted_versions，通过 file_utils.get_newest_full_version 比较
            for i, version in enumerate(sorted_versions):
                if file_utils.get_newest_full_version([current_ver, version]) == current_ver:
                    # 如果找到第一个不高于 current_ver 的版本
                    lower_or_equal_versions = sorted_versions[i:]
                    higher_versions = sorted_versions[:i]
                    break
            else:
                # 如果没有找到比 current_ver 小或等于的版本，所有都更高
                higher_versions = sorted_versions
                lower_or_equal_versions = []
            return higher_versions, lower_or_equal_versions

    except Exception as e:
        print(f"发生错误：{str(e)}")
        return "错误：无法获取版本信息"


def download_files(ver_dicts, download_dir, progress_callback, on_complete_callback, status):
    try:
        print("进入下载文件方法...")
        for ver_dict in ver_dicts:
            if status.get("stop"):  # 检查停止状态
                print("下载被用户中断")
                return False
            url = ver_dict.get("url", "")
            if not url:
                print("URL为空，跳过此文件字典...")
                continue
            try:
                urls = [url]
                for idx, url in enumerate(urls):
                    print(f"Downloading to {download_dir}")
                    with requests.get(url, stream=True, allow_redirects=True) as r:
                        r.raise_for_status()
                        total_length = int(r.headers.get('content-length', 0))
                        with open(download_dir, 'wb') as f:
                            downloaded = 0
                            for chunk in r.iter_content(chunk_size=8192):
                                if status.get("stop"):  # 每次读取chunk都检查停止状态
                                    print("下载被用户中断")
                                    return False
                                if chunk:
                                    f.write(chunk)
                                    downloaded += len(chunk)
                                    progress_callback(idx, len(urls), downloaded, total_length)

                print("所有文件下载成功。")
                on_complete_callback()
                return True
            except Exception as e:
                print(f"从 {url} 下载失败, 错误: {e}")
        print("所有提供的URL下载失败。")
        return False
    except Exception as e:
        print(f"发生异常: {e}")
        raise e


def close_and_update(tmp_path):
    if getattr(sys, 'frozen', False):
        answer = messagebox.askokcancel("提醒", "将关闭主程序进行更新操作，请确认")
        if answer:
            exe_path = sys.executable
            current_version = subfunc_file.get_app_current_version()
            install_dir = os.path.dirname(exe_path)

            update_exe_path = os.path.join(Config.PROJ_EXTERNAL_RES_PATH, 'Updater.exe')
            new_update_exe_path = os.path.join(os.path.dirname(tmp_path), 'Updater.exe')
            try:
                shutil.copy(update_exe_path, new_update_exe_path)
                print(f"成功将 {update_exe_path} 拷贝到 {new_update_exe_path}")
            except Exception as e:
                print(f"拷贝文件时出错: {e}")
            subprocess.Popen([new_update_exe_path, current_version, install_dir, tmp_path],
                             creationflags=subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS)
    else:
        messagebox.showinfo("提醒", "请在打包环境中执行")
