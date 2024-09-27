import os
import xml.etree.ElementTree as ET

base_dir = os.getcwd().replace('\\', '/')


def get_title_by_path(xml_file, search_path):
    tree = ET.parse(xml_file)
    root = tree.getroot()

    for tree_element in root.findall('tree'):
        if tree_element.get('path') == search_path:
            return tree_element.get('title')

    return ''  # 如果未找到对应的path，返回None


def load_config(xml_file):
    tree = ET.parse(xml_file)
    root = tree.getroot()
    config = {child.tag: child.text for child in root}
    return config


def traverse_directory(path, level=0, **kwargs):
    formatted_dirs = []  # 用于存放文件夹的列表
    formatted_files = []  # 用于存放文件的列表
    indent = '│ ' * level + '├─'

    ignore_dot_dir = kwargs.get('ignore_dot_dir', 'false').lower() == 'true'
    ignore_dot_file = kwargs.get('ignore_dot_file', 'false').lower() == 'true'
    ignore_file_suffix_list = kwargs.get('ignore_file_suffix_list', '').split(',')
    ignore_dir_list = kwargs.get('ignore_dir_list', '').split(',')
    tree_info_tip_xml = kwargs.get('tree_info_tip_xml', '')

    for item in os.listdir(path):
        item_path = os.path.join(path, item)
        if os.path.isdir(item_path):
            if ignore_dot_dir and item.startswith('.'):
                continue
            if len(ignore_dir_list) > 0 and any(item == dirname for dirname in ignore_dir_list):
                continue
            comment = ''
            if tree_info_tip_xml:
                comment = get_title_by_path(tree_info_tip_xml, item_path.replace('\\', '/').replace(base_dir, ''))
                if comment:
                    comment = " # " + comment
            formatted_dirs.append((f"{indent}📁 {item}", comment))
            formatted_dirs.extend(traverse_directory(item_path, level + 1, **kwargs))  # Recurse into the folder
        else:
            if ignore_dot_file and item.startswith('.'):
                continue
            if ignore_file_suffix_list and any(item.endswith(suffix) for suffix in ignore_file_suffix_list):
                continue
            comment = ''
            if tree_info_tip_xml:
                comment = get_title_by_path(tree_info_tip_xml, item_path.replace('\\', '/').replace(base_dir, ''))
                if comment:
                    comment = " # " + comment
            formatted_files.append((f"{indent}📄 {item}", comment))

    # 合并文件夹和文件
    return formatted_dirs + formatted_files


def main():
    config = load_config('tree_config.xml')
    formatted_output = traverse_directory(os.getcwd(), **config)
    print(os.getcwd())

    max_length = max(len(line[0]) for line in formatted_output) if formatted_output else 0
    least_indent_length = config.get('least_indent_length', '2')  # 默认值为字符串'2'
    try:
        least_indent_length = int(least_indent_length)
    except ValueError:
        least_indent_length = 2  # 转换失败时使用默认值2
    indent_char = config.get('indent_char', '-')

    dir_tree = []
    for i in range(len(formatted_output)):
        dir_tree_lines = formatted_output[i][0] + indent_char * (
                max_length - len(formatted_output[i][0]) + least_indent_length) + formatted_output[i][1]
        dir_tree.append(dir_tree_lines)
    # Write to tree.txt
    with open('tree.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(dir_tree))


if __name__ == "__main__":
    main()