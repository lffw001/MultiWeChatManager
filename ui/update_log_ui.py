import os
import tempfile
import threading
import tkinter as tk
import uuid
from abc import ABC
from functools import partial
from tkinter import messagebox, ttk

from functions import func_update, subfunc_file
from public_class.reusable_widget import SubToolWnd
from resources import Constants
from utils import file_utils, sys_utils


class UpdateLogWnd(SubToolWnd, ABC):
    def __init__(self, wnd, title, old_versions, new_versions=None):
        self.log_text = None
        self.old_versions = old_versions
        self.new_versions = new_versions

        super().__init__(wnd, title)

    def initialize_members_in_init(self):
        self.wnd_width, self.wnd_height = Constants.UPDATE_LOG_WND_SIZE

    def set_wnd(self):
        self.wnd.resizable(False, False)
        self.wnd.title("版本日志" if not self.new_versions else "发现新版本")

    def load_content(self):
        new_versions = self.new_versions
        old_versions = self.old_versions

        main_frame = ttk.Frame(self.wnd, padding="5")
        main_frame.pack(fill="both", expand=True)

        # 更新日志(标题)
        log_label = ttk.Label(main_frame, text="更新日志", font=("", 11))
        log_label.pack(anchor='w', pady=(10, 0))

        print("显示更新日志")

        config_data = subfunc_file.read_remote_cfg_in_rules()
        if config_data is None:
            messagebox.showerror("错误", "无法获取远程配置文件")
            self.wnd.destroy()
            return

        global_info = config_data["global"]
        # 创建一个用于放置滚动文本框的框架
        log_frame = ttk.Frame(main_frame)
        log_frame.pack(pady=(5, 0), fill=tk.BOTH, expand=True)

        # 创建滚动条
        scrollbar = tk.Scrollbar(log_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 创建不可编辑且可滚动的文本框
        self.log_text = tk.Text(log_frame, wrap=tk.WORD, font=("", 10), height=6, bg=self.wnd.cget("bg"),
                                yscrollcommand=scrollbar.set, bd=0, highlightthickness=0)

        # 需要显示新版本
        if new_versions:
            try:
                newest_version = file_utils.get_newest_full_version(new_versions)
                print(newest_version)
                curr_sys_ver_name = sys_utils.get_sys_major_version_name()
                curr_sys_newest_ver_dicts = global_info["update"][newest_version]["pkgs"][curr_sys_ver_name]
                bottom_frame = ttk.Frame(main_frame)
                bottom_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=20, pady=20)
                cancel_button = ttk.Button(bottom_frame, text="以后再说",
                                           command=lambda: self.root.destroy())
                cancel_button.pack(side=tk.RIGHT)
                download_button = ttk.Button(bottom_frame, text="下载新版",
                                             command=partial(self.show_download_window,
                                                             ver_dicts=curr_sys_newest_ver_dicts))
                download_button.pack(side=tk.RIGHT)
                # 说明
                information_label = ttk.Label(
                    bottom_frame,
                    text="发现新版本，是否下载？"
                )
                information_label.pack(side=tk.RIGHT, pady=(5, 0))

                self.log_text.insert(tk.END, "新版本：\n")
                for v in new_versions:
                    self.log_text.insert(tk.END, v + "：\n")

                    # 遍历每个分类（如"新增"、"修复"、"优化"等）
                    for category, logs in global_info["update"][v]["logs"].items():
                        self.log_text.insert(tk.END, f"#{category}：\n")
                        for log in logs:
                            self.log_text.insert(tk.END, f"-{log}\n")  # 在日志前添加适当的缩进
                        self.log_text.insert(tk.END, "\n")

                self.log_text.insert(tk.END, "\n\n旧版本：\n")
            except Exception as e:
                print(e)
                messagebox.showerror("错误", f"发生错误：{e}")

        try:
            for v in old_versions:
                self.log_text.insert(tk.END, v + "：\n")

                # 遍历每个分类（如"新增"、"修复"、"优化"等）
                for category, logs in global_info["update"][v]["logs"].items():
                    self.log_text.insert(tk.END, f"#{category}：\n")
                    for log in logs:
                        self.log_text.insert(tk.END, f"-{log}\n")  # 在日志前添加适当的缩进
                    self.log_text.insert(tk.END, "\n")

        except Exception as e:
            print(e)
            messagebox.showerror("错误", f"发生错误：{e}")

        # 设置文本框为不可编辑
        self.log_text.config(state=tk.DISABLED)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 配置滚动条
        scrollbar.config(command=self.log_text.yview)

    def show_download_window(self, ver_dicts, download_dir=None):
        def update_progress(idx, total_files, downloaded, total_length):
            try:
                percentage = (downloaded / total_length) * 100 if total_length else 0
                progress_var.set(f"下载文件 {idx + 1}/{total_files}: {percentage:.2f}% 完成")
                progress_bar['value'] = percentage
                self.root.update_idletasks()
            except Exception as e:
                print(e)

        def on_window_close():
            status["stop"] = True  # 更新状态为停止下载
            download_window.destroy()

        # 下载文件夹及下载路径的生成
        if download_dir is None:
            download_dir = tempfile.gettempdir()
        # 在路径中创建一个临时文件夹和临时文件路径
        download_path = os.path.join(tempfile.mkdtemp(dir=download_dir), f"{uuid.uuid4().hex}.zip")

        # 在下载文件夹中查找近期的文件夹
        recent_folders = file_utils.get_recent_folders_from_dir(download_dir)
        md5_list = [d.get("md5") for d in ver_dicts if "md5" in d]
        matched_file = subfunc_file.get_file_with_correct_md5(recent_folders, md5_list)

        if matched_file:
            download_path = matched_file

        status = {"stop": False}  # 定义状态字典

        # 创建窗口、设置进度条等 UI 元素
        download_window = tk.Toplevel(self.root)
        download_window.title("下载更新")
        window_width = 300
        window_height = 135
        # 计算窗口位置
        screen_width = download_window.winfo_screenwidth()
        screen_height = download_window.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        download_window.geometry(f"{window_width}x{window_height}+{x}+{y}")
        download_window.resizable(False, False)
        download_window.grab_set()

        progress_var = tk.StringVar(value="开始下载...")
        tk.Label(download_window, textvariable=progress_var).pack(pady=10)
        progress_bar = ttk.Progressbar(download_window, orient="horizontal", length=250, mode="determinate")

        # 关闭并更新按钮
        close_and_update_btn = ttk.Button(download_window, text="关闭并更新", style='Custom.TButton',
                                          command=partial(func_update.close_and_update, tmp_path=download_path))
        progress_bar.pack(pady=5)
        close_and_update_btn.pack(pady=5)
        close_and_update_btn.config(state="disabled")

        # 当用户关闭窗口时，设置`status["stop"]`为True
        download_window.protocol("WM_DELETE_WINDOW", on_window_close)  # 绑定窗口关闭事件

        if matched_file:
            print(f"找到匹配的文件: {matched_file}")
            progress_var.set(f"您近期已经完成下载！")
            progress_bar['value'] = 100
            close_and_update_btn.config(state="normal")
            self.root.update_idletasks()
        else:
            print("没有找到匹配的文件")
            # 开始下载文件（多线程）
            t = threading.Thread(target=func_update.download_files,
                                 args=(ver_dicts, download_path, update_progress,
                                       lambda: close_and_update_btn.config(state="normal"), status))
            t.start()
