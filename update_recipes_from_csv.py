import pandas as pd
import pymysql
import json

# 数据库连接配置
db_config = {
    'host': 'mysql-testn-80.mysql.database.azure.com',
    'user': 'yanshen',
    'password': 'TT473927950&*',
    'database': 'fitnexa',
    'charset': 'utf8mb4',
    'ssl': {
        'ssl': True,
        'ssl_verify_cert': True,
        'ssl_verify_identity': True
    }
}

# 需要更新的字段映射（csv列名 -> 数据库列名）
update_fields = {
    'content': 'content',


}

#将CSV中的数据转换为适合数据库存储的格式
def prepare_value(value):
#     print(f"已更新 tpype ={type(value)}")
    """将字段转为json数组字符串，空值转为[""]"""
    if value is None  or (isinstance(value, str) and value.strip() == '') or (isinstance(value, float) and pd.isna(value)):
        return json.dumps([""], ensure_ascii=False)
    # 如果本身是list或dict，转json
    if isinstance(value, (list, dict)):
        return json.dumps(value, ensure_ascii=False)
    # 如果是字符串，尝试转为json
    try:
        v = json.loads(value)
        if isinstance(v, (list, dict)):
            return json.dumps(v, ensure_ascii=False)
    except Exception:
        pass
    # 其他情况，包裹成数组
    try:
        return int(value)
    except Exception:
        return json.dumps([value], ensure_ascii=False)
    return json.dumps([value], ensure_ascii=False)

def main():
    # 读取csv
    df = pd.read_csv('recipes_801_934_with_images.csv', dtype=str).fillna('')

    # 建立数据库连接
    conn = pymysql.connect(**db_config)
    try:
        with conn.cursor() as cur:
            for idx, row in df.iterrows():
                source_id = row.get('source_id', '').strip()
                language_code = row.get('language_code', '').strip()
                
                if not source_id:
                    print(f"第{idx+1}行缺少source_id，跳过")
                    continue
                    
                if not language_code:
                    print(f"第{idx+1}行缺少language_code，跳过")
                    continue

                # 构造SET子句
                set_clauses = []
                values = []
                for csv_col, db_col in update_fields.items():
                    val = row.get(csv_col, '')
                    val = prepare_value(val)
                    set_clauses.append(f"{db_col} = %s")
                    values.append(val)

                set_clause = ', '.join(set_clauses)
                sql = f"UPDATE recipes SET {set_clause} WHERE source_id = %s and language_code = %s"
                values.append(source_id)
                values.append(language_code)
                cur.execute(sql, values)
                print(f"已更新 source_id={source_id}, language_code={language_code}")

            conn.commit()
    except Exception as e:
        print(f"发生错误: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    main()
