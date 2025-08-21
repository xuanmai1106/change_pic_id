#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import os
import re
import sys
from typing import List, Set

import pandas as pd

#读取文件名在main中修改

IMAGE_URL_PATTERN = re.compile(r'image_url"\s*:\s*"https?://[^/]+/recipe/(\d+_\d+)\.jpg"', re.IGNORECASE)


def extract_filenames_from_text(text: str) -> List[str]:
    """从包含 stages 文本的单元格中抽取所有图片文件基名（不含扩展名）。

    例如返回 ["206_1", "206_2", ...]
    """
    if not isinstance(text, str) or not text:
        return []
    return IMAGE_URL_PATTERN.findall(text)


def collect_expected_filenames(csv_path: str) -> Set[str]:
    """读取 CSV，汇总所有期望存在的图片文件基名集合（不含扩展名）。"""
    df = pd.read_csv(csv_path, encoding='utf-8-sig')

    # 兼容不同列名：stage 或 content 等
    candidate_cols = [
        'stage', 'stages', 'content',  # 最常见
    ]
    col = None
    for c in candidate_cols:
        if c in df.columns:
            col = c
            break
    if col is None:
        raise ValueError(f"未找到包含阶段数据的列，尝试列名：{candidate_cols}")

    expected: Set[str] = set()
    for cell in df[col].astype(str).tolist():
        names = extract_filenames_from_text(cell)
        expected.update(names)
    return expected


def main() -> int:
    parser = argparse.ArgumentParser(description='检查 CSV 中 image_url 对应图片在目录下是否存在')
    parser.add_argument('--csv', default='recipes_801_934_extract_stage.csv', help='输入 CSV 文件路径')
    parser.add_argument('--image-dir', default=os.path.join('801_934'), help='图片所在目录')
    args = parser.parse_args()

    csv_path = args.csv
    image_dir = args.image_dir

    if not os.path.exists(csv_path):
        print(f"错误：找不到 CSV 文件：{csv_path}")
        return 1
    if not os.path.isdir(image_dir):
        print(f"错误：找不到图片目录：{image_dir}")
        return 1

    try:
        expected = collect_expected_filenames(csv_path)
    except Exception as e:
        print(f"解析 CSV 失败：{e}")
        return 1

    missing: List[str] = []
    for name in sorted(expected, key=lambda x: (int(x.split('_')[0]), int(x.split('_')[1])) if '_' in x else x):
        jpg_path = os.path.join(image_dir, f"{name}.jpg")
        if not os.path.exists(jpg_path):
            missing.append(f"{name}.jpg")

    # 接受的图片扩展名（仅 .jpg）
    accepted_exts = ['.jpg']

    # 实际存在的图片：
    # 1) present_map：命名符合 NNN_S（如 233_3） 的基名 -> 实际文件名列表（可能含不同扩展）
    # 2) other_present_files：图片文件但命名不符合 NNN_S（如 500.jpg、readme.jpeg 等）
    present_map: dict[str, list[str]] = {}
    other_present_files: list[str] = []
    try:
        for entry in os.scandir(image_dir):
            if not entry.is_file():
                continue
            name = entry.name
            name_lower = name.lower()
            matched = False
            for ext in accepted_exts:
                if name_lower.endswith(ext):
                    matched = True
                    stem = name_lower[:-len(ext)]
                    if re.fullmatch(r"\d+_\d+", stem):
                        present_map.setdefault(stem, []).append(name)
                    else:
                        # 不是 NNN_S 的图片文件（如仅数字 500.jpg），记为多余
                        other_present_files.append(name)
                    break
            # 不处理无扩展名或其他扩展的文件
    except Exception as e:
        print(f"读取图片目录失败：{e}")

    # 统计缺失：若该基名在 present_map 中存在任一扩展名，即不缺失
    missing: List[str] = []
    for name in sorted(expected, key=lambda x: (int(x.split('_')[0]), int(x.split('_')[1])) if '_' in x else x):
        if name not in present_map:
            # 按原始规则输出为 .jpg 名称
            missing.append(f"{name}.jpg")

    # 统计“多出来的图片”
    extras: List[str] = []
    # a) 符合 NNN_S 但 CSV 未包含的基名 -> 列出其实际文件名
    for stem in sorted(set(present_map.keys()) - expected, key=lambda x: (int(x.split('_')[0]), int(x.split('_')[1]))):
        extras.extend(sorted(present_map[stem]))
    # b) 不符合 NNN_S 的图片文件，直接视为多余（如 500.jpg）
    extras.extend(sorted(other_present_files))

    total_expected = len(expected)
    # 目录内图片总数（符合扩展的全部文件 + 无扩展但疑似图片名）
    total_present = sum(len(v) for v in present_map.values()) + len(other_present_files)
    print(f"CSV 解析应存在图片数：{total_expected}")
    print(f"目录实际存在图片数：{total_present}")

    if missing:
        print(f"缺失图片数量：{len(missing)}")
        print("缺失列表（文件名）：")
        for fn in missing:
            print(fn)
    else:
        print("缺失图片数量：0")

    if extras:
        print(f"多出来的图片数量：{len(extras)}")
        print("多余列表（文件名）：")
        for fn in extras:
            print(fn)
    else:
        print("多出来的图片数量：0")

    return 0


if __name__ == '__main__':
    sys.exit(main())


