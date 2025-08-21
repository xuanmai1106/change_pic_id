#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
为CSV文件中content列的每个stage添加image_url

功能：
1. 删除CSV文件的第一列和最后一列（可选）
2. 读取CSV文件
3. 解析content列中的JSON数据
4. 为每个stage添加image_url，格式：https://aitest.fitnexa.com/recipe/{source_id}_{stage}.jpg
5. 保存更新后的文件
"""

import pandas as pd
import json

# 在这里修改输入和输出文件名
INPUT_FILE = "recipes_601_700.csv"  # 输入文件名
OUTPUT_FILE = "recipes_601_700_with_images.csv"  # 输出文件名

# 功能开关
REMOVE_FIRST_AND_LAST_COLUMNS = True  # 是否删除第一列和最后一列
ADD_IMAGE_URLS = True  # 是否添加image_url


def remove_first_and_last_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    删除DataFrame的第一列和最后一列
    
    Args:
        df: 输入的DataFrame
    
    Returns:
        处理后的DataFrame
    """
    if len(df.columns) < 3:
        print("警告：列数少于3列，无法删除第一列和最后一列")
        return df
    
    # 删除第一列和最后一列
    df_modified = df.iloc[:, 1:-1]
    print(f"已删除的列: {df.columns[0]}, {df.columns[-1]}")
    print(f"处理后文件包含 {len(df_modified)} 行，{len(df_modified.columns)} 列")
    return df_modified


def add_image_urls_to_stages(content_data: dict, source_id: int) -> dict:
    """
    为content数据中的每个stage添加image_url
    
    Args:
        content_data: 解析后的JSON内容数据
        source_id: 食谱的source_id
    
    Returns:
        更新后的content数据
    """
    if 'stages' in content_data:
        for stage in content_data['stages']:
            if 'stage' in stage:
                stage_num = stage['stage']
                image_url = f'https://aitest.fitnexa.com/recipe/{source_id}_{stage_num}.jpg'
                stage['image_url'] = image_url
    return content_data


def process_csv_to_df(input_file: str, remove_columns: bool = True, add_images: bool = True) -> pd.DataFrame:
    """
    在内存中处理CSV：可删除首尾列、为每个stage添加image_url，返回处理后的DataFrame。
    不进行任何中间文件保存。
    """
    # 读取CSV文件
    print(f"正在读取文件: {input_file}")
    df = pd.read_csv(input_file, encoding='utf-8-sig')
    print(f"原始文件包含 {len(df)} 行，{len(df.columns)} 列")

    # 步骤1：删除第一列和最后一列（如果需要）
    if remove_columns:
        print("\n步骤1：删除第一列和最后一列")
        df = remove_first_and_last_columns(df)

    # 步骤2：添加image_url（如果需要）
    if add_images:
        print("\n步骤2：为每个stage添加image_url")

        # 检查必要的列是否存在
        if 'content' not in df.columns or 'source_id' not in df.columns:
            raise ValueError("CSV文件必须包含'content'和'source_id'列")

        # 处理每一行
        updated_count = 0
        
        for index, row in df.iterrows():
            try:
                # 解析content列
                content = json.loads(row['content'])
                source_id = row['source_id']
                
                # 为每个stage添加image_url
                updated_content = add_image_urls_to_stages(content, source_id)
                df.at[index, 'content'] = json.dumps(updated_content, ensure_ascii=False)
                updated_count += 1
            except json.JSONDecodeError:
                print(f"行 {index} 的content列无法解析为JSON")
                continue
        print(f"已更新 {updated_count} 行的content列")

    return df


 


def extract_stages_and_source_id_from_df(df: pd.DataFrame, input_file: str) -> None:
    """
    直接从内存中的DataFrame提取 content->stages 与 source_id，生成提取文件。
    默认仅处理 language_code == 'en'（若存在 language_code 列）。
    """
    try:
        # 只保留 en（若有 language_code 列）
        if 'language_code' in df.columns:
            df = df[df['language_code'] == 'en']

        # 检查必要的列是否存在
        if 'content' not in df.columns or 'source_id' not in df.columns:
            print("错误：CSV文件必须包含'content'和'source_id'列")
            return

        extracted_data = []

        for index, row in df.iterrows():
            try:
                content = json.loads(row['content'])
                source_id = row['source_id']

                if 'stages' in content:
                    # 合并所有stage数据
                    stages_data = json.dumps(content['stages'], ensure_ascii=False)
                    # 添加前缀
                    stages_data_with_prefix = (
                        "该图为一张食谱图片，以下数据包括了完成这道菜的步骤（stage）。"
                        "为每个stage生成一张配图，图中不要出现文字，图片背景浅白色系，ins风格。"
                        "所有图片为正方形，长宽比为1：1。以下为数据内容：" + stages_data
                    )
                    extracted_data.append({'source_id': source_id, 'stage': stages_data_with_prefix})
            except json.JSONDecodeError:
                print(f"行 {index} 的content列无法解析为JSON")
                continue

        # 创建新的DataFrame
        extracted_df = pd.DataFrame(extracted_data)

        # 生成新文件名
        new_file_name = f"{input_file.rsplit('.', 1)[0]}_extract_stage.csv"

        # 保存提取后的数据到新的CSV文件
        extracted_df.to_csv(new_file_name, index=False, encoding='utf-8-sig')
        print(f"已保存提取文件: {new_file_name}")
    except Exception as e:
        print(f"提取文件时出错: {e}")


if __name__ == "__main__":
    try:
        # 在内存中处理，保存含 image_url 的全量CSV（所有语言）
        df_processed = process_csv_to_df(INPUT_FILE, REMOVE_FIRST_AND_LAST_COLUMNS, ADD_IMAGE_URLS)
        df_processed.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')
        print(f"已保存更新后的文件: {OUTPUT_FILE}")

        # 从处理后的数据中仅筛选 en 语言，生成用于图片生成的提取文件
        extract_stages_and_source_id_from_df(df_processed, INPUT_FILE)
        print("已生成含 image_url 的全量CSV与仅 en 语言的提取CSV。")
    except Exception as e:
        print(f"处理文件时出错: {e}")