import tkinter as tk
from tkinter import ttk

from resources import Config, Constants
from utils import json_utils, hwnd_utils
from utils.logger_utils import mylogger as logger


def try_convert(value):
    try:
        return float(value)
    except ValueError:
        return value


class StatisticWindow:
    def __init__(self, wnd, sw, view):
        self.sw = sw
        self.refresh_mode_combobox = None
        self.refresh_tree = None
        self.manual_tree = None
        self.auto_tree = None
        self.auto_count_combobox = None
        self.wnd = wnd
        self.wnd.title(f"{sw}统计数据")
        self.view = view
        self.wnd.attributes('-toolwindow', True)
        self.window_width, self.window_height = Constants.STATISTIC_WND_SIZE
        hwnd_utils.bring_wnd_to_center(self.wnd, self.window_width, self.window_height)
        wnd.grab_set()
        wnd.update_idletasks()

        style = ttk.Style()
        style.configure("Treeview")

        # 创建canvas和滚动条区域，注意要先pack滚动条区域，这样能保证滚动条区域优先级更高
        self.scrollbar_frame = tk.Frame(wnd)
        self.scrollbar_frame.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas = tk.Canvas(wnd, highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, side=tk.LEFT, expand=True)

        # 创建滚动条
        self.scrollbar = ttk.Scrollbar(self.scrollbar_frame, orient="vertical", command=self.canvas.yview)
        self.scrollbar.pack(side=tk.LEFT, fill=tk.Y)
        # 创建一个Frame在Canvas中
        self.main_frame = ttk.Frame(self.canvas)
        # 将main_frame放置到Canvas的窗口中，并禁用Canvas的宽高跟随调整
        self.canvas_window = self.canvas.create_window((0, 0), window=self.main_frame, anchor="nw")
        # 将滚动条连接到Canvas
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        # 配置Canvas的滚动区域
        self.canvas.bind('<Configure>', self.on_canvas_configure)

        self.tree_dict = {
            "manual": {
                "sort": False
            },
            "auto": {
                "sort": False
            },
            "refresh": {
                "sort": False
            }
        }

        self.create_manual_table()
        self.create_auto_table()
        self.create_refresh_table()

        self.display_table()

    def on_mousewheel(self, event):
        """鼠标滚轮触发动作"""
        # 对于Windows和MacOS
        if event.delta:
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        # 对于Linux
        else:
            if event.num == 5:
                self.canvas.yview_scroll(1, "units")
            elif event.num == 4:
                self.canvas.yview_scroll(-1, "units")

    def bind_mouse_wheel(self, widget):
        """递归地为widget及其所有子控件绑定鼠标滚轮事件"""
        widget.bind("<MouseWheel>", self.on_mousewheel, add='+')
        widget.bind("<Button-4>", self.on_mousewheel, add='+')
        widget.bind("<Button-5>", self.on_mousewheel, add='+')

        for child in widget.winfo_children():
            self.bind_mouse_wheel(child)

    def unbind_mouse_wheel(self, widget):
        """递归地为widget及其所有子控件绑定鼠标滚轮事件"""
        widget.unbind("<MouseWheel>")
        widget.unbind("<Button-4>")
        widget.unbind("<Button-5>")

        for child in widget.winfo_children():
            self.unbind_mouse_wheel(child)

    def on_canvas_configure(self, event):
        """动态调整canvas中窗口的宽度，并根据父子间高度关系进行滚轮事件绑定与解绑"""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        width = event.width
        self.canvas.itemconfig(self.canvas_window, width=width)

        if self.main_frame.winfo_height() > self.canvas.winfo_height():
            self.bind_mouse_wheel(self.canvas)
            self.scrollbar.pack(side=tk.LEFT, fill=tk.Y)
        else:
            self.unbind_mouse_wheel(self.canvas)
            self.scrollbar.pack_forget()

    def create_manual_table(self):
        """定义手动登录表格"""
        label = tk.Label(self.main_frame, text="手动登录", font=("Microsoft YaHei", 14, "bold"))
        label.pack(padx=(20, 5))

        columns = ("模式", "最短时间", "使用次数", "平均时间", "最长时间")
        self.manual_tree = ttk.Treeview(self.main_frame,
                                        columns=columns,
                                        show='headings', height=1)
        for col in columns:
            self.manual_tree.heading(col, text=col,
                                     command=lambda c=col: self.sort_column("manual", c))
            self.manual_tree.column(col, anchor='center' if col == "模式" else 'e', width=100)  # 设置列宽

        self.manual_tree.pack(fill=tk.X, expand=True, padx=(20, 5), pady=(0, 10))
        self.tree_dict["manual"]["tree"] = self.manual_tree

    def create_auto_table(self):
        """定义自动登录表格"""
        label = tk.Label(self.main_frame, text="自动登录", font=("Microsoft YaHei", 14, "bold"))
        label.pack(padx=(20, 5))

        description = tk.Label(self.main_frame, text="查看登录第i个账号的数据：")
        description.pack()

        self.auto_count_combobox = ttk.Combobox(self.main_frame, values=[], state="readonly")
        self.auto_count_combobox.pack()
        self.auto_count_combobox.bind("<<ComboboxSelected>>", self.on_selected_auto)

        columns = ("模式", "最短时间", "使用次数", "平均时间", "最长时间")

        self.auto_tree = ttk.Treeview(self.main_frame, columns=columns,
                                      show='headings', height=1)
        for col in columns:
            self.auto_tree.heading(col, text=col,
                                   command=lambda c=col: self.sort_column("auto", c))
            self.auto_tree.column(col, anchor='center' if col == "模式" else 'e', width=100)  # 设置列宽

        self.auto_tree.pack(fill=tk.X, expand=True, padx=(20, 5), pady=(0, 10))
        self.tree_dict["auto"]["tree"] = self.auto_tree

    def create_refresh_table(self):
        """定义刷新表格"""
        label = tk.Label(self.main_frame, text="刷新", font=("Microsoft YaHei", 14, "bold"))
        label.pack(padx=(20, 5))

        description = tk.Label(self.main_frame, text="选择视图查看：")
        description.pack()

        self.refresh_mode_combobox = ttk.Combobox(self.main_frame, values=[], state="readonly")
        self.refresh_mode_combobox.pack()
        self.refresh_mode_combobox.bind("<<ComboboxSelected>>", self.on_selected_refresh)

        columns = ("账号数", "最短时间", "使用次数", "平均时间", "最长时间")
        self.refresh_tree = ttk.Treeview(self.main_frame,
                                         columns=columns,
                                         show='headings', height=1)
        for col in columns:
            self.refresh_tree.heading(col, text=col,
                                      command=lambda c=col: self.sort_column("refresh", c))
            self.refresh_tree.column(col, anchor='center' if col == "账号数" else 'e', width=100)  # 设置列宽

        self.refresh_tree.pack(fill=tk.X, expand=True, padx=(20, 5), pady=(0, 10))
        self.refresh_tree.var = "refresh"
        self.tree_dict["refresh"]["tree"] = self.refresh_tree

    def display_table(self):
        data = json_utils.load_json_data(Config.STATISTIC_JSON_PATH)
        if self.sw not in data:
            data[self.sw] = {}
        tab_info = data.get(self.sw, {})

        # 添加手动统计数据
        manual_data = tab_info.get("manual", {}).get("_", {})
        for mode, stats in manual_data.items():
            min_time, count, avg_time, max_time = stats.split(",")
            self.manual_tree.insert("", "end",
                                    values=(mode, min_time.replace("inf", "null"),
                                            int(float(count)), avg_time, max_time))
        self.manual_tree.config(height=len(manual_data.items()) + 1)

        # 更新下拉框选项
        auto_data = tab_info.get("auto", {})
        index_values = set()  # 使用集合去重
        for mode, _ in auto_data.items():
            if mode == 'avg':
                continue
            index_values.add(mode)  # 添加索引值
        sorted_index_values = sorted(map(int, index_values))  # 将字符串转为整数后排序
        self.auto_count_combobox['values'] = ['avg'] + sorted_index_values  # 设置为排序后的列表
        # 添加自动统计数据
        if self.auto_count_combobox['values']:  # 确保下拉框有值
            self.auto_count_combobox.current(0)  # 默认选择第一个
            # self.update_auto_table_from_selection(self.auto_count_combobox.get())
            self.update_table_from_selection('auto', self.auto_count_combobox.get())

        # 更新下拉框选项
        refresh_data = tab_info.get("refresh", {})
        view_values = set()  # 使用集合去重
        for mode, _ in refresh_data.items():
            # print(f"mode={mode}")
            view_values.add(mode)  # 添加索引值
        # print(view_values)
        sorted_view_values = sorted(map(str, view_values))  # 字符串排序
        self.refresh_mode_combobox['values'] = sorted_view_values  # 设置为排序后的列表
        # 添加刷新统计数据
        if self.refresh_mode_combobox['values']:  # 确保下拉框有值
            if self.view in self.refresh_mode_combobox['values']:
                self.refresh_mode_combobox.current(sorted_view_values.index(self.view))  # 选择当前的视图
            else:
                self.refresh_mode_combobox.current(0)  # 默认选择第一个
            # self.update_refresh_table_from_selection(self.refresh_mode_combobox.get())
            self.update_table_from_selection('refresh', self.refresh_mode_combobox.get())

        for t in self.tree_dict.keys():
            self.sort_column(t, "平均时间")

    def update_table_from_selection(self, mode, selected):
        """根据下拉框的选择，更新对应的表数据"""
        data = json_utils.load_json_data(Config.STATISTIC_JSON_PATH)
        tree = self.tree_dict[mode]['tree']
        # 清空之前的数据
        for item in tree.get_children():
            tree.delete(item)
        refresh_data = data.get(self.sw, {}).get(mode, {}).get(selected, {}).items()
        try:
            for acc_count, stats in refresh_data:
                min_time, count, avg_time, max_time = stats.split(",")
                tree.insert("", "end",
                                         values=(acc_count, min_time.replace("inf", "null"),
                                                 int(float(count)), avg_time, max_time))
            tree.config(height=len(refresh_data) + 1)
        except Exception as e:
            logger.error(e)

    def on_selected_auto(self, event):
        """选中下拉框中的数值时"""
        selected_index = event.widget.get()  # 获取选中的index
        self.update_table_from_selection('auto', selected_index)

    def on_selected_refresh(self, event):
        """选中下拉框中的数值时"""
        selected_view = event.widget.get()  # 获取选中的index
        self.update_table_from_selection("refresh", selected_view)

    def sort_column(self, tree_type, col):
        tree = self.tree_dict[tree_type]['tree']
        items = [(tree.item(i)["values"], i) for i in tree.get_children()]
        is_ascending = self.tree_dict[tree_type]['sort']
        need_to_reverse = is_ascending
        items.sort(key=lambda x: (try_convert(x[0][list(tree["columns"]).index(col)])
                                  if col not in ["模式"] else x[0][list(tree["columns"]).index(col)]),
                   reverse=need_to_reverse)
        # 清空表格并重新插入排序后的数据
        for i in tree.get_children():
            tree.delete(i)
        for item in items:
            tree.insert("", "end", values=item[0])
        tree.configure(height=len(items) + 1)
        self.tree_dict[tree_type]['sort'] = not is_ascending  # 切换排序顺序


# 创建主窗口
if __name__ == "__main__":
    root = tk.Tk()
    statistic_window = StatisticWindow(root, "WeChat", 'tree')
    root.mainloop()
