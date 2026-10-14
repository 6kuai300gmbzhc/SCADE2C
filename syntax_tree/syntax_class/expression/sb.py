from typing import Optional
import os

def get_files_from_subfolders(target_folder):
    # 遍历目标文件夹下的所有一级子文件夹
    for subfolder in os.listdir(target_folder):
        if subfolder.startswith("__"):
            continue
        subfolder_path = os.path.join(target_folder, subfolder)
        # 判断是否为文件夹
        if os.path.isdir(subfolder_path):
            # 遍历子文件夹中的所有文件
            for file in os.listdir(subfolder_path):
                file_path = os.path.join(subfolder_path, file)
                if os.path.isfile(file_path):
                    print(f"{subfolder}_{file[:-3]}")
                    # print(f"from .{subfolder}.{file[:-3]} import {subfolder}_{file[:-3]}")

# 替换为你的目标文件夹路径
target_folder_path = "."
get_files_from_subfolders(target_folder_path)