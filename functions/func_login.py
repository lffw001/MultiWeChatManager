# func_login.py
import threading
import time
import tkinter as tk
from tkinter import messagebox
from typing import Dict

import win32con
import win32gui

from functions import func_config, subfunc_sw, subfunc_file, func_account
from resources import Config
from utils import hwnd_utils, handle_utils
from utils.logger_utils import mylogger as logger


def login_auto_start_accounts(root, root_class):
    all_sw_dict, = subfunc_file.get_details_from_remote_setting_json("global", all_sw=None)
    all_sw = [key for key in all_sw_dict.keys()]
    print("所有平台：", all_sw)

    # 获取需要自启动的账号
    can_auto_start: Dict[str, set] = {

    }
    for sw in all_sw:
        if sw not in can_auto_start:
            can_auto_start[sw] = set()
        sw_data = subfunc_file.get_sw_acc_details_from_json(sw)
        for acc in sw_data:
            auto_start, = subfunc_file.get_sw_acc_details_from_json(sw, acc, auto_start=None)
            if auto_start is True:
                can_auto_start[sw].add(acc)
    print(f"设置了自启动：{can_auto_start}")

    # 获取已经登录的账号
    for sw in all_sw:
        success, result = func_account.get_sw_acc_list(root, root_class, sw)
        if success is not True:
            continue
        acc_list_dict, _, _ = result
        logged_in = acc_list_dict["login"]
        for acc in logged_in:
            can_auto_start[sw].discard(acc)

    if any(len(sw_set) != 0 for sw, sw_set in can_auto_start.items()):
        print(f"排除已登录之后需要登录：{can_auto_start}")
        # 打印即将自动登录的提示
        for i in range(0, 3):
            print(f"即将自动登录：{3 - i}秒")
            time.sleep(1)

    # 遍历登录需要自启但未登录的账号
    for sw in can_auto_start:
        try:
            threading.Thread(
                target=auto_login_accounts,
                args=(root_class, sw, list(can_auto_start[sw]))
            ).start()
        except Exception as e:
            logger.error(e)


def manual_login(root, root_class, sw):
    """
    根据状态进行手动登录过程
    :param root: 主窗口
    :param root_class: 主窗口类
    :param sw: 选择的软件标签
    :return: 成功与否
    """
    # 初始化操作：清空闲置的登录窗口、多开器，清空并拉取各账户的登录和互斥体情况
    start_time = time.time()
    redundant_wnd_list, login_wnd_class, executable_name, cfg_handles = subfunc_file.get_details_from_remote_setting_json(
        sw, redundant_wnd_class=None, login_wnd_class=None, executable=None, cfg_handle_regex_list=None)
    if redundant_wnd_list is None or login_wnd_class is None or cfg_handles is None or executable_name is None:
        messagebox.showinfo("错误", "尚未适配！")
        return
    # 关闭配置文件锁
    handle_utils.close_sw_mutex_by_handle(
        Config.HANDLE_EXE_PATH, executable_name, cfg_handles)

    hwnd_utils.close_all_by_wnd_classes(redundant_wnd_list)
    subfunc_sw.kill_sw_multiple_processes(sw)
    time.sleep(0.5)
    subfunc_file.clear_all_acc_in_acc_json(sw)
    subfunc_file.update_all_acc_in_acc_json(sw)

    state = root_class.sw_classes[sw].multiple_state
    logger.info(f"当前模式是：{state}")
    has_mutex_dict = subfunc_sw.get_mutex_dict(sw)
    sub_exe_process, sub_exe = subfunc_sw.open_sw(sw, state, has_mutex_dict)
    wechat_hwnd = hwnd_utils.wait_open_to_get_hwnd(login_wnd_class, 20)
    if wechat_hwnd:
        subfunc_file.set_all_acc_values_to_false(sw)
        subfunc_file.update_statistic_data(sw, 'manual', '_', sub_exe, time.time() - start_time)
        print(f"打开了登录窗口{wechat_hwnd}")
        if sub_exe_process:
            sub_exe_process.terminate()
        if hwnd_utils.wait_hwnd_close(wechat_hwnd, timeout=60):
            print(f"手动登录成功，正在刷新...")
        else:
            messagebox.showinfo("提示", "登录窗口长时间未操作，即将刷新列表")
    else:
        logger.warning(f"打开失败，请重试！")
        messagebox.showerror("错误", "手动登录失败，请重试")

    # 刷新菜单和窗口前置
    root_class.root.after(0, root_class.refresh_sw_main_frame)
    hwnd_utils.bring_tk_wnd_to_front(root, root)


def auto_login_accounts(root_class, sw, accounts):
    """
    对选择的账号，进行全自动登录
    :param root_class:
    :param sw: 选择的软件标签
    :param accounts: 选择的账号列表
    :return: 是否成功
    """

    def get_wnd_positions(n):
        # 实际的间隔设置
        actual_gap_width = int((screen_width - n * login_width) / (n + 1))
        # 去除两边间隔总共的宽度
        all_login_width = int(n * login_width + (n - 1) * actual_gap_width)
        # 计算起始位置x，y
        x = int((screen_width - all_login_width) / 2)
        y = int((screen_height - login_height) / 2) - 25
        # 计算每个窗口的位置
        for i in range(n):
            positions.append((x + i * (login_width + actual_gap_width), y))
        print(positions)

    status = root_class.sw_classes[sw].multiple_state

    if accounts is None or len(accounts) == 0:
        return False

    # 初始化操作：清空闲置的登录窗口、多开器，清空并拉取各账户的登录和互斥体情况
    redundant_wnd_list, login_wnd_class, executable_name, cfg_handles = (
        subfunc_file.get_details_from_remote_setting_json(
            sw, redundant_wnd_class=None, login_wnd_class=None, executable=None, cfg_handle_regex_list=None))
    hwnd_utils.close_all_by_wnd_classes(redundant_wnd_list)
    subfunc_sw.kill_sw_multiple_processes(sw)
    time.sleep(0.5)
    subfunc_file.clear_all_acc_in_acc_json(sw)
    subfunc_file.update_all_acc_in_acc_json(sw)

    # 检测尺寸设置是否完整
    login_size = subfunc_file.fetch_sw_setting_or_set_default(sw, "login_size")
    if not login_size or login_size == "":
        messagebox.showinfo("提醒", "缺少登录窗口尺寸配置，请到应用设置中添加！")
        return False
    else:
        login_width, login_height = login_size.split('*')

    # 确保整数
    login_width = int(login_width)
    login_height = int(login_height)

    # 优先自动获取尺寸，若获取不到从配置中获取
    screen_width = int(tk.Tk().winfo_screenwidth())
    screen_height = int(tk.Tk().winfo_screenheight())
    if not screen_height or not screen_width:
        size = subfunc_file.fetch_global_setting_or_set_default("screen_size").split('*')
        screen_width, screen_height = int(size[0]), int(size[1])
    # 计算一行最多可以显示多少个
    max_column = int(screen_width / login_width)

    # 存放登录窗口的起始位置的列表
    positions = []
    # 若账号个数超过最多显示个数，则只创建最多显示个数的位置列表
    count = len(accounts)
    if count > max_column:
        print(f"不能一行显示")
        get_wnd_positions(max_column)
    else:
        print(f"可以一行显示")
        get_wnd_positions(count)

    if status == "已开启":
        multiple_mode = "全局多开"
    else:
        multiple_mode = subfunc_file.fetch_sw_setting_or_set_default(sw, 'rest_mode')
    # 开始遍历登录账号过程
    start_time = time.time()
    # 使用一个set存储不重复的handle
    wechat_handles = set()
    for j in range(count):
        # 关闭配置文件锁
        handle_utils.close_sw_mutex_by_handle(
            Config.HANDLE_EXE_PATH, executable_name, cfg_handles)

        # 读取配置
        success, _ = func_config.operate_config('use', sw, accounts[j])
        if success:
            print(f"{accounts[j]}:复制配置文件成功")
        else:
            print(f"{accounts[j]}:复制配置文件失败")
            break

        # 打开微信
        has_mutex_dict = subfunc_sw.get_mutex_dict(sw)
        sub_exe_process, sub_exe = subfunc_sw.open_sw(sw, status, has_mutex_dict)

        # 等待打开窗口
        end_time = time.time() + 20
        while True:
            wechat_hwnd = hwnd_utils.wait_open_to_get_hwnd(login_wnd_class, 1)
            if wechat_hwnd is not None and wechat_hwnd not in wechat_handles:
                # 确保打开了新的微信登录窗口
                wechat_handles.add(wechat_hwnd)
                if sub_exe_process:
                    sub_exe_process.terminate()
                print(f"打开窗口成功：{wechat_hwnd}")
                subfunc_file.set_all_acc_values_to_false(sw)
                subfunc_file.update_has_mutex_from_all_acc(sw)
                break
            if time.time() > end_time:
                print(f"超时！换下一个账号")
                break

        # 安排窗口位置
        # 横坐标算出完美的平均位置
        new_left = positions[j % max_column][0]
        # 纵坐标由居中位置稍向上偏移，然后每轮完一行，位置向下移动一个登录窗口宽度的距离
        new_top = positions[j % max_column][1] - int(login_width / 2) + int(j / max_column) * login_width
        # 只调整窗口的位置，不改变大小
        try:
            win32gui.SetWindowPos(
                wechat_hwnd,
                win32con.HWND_TOP,
                new_left,
                new_top,
                0,  # 宽度设置为 0 表示不改变
                0,  # 高度设置为 0 表示不改变
                win32con.SWP_NOSIZE | win32con.SWP_SHOWWINDOW
            )
        except Exception as e:
            logger.error(e)

        # 逐次统计时间
        subfunc_file.update_statistic_data(sw, 'auto', str(j + 1), sub_exe, time.time() - start_time)
    # 统计平均时间
    subfunc_file.update_statistic_data(sw, 'auto', 'avg', multiple_mode,
                                       (time.time() - start_time) / count)

    # 循环登录完成
    # 如果有，关掉多余的多开器
    subfunc_sw.kill_sw_multiple_processes(sw)

    def func():
        # 两轮点击所有窗口的登录，防止遗漏
        hwnd_list = hwnd_utils.get_hwnd_list_by_class_and_title(login_wnd_class)
        time.sleep(0.5)
        inner_start_time = time.time()
        for h in hwnd_list:
            hwnd_utils.do_click_in_wnd(h, int(login_width * 0.5), int(login_height * 0.75))
            time.sleep(0.2)
        print("查找后用时：", time.time() - inner_start_time, "s")
        # for h in hwnd_list:
        #     hwnd_utils.do_click_in_wnd(h, int(login_width * 0.5), int(login_height * 0.75))
        #     time.sleep(0.2)
        inner_start_time = time.time()
        for h in hwnd_list:
            titles = ["进入微信", "进入WeChat", "Enter Weixin", "进入微信"]  # 添加所有需要查找的标题
            try:
                # cx, cy = hwnd_utils.get_widget_center_pos_by_hwnd_and_possible_titles(h, titles)  # avg:2.4s
                cx, cy = hwnd_utils.find_widget_with_uiautomation(h, titles)  # avg:1.9s
                print(hwnd_utils.get_child_hwnd_list_of_(h))
                # cx, cy = hwnd_utils.find_widget_with_win32(h, titles)  # 微信窗口非标准窗口，查找不了
                # cx, cy = hwnd_utils.find_widget_with_pygetwindow(h, titles)  # 只能用来查找窗口标题，无法用来查找窗口内的控件
                # cx, cy = hwnd_utils.find_widget_with_uia(h, titles)  # 有问题，修复较复杂，不管
                print("查找后用时：", time.time() - inner_start_time, "s")
                if cx is not None and cy is not None:
                    hwnd_utils.do_click_in_wnd(h, int(cx), int(cy))
                    break  # 找到有效坐标后退出循环
            except TypeError as te:
                logger.warning(te)
                print("没有按钮，应该是点过啦~")
            except Exception as fe:
                logger.error(fe)

    threading.Thread(target=func).start()

    # 结束条件为所有窗口消失或等待超过20秒（网络不好则会这样）
    end_time = time.time() + 30
    while True:
        hs = hwnd_utils.get_hwnd_list_by_class_and_title(login_wnd_class)
        # print("等待登录完成")
        if len(hs) == 0:
            break
        if time.time() > end_time:
            break
    root_class.root.after(0, root_class.refresh_sw_main_frame)
    return True
