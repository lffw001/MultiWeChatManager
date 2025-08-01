import os
import shutil
import time
from unittest import TestCase

import psutil

from functions import subfunc_file
from functions.acc_func import AccOperator
from functions.sw_func import SwInfoUtils, SwOperator, SwInfoFunc
from public_class.enums import RemoteCfg
from resources import Config
from ui.sidebar_ui import SidebarUI, WndProperties
from utils import handle_utils, hwnd_utils
from utils.encoding_utils import VersionUtils
from utils.file_utils import IniUtils
from utils.logger_utils import Printer


class Test(TestCase):
    def test_get_wnd_by_classname(self):
        hwnds = hwnd_utils.win32_wait_hwnd_by_class("Qt51514QWindowIcon")
        print(hwnds)

    def test_multi_new_weixin(self):
        redundant_wnd_list, login_wnd_class, executable_name, cfg_handles = subfunc_file.get_remote_cfg(
            "Weixin", redundant_wnd_class=None, login_wnd_class=None, executable=None, cfg_handle_regex_list=None)
        # 关闭配置文件锁
        handle_utils.close_sw_mutex_by_handle(
            Config.HANDLE_EXE_PATH, executable_name, cfg_handles)
        # 构建源文件和目标文件路径
        # source_dir1 = r"E:\Now\Desktop\不吃鱼的猫\global_config".replace('\\', '/')
        # source_dir2 = r"E:\Now\Desktop\不吃鱼的猫\global_config.crc".replace('\\', '/')
        source_dir1 = r"E:\Now\Desktop\极峰创科\global_config".replace('\\', '/')
        source_dir2 = r"E:\Now\Desktop\极峰创科\global_config.crc".replace('\\', '/')
        target_dir1 = r'E:\data\Tencent\xwechat_files\all_users\config\global_config'.replace('\\', '/')
        target_dir2 = r'E:\data\Tencent\xwechat_files\all_users\config\global_config.crc'.replace('\\', '/')

        # 复制配置文件
        try:
            os.remove(target_dir1)
            os.remove(target_dir2)
            # shutil.rmtree(r'E:\data\Tencent\xwechat_files\all_users\config')
            # os.makedirs(r'E:\data\Tencent\xwechat_files\all_users\config')
            shutil.copy2(source_dir1, target_dir1)
            shutil.copy2(source_dir2, target_dir2)
        except Exception as e:
            print(f"复制配置文件失败: {e}")

        os.startfile('D:\software\Tencent\Weixin\Weixin.exe')

    # def test_unlock(self):
    #     # [Weixin.dll]
    #     dll = path(input("\nWeixin.dll: "))
    #     data = load(dll)
    #     # Block multi-instance check (lock.ini)
    #     # Search 'lock.ini' and move down a bit, find something like:
    #     # `if ( sub_7FFF9EDBF6E0(&unk_7FFFA6A09B48) && !sub_7FFF9EDC0880(&unk_7FFFA6A09B48, 1LL) )`
    #     # The second function is the LockFileHandler, check it out, find:
    #     # ```
    #     # if ( !LockFileEx(v4, 2 * (a2 != 0) + 1, 0, 0xFFFFFFFF, 0xFFFFFFFF, &Overlapped) )
    #     # {
    #     #   LastError = GetLastError();
    #     #   v5 = sub_7FFF9EDC09C0(LastError);
    #     # }
    #     # ```
    #     # Hex context:
    #     # C7 44 24: [20] FF FF FF FF  // MOV [RSP+20], 0xFFFFFFFF
    #     #                                  Overlapped.Offset = -1
    #     # 31 F6                       // XOR ESI, ESI
    #     # 45 31 C0                    // XOR R8D, R8D
    #     # 41 B9:     FF FF FF FF      // MOV R9D, 0xFFFFFFFF
    #     #                                  Overlapped.OffsetHigh = -1
    #     # FF 15:    [CB 31 48 06]     // CALL [<LockFileEx>]
    #     # 85 C0                       // TEST EAX, EAX
    #     # 75:       [0F]              // JNE [+0F], the if statement
    #     # Change JNZ to JMP in order to force check pass.
    #     print(f"\n> Blocking multi-instance check")
    #     UNLOCK_PATTERN = """
    #     C7 44 24 ?? FF FF FF FF
    #     31 F6
    #     45 31 C0
    #     41 B9 FF FF FF FF
    #     FF 15 ?? ?? ?? ??
    #     85 C0
    #     75 0F
    #     """
    #     UNLOCK_REPLACE = """
    #     ...
    #     EB 0F
    #     """
    #     data = wildcard_replace(data, UNLOCK_PATTERN, UNLOCK_REPLACE)
    #     # Backup and save
    #     backup(dll)
    #     save(dll, data)
    #     pause()

    def test_set_parent_wnd(self):
        import ctypes
        from ctypes import wintypes
        import time

        # 定义 Windows API 函数
        user32 = ctypes.windll.user32

        # 获取目标窗口句柄和你的窗口句柄
        hwnd_target = user32.FindWindowW(None, "微信 - 吾峰起浪")
        hwnd_my_window = user32.FindWindowW(None, "微信多开管理器")

        # 获取你的窗口大小
        my_window_rect = wintypes.RECT()
        user32.GetWindowRect(hwnd_my_window, ctypes.byref(my_window_rect))
        my_window_width = my_window_rect.right - my_window_rect.left
        my_window_height = my_window_rect.bottom - my_window_rect.top

        # 记录目标窗口的初始位置
        last_rect = wintypes.RECT()
        user32.GetWindowRect(hwnd_target, ctypes.byref(last_rect))

        # 调整你的窗口初始位置（位于目标窗口左侧）
        user32.SetWindowPos(
            hwnd_my_window,
            None,  # 无 Z 序调整
            last_rect.left - my_window_width,  # 目标窗口左侧
            last_rect.top,  # 与目标窗口顶部对齐
            0, 0,  # 不调整窗口大小
            0x0001  # SWP_NOSIZE
        )

        # 定期检查目标窗口位置
        while True:
            rect = wintypes.RECT()
            user32.GetWindowRect(hwnd_target, ctypes.byref(rect))

            # 如果目标窗口位置发生变化，调整你的窗口位置
            if rect.left != last_rect.left or rect.top != last_rect.top:
                # 计算你的窗口位置（位于目标窗口左侧）
                user32.SetWindowPos(
                    hwnd_my_window,
                    None,  # 无 Z 序调整
                    rect.left - my_window_width,  # 目标窗口左侧
                    rect.top,  # 与目标窗口顶部对齐
                    0, 0,  # 不调整窗口大小
                    0x0001  # SWP_NOSIZE
                )
                last_rect = rect

            # 设置检查间隔（100ms）
            time.sleep(0.02)

    def test_get_ini_config(self):
        config = IniUtils.load_ini_as_dict(Config.SETTING_INI_PATH)
        print(config.__dict__)

    def test_get_wnd_state(self):
        hwnd = 334080
        while True:
            curr_linked_wnd_state = SidebarUI.get_linked_wnd_state(hwnd)
            print(f"{hwnd}当前状态: "
                  f"最小化={curr_linked_wnd_state[WndProperties.IS_MINIMIZED]}, "
                  f"最大化={curr_linked_wnd_state[WndProperties.IS_MAXIMIZED]}, "
                  f"前台={curr_linked_wnd_state[WndProperties.IS_FOREGROUND]}, "
                  f"隐藏={curr_linked_wnd_state[WndProperties.IS_HIDDEN]},"
                  f"位置={curr_linked_wnd_state[WndProperties.RECT]}")  # 每次监听都打印状态

    def test_get_widget_by_name(self):
        main_hwnd = 93198856
        hwnd_utils.restore_window(main_hwnd)
        time.sleep(0.2)
        hwnd_utils.do_click_in_wnd(main_hwnd, 8, 8)
        hwnd_utils.do_click_in_wnd(main_hwnd, 8, 8)

    def test_get_WXWork_mmap(self):
        for f in psutil.Process(27644).memory_maps():
            print(f)

    def test_get_all_sw_mutant_handles(self):
        sw = "Weixin"
        mutant_handles = SwOperator.get_sw_all_mutex_handles_and_try_kill_if_need(sw)
        Printer().debug(mutant_handles)

    def test_get_handles_by_pids_and_handle_name_wildcards(self):
        pids = [47632]
        handle_names = ['_WeChat_App_Instance_Identity_Mutex_Name']
        handles = handle_utils.pywinhandle_find_handles_by_pids_and_handle_name_wildcards(pids, handle_names)
        print(handles)

    def test_my_find_handle_in_pid(self):
        pid = 30556
        handle_names = ["global_config"]
        result = handle_utils.pywinhandle_find_handles_by_pids_and_handle_names(
            [pid],
            handle_names
        )
        print(result)

    def test_search_from_features(self):
        dll_path = r'D:\software\Tencent\Weixin\4.0.5.13\Weixin.dll'
        original_features = [
            "E9 68 02 00 00 0F 1F 84 00 00 00 00 00",
            "6b ?? ?? 73 48 89 05 3a db 7f 00 66",
            "E4 B8 8D E6 94 AF E6 8C 81 E7 B1 BB E5 9E 8B E6 B6 88 E6 81 AF 5D 00",
            "9A 82 E4 B8 8D E6 94 AF E6 8C 81 E8 AF A5 E5 86 85 E5 AE B9 EF BC 8C"
        ]
        modified_features = [
            "3D 12 27 00 00 0F 85 62 02 00 00 90 90",
            "8B B5 20 04 00 00 81 C6 12 27 00 00",
            "E6 92 A4 E5 9B 9E E4 BA 86 E4 B8 80 E6 9D A1 E6 B6 88 E6 81 AF 5D 00",
            "92 A4 E5 9B 9E E4 BA 86 E4 B8 80 E6 9D A1 E6 B6 88 E6 81 AF 00 BC 8C"
        ]
        features_tuple = (original_features, modified_features)
        res = SwInfoUtils.search_patterns_and_replaces_by_features(dll_path, features_tuple)
        print(res)

    def test_create_lnk_for_account(self):
        AccOperator._create_starter_lnk_for_acc("WeChat", "wxid_5daddxikoccs22")
        AccOperator._create_starter_lnk_for_acc("WeChat", "wxid_h5m0aq1uvr2f22")

    def test_add_coexist_extra_cfg(self):
        sw = "WXWork"
        mode = RemoteCfg.COEXIST.value
        # dll_dir = r"D:\software\Tencent\Weixin\4.0.6.21"
        # SwInfoFunc._update_adaptation_from_remote_to_extra(sw, mode, dll_dir)
        """根据远程表内容更新额外表"""
        config_data = subfunc_file.read_remote_cfg_in_rules()
        if not config_data:
            return
        patch_dll, mode_branches_dict = subfunc_file.get_remote_cfg(sw, patch_dll=None, **{mode: None})
        if patch_dll is None or mode_branches_dict is None:
            return
        dll_path = r"D:\software\Tencent\WXWork\WXWork.exe"
        # 尝试寻找兼容版本并添加到额外表中
        cur_sw_ver = SwInfoFunc.calc_sw_ver(sw)
        subfunc_file.update_extra_cfg(sw, patch_dll=os.path.basename(dll_path))
        if "precise" in mode_branches_dict:
            precise_vers_dict = mode_branches_dict["precise"]
            if cur_sw_ver in precise_vers_dict:
                # 用精确版本特征码查找适配
                precise_ver_adaptations = precise_vers_dict[cur_sw_ver]
                for channel, adaptation in precise_ver_adaptations.items():
                    subfunc_file.update_extra_cfg(
                        sw, mode, "precise", cur_sw_ver, **{channel: adaptation})
        if "feature" in mode_branches_dict:
            feature_vers = list(mode_branches_dict["feature"].keys())
            compatible_ver = VersionUtils.find_compatible_version(cur_sw_ver, feature_vers)
            ver_channels_dict = subfunc_file.get_cache_cfg(sw, mode, "precise", cur_sw_ver)
            if compatible_ver:
                # 用兼容版本特征码查找适配
                compatible_ver_adaptations = mode_branches_dict["feature"][compatible_ver]
                for channel in compatible_ver_adaptations.keys():
                    if ver_channels_dict is not None and channel in ver_channels_dict:
                        print("已存在缓存的精确适配")
                        continue
                    original_feature = compatible_ver_adaptations[channel]["original"]
                    modified_feature = compatible_ver_adaptations[channel]["modified"]
                    result_dict = SwInfoUtils.search_patterns_and_replaces_by_features(
                        dll_path, (original_feature, modified_feature))
                    if result_dict:
                        # 添加到额外表中
                        subfunc_file.update_extra_cfg(
                            sw, mode, "precise", cur_sw_ver, **{channel: result_dict})

    def test_create_new_coexist(self):
        """测试"""
