import pandas as pd

# 指定要删除的source_id列表
target_source_ids = {1, 9, 16, 19, 20, 22, 27, 28, 30, 31, 34, 43, 44, 59, 63, 74, 80, 94, 99, 101, 113, 123, 139, 143, 182, 203, 205, 209, 234, 252, 253, 254, 280, 291, 321, 463, 495, 508}

# 指定要读取的文件名
input_file = 'recipes_401_500_extract_stage.csv'

# 读取CSV文件
df = pd.read_csv(input_file, encoding='utf-8-sig')

# 检查source_id列是否存在
if 'source_id' not in df.columns:
    print("错误：CSV文件必须包含'source_id'列")
else:
    # 删除包含指定source_id的行
    df_filtered = df[~df['source_id'].isin(target_source_ids)]
    
    # 生成输出文件名（在原文件名基础上添加_filtered后缀）
    output_file = input_file.replace('.csv', '_filtered.csv')
    
    # 保存过滤后的数据到新的CSV文件
    df_filtered.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f"已删除指定source_id的行，并保存到 {output_file}") 