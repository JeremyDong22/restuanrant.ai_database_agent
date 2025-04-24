# 创建日期: 当前
# 作者: Claude 3.7 Sonnet
# 描述: 简单脚本，用于测试数据库连接

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# 加载.env文件
load_dotenv()

# 获取环境变量
db_uri = os.getenv("SUPABASE_DB_URI")
print(f"数据库URI: {db_uri}")

try:
    # 尝试连接数据库
    print("尝试连接数据库...")
    engine = create_engine(db_uri)
    
    # 测试连接
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))
        print(f"查询结果: {result.fetchone()}")
    
    print("成功连接到数据库!")
except Exception as e:
    print(f"连接失败: {e}") 