import tkinter as tk
from functools import partial
from tkinter import ttk

from PIL import ImageTk, Image

from functions import func_config, func_account, subfunc_file, subfunc_sw
from resources import Constants, Strings
from ui import detail_ui
from utils import widget_utils, string_utils
from utils.logger_utils import mylogger as logger
from utils.widget_utils import UnlimitedClickHandler


def try_convert(value):
    try:
        return float(value)
    except ValueError:
        return value


class TreeviewRowUI:
    def __init__(self, root, root_class, root_main_frame, result, data_path, sw):
        self.sw = sw
        self.acc_index = None
        self.hovered_item = None
        self.photo_images = []
        self.selected_accounts = {
            "login": [],
            "logout": []
        }
        self.selected_items = {
            "login": [],
            "logout": []
        }
        self.logout_tree = None
        self.login_tree = None
        self.root_class = root_class
        self.data_path = data_path
        self.tooltips = {}
        self.root = root
        self.main_frame = root_main_frame

        # 构建ui
        self.tree_frame = tk.Frame(self.main_frame)
        self.tree_frame.pack(expand=True, fill=tk.BOTH)
        self.sign_visible:bool = subfunc_file.fetch_global_setting_or_set_default("sign_visible") == "True"

        # 构建列表
        acc_list_dict, _, _ = result
        logins = acc_list_dict["login"]
        logouts = acc_list_dict["logout"]
        # 调整行高
        style = ttk.Style()
        style.configure("RowTreeview", background="#FFFFFF", foreground="black",
                        rowheight=Constants.TREE_ROW_HEIGHT, selectmode="none")
        style.layout("RowTreeview", style.layout("Treeview"))  # 继承默认布局

        if len(logins) != 0:
            # 已登录框架=已登录标题+已登录列表
            self.login_frame = ttk.Frame(self.tree_frame)
            self.login_frame.pack(side=tk.TOP, fill=tk.X,
                                  padx=Constants.LOG_IO_FRM_PAD_X, pady=Constants.LOG_IO_FRM_PAD_Y)

            # 已登录标题=已登录复选框+已登录标签+已登录按钮区域
            self.login_title = ttk.Frame(self.login_frame)
            self.login_title.pack(side=tk.TOP, fill=tk.X)

            # 已登录复选框
            self.login_checkbox_var = tk.IntVar(value=0)
            self.login_checkbox = tk.Checkbutton(
                self.login_title,
                variable=self.login_checkbox_var,
                tristatevalue=-1
            )
            self.login_checkbox.pack(side=tk.LEFT)

            # 已登录标签
            self.login_label = ttk.Label(self.login_title, text="已登录账号：",
                                         style='FirstTitle.TLabel')
            self.login_label.pack(side=tk.LEFT, fill=tk.X, anchor="w", pady=Constants.LOG_IO_LBL_PAD_Y)

            # 已登录按钮区域=一键退出
            self.login_button_frame = ttk.Frame(self.login_title)
            self.login_button_frame.pack(side=tk.RIGHT)

            # 一键退出
            self.one_key_quit = ttk.Button(
                self.login_button_frame, text="一键退出", style='Custom.TButton',
                command=lambda: func_account.to_quit_selected_accounts(
                    self.sw, self.selected_accounts["login"], self.root_class.refresh_main_frame
                ))
            self.one_key_quit.pack(side=tk.RIGHT)
            # 配置
            self.config_btn = ttk.Button(
                self.login_button_frame, text="❐配 置", style='Custom.TButton',
                command=lambda: self.root_class.to_create_config(self.selected_accounts["login"][0])
            )
            self.config_btn.pack(side=tk.RIGHT)
            widget_utils.disable_button_and_add_tip(
                self.tooltips, self.config_btn, "请选择一个账号进行配置，配置前有符号表示推荐配置的账号")

            login_tree = self.create_table("login")
            # self.login_trees[self.chosen_tab] = login_tree
            # self.login_tree = self.login_trees[self.chosen_tab]
            self.login_tree = login_tree
            self.display_table(logins, "login")
            self.update_top_title("login")
            self.login_tree.bind("<Leave>", partial(self.on_leave))
            self.login_tree.bind("<Motion>", partial(self.on_mouse_motion))

            UnlimitedClickHandler(
                self.root,
                self.login_tree,
                partial(self.toggle_selection, "login"),
                partial(self.double_selection, "login")
            )

            self.apply_or_switch_col_order(self.login_tree, "login")

        if len(logouts) != 0:
            # 未登录框架=未登录标题+未登录列表
            self.logout_frame = ttk.Frame(self.tree_frame)
            self.logout_frame.pack(side=tk.TOP, fill=tk.X,
                                   padx=Constants.LOG_IO_FRM_PAD_X, pady=Constants.LOG_IO_FRM_PAD_Y)

            # 未登录标题=未登录复选框+未登录标签+未登录按钮区域
            self.logout_title = ttk.Frame(self.logout_frame)
            self.logout_title.pack(side=tk.TOP, fill=tk.X)

            # 未登录复选框
            self.logout_checkbox_var = tk.IntVar(value=0)
            self.logout_checkbox = tk.Checkbutton(
                self.logout_title,
                variable=self.logout_checkbox_var,
                tristatevalue=-1
            )
            self.logout_checkbox.pack(side=tk.LEFT)

            # 未登录标签
            self.logout_label = ttk.Label(self.logout_title, text=f"未登录账号：",
                                          style='FirstTitle.TLabel')
            self.logout_label.pack(side=tk.LEFT, fill=tk.X, anchor="w", pady=Constants.LOG_IO_LBL_PAD_Y)

            # 未登录按钮区域=一键登录
            self.logout_button_frame = ttk.Frame(self.logout_title)
            self.logout_button_frame.pack(side=tk.RIGHT)

            # 一键登录
            self.one_key_auto_login = ttk.Button(
                self.logout_button_frame, text="一键登录", style='Custom.TButton',
                command=lambda: self.root_class.to_auto_login(self.selected_items["logout"])
            )
            self.one_key_auto_login.pack(side=tk.RIGHT)

            # 更新顶部复选框状态
            self.logout_tree = self.create_table("logout")
            self.display_table(logouts, "logout")
            self.update_top_title("logout")
            self.logout_tree.bind("<Leave>", partial(self.on_leave))
            self.logout_tree.bind("<Motion>", partial(self.on_mouse_motion))

            UnlimitedClickHandler(
                self.root,
                self.logout_tree,
                partial(self.toggle_selection, "logout"),
                partial(self.double_selection, "logout")
            )

            self.apply_or_switch_col_order(self.logout_tree, "logout")

    def create_table(self, table_type):
        """定义表格，根据表格类型选择手动或自动登录表格"""
        columns = (" ", "配置", "pid", "原始id", "当前id", "昵称")
        self.acc_index = columns.index("原始id")
        tree = ttk.Treeview(self.tree_frame, columns=columns, show='tree', height=1, style="RowTreeview")

        # 设置列标题和排序功能
        for col in columns:
            tree.heading(
                col, text=col,
                command=lambda c=col: self.apply_or_switch_col_order(tree, table_type, c)
            )
            tree.column(col, anchor='center')  # 设置列宽

        # 特定列的宽度和样式设置
        tree.column("#0", minwidth=Constants.TREE_ID_MIN_WIDTH,
                    width=Constants.TREE_ID_WIDTH, stretch=tk.NO)
        tree.column("pid", minwidth=Constants.TREE_PID_MIN_WIDTH,
                    width=Constants.TREE_PID_WIDTH, anchor='e', stretch=tk.NO)
        tree.column("配置", minwidth=Constants.TREE_CFG_MIN_WIDTH,
                    width=Constants.TREE_CFG_WIDTH, anchor='center', stretch=tk.NO)
        tree.column(" ", minwidth=Constants.TREE_DSP_MIN_WIDTH,
                    width=Constants.TREE_DSP_WIDTH, anchor='w')
        tree.column("原始id", anchor='center')
        tree.column("当前id", anchor='center')

        tree.pack(fill=tk.X, expand=True, padx=(10, 0))

        selected_bg = "#B2E0F7"
        hover_bg = "#E5F5FD"

        # 设置标签样式
        tree.tag_configure("disabled", background="#F5F7FA", foreground="grey")
        tree.tag_configure("selected", background=selected_bg, foreground="black")
        tree.tag_configure("hover", background=hover_bg, foreground="black")

        tree.bind("<Configure>", lambda e,t=tree:self.adjust_columns_on_maximize(e,t), add='+')

        return tree

    def display_table(self, accounts, login_status):
        if login_status == "login":
            tree = self.login_tree
        elif login_status == "logout":
            tree = self.logout_tree
        else:
            tree = ttk.Treeview(self.tree_frame, show='tree', height=1, style="RowTreeview")
        curr_config_acc = subfunc_file.get_curr_wx_id_from_config_file(self.data_path, self.sw)
        for account in accounts:
            display_name = "  " + func_account.get_acc_origin_display_name(self.sw, account)
            config_status = func_config.get_config_status_by_account(account, self.data_path, self.sw)
            avatar_url, alias, nickname, pid, has_mutex = subfunc_file.get_sw_acc_details_from_json(
                self.sw,
                account,
                avatar_url=None,
                alias="请获取数据",
                nickname="请获取数据",
                pid=None,
                has_mutex=None
            )

            img = func_account.get_acc_avatar_from_files(account, self.sw)
            img = img.resize(Constants.AVT_SIZE, Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)

            self.photo_images.append(photo)


            prefix = Strings.MUTEX_SIGN if has_mutex and self.sign_visible else ""
            pid = prefix + str(pid) + " "
            prefix = Strings.CFG_SIGN if account == curr_config_acc and self.sign_visible else ""
            config_status = prefix + str(config_status) + ""

            try:
                tree.insert("", "end", iid=account, image=photo,
                            values=(display_name, config_status, pid, account, alias, nickname))
            except Exception as ec:
                logger.warning(ec)
                cleaned_display_name = string_utils.clean_display_name(display_name)
                cleaned_nickname = string_utils.clean_display_name(nickname)
                tree.insert("", "end", iid=account, image=photo,
                            values=(cleaned_display_name, config_status,
                                    pid, account, alias, cleaned_nickname))

            if config_status == "无配置" and login_status == "logout":
                widget_utils.add_a_tag_to_item(self.logout_tree, account, "disabled")

        tree.config(height=len(accounts))

    def adjust_columns_on_maximize(self, _event, tree):
        # print("触发列宽调整")
        columns_to_hide = ["原始id", "当前id", "昵称"]
        # print(tree)
        # print(event.widget)
        tree = tree.nametowidget(tree)
        if self.root.state() != "zoomed":
            # 非最大化时隐藏列和标题
            tree["show"] = "tree"  # 隐藏标题
            for col in columns_to_hide:
                tree.column(col, width=0, stretch=False)
        else:
            # 最大化时显示列和标题
            width = int(self.root.winfo_screenwidth() / 5)
            tree["show"] = "tree headings"  # 显示标题
            for col in columns_to_hide:
                tree.column(col, width=width)  # 设置合适的宽度

    def apply_or_switch_col_order(self, tree, login_status, col=None):
        # 加载列表排序设置
        sort_str = subfunc_file.fetch_sw_setting_or_set_default(self.sw, f"{login_status}_sort")
        tmp_col, sort = sort_str.split(",")
        is_asc: bool = sort == "True"

        if col is not None:
            print("切换列排序...")
            need_switch = True
        else:
            print("应用列排序...")
            need_switch = False
            col = tmp_col

        # 获取当前表格数据的 values、text、image 和 tags
        # print(tree)
        # print(tree.winfo_parent())

        items = [
            {
                "values": tree.item(i)["values"],
                "text": tree.item(i)["text"],
                "image": tree.item(i)["image"],
                "tags": tree.item(i)["tags"],
                "iid": i  # 包括 iid
            }
            for i in tree.get_children()
        ]

        # 当前是否要调成倒序，其和当前顺序的真值是一样的
        need_to_desc:bool = is_asc if need_switch else not is_asc

        # print(f"当前的顺序是：{is_asc}, 是否调整为倒序：{need_to_desc}")

        # 按列排序
        items.sort(
            key=lambda x: (try_convert(x["values"][list(tree["columns"]).index(col)])),
            reverse=need_to_desc # 是否逆序
        )

        # 清空表格并重新插入排序后的数据，保留 values、text、image 和 tags 信息
        for i in tree.get_children():
            tree.delete(i)
        for item in items:
            tree.insert(
                "",  # 父节点为空，表示插入到根节点
                "end",  # 插入位置
                iid=item["iid"],  # 使用字典中的 iid
                text=item["text"],  # #0 列的文本
                image=item["image"],  # 图像对象
                values=item["values"],  # 列数据
                tags=item["tags"]  # 标签
            )

        # 根据排序后的行数调整 Treeview 的高度
        tree.configure(height=len(items))

        # 判断是否切换排序顺序，并保存
        now_asc = not is_asc if need_switch else is_asc
        subfunc_file.save_sw_setting(self.sw, f'{login_status}_sort', f"{col},{now_asc}")

    def get_selected_accounts(self, login_status):
        # 获取选中行的“英语”列数据
        if login_status == "login":
            tree = self.login_tree
            selected_items = self.selected_items["login"]
            selected_accounts = [tree.item(item, "values")[self.acc_index] for item in selected_items]
            self.selected_accounts["login"] = selected_accounts
            # 配置只能是某1个账号
            if len(selected_accounts) == 1:
                widget_utils.enable_button_and_unbind_tip(
                    self.tooltips, self.config_btn)
            else:
                widget_utils.disable_button_and_add_tip(
                    self.tooltips, self.config_btn, "请选择一个账号进行配置，配置前有符号表示推荐配置的账号")
        else:
            tree = self.logout_tree
            selected_items = self.selected_items["logout"]
            selected_accounts = [tree.item(i, "values")[self.acc_index] for i in selected_items]
            self.selected_accounts["logout"] = selected_accounts

    def toggle_top_checkbox(self, _event, login_status):
        """
        切换顶部复选框状态，更新子列表
        :param _event: 触发事件的控件
        :param login_status: 是否登录
        :return: 阻断继续切换
        """
        # print(event.widget)
        # print(self.login_checkbox)
        if login_status == "login":
            checkbox_var = self.login_checkbox_var
            tree = self.login_tree
            selected_items = self.selected_items["login"]
            button = self.one_key_quit
            tip = "请选择要退出的账号"
        else:
            checkbox_var = self.logout_checkbox_var
            tree = self.logout_tree
            selected_items = self.selected_items["logout"]
            button = self.one_key_auto_login
            tip = "请选择要登录的账号"
        checkbox_var.set(not checkbox_var.get())
        value = checkbox_var.get()
        if value:
            widget_utils.enable_button_and_unbind_tip(self.tooltips, button)
            # 执行全选
            for item_id in tree.get_children():
                # print(tree.item(item_id, "tags"))
                if "disabled" not in tree.item(item_id, "tags"):  # 只选择允许选中的行
                    selected_items.append(item_id)
                    widget_utils.add_a_tag_to_item(tree, item_id, "selected")
        else:
            widget_utils.disable_button_and_add_tip(self.tooltips, button, tip)
            # 取消所有选择
            selected_items.clear()
            for item_id in tree.get_children():
                if "disabled" not in tree.item(item_id, "tags"):
                    widget_utils.remove_a_tag_of_item(tree, item_id, "selected")
        self.get_selected_accounts(login_status)  # 更新显示
        return "break"

    def update_top_title(self, login_status):
        """根据AccountRow实例的复选框状态更新顶行复选框状态"""
        # toggle方法
        toggle = partial(self.toggle_top_checkbox, login_status=login_status)

        # 判断是要更新哪一个顶行
        if login_status == "login":
            all_rows = [item for item in self.login_tree.get_children()
                        if "disabled" not in self.login_tree.item(item, "tags")]
            selected_rows = self.selected_items["login"]
            checkbox = self.login_checkbox
            title = self.login_title
            checkbox_var = self.login_checkbox_var
            button = self.one_key_quit
            tip = "请选择要退出的账号"
        else:
            all_rows = [item for item in self.logout_tree.get_children()
                        if "disabled" not in self.logout_tree.item(item, "tags")]
            selected_rows = self.selected_items["logout"]
            checkbox = self.logout_checkbox
            title = self.logout_title
            checkbox_var = self.logout_checkbox_var
            button = self.one_key_auto_login
            tip = "请选择要登录的账号"

        if len(all_rows) == 0 or all_rows is None:
            # 列表为空时解绑复选框相关事件，禁用复选框和按钮
            title.unbind("<Button-1>")
            for child in title.winfo_children():
                child.unbind("<Button-1>")
            checkbox.config(state="disabled")
            widget_utils.disable_button_and_add_tip(self.tooltips, button, tip)
        else:
            # 列表不为空则绑定和复用
            title.bind("<Button-1>", toggle, add="+")
            for child in title.winfo_children():
                child.bind("<Button-1>", toggle, add="+")
            checkbox.config(state="normal")

            # 从子列表的状态来更新顶部复选框
            if len(selected_rows) == len(all_rows):
                checkbox_var.set(1)
                widget_utils.enable_button_and_unbind_tip(self.tooltips, button)
            elif 0 < len(selected_rows) < len(all_rows):
                checkbox_var.set(-1)
                widget_utils.enable_button_and_unbind_tip(self.tooltips, button)
            else:
                checkbox_var.set(0)
                widget_utils.disable_button_and_add_tip(self.tooltips, button, tip)

    def on_leave(self, _event):
        if self.hovered_item is not None:
            widget_utils.remove_a_tag_of_item(self.hovered_item[0], self.hovered_item[1], "hover")
            self.hovered_item = None

    def on_mouse_motion(self, event):
        tree = event.widget

        # 获取当前鼠标所在的行 ID
        item = tree.identify_row(event.y)

        # 检查是否是新的悬停行
        if self.hovered_item is not None:
            if self.hovered_item[0] != tree or self.hovered_item[1] != item:
                widget_utils.remove_a_tag_of_item(tree, self.hovered_item[1], "hover")
                widget_utils.add_a_tag_to_item(tree, item, "hover")
                # 更新当前悬停行
                self.hovered_item = (tree, item)
        else:
            widget_utils.add_a_tag_to_item(tree, item, "hover")
            # 更新当前悬停行
            self.hovered_item = (tree, item)

    def toggle_selection(self, login_status, event=None):
        # print("进入了单击判定")
        if login_status == "login":
            tree = self.login_tree
            selected_items = self.selected_items["login"]
        elif login_status == "logout":
            tree = self.logout_tree
            selected_items = self.selected_items["logout"]
        else:
            tree = None
            selected_items = []
        item_id = tree.identify_row(event.y)
        if len(item_id) == 0:
            return
        if tree.identify_column(event.x) == "#0":  # 检查是否点击了图片列
            self.root_class.open_acc_detail(tree.item(item_id, "values")[self.acc_index])
        else:
            if item_id and "disabled" not in tree.item(item_id, "tags"):  # 确保不可选的行不触发
                if item_id in selected_items:
                    selected_items.remove(item_id)
                    widget_utils.remove_a_tag_of_item(tree, item_id, "selected")
                else:
                    selected_items.append(item_id)
                    widget_utils.add_a_tag_to_item(tree, item_id, "selected")
                self.get_selected_accounts(login_status)  # 实时更新选中行显示
                self.update_top_title(login_status)

    def double_selection(self, login_status, event=None):
        if login_status == "login":
            tree = self.login_tree
            selected_items = self.selected_items["login"]
            callback = lambda: func_account.to_quit_selected_accounts(
                    self.sw, self.selected_accounts["login"], self.root_class.refresh_main_frame
                )
        elif login_status == "logout":
            tree = self.logout_tree
            selected_items = self.selected_items["logout"]
            callback = lambda: self.root_class.to_auto_login(self.selected_accounts["logout"])
        else:
            tree = event.widget
            selected_items = []
            callback = None
        item_id = tree.identify_row(event.y)
        if len(item_id) == 0:
            return
        if tree.identify_column(event.x) == "#0":  # 检查是否点击了图片列
            subfunc_sw.switch_to_sw_account_wnd(
                self.sw, tree.item(item_id, "values")[self.acc_index], self.root)
        else:
            if item_id and "disabled" not in tree.item(item_id, "tags"):  # 确保不可选的行不触发
                selected_items.clear()
                for i in tree.get_children():
                    widget_utils.remove_a_tag_of_item(tree, i, "selected")
                selected_items.append(item_id)
                widget_utils.add_a_tag_to_item(tree, item_id, "selected")
                self.get_selected_accounts(login_status)  # 实时更新选中行显示
                self.update_top_title(login_status)
                callback()
