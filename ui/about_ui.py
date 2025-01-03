# about_ui.py
import tkinter as tk
import webbrowser
from functools import partial
from tkinter import ttk, messagebox

from PIL import Image, ImageTk

from functions import func_update, subfunc_file
from resources import Config, Strings, Constants
from ui import update_log_ui
from utils import hwnd_utils, widget_utils


class Direction:
    def __init__(self, initial=1):
        self.value = initial


def open_url(url):
    if url is None or url == "":
        return
    webbrowser.open_new(url)


class AboutWindow:
    def __init__(self, root, parent, wnd, need_to_update):
        self.root = root
        self.parent = parent
        self.wnd = wnd
        self.wnd.title("关于")
        self.width, self.height = Constants.ABOUT_WND_SIZE
        hwnd_utils.bring_wnd_to_center(self.wnd, self.width, self.height)
        self.wnd.protocol("WM_DELETE_WINDOW", self.on_close)

        # 禁用窗口大小调整
        self.wnd.resizable(False, False)

        # 移除窗口装饰并设置为工具窗口
        self.wnd.attributes('-toolwindow', True)
        self.wnd.grab_set()

        self.main_frame = ttk.Frame(self.wnd, padding=Constants.FRM_PAD)
        self.main_frame.pack(**Constants.FRM_PACK)

        # 图标框架（左框架）
        logo_frame = ttk.Frame(self.main_frame, padding=Constants.L_FRM_PAD)
        logo_frame.pack(**Constants.L_FRM_PACK)

        # 内容框架（右框架）
        content_frame = ttk.Frame(self.main_frame, padding=Constants.R_FRM_PAD)
        content_frame.pack(**Constants.R_FRM_PACK)

        # 加载并调整图标
        try:
            icon_image = Image.open(Config.PROJ_ICO_PATH)
            icon_image = icon_image.resize(Constants.LOGO_SIZE, Image.LANCZOS)
            self.icon_photo = ImageTk.PhotoImage(icon_image)
        except Exception as e:
            print(f"无法加载图标图片: {e}")
            # 如果图标加载失败，仍然继续布局
            self.icon_photo = ImageTk.PhotoImage(Image.new('RGB', Constants.LOGO_SIZE, color='white'))
        icon_label = ttk.Label(logo_frame, image=self.icon_photo)
        icon_label.image = self.icon_photo
        icon_label.pack(**Constants.T_WGT_PACK)

        # 顶部：标题和版本号框架
        title_version_frame = ttk.Frame(content_frame)
        title_version_frame.pack(**Constants.T_FRM_PACK)

        # 标题和版本号标签
        current_full_version = subfunc_file.get_app_current_version()
        title_version_label = ttk.Label(
            title_version_frame,
            text=f"微信多开管理器 {current_full_version}",
            style='FirstTitle.TLabel',
        )
        title_version_label.pack(anchor='sw', **Constants.T_WGT_PACK, ipady=Constants.IPAD_Y)

        # 开发者主页
        author_label = ttk.Label(content_frame, text="by 吾峰起浪", style='SecondTitle.TLabel')
        author_label.pack(anchor='sw', **Constants.T_WGT_PACK)
        author_grids = ttk.Frame(content_frame)
        author_grids.pack(**Constants.T_FRM_PACK)
        row = 0
        for idx, (text, url) in enumerate(Strings.AUTHOR.items()):
            link = ttk.Label(author_grids, text=text,
                             style="Link.TLabel", cursor="hand2")
            link.grid(row=row, column=idx, **Constants.W_GRID_PACK)
            # 绑定点击事件
            link.bind("<Button-1>", lambda event, url2open=url: open_url(url2open))

        # 项目信息
        proj_label = ttk.Label(content_frame, text="项目信息", style='SecondTitle.TLabel')
        proj_label.pack(anchor='sw', **Constants.T_WGT_PACK)
        proj_grids = ttk.Frame(content_frame)
        proj_grids.pack(**Constants.T_FRM_PACK)
        row = 0
        for idx, (text, url) in enumerate(Strings.PROJ.items()):
            link = ttk.Label(proj_grids, text=text,
                             style="Link.TLabel", cursor="hand2")
            link.grid(row=row, column=idx, **Constants.W_GRID_PACK)
            # 绑定点击事件
            link.bind("<Button-1>", lambda event, url2open=url: open_url(url2open))

        # 鸣谢
        thanks_label = ttk.Label(content_frame, text="鸣谢", style='SecondTitle.TLabel')
        thanks_label.pack(anchor='sw', **Constants.T_WGT_PACK)
        thanks_grids = ttk.Frame(content_frame)
        thanks_grids.pack(**Constants.T_FRM_PACK)
        for idx, (person, info) in enumerate(Strings.THANKS.items()):
            link = ttk.Label(thanks_grids, text=info.get('text', None),
                             style="Link.TLabel", cursor="hand2")
            row = idx // 6
            column = idx % 6
            link.grid(row=row, column=column, **Constants.W_GRID_PACK)
            # 绑定点击事件
            link.bind(
                "<Button-1>",
                lambda
                    event,
                    bilibili=info.get('bilibili', None),
                    github=info.get('github', None),
                    pj=info.get('52pj', None):
                (
                    open_url(bilibili),
                    open_url(github),
                    open_url(pj)
                )
            )

        # 技术参考
        reference_label = ttk.Label(content_frame, text="技术参考", style='SecondTitle.TLabel')
        reference_label.pack(anchor='w', **Constants.T_WGT_PACK)
        reference_frame = ttk.Frame(content_frame)
        reference_frame.pack(**Constants.T_FRM_PACK)
        reference_scrollbar = tk.Scrollbar(reference_frame)
        reference_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        reference_text = tk.Text(reference_frame, wrap=tk.WORD, font=("", Constants.LITTLE_FONTSIZE),
                                 height=12, bg=wnd.cget("bg"),
                                 yscrollcommand=reference_scrollbar.set, bd=0, highlightthickness=0)

        reference_text.insert(tk.END, '\n')
        reference_text.insert(tk.END, Strings.REFERENCE_TEXT)
        reference_text.insert(tk.END, '\n')

        widget_utils.add_hyperlink_events(reference_text, Strings.REFERENCE_TEXT)
        reference_text.config(state=tk.DISABLED)
        reference_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=Constants.GRID_PAD)
        reference_scrollbar.config(command=reference_text.yview)
        # 创建方向对象
        self.reference_scroll_direction = Direction(1)  # 初始方向为向下
        self.reference_scroll_tasks = []
        # 启动滚动任务
        widget_utils.auto_scroll_text(
            self.reference_scroll_tasks, self.reference_scroll_direction, reference_text, self.root
        )
        # 鼠标进入控件时取消所有任务
        reference_text.bind(
            "<Enter>",
            lambda event: [
                              self.root.after_cancel(task) for task in self.reference_scroll_tasks
                          ] and self.reference_scroll_tasks.clear()
        )
        # 鼠标离开控件时继续滚动，保留当前方向
        reference_text.bind(
            "<Leave>",
            lambda event: widget_utils.auto_scroll_text(
                self.reference_scroll_tasks, self.reference_scroll_direction, reference_text, self.root
            )
        )

        # 赞助
        sponsor_label = ttk.Label(content_frame, text="赞助", style='SecondTitle.TLabel')
        sponsor_frame = ttk.Frame(content_frame)
        sponsor_label.pack(anchor='w', **Constants.T_WGT_PACK)
        sponsor_frame.pack(**Constants.T_FRM_PACK)
        sponsor_scrollbar = tk.Scrollbar(sponsor_frame)
        sponsor_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        sponsor_text = tk.Text(sponsor_frame, wrap=tk.WORD, font=("", Constants.LITTLE_FONTSIZE),
                               height=5, bg=wnd.cget("bg"), foreground='grey',
                               yscrollcommand=sponsor_scrollbar.set, bd=0, highlightthickness=0)

        sponsor_list = Strings.SPONSOR_TEXT
        sponsor_list_lines = []
        for idx, item in enumerate(sponsor_list):
            date = sponsor_list[idx].get('date', None)
            currency = sponsor_list[idx].get('currency', None)
            amount = sponsor_list[idx].get('amount', None)
            user = sponsor_list[idx].get('user', None)
            sponsor_list_lines.append(f"• {date}  {currency}{amount}  {user}")
        sponsor_text.insert(tk.END, '\n')
        sponsor_text.insert(tk.END, '\n'.join(sponsor_list_lines))
        sponsor_text.insert(tk.END, '\n')
        sponsor_text.config(state=tk.DISABLED)
        sponsor_text.pack(side=tk.LEFT, fill=tk.X, expand=False, padx=Constants.GRID_PAD)
        sponsor_scrollbar.config(command=sponsor_text.yview)
        # 创建方向对象
        self.sponsor_scroll_direction = Direction(1)  # 初始方向为向下
        self.sponsor_scroll_tasks = []
        # 启动滚动任务
        widget_utils.auto_scroll_text(
            self.sponsor_scroll_tasks, self.sponsor_scroll_direction, sponsor_text, self.root
        )
        # 鼠标进入控件时取消所有任务
        sponsor_text.bind(
            "<Enter>",
            lambda event: [
                self.root.after_cancel(task) for task in self.sponsor_scroll_tasks
            ]
        )
        # 鼠标离开控件时继续滚动，保留当前方向
        sponsor_text.bind(
            "<Leave>",
            lambda event: widget_utils.auto_scroll_text(
                self.sponsor_scroll_tasks, self.sponsor_scroll_direction, sponsor_text, self.root
            )
        )

        # 底部区域=声明+检查更新按钮
        bottom_frame = ttk.Frame(content_frame)
        bottom_frame.pack(**Constants.B_FRM_PACK)

        surprise_sign = Strings.SURPRISE_SIGN
        prefix = surprise_sign if need_to_update is True else ""

        # 左边：声明框架
        disclaimer_frame = ttk.Frame(bottom_frame, padding=Constants.L_FRM_PAD)
        disclaimer_frame.pack(**Constants.L_FRM_PACK)
        # 右边：更新按钮
        update_button = ttk.Button(bottom_frame, text=f"{prefix}检查更新", style='Custom.TButton',
                                   command=partial(self.check_for_updates,
                                                   current_full_version=current_full_version))
        update_button.pack(side=tk.RIGHT)

        # 免责声明
        disclaimer_label = ttk.Label(disclaimer_frame, style="RedWarning.TLabel",
                                     text="仅供学习交流，严禁用于商业用途，请于24小时内删除")
        disclaimer_label.pack(**Constants.B_WGT_PACK)

        # 版权信息标签
        copyright_label = ttk.Label(
            disclaimer_frame,
            text="Copyright © 2024 吾峰起浪. All rights reserved.",
            style="LittleText.TLabel",
        )
        copyright_label.pack(**Constants.T_WGT_PACK)

    def check_for_updates(self, current_full_version):
        subfunc_file.force_fetch_remote_encrypted_cfg()
        success, result = func_update.split_vers_by_cur_from_local(current_full_version)
        if success is True:
            new_versions, old_versions = result
            if len(new_versions) != 0:
                update_log_window = tk.Toplevel(self.wnd)
                update_log_ui.UpdateLogWindow(self.root, self.wnd, update_log_window, old_versions, new_versions)
            else:
                messagebox.showinfo("提醒", f"当前版本{current_full_version}已是最新版本。")
                return True
        else:
            messagebox.showinfo("错误", result)
            return False

    def on_close(self):
        """窗口关闭时执行的操作"""
        for task in self.reference_scroll_tasks:
            try:
                self.root.after_cancel(task)  # 取消滚动任务
            except Exception as e:
                print(f"Error cancelling task: {e}")

        for task in self.sponsor_scroll_tasks:
            try:
                self.root.after_cancel(task)  # 取消滚动任务
            except Exception as e:
                print(f"Error cancelling task: {e}")

        self.wnd.destroy()  # 关闭窗口
        if self.parent != self.root:
            self.parent.grab_set()  # 恢复父窗口的焦点


if __name__ == '__main__':
    test_root = tk.Tk()
    about_window = AboutWindow(test_root, test_root, test_root, True)
    test_root.mainloop()
