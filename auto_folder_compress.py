#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
一键图片压缩脚本（可独立运行）

使用方法：
1. 修改下方“可配置参数”中的 TARGET_DIR_NAME（或直接设置 INPUT_DIR）为需要压缩的文件夹
2. 直接运行：python auto_folder_compress.py
3. 压缩结果将输出到输入目录下的 compressed 子目录，并统一为 JPG 格式

支持常见图片格式：JPEG, PNG, WebP, BMP, TIFF 等
压缩策略：
- 小于 min_size_kb：直接转成高质量 JPG（尽量不放大体积）
- 位于 [min_size_kb, max_size_kb]：转成高质量 JPG 归一化格式
- 大于 max_size_kb：按目标大小缩放分辨率并逐步降低质量，直至不超过目标大小
"""

import os
import math
from pathlib import Path
from PIL import Image


# ======================== 可配置参数（请在此修改） ========================
# 方式一：只改文件夹名称（相对于本脚本所在目录）
TARGET_DIR_NAME = "recipes_801_934"  # 例如："recipes_601_700"

# 方式二：直接指定绝对路径（如不使用请留空字符串）
INPUT_DIR_ABS = ""  # 例如：r"D:\\recipe_picture\\recipe_wyc\\压缩\\recipes_601_700"

# 输出目录名称（位于输入目录内）
OUTPUT_SUBDIR_NAME = "compressed"

# 压缩阈值（单位：KB）
MIN_SIZE_KB = 400
MAX_SIZE_KB = 600  # 目标最大大小，同时作为压缩目标

# 初始 JPEG 质量（1-100）
INITIAL_QUALITY = 85
# ======================================================================


class ImageCompressor:
    def __init__(self, min_size_kb: int = 400, max_size_kb: int = 600):
        self.min_size_bytes = min_size_kb * 1024
        self.max_size_bytes = max_size_kb * 1024
        self.target_size_bytes = max_size_kb * 1024

    def _get_file_size(self, filepath: Path) -> int:
        return os.path.getsize(filepath)

    def compress_image(self, input_path: Path, output_path: Path, quality: int = 85) -> str | None:
        input_path = Path(input_path)
        output_path = Path(output_path)

        if not input_path.exists():
            raise FileNotFoundError(f"文件不存在: {input_path}")

        try:
            with Image.open(input_path) as img:
                # 统一转成 RGB；对带透明通道的图（PNG/WebP），使用白色背景
                if img.mode in ("RGBA", "LA", "P"):
                    background = Image.new("RGB", img.size, (255, 255, 255))
                    if img.mode == "P":
                        img = img.convert("RGBA")
                    background.paste(img, mask=img.split()[-1] if img.mode == "RGBA" else None)
                    img = background
                elif img.mode != "RGB":
                    img = img.convert("RGB")

                original_width, original_height = img.size
                original_size = self._get_file_size(input_path)

                # 情况一：小图，转 JPG 高质量
                if original_size < self.min_size_bytes:
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    final_output = output_path.with_suffix(".jpg")
                    img.save(final_output, "JPEG", quality=95, optimize=True)
                    return str(final_output)

                # 情况二：在区间内，标准化为 JPG
                if self.min_size_bytes <= original_size <= self.max_size_bytes:
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    final_output = output_path.with_suffix(".jpg")
                    img.save(final_output, "JPEG", quality=95, optimize=True)
                    return str(final_output)

                # 情况三：大图，按目标大小压缩
                output_path.parent.mkdir(parents=True, exist_ok=True)

                scale_factor = math.sqrt(self.target_size_bytes / original_size)
                new_width = max(1, int(original_width * scale_factor))
                new_height = max(1, int(original_height * scale_factor))

                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

                current_quality = quality
                temp_path = output_path.with_suffix(".tmp.jpg")

                while current_quality > 10:
                    img.save(temp_path, "JPEG", quality=current_quality, optimize=True)
                    current_size = self._get_file_size(temp_path)
                    if current_size <= self.target_size_bytes:
                        final_output = output_path.with_suffix(".jpg")
                        os.replace(temp_path, final_output)
                        return str(final_output)
                    current_quality -= 5

                # 若质量很低仍超标，则继续缩小分辨率
                if os.path.exists(temp_path):
                    os.remove(temp_path)

                while True:
                    new_width = int(new_width * 0.9)
                    new_height = int(new_height * 0.9)
                    if new_width < 100 or new_height < 100:
                        raise ValueError("无法压缩到目标大小，图片太大或目标尺寸太小")

                    img_resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                    img_resized.save(temp_path, "JPEG", quality=50, optimize=True)
                    current_size = self._get_file_size(temp_path)
                    if current_size <= self.target_size_bytes:
                        final_output = output_path.with_suffix(".jpg")
                        os.replace(temp_path, final_output)
                        return str(final_output)

        except Exception as exc:
            print(f"压缩失败: {input_path.name} -> {exc}")
            return None

    def compress_directory(self, input_dir: Path, output_dir: Path | None = None,
                            initial_quality: int = 85) -> list[str]:
        input_dir = Path(input_dir)
        if not input_dir.exists():
            raise FileNotFoundError(f"目录不存在: {input_dir}")

        if output_dir is None:
            output_dir = input_dir / "compressed"
        else:
            output_dir = Path(output_dir)

        output_dir.mkdir(exist_ok=True)

        image_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp"}
        processed_files: list[str] = []
        failed_files: list[str] = []

        # 仅遍历输入目录下的一级文件（不递归）
        for img_file in input_dir.iterdir():
            if img_file.is_file() and img_file.suffix.lower() in image_extensions:
                out_path = output_dir / f"{img_file.stem}.jpg"
                try:
                    result = self.compress_image(img_file, out_path, quality=initial_quality)
                    if result:
                        processed_files.append(result)
                except Exception as exc:
                    print(f"处理失败: {img_file.name} -> {exc}")
                    failed_files.append(str(img_file))

        print("\n批量处理完成!")
        print(f"成功处理: {len(processed_files)} 个文件")
        print(f"失败: {len(failed_files)} 个文件")
        if failed_files:
            print("失败文件列表：")
            for f in failed_files:
                print(f"  - {f}")

        return processed_files


def resolve_input_directory() -> Path:
    # 若指定绝对路径，则优先使用
    if INPUT_DIR_ABS.strip():
        return Path(INPUT_DIR_ABS).expanduser().resolve()
    # 否则使用脚本同级目录下的目标文件夹
    base_dir = Path(__file__).resolve().parent
    return (base_dir / TARGET_DIR_NAME).resolve()


def main() -> None:
    input_dir = resolve_input_directory()
    output_dir = input_dir / OUTPUT_SUBDIR_NAME

    print("================ 图片压缩开始 ================")
    print(f"输入目录: {input_dir}")
    print(f"输出目录: {output_dir}")
    print(f"阈值设置: MIN={MIN_SIZE_KB}KB, MAX/TARGET={MAX_SIZE_KB}KB, 初始质量={INITIAL_QUALITY}")

    compressor = ImageCompressor(min_size_kb=MIN_SIZE_KB, max_size_kb=MAX_SIZE_KB)
    results = compressor.compress_directory(input_dir, output_dir, initial_quality=INITIAL_QUALITY)

    print(f"\n完成，共处理 {len(results)} 个文件")
    print("============================================")


if __name__ == "__main__":
    main()


