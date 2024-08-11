import configparser
import os
import winreg

import psutil


def get_wechat_install_path_from_ini():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    ini_path = os.path.join(script_dir, 'path.ini').replace('\\', '/')
    if os.path.exists(ini_path):
        config = configparser.ConfigParser()
        config.read(ini_path)
        if 'WxMultiple' in config and 'WxPath' in config['WxMultiple']:
            wx_path = config['WxMultiple']['WxPath']
            if os.path.exists(wx_path):
                return wx_path
    return None


def save_wechat_install_path_to_ini(wx_path):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    ini_path = os.path.join(script_dir, 'path.ini').replace('\\', '/')
    config = configparser.ConfigParser()
    if os.path.exists(ini_path):
        config.read(ini_path)
    if 'WxMultiple' not in config:
        config['WxMultiple'] = {}
    config['WxMultiple']['WxPath'] = wx_path
    with open(ini_path, 'w') as configfile:
        config.write(configfile)


def get_wechat_install_path_from_process():
    for process in psutil.process_iter(['name', 'exe']):
        if process.info['name'] == 'WeChat.exe':
            return process.info['exe'].replace('\\', '/')
    return None


def get_wechat_install_path_from_register():
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                             r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\WeChat")
        path = winreg.QueryValueEx(key, "InstallLocation")[0].replace('\\', '/')
        winreg.CloseKey(key)
        print(f"在注册表获取到微信安装地址：{path}")
        return path
    except:
        return None


def is_valid_wechat_install_path(path):
    config_data_path = os.path.join(path, "Wechat.exe").replace('\\', '/')
    return os.path.isfile(config_data_path)


def get_wechat_install_path():
    wechat_install_path = get_wechat_install_path_from_ini()

    if not wechat_install_path:
        wechat_install_path = os.path.join(get_wechat_install_path_from_register(),
                                           'WeChat.exe').replace('\\', '/')
        if not os.path.exists(wechat_install_path):
            wechat_install_path = os.path.join(os.environ.get('ProgramFiles'), 'Tencent', 'WeChat',
                                               'WeChat.exe').replace('\\', '/')

        if not os.path.exists(wechat_install_path):
            wechat_install_path = os.path.join(os.environ.get('ProgramFiles(x86)'), 'Tencent', 'WeChat',
                                               'WeChat.exe').replace('\\', '/')

        if not os.path.exists(wechat_install_path):
            wechat_install_path = get_wechat_install_path_from_process()

        if not wechat_install_path or not os.path.exists(wechat_install_path):
            return None

        save_wechat_install_path_to_ini(wechat_install_path)

    return wechat_install_path


def get_wechat_data_path_from_ini():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    ini_path = os.path.join(script_dir, 'path.ini').replace('\\', '/')
    if os.path.exists(ini_path):
        config = configparser.ConfigParser()
        config.read(ini_path)
        if 'WxMultiple' in config and 'DtPath' in config['WxMultiple']:
            dt_path = config['WxMultiple']['DtPath']
            if is_valid_wechat_data_path(dt_path):
                return dt_path
    return None


def save_wechat_data_path_to_ini(dt_path):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    ini_path = os.path.join(script_dir, 'path.ini').replace('\\', '/')
    config = configparser.ConfigParser()
    if os.path.exists(ini_path):
        config.read(ini_path)
    if 'WxMultiple' not in config:
        config['WxMultiple'] = {}
    config['WxMultiple']['DtPath'] = dt_path
    with open(ini_path, 'w') as configfile:
        config.write(configfile)


def get_wechat_data_path_from_registry():
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Tencent\WeChat", 0, winreg.KEY_READ)
        value, _ = winreg.QueryValueEx(key, "FileSavePath")
        winreg.CloseKey(key)
        value = os.path.join(value, "WeChat Files").replace('\\', '/')
        if is_valid_wechat_data_path(value):
            print(f"在注册表获取到微信数据地址：{value}")
            return value
    except WindowsError:
        pass
    return None


def is_valid_wechat_data_path(path):
    config_data_path = os.path.join(path, "All Users", "config", "config.data").replace('\\', '/')
    return os.path.isfile(config_data_path)


def get_wechat_data_path():
    wechat_data_path = get_wechat_data_path_from_ini()

    if not wechat_data_path:
        common_paths = [
            os.path.join(os.path.expanduser('~'), 'Documents', 'WeChat Files').replace('\\', '/'),
            os.path.join(os.environ.get('APPDATA'), 'Tencent', 'WeChat').replace('\\', '/'),
        ]

        for path in common_paths:
            if is_valid_wechat_data_path(path):
                wechat_data_path = path
                break

        if not wechat_data_path:
            wechat_data_path = get_wechat_data_path_from_registry()

        if not wechat_data_path:
            for process in psutil.process_iter(['name', 'cmdline']):
                if process.info['name'] == 'WeChat.exe':
                    cmdline = process.info['cmdline']
                    for arg in cmdline:
                        arg = arg.replace('\\', '/')
                        if is_valid_wechat_data_path(arg):
                            wechat_data_path = arg
                            break
                    if wechat_data_path:
                        break

        if wechat_data_path:
            save_wechat_data_path_to_ini(wechat_data_path)
        else:
            return None

    return wechat_data_path


if __name__ == "__main__":
    path = get_wechat_install_path()
    if path:
        print(f"微信安装路径: {path}")
    else:
        print("未能找到微信安装路径")
    path = get_wechat_data_path()
    if path:
        print(f"微信数据存储路径: {path}")
    else:
        print("未能找到微信数据存储路径")
