# 获取最新版本号
import os
import shutil
import subprocess
import sys
import zipfile
from tkinter import messagebox

import requests

from functions import subfunc_file
from resources import Config
from utils import file_utils


def split_versions_by_current(current_ver):
    try:
        config_data = subfunc_file.fetch_config_data()
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


def download_files(file_urls, download_dir, progress_callback, on_complete_callback):
    try:
        print("进入下载文件方法...")
        for idx, url in enumerate(file_urls):
            print(f"Downloading to {download_dir}")
            with requests.get(url, stream=True, allow_redirects=True) as r:
                r.raise_for_status()
                total_length = int(r.headers.get('content-length', 0))
                with open(download_dir, 'wb') as f:
                    downloaded = 0
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:  # 过滤掉保持连接的chunk
                            f.write(chunk)
                            downloaded += len(chunk)
                            progress_callback(idx, len(file_urls), downloaded, total_length)

        print("所有文件下载成功。")
        on_complete_callback()  # 调用回调启用按钮
        return True
    except Exception as e:
        print(e)
        raise e


def close_and_update(tmp_path):
    if getattr(sys, 'frozen', False):
        answer = messagebox.askokcancel("将关闭主程序进行更新操作，请确认")
        if answer:
            exe_path = sys.executable
            current_version = subfunc_file.get_app_current_version()
            install_dir = os.path.dirname(exe_path)

            update_exe_path = os.path.join(Config.PROJ_EXTERNAL_RES_PATH, 'update.exe')
            new_update_exe_path = os.path.join(os.path.dirname(tmp_path), 'update.exe')
            try:
                shutil.copy(update_exe_path, new_update_exe_path)
                print(f"成功将 {update_exe_path} 拷贝到 {new_update_exe_path}")
            except Exception as e:
                print(f"拷贝文件时出错: {e}")

            subprocess.Popen([new_update_exe_path, current_version, install_dir],
                             creationflags=subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS)
