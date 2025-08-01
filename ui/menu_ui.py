import os
import threading
import time
import tkinter as tk
import webbrowser
from functools import partial
from pathlib import Path
from tkinter import messagebox, simpledialog

from functions import subfunc_file
from functions.app_func import AppFunc
from functions.main_func import MultiSwFunc
from functions.sw_func import SwInfoFunc, SwOperator
from public_class.enums import LocalCfg, MultirunMode, RemoteCfg
from public_class.global_members import GlobalMembers
from resources import Strings, Config
from ui import sidebar_ui
from ui.wnd_ui import WndCreator
from utils import widget_utils
from utils.logger_utils import mylogger as logger, Printer
from utils.logger_utils import myprinter as printer
from utils.sys_utils import Tk2Sys


# TODO: 用户可以自定义多开的全流程
# TODO: 主题色选择

class MenuUI:
    def __init__(self):
        """获取必要的设置项信息"""
        self.coexist_menu = None
        self._to_tray_label = None
        self.used_tray = None
        self.sidebar_menu_label = None
        print("构建菜单ui...")
        self.sw_class = None
        self.sw = None
        self.acc_tab_ui = None
        self.is_login_menu = None
        self.menu_updater = None
        self.multirun_menu_index = None
        self.anti_revoke_menu_index = None
        self.menu_queue = None
        self.start_time = None
        self.coexist_channel_menus_dict = {}
        self.multirun_channel_menus_dict = {}
        self.anti_revoke_channel_menus_dict = {}
        self.coexist_channel_radio_list = []
        self.multirun_channel_vars_dict = {}
        self.anti_revoke_channel_vars_dict = {}
        self.multirun_menu = None
        self.anti_revoke_menu = None
        self.freely_multirun_var = None
        self.sidebar_ui = None
        self.sidebar_wnd = None
        self.call_mode_menu = None
        self.auto_start_menu = None
        self.path_error = None
        self.multiple_err = None
        self.help_menu = None
        self.rest_mode_menu = None
        self.settings_menu = None
        self.wnd_scale_menu = None
        self.view_options_menu = None
        self.view_menu = None
        self.edit_menu = None
        self.statistic_menu = None
        self.program_file_menu = None
        self.config_file_menu = None
        self.user_file_menu = None
        self.file_menu = None
        self.menu_bar = None

        self.root_class = GlobalMembers.root_class
        self.root = self.root_class.root
        self.global_settings_value = self.root_class.global_settings_value
        self.global_settings_var = self.root_class.global_settings_var
        self.app_info = self.root_class.app_info
        self.sw_classes = self.root_class.sw_classes

    def create_root_menu_bar(self):
        """创建菜单栏"""
        root_tab = subfunc_file.fetch_global_setting_or_set_default_or_none(LocalCfg.ROOT_TAB)
        self.is_login_menu = root_tab == "login"
        if self.is_login_menu:
            self.acc_tab_ui = self.root_class.login_ui
            self.sw = self.acc_tab_ui.sw
            self.sw_class = self.sw_classes[self.sw]

            # 传递错误信息给主窗口
            if self.sw_class.inst_path is None or self.sw_class.data_dir is None or self.sw_class.dll_dir is None:
                print("路径设置错误...")
                self.acc_tab_ui.path_error = True

        print("创建菜单栏...")
        self.start_time = time.time()

        if not isinstance(self.menu_bar, tk.Menu):
            self.menu_bar = tk.Menu(self.root)
            self.root.config(menu=self.menu_bar)

        self.menu_bar.delete(0, tk.END)

        # ————————————————————————————侧栏菜单————————————————————————————
        used_sidebar = subfunc_file.fetch_global_setting_or_set_default_or_none(LocalCfg.USED_SIDEBAR)
        suffix = "" if used_sidebar is True else Strings.SIDEBAR_HINT
        label = "❯" if self.sidebar_wnd is not None and self.sidebar_wnd.winfo_exists() else "❮"
        self.sidebar_menu_label = f"{label}{suffix}"
        self.menu_bar.add_command(label=self.sidebar_menu_label, command=partial(self._open_sidebar))
        # ————————————————————————————文件菜单————————————————————————————
        self.file_menu = tk.Menu(self.menu_bar, tearoff=False)
        self.menu_bar.add_cascade(label="文件", menu=self.file_menu)
        # >用户文件
        self.user_file_menu = tk.Menu(self.file_menu, tearoff=False)
        self.file_menu.add_cascade(label="用户文件", menu=self.user_file_menu)
        self.user_file_menu.add_command(label="打开", command=AppFunc.open_user_file)
        self.user_file_menu.add_command(label="清除", command=partial(
            AppFunc.clear_user_file, self.root_class.initialize_in_root))
        # >程序目录
        self.program_file_menu = tk.Menu(self.file_menu, tearoff=False)
        self.file_menu.add_cascade(label="程序目录", menu=self.program_file_menu)
        self.program_file_menu.add_command(label="打开", command=AppFunc.open_program_file)
        self.program_file_menu.add_command(label="删除旧版备份",
                                           command=partial(AppFunc.mov_backup))
        # -创建软件快捷方式
        self.file_menu.add_command(label="创建程序快捷方式", command=AppFunc.create_app_lnk)

        if self.is_login_menu:
            self.file_menu.add_separator()  # ————————————————分割线————————————————
            # >统计数据
            self.statistic_menu = tk.Menu(self.file_menu, tearoff=False)
            self.file_menu.add_cascade(label="统计", menu=self.statistic_menu)
            self.statistic_menu.add_command(label="查看", command=partial(WndCreator.open_statistic, self.sw))
            self.statistic_menu.add_command(label="清除",
                                            command=partial(AppFunc.clear_statistic_data,
                                                            self.create_root_menu_bar))
            # >配置文件
            self.config_file_menu = tk.Menu(self.file_menu, tearoff=False)
            if not self.sw_class.data_dir:
                self.file_menu.add_command(label="配置文件  未获取")
                self.file_menu.entryconfig(f"配置文件  未获取", state="disable")
            else:
                self.file_menu.add_cascade(label="配置文件", menu=self.config_file_menu)
                self.config_file_menu.add_command(label="打开",
                                                  command=partial(SwOperator.open_config_file, self.sw))
                self.config_file_menu.add_command(label="清除",
                                                  command=partial(SwOperator.clear_config_file, self.sw,
                                                                  self.root_class.login_ui.refresh))
            # -打开主dll所在文件夹
            self.file_menu.add_command(label="查看DLL目录", command=partial(SwOperator.open_dll_dir, self.sw))
            if self.sw_class.dll_dir is None:
                self.file_menu.entryconfig(f"查看DLL目录", state="disable")
            print(f"文件菜单用时：{time.time() - self.start_time:.4f}秒")

        # ————————————————————————————编辑菜单————————————————————————————
        self.edit_menu = tk.Menu(self.menu_bar, tearoff=False)
        self.menu_bar.add_cascade(label="编辑", menu=self.edit_menu)
        # -刷新
        self.edit_menu.add_command(label="快速刷新", command=self.root_class.root_ui.refresh_current_tab)
        self.edit_menu.add_command(
            label="刷新", command=partial(self.root_class.root_ui.refresh_current_tab, False))
        self.edit_menu.add_separator()  # ————————————————分割线————————————————
        self.edit_menu.add_command(label="热更新", command=self._to_update_remote_cfg)
        self.edit_menu.add_separator()  # ————————————————分割线————————————————
        self.edit_menu.add_command(label="初始化", command=self._to_initialize)
        print(f"编辑菜单用时：{time.time() - self.start_time:.4f}秒")

        # ————————————————————————————视图菜单————————————————————————————
        self.view_menu = tk.Menu(self.menu_bar, tearoff=False)
        self.menu_bar.add_cascade(label="视图", menu=self.view_menu)
        if self.is_login_menu:
            # 视图单选
            view_value = self.global_settings_value.view = subfunc_file.fetch_sw_setting_or_set_default_or_none(
                self.sw, "view")
            view_var = self.global_settings_var.view = tk.StringVar(value=view_value)

            self.view_menu.add_radiobutton(label="经典", variable=view_var, value="classic",
                                           command=self._switch_to_classic_view)
            self.view_menu.add_radiobutton(label="列表", variable=view_var, value="tree",
                                           command=self._switch_to_tree_view)
            self.view_menu.add_separator()  # ————————————————分割线————————————————
        # 全局菜单:缩放+选项
        # 视图选项
        self.view_options_menu = tk.Menu(self.view_menu, tearoff=False)
        self.view_menu.add_cascade(label=f"视图选项", menu=self.view_options_menu)
        sign_vis_value = self.global_settings_value.sign_vis = \
            subfunc_file.fetch_global_setting_or_set_default_or_none(LocalCfg.SIGN_VISIBLE)
        sign_vis_var = self.global_settings_var.sign_vis = tk.BooleanVar(value=sign_vis_value)
        self.view_options_menu.add_checkbutton(
            label="显示状态标志", variable=sign_vis_var,
            command=partial(subfunc_file.save_a_global_setting_and_callback,
                            LocalCfg.SIGN_VISIBLE, not self.global_settings_value.sign_vis,
                            self.root_class.login_ui.refresh)
        )
        use_txt_avt = self.global_settings_value.use_txt_avt = \
            subfunc_file.fetch_global_setting_or_set_default_or_none(LocalCfg.USE_TXT_AVT)
        use_txt_avt_var = self.global_settings_var.use_txt_avt = tk.BooleanVar(value=use_txt_avt)
        self.view_options_menu.add_checkbutton(
            label="使用文字头像", variable=use_txt_avt_var,
            command=partial(subfunc_file.save_a_global_setting_and_callback,
                            LocalCfg.USE_TXT_AVT, not use_txt_avt,
                            self.root_class.login_ui.refresh)
        )
        # sidebar_var = tk.BooleanVar(value=False)
        # self.view_menu.add_checkbutton(label="侧栏", variable=sidebar_var,
        #                                command=self._open_sidebar)
        scale_value = self.global_settings_value.scale = subfunc_file.fetch_global_setting_or_set_default_or_none(
            "scale")
        scale_var = self.global_settings_var.scale = tk.StringVar(value=scale_value)
        self.wnd_scale_menu = tk.Menu(self.view_menu, tearoff=False)
        self.view_menu.add_cascade(label=f"窗口缩放", menu=self.wnd_scale_menu)
        self.wnd_scale_menu.add_radiobutton(label="跟随系统", variable=scale_var, value="auto",
                                            command=partial(self._set_wnd_scale,
                                                            self.create_root_menu_bar, "auto"))
        options = ["100", "125", "150", "175", "200"]
        for option in options:
            self.wnd_scale_menu.add_radiobutton(label=f"{option}%", variable=scale_var, value=option,
                                                command=partial(self._set_wnd_scale,
                                                                self.create_root_menu_bar, option))
        if scale_value != "auto" and scale_value not in options:
            self.wnd_scale_menu.add_radiobutton(label=f"自定义:{scale_value}%",
                                                variable=scale_var, value=scale_value,
                                                command=partial(self._set_wnd_scale,
                                                                self.create_root_menu_bar))
        else:
            self.wnd_scale_menu.add_radiobutton(label=f"自定义",
                                                variable=scale_var, value="0",
                                                command=partial(self._set_wnd_scale,
                                                                self.create_root_menu_bar))
        print(f"视图菜单用时：{time.time() - self.start_time:.4f}秒")

        # ————————————————————————————设置菜单————————————————————————————
        self.settings_menu = tk.Menu(self.menu_bar, tearoff=False)
        self.menu_bar.add_cascade(label="设置", menu=self.settings_menu)
        self._create_setting_menu()
        print(f"设置菜单用时：{time.time() - self.start_time:.4f}秒")

        # ————————————————————————————帮助菜单————————————————————————————
        # 检查版本表是否当天已更新
        subfunc_file.read_remote_cfg_in_rules()
        surprise_sign = Strings.SURPRISE_SIGN
        self.app_info.need_update = AppFunc.has_newer_version(self.app_info.curr_full_ver)
        prefix = surprise_sign if self.app_info.need_update is True else ""
        self.help_menu = tk.Menu(self.menu_bar, tearoff=False)
        self.menu_bar.add_cascade(label=f"{prefix}帮助", menu=self.help_menu)
        self.help_menu.add_command(label="我来赏你！", command=WndCreator.open_rewards)
        self.help_menu.add_command(label="视频教程",
                                   command=lambda: webbrowser.open_new(Strings.VIDEO_TUTORIAL_LINK))
        self.help_menu.add_command(label="更新日志", command=WndCreator.open_update_log)
        self.help_menu.add_command(label="反馈渠道", command=WndCreator.open_feedback)
        self.help_menu.add_command(label=f"{prefix}关于",
                                   command=partial(WndCreator.open_about, self.app_info))
        print(f"帮助菜单用时：{time.time() - self.start_time:.4f}秒")

        # ————————————————————————————作者标签————————————————————————————
        new_func_value = self.global_settings_value.new_func = \
            subfunc_file.fetch_global_setting_or_set_default_or_none(
                LocalCfg.ENABLE_NEW_FUNC)
        author_str = self.app_info.author
        hint_str = self.app_info.hint
        author_str_without_hint = f"by {author_str}"
        author_str_with_hint = f"by {author_str}（{hint_str}）"

        if new_func_value is True:
            self.menu_bar.add_command(label=author_str_without_hint)
            self.menu_bar.entryconfigure(author_str_without_hint, state="disabled")
        else:
            self.menu_bar.add_command(label=author_str_with_hint)
            handler = widget_utils.UnlimitedClickHandler(
                self.root,
                self.menu_bar,
                **{"3": partial(self._to_enable_new_func)}
            )
            self.menu_bar.entryconfigure(author_str_with_hint, command=handler.on_click_down)

        self.used_tray = subfunc_file.fetch_global_setting_or_set_default_or_none(LocalCfg.USED_TRAY)
        suffix = "" if self.used_tray is True else Strings.TRAY_HINT
        self._to_tray_label = f"⌟{suffix}"
        self.menu_bar.add_command(label=self._to_tray_label, command=self._to_bring_tk_to_tray)

    def _create_setting_menu(self):
        # -全局设置
        self.settings_menu.add_command(label=f"全局设置", command=WndCreator.open_global_setting_wnd)
        _, self.global_settings_value.auto_start = AppFunc.check_auto_start_or_toggle_to_()
        auto_start_value = self.global_settings_value.auto_start
        auto_start_var = self.global_settings_var.auto_start = tk.BooleanVar(value=auto_start_value)
        self.auto_start_menu = tk.Menu(self.settings_menu, tearoff=False)
        self.settings_menu.add_cascade(label="自启动", menu=self.auto_start_menu)
        self.auto_start_menu.add_checkbutton(
            label="开机自启动", variable=auto_start_var,
            command=partial(self._toggle_auto_start,
                            not self.global_settings_value.auto_start))
        self.auto_start_menu.add_command(
            label="测试登录自启动账号", command=MultiSwFunc.thread_to_login_auto_start_accounts)

        if self.is_login_menu:
            # -应用设置
            self.settings_menu.add_separator()  # ————————————————分割线————————————————
            self.settings_menu.add_command(label="平台设置", command=partial(WndCreator.open_sw_settings, self.sw))
            self.coexist_menu = tk.Menu(self.settings_menu, tearoff=False)
            self.settings_menu.add_cascade(label="共存", menu=self.coexist_menu)
            self.anti_revoke_menu = tk.Menu(self.settings_menu, tearoff=False)
            self.settings_menu.add_cascade(label="防撤回", menu=self.anti_revoke_menu)
            self.multirun_menu = tk.Menu(self.settings_menu, tearoff=False)
            self.settings_menu.add_cascade(label="全局多开", menu=self.multirun_menu)
            self.settings_menu.add_separator()  # ————————————————分割线————————————————

            # 开启更新多开,防撤回等子菜单的更新线程
            # self._update_settings_sub_menus_in_thread()
            self.update_settings_menu_thread()

            hide_wnd_value = self.global_settings_value.hide_wnd = \
                subfunc_file.fetch_global_setting_or_set_default_or_none(LocalCfg.HIDE_WND)
            hide_wnd_var = self.global_settings_var.hide_wnd = tk.BooleanVar(value=hide_wnd_value)
            self.settings_menu.add_checkbutton(
                label="自动登录前隐藏主窗口", variable=hide_wnd_var,
                command=partial(subfunc_file.save_a_global_setting_and_callback,
                                LocalCfg.HIDE_WND, not hide_wnd_value, self.create_root_menu_bar))

            # >调用模式
            self.call_mode_menu = tk.Menu(self.settings_menu, tearoff=False)
            self.settings_menu.add_cascade(label="调用模式", menu=self.call_mode_menu)
            call_mode_value = self.global_settings_value.call_mode = subfunc_file.fetch_global_setting_or_set_default_or_none(
                "call_mode")
            call_mode_var = self.global_settings_var.call_mode = tk.StringVar(value=call_mode_value)  # 设置初始选中的子程序

            # 添加 HANDLE 的单选按钮
            self.call_mode_menu.add_radiobutton(
                label='HANDLE',
                value='HANDLE',
                variable=call_mode_var,
                command=partial(subfunc_file.save_a_global_setting_and_callback,
                                "call_mode", "HANDLE", self.create_root_menu_bar),
            )
            # 添加 DEFAULT 的单选按钮
            self.call_mode_menu.add_radiobutton(
                label='DEFAULT',
                value='DEFAULT',
                variable=call_mode_var,
                command=partial(subfunc_file.save_a_global_setting_and_callback,
                                "call_mode", "DEFAULT", self.create_root_menu_bar),
            )
            # 添加 LOGON 的单选按钮
            self.call_mode_menu.add_radiobutton(
                label='LOGON',
                value='LOGON',
                variable=call_mode_var,
                command=partial(subfunc_file.save_a_global_setting_and_callback,
                                "call_mode", "LOGON", self.create_root_menu_bar),
            )

            auto_press_value = self.global_settings_value.auto_press = \
                subfunc_file.fetch_global_setting_or_set_default_or_none(LocalCfg.AUTO_PRESS)
            auto_press_var = self.global_settings_var.auto_press = tk.BooleanVar(value=auto_press_value)
            self.settings_menu.add_checkbutton(
                label="自动点击登录按钮", variable=auto_press_var,
                command=partial(subfunc_file.save_a_global_setting_and_callback,
                                "auto_press", not auto_press_value, self.create_root_menu_bar))

        self.settings_menu.add_separator()  # ————————————————分割线————————————————
        self.settings_menu.add_command(
            label="重置", command=partial(AppFunc.reset, self.root_class.initialize_in_root))

    def _calc_multirun_mode_and_save(self, mode):
        """计算多开模式并保存"""
        subfunc_file.save_a_setting_and_callback(
            self.sw, LocalCfg.REST_MULTIRUN_MODE, mode, self.create_root_menu_bar)
        self.sw_class.multirun_mode = MultirunMode.FREELY_MULTIRUN if self.sw_class.can_freely_multirun is True else mode

    def _to_update_remote_cfg(self):
        printer.vital("更新远程配置")
        config_data = subfunc_file.force_fetch_remote_encrypted_cfg()
        if config_data is None:
            messagebox.showinfo("提示", "无法获取配置文件，请检查网络连接后重试")
            return False
        messagebox.showinfo("提示", "更新成功")
        self.root_class.root_ui.refresh_current_tab()
        return True

    def _to_initialize(self):
        printer.vital("初始化")
        self.root_class.initialize_in_root()

    def _switch_to_classic_view(self):
        self.root.unbind("<Configure>")
        subfunc_file.save_a_setting_and_callback(self.sw, "view", "classic", self.root_class.login_ui.refresh)

    def _switch_to_tree_view(self):
        subfunc_file.save_a_setting_and_callback(self.sw, "view", "tree", self.root_class.login_ui.refresh)

    def _open_sidebar(self):
        if self.sidebar_wnd is not None and self.sidebar_wnd.winfo_exists():
            print("销毁", self.sidebar_wnd)
            new_label = "❮"
            self.menu_bar.entryconfigure(self.sidebar_menu_label, label=new_label)
            self.sidebar_menu_label = new_label
            if self.sidebar_ui is not None:
                self.sidebar_ui.listener_running = False
                self.sidebar_ui = None
            self.sidebar_wnd.destroy()
        else:
            print("创建", self.sidebar_wnd)
            new_label = "❯"
            self.menu_bar.entryconfigure(self.sidebar_menu_label, label=new_label)
            if len(self.sidebar_menu_label) > 1:
                subfunc_file.update_settings(LocalCfg.GLOBAL_SECTION, **{LocalCfg.USED_SIDEBAR: True})
            self.sidebar_menu_label = new_label
            self.sidebar_wnd = tk.Toplevel(self.root)
            self.sidebar_ui = sidebar_ui.SidebarUI(self.sidebar_wnd, "导航条")

    def _set_wnd_scale(self, scale=None):
        if scale is None:
            # 创建输入框
            try:
                user_input = simpledialog.askstring(
                    title="输入 Scale",
                    prompt="请输入一个 75-500 之间的数字（含边界）："
                )
                if user_input is None:  # 用户取消或关闭输入框
                    return
                # 尝试将输入转换为整数并验证范围
                scale = int(user_input)
                if not (75 <= scale <= 500):
                    raise ValueError("输入值不在 75-500 范围内")
            except (ValueError, TypeError):
                messagebox.showerror("错误", "无效输入，操作已取消")
                return
        subfunc_file.save_a_global_setting_and_callback(
            LocalCfg.SCALE,
            str(scale)
        )
        messagebox.showinfo("提示", "修改成功，将在重新启动程序后生效！")
        self.create_root_menu_bar()
        print(f"成功设置窗口缩放比例为 {scale}！")
        return

    def _toggle_patch_mode(self, mode, channel):
        """切换是否全局多开或防撤回"""
        try:
            success, msg = SwOperator.switch_dll(self.sw, mode, channel)  # 执行切换操作
            if success:
                channel_des, = subfunc_file.get_remote_cfg(
                    self.sw, mode, "channel", **{channel: None})
                channel_authors = []
                channel_label = ""
                if channel_des is not None and isinstance(channel_des, dict):
                    if "author" in channel_des:
                        channel_authors = channel_des["author"]
                    if "label" in channel_des:
                        channel_label = channel_des["label"]
                if len(channel_authors) > 0:
                    author_text = ", ".join(channel_authors)
                    msg = f"{msg}\n鸣谢:{channel_label}方案特征码来自{author_text}"
                messagebox.showinfo("提示", f"{msg}")
            else:
                messagebox.showerror("错误", f"{msg}")
        except Exception as e:
            messagebox.showerror("错误", f"操作失败: {str(e)}")
            logger.error(f"发生错误: {str(e)}")
        finally:
            self.root_class.login_ui.refresh()

    def _toggle_auto_start(self, value):
        """切换是否开机自启动"""
        success, res = AppFunc.check_auto_start_or_toggle_to_(value)
        self.create_root_menu_bar()
        if success is not True:
            messagebox.showerror("错误", res)
            print("操作失败！")
        else:
            print(f"已添加自启动！" if value is True else f"已关闭自启动！")

    def _to_enable_new_func(self):
        subfunc_file.save_a_global_setting_and_callback('enable_new_func', True)
        messagebox.showinfo("发现彩蛋", "解锁新功能，快去找找吧！")
        self.create_root_menu_bar()

    def _to_bring_tk_to_tray(self):
        """将tk窗口最小化到托盘"""
        self.root.withdraw()
        if self.used_tray is not True:
            self.used_tray = False
            subfunc_file.update_settings(LocalCfg.GLOBAL_SECTION, **{LocalCfg.USED_TRAY: True})
            new_label = self._to_tray_label.replace(Strings.TRAY_HINT, "")
            self.menu_bar.entryconfigure(self._to_tray_label, label=new_label)
            self._to_tray_label = new_label
        if not (self.root_class.global_settings_value.in_tray is True):
            AppFunc.create_tray(self.root)
            self.root_class.global_settings_value.in_tray = True

    def _introduce_channel(self, mode, res_dict):
        text = ""
        for channel, res_tuple in res_dict.items():
            if not isinstance(res_tuple, tuple) or len(res_tuple) != 3:
                continue
            channel_des, = subfunc_file.get_remote_cfg(
                self.sw, mode, "channel", **{channel: None})
            channel_label = channel
            channel_introduce = "暂无介绍"
            channel_author = "未知"
            if channel_des is not None and isinstance(channel_des, dict):
                if "label" in channel_des:
                    channel_label = channel_des["label"]
                if "introduce" in channel_des:
                    channel_introduce = channel_des["introduce"]
                if "author" in channel_des:
                    channel_author = channel_des["author"]
            text = f"{text}\n[{channel_label}]\n{channel_introduce}\n作者：{channel_author}\n"
        messagebox.showinfo("简介", text)

    def _clear_cache(self, mode):
        """清除缓存"""
        # 询问用户
        if messagebox.askyesno(
                "确认",
                "清除缓存将重新尝试基于特征码扫描精确适配.\n"
                "注意: 对已经开启的模式,清除缓存后可能导致该模式扫描失败,请确保已经关闭该模式!\n"
                "是否继续?"):
            SwInfoFunc.clear_adaptation_cache(self.sw, mode)
            messagebox.showinfo("提示", "缓存已清除！")
            self.create_root_menu_bar()

    """更新多开,共存,防撤回子菜单的线程"""

    def _update_coexist_menu(self, mode_channel_res_dict, msg):
        Printer().debug(mode_channel_res_dict)
        if mode_channel_res_dict is None:
            self.settings_menu.entryconfig("共存", label="！共存", foreground="red")
            self.coexist_menu.add_command(label=f"[点击复制]{msg}", foreground="red",
                                              command=lambda i=msg: Tk2Sys.copy_to_clipboard(self.root, i))
        else:
            for channel, channel_res_tuple in mode_channel_res_dict.items():
                if not isinstance(channel_res_tuple, tuple) or len(channel_res_tuple) != 3:
                    continue
                channel_des, = subfunc_file.get_remote_cfg(
                    self.sw, RemoteCfg.COEXIST.value, "channel", **{channel: None})
                # print(channel_des)
                channel_label = channel
                if isinstance(channel_des, dict):
                    if "label" in channel_des:
                        channel_label = channel_des["label"]
                coexist_status, channel_msg, _ = channel_res_tuple
                if coexist_status is None or coexist_status is False:
                    menu = self.coexist_channel_menus_dict[channel] = tk.Menu(
                        self.coexist_menu, tearoff=False)
                    self.coexist_menu.add_cascade(label=channel_label, menu=menu)
                    menu.add_command(label=f"[点击复制]{channel_msg}", foreground="red",
                                     command=lambda i=channel_msg: Tk2Sys.copy_to_clipboard(self.root, i))
                else:
                    self.coexist_channel_var = tk.StringVar()
                    self.coexist_menu.add_radiobutton(
                        label=channel_label,
                        value=channel,
                        variable=self.coexist_channel_var,
                        command=partial(
                            subfunc_file.save_a_setting_and_callback,
                            self.sw, LocalCfg.COEXIST_MODE.value, channel, self.create_root_menu_bar),
                    )
                    self.coexist_channel_radio_list.append(channel)
            current_coexist_mode = subfunc_file.fetch_sw_setting_or_set_default_or_none(
                self.sw, LocalCfg.COEXIST_MODE.value)
            # 如果这个模式在单选值列表中,则选择这个值,否则选择第一个值
            if current_coexist_mode in self.coexist_channel_radio_list:
                self.coexist_channel_var.set(current_coexist_mode)
            else:
                if len(self.coexist_channel_radio_list) > 0:
                    self.coexist_channel_var.set(self.coexist_channel_radio_list[0])

            # 频道简介菜单
            self.coexist_menu.add_separator()  # ————————————————分割线————————————————
            self.coexist_menu.add_command(
                label="频道简介", command=partial(
                    self._introduce_channel, RemoteCfg.COEXIST.value, mode_channel_res_dict))
        self.coexist_menu.add_separator()  # ————————————————分割线————————————————
        self.coexist_menu.add_command(
            label="清除缓存",
            command=partial(self._clear_cache, RemoteCfg.COEXIST.value))
        printer.print_last()

    def _update_anti_revoke_menu(self, mode_channel_res_dict, msg):
        # 原来的防撤回菜单创建代码
        Printer().debug(mode_channel_res_dict)
        if mode_channel_res_dict is None:
            self.settings_menu.entryconfig("防撤回", label="！防撤回", foreground="red")
            self.anti_revoke_menu.add_command(label=f"[点击复制]{msg}", foreground="red",
                                              command=lambda i=msg: Tk2Sys.copy_to_clipboard(self.root, i))
        else:
            for channel, channel_res_tuple in mode_channel_res_dict.items():
                if not isinstance(channel_res_tuple, tuple) or len(channel_res_tuple) != 3:
                    continue
                channel_des, = subfunc_file.get_remote_cfg(
                    self.sw, RemoteCfg.REVOKE.value, "channel", **{channel: None})
                # print(channel_des)
                channel_label = channel
                if isinstance(channel_des, dict):
                    if "label" in channel_des:
                        channel_label = channel_des["label"]
                anti_revoke_status, channel_msg, _ = channel_res_tuple
                if anti_revoke_status is None:
                    menu = self.anti_revoke_channel_menus_dict[channel] = tk.Menu(
                        self.anti_revoke_menu, tearoff=False)
                    self.anti_revoke_menu.add_cascade(label=channel_label, menu=menu)
                    menu.add_command(label=f"[点击复制]{channel_msg}", foreground="red",
                                     command=lambda i=channel_msg: Tk2Sys.copy_to_clipboard(self.root, i))
                else:
                    self.anti_revoke_channel_vars_dict[channel] = tk.BooleanVar(value=anti_revoke_status)
                    self.anti_revoke_menu.add_checkbutton(
                        label=channel_label, variable=self.anti_revoke_channel_vars_dict[channel],
                        command=partial(self._toggle_patch_mode, mode=RemoteCfg.REVOKE, channel=channel))
            self.anti_revoke_menu.add_separator()  # ————————————————分割线————————————————
            # 频道简介菜单
            self.anti_revoke_menu.add_command(
                label="频道简介",
                command=partial(self._introduce_channel, RemoteCfg.REVOKE.value, mode_channel_res_dict))
        self.anti_revoke_menu.add_separator()  # ————————————————分割线————————————————
        self.anti_revoke_menu.add_command(
            label="清除缓存",
            command=partial(self._clear_cache, RemoteCfg.REVOKE.value))
        printer.print_last()

    def _update_multirun_menu(self, mode_channel_res_dict, msg):
        self.sw_class.can_freely_multirun = None
        # 以有无适配为准;
        if mode_channel_res_dict is None:
            # 若没有适配,检查是否是原生支持多开
            native_multirun, = subfunc_file.get_remote_cfg(self.sw, **{RemoteCfg.NATIVE_MULTI.value: None})
            if native_multirun is True:
                self.sw_class.can_freely_multirun = True
                self.multirun_menu.add_command(label="原生支持多开", state="disabled")
            else:
                self.settings_menu.entryconfig("全局多开", label="！全局多开", foreground="red")
                self.multirun_menu.add_command(label=f"[点击复制]{msg}", foreground="red",
                                               command=lambda i=msg: Tk2Sys.copy_to_clipboard(self.root, i))
        else:
            # 列出所有频道
            for channel, channel_res_tuple in mode_channel_res_dict.items():
                if not isinstance(channel_res_tuple, tuple) or len(channel_res_tuple) != 3:
                    continue
                channel_des, = subfunc_file.get_remote_cfg(
                    self.sw, RemoteCfg.MULTI.value, "channel", **{channel: None})
                # print(channel_des)
                channel_label = channel
                if channel_des is not None and isinstance(channel_des, dict):
                    if "label" in channel_des:
                        channel_label = channel_des["label"]
                freely_multirun_status, channel_msg, _ = channel_res_tuple
                if freely_multirun_status is None:
                    menu = self.multirun_channel_menus_dict[channel] = tk.Menu(
                        self.multirun_menu, tearoff=False)
                    self.multirun_menu.add_cascade(label=channel_label, menu=menu)
                    menu.add_command(label=f"[点击复制]{channel_msg}", foreground="red",
                                     command=lambda i=channel_msg: Tk2Sys.copy_to_clipboard(self.root, i))
                else:
                    # 只要有freely_multirun为True，就将其设为True
                    if freely_multirun_status is True:
                        self.sw_class.can_freely_multirun = True
                    self.multirun_channel_vars_dict[channel] = tk.BooleanVar(value=freely_multirun_status)
                    self.multirun_menu.add_checkbutton(
                        label=channel_label, variable=self.multirun_channel_vars_dict[channel],
                        command=partial(self._toggle_patch_mode, mode=RemoteCfg.MULTI, channel=channel))
            self.multirun_menu.add_separator()  # ————————————————分割线————————————————
            # 频道简介菜单
            self.multirun_menu.add_command(
                label="频道简介",
                command=partial(self._introduce_channel, RemoteCfg.MULTI.value, mode_channel_res_dict))
        self.multirun_menu.add_separator()  # ————————————————分割线————————————————

        # >多开子程序选择
        # 得出使用的多开模式,若开了全局多开,则使用全局多开模式,否则使用其他模式
        if self.sw_class.can_freely_multirun:
            self.sw_class.multirun_mode = MultirunMode.FREELY_MULTIRUN
            self.multirun_menu.add_command(label="其余模式", state="disabled")
        else:
            self.rest_mode_menu = tk.Menu(self.multirun_menu, tearoff=False)
            self.multirun_menu.add_cascade(label="其余模式", menu=self.rest_mode_menu)
            rest_mode_value = self.global_settings_value.rest_mode = subfunc_file.fetch_sw_setting_or_set_default_or_none(
                self.sw, LocalCfg.REST_MULTIRUN_MODE)
            # print("当前项", rest_mode_value)
            self.sw_class.multirun_mode = rest_mode_value
            rest_mode_var = self.global_settings_var.rest_mode = tk.StringVar(value=rest_mode_value)  # 设置初始选中的子程序
            # 添加 Python 的单选按钮
            self.rest_mode_menu.add_radiobutton(
                label='内置',
                value='内置',
                variable=rest_mode_var,
                command=partial(self._calc_multirun_mode_and_save, MultirunMode.BUILTIN.value),
            )
            # 添加 Handle 的单选按钮
            self.rest_mode_menu.add_radiobutton(
                label='handle',
                value='handle',
                variable=rest_mode_var,
                command=partial(self._calc_multirun_mode_and_save, MultirunMode.HANDLE.value),
            )
            # 动态添加外部子程序
            external_res_path = Config.PROJ_EXTERNAL_RES_PATH
            exe_files = [str(p) for p in Path(external_res_path).rglob(f"{self.sw}Multiple_*.exe")]
            if len(exe_files) != 0:
                self.rest_mode_menu.add_separator()  # ————————————————分割线————————————————
                for exe_file in exe_files:
                    exe_name = os.path.basename(exe_file)
                    right_part = exe_name.split('_', 1)[1].rsplit('.exe', 1)[0]
                    self.rest_mode_menu.add_radiobutton(
                        label=right_part,
                        value=exe_name,
                        variable=rest_mode_var,
                        command=partial(self._calc_multirun_mode_and_save, exe_name),
                    )
        self.multirun_menu.add_separator()  # ————————————————分割线————————————————
        self.multirun_menu.add_command(
            label="清除缓存",
            command=partial(self._clear_cache, RemoteCfg.MULTI.value))
        printer.print_last()

    def update_settings_menu_thread(self):
        threading.Thread(target=self._identify_dll_and_update_menu).start()

    def _identify_dll_and_update_menu(self):
        """实现抽象方法（原_create_menus_thread逻辑）"""
        try:
            # 共存部分
            res_dict, msg = SwInfoFunc.identify_dll(
                self.sw, RemoteCfg.COEXIST.value, True)
            self.root.after(0, self._update_coexist_menu, res_dict, msg)
            # 防撤回部分
            res_dict, msg = SwInfoFunc.identify_dll(
                self.sw, RemoteCfg.REVOKE.value)
            self.root.after(0, self._update_anti_revoke_menu, res_dict, msg)
            # 全局多开部分
            res_dict, msg = SwInfoFunc.identify_dll(
                self.sw, RemoteCfg.MULTI.value)
            self.root.after(0, self._update_multirun_menu, res_dict, msg)
        except Exception as e:
            print(e)
