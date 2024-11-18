import argparse
import ctypes
import logging
import os
import shutil
import subprocess
import sys
import threading
import time
import tkinter as tk
import zipfile
from tkinter import ttk, messagebox

import colorlog

CREATE_NO_WINDOW = 0x08000000


class LoggerUtils:
    def __init__(self, file):
        self.logger = self.get_logger(file)

    @staticmethod
    def get_logger(file):
        # 定log输出格式，配置同时输出到标准输出与log文件，返回logger这个对象
        log_colors_config = {
            # 终端输出日志颜色配置
            'DEBUG': 'white',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'bold_red',
        }

        default_formats = {
            # 终端输出格式
            'color_format':
                '%(log_color)s%(levelname)s - %(asctime)s - %(filename)s[line:%(lineno)d] - %(message)s',
            # 日志输出格式
            'log_format': '%(levelname)s - %(asctime)s - %(filename)s[line:%(lineno)d] - %(message)s'
        }

        logger = logging.getLogger('mylogger')
        logger.setLevel(logging.DEBUG)
        fh_log_format = logging.Formatter(default_formats["log_format"])
        ch_log_format = colorlog.ColoredFormatter(default_formats["color_format"], log_colors=log_colors_config)

        # 创建文件处理器
        log_fh = logging.FileHandler(file)
        log_fh.setLevel(logging.DEBUG)
        log_fh.setFormatter(fh_log_format)
        logger.addHandler(log_fh)
        # 创建控制台处理器
        log_ch = logging.StreamHandler()
        log_ch.setFormatter(ch_log_format)
        log_ch.setLevel(logging.DEBUG)
        logger.addHandler(log_ch)

        return logger


app_path = os.path.basename(os.path.abspath(sys.argv[0]))
log_file = app_path.split('.')[0] + '.log'
logger = LoggerUtils.get_logger(log_file)


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


def elevate():
    if ctypes.windll.shell32.IsUserAnAdmin():
        return True
    else:
        try:
            hinstance = ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, " ".join(sys.argv), None, 1
            )
            if hinstance <= 32:
                return False
            return True
        except Exception as e:
            print(e)
            return False


def is_admin():
    """检查当前进程是否具有管理员权限。"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except AttributeError:
        # 非 Windows 系统，默认返回 True
        return os.geteuid() == 0


def quit_main():
    if getattr(sys, 'frozen', False):
        # 查找进程ID并结束进程
        subprocess.run(["taskkill", "/f", "/im", "微信多开管理器.exe"], stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE, creationflags=CREATE_NO_WINDOW)
        logger.info("已结束 '微信多开管理器.exe'")


def update_and_reopen(args, root):
    # 提取参数
    before_version = args.before_version
    install_dir = args.install_dir
    download_path = args.download_path

    version_dir = os.path.join(install_dir, f"[{before_version}]")
    os.makedirs(version_dir, exist_ok=True)

    try:
        quit_main()
    except Exception as e:
        logger.error(f"结束进程时出错: {e}")
        messagebox.showerror("错误", f"非常抱歉！{e}，请手动关闭旧版程序后点确定！")
        quit_main()

    # 1. 解压下载的压缩包
    update_exe_path = sys.executable
    tmp_zip = download_path
    tmp_dir = os.path.dirname(update_exe_path)
    try:
        with zipfile.ZipFile(tmp_zip, 'r') as zip_ref:
            zip_ref.extractall(tmp_dir)
    except Exception as e:
        logger.error(e)
        messagebox.showerror("错误",
                             f"非常抱歉解压新版失败！{e}，将打开压缩文件所在目录和当前安装目录，稍后可手动解压替换，或稍后重试！")
        os.startfile(tmp_dir)
        os.startfile(install_dir)
        root.after(0, root.destroy)  # 安全销毁

    # 2. 拷贝 install_path 中的所有文件和文件夹（排除 “[xxx]” 文件夹）
    for item in os.listdir(install_dir):
        try:
            item_path = os.path.join(install_dir, item)
            if os.path.isdir(item_path) and item.startswith("[") and item.endswith("]"):
                continue  # 排除 "[xxx]" 文件夹
            # shutil.move(item_path, version_dir)  # 移动所有项目到目标文件夹
            if os.path.isdir(item_path):
                shutil.copytree(item_path, os.path.join(version_dir, item))
            if os.path.isfile(item_path):
                shutil.copy2(item_path, os.path.join(version_dir, item))
        except Exception as e:
            logger.error(e)
            messagebox.showerror("错误",
                                 f"非常抱歉备份旧版失败！{e}，\n"
                                 f"将打开压缩文件所在目录和当前安装目录，请备份好user文件夹后手动安装！")
            os.startfile(tmp_dir)
            os.startfile(install_dir)
            root.after(0, root.destroy)  # 安全销毁

    # 3. 拷贝并覆盖旧版 version 文件夹中的 user_files 文件夹到 新版本临时文件夹 中的 external_res 同级目录
    external_res_path = find_dir(tmp_dir, 'external_res')
    user_files_src = find_dir(version_dir, 'user_files')
    logger.info(external_res_path, user_files_src)
    if user_files_src is not None and external_res_path is not None:
        dest_path = os.path.join(os.path.dirname(external_res_path), 'user_files')
        if os.path.exists(dest_path):
            shutil.rmtree(dest_path)
        try:
            shutil.copytree(str(user_files_src), dest_path)
        except Exception as e:
            logger.error(e)
            messagebox.showerror("错误",
                                 f"非常抱歉迁移user_files失败，\n"
                                 f"将打开新版本临时目录和备份目录，请拷贝旧版user文件夹后手动安装！")
            os.startfile(os.path.dirname(external_res_path))
            os.startfile(version_dir)
            root.after(0, root.destroy)  # 安全销毁
    else:
        logger.error("未找到 external_res 文件夹或 user_files 文件夹。")
        messagebox.showerror("错误",
                             f"未找到 external_res 文件夹或 user_files 文件夹。\n"
                             f"将打开压缩文件所在目录和备份目录，请备份好user文件夹后手动安装！")
        os.startfile(tmp_dir)
        os.startfile(version_dir)
        root.after(0, root.destroy)  # 安全销毁

    # 4. 拷贝 tmp_dir 中 "微信多开管理器.exe" 所在的目录的所有文件和文件夹到 install_path 中并覆盖
    new_exe_path = find_file(tmp_dir, "微信多开管理器.exe")
    if new_exe_path is not None:
        exe_dir = os.path.dirname(new_exe_path)
        for item in os.listdir(exe_dir):
            item_path = os.path.join(exe_dir, item)
            target_path = os.path.join(install_dir, item)
            # 先删除
            try:
                if os.path.exists(target_path):
                    if os.path.isdir(target_path):
                        shutil.rmtree(target_path)  # 删除目标文件夹
                    else:
                        os.remove(target_path)  # 删除目标文件
            except Exception as e:
                logger.error(f"删除目录出错: {e}")
            # 再拷贝
            try:
                if os.path.isdir(item_path):
                    shutil.copytree(item_path, target_path)  # 拷贝文件夹
                else:
                    shutil.copy2(item_path, target_path)  # 拷贝文件
            except Exception as e:
                logger.error(f"拷贝错误: {e}")
    else:
        logger.error("未找到新版程序")
        messagebox.showerror("错误",
                             f"未找到新版程序，\n"
                             f"将打开压缩文件所在目录和备份目录，请备份好user文件夹后手动安装！")
        os.startfile(tmp_dir)
        os.startfile(version_dir)
        root.after(0, root.destroy)  # 安全销毁

    # 5. 启动 install_path 中的 "微信多开管理器.exe"
    wechat_exe_path = os.path.join(install_dir, "微信多开管理器.exe")
    if os.path.exists(wechat_exe_path):
        # os.startfile(wechat_exe_path)  # 在 Windows 上启动 exe 文件
        # 使用 subprocess 启动程序并添加参数
        subprocess.Popen([wechat_exe_path, "--new"])
        print("微信多开管理器已启动，参数: --new")
    else:
        logger.error("微信多开管理器.exe 不存在。")
        messagebox.showerror("错误",
                             f"未找到新版程序，\n"
                             f"将打开压缩文件所在目录和备份目录，请备份好user文件夹后手动安装！")
        os.startfile(tmp_dir)
        os.startfile(version_dir)
        root.after(0, root.destroy)  # 安全销毁

    # 在主线程中销毁窗口
    root.after(0, root.destroy)  # 安全销毁


def test_to_destroy(root):
    time.sleep(10)
    # 在主线程中销毁窗口
    root.after(0, root.destroy)  # 安全销毁


def main():
    # 设置环境变量，告诉 Python 不使用代理
    os.environ['http_proxy'] = ''
    os.environ['https_proxy'] = ''
    os.environ['no_proxy'] = '*'
    logger.error(f"是否管理员模式：{is_admin()}")
    # 创建参数解析器
    parser = argparse.ArgumentParser(description="Process command line flags.")
    # 添加 --debug 和 -d 选项
    parser.add_argument('--debug', '-d', action='store_true', help="Enable debug mode.")
    parser.add_argument("before_version", help="更新前版本号")
    parser.add_argument("install_dir", help="安装目录")
    parser.add_argument("download_path", help="下载路径")
    # 解析命令行参数
    args, unknown = parser.parse_known_args()

    root = tk.Tk()
    root.title("更新程序")

    # 打开升级程序窗口
    window_width = 300
    window_height = 100
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = (screen_width - window_width) // 2
    y = (screen_height - window_height) // 2
    root.geometry(f"{window_width}x{window_height}+{x}+{y}")
    # 禁用窗口大小调整
    root.resizable(False, False)
    # 移除窗口装饰并设置为工具窗口
    root.attributes('-toolwindow', True)
    root.grab_set()

    label = ttk.Label(root, text="正在升级，请勿关闭该窗口……")
    label.pack(pady=20)

    progress = ttk.Progressbar(root, mode="indeterminate", length=250)
    progress.pack(pady=10)

    progress.start(5)

    # 将更新和重启的操作放在一个线程中执行
    threading.Thread(target=update_and_reopen, args=(args, root)).start()
    # threading.Thread(target=test_to_destroy, args=(root,)).start()

    root.mainloop()
    logger.info("窗口已经关闭，才会执行下面")
    # sys.exit()


if __name__ == "__main__":
    if not is_admin():
        logger.warning("当前没有管理员权限，尝试获取...")
        if not elevate():
            logger.error("无法获得管理员权限，程序将退出。")
            sys.exit(1)
    else:
        logger.info("已获得管理员权限，正在执行主逻辑...")
        main()
