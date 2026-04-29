import os
from dotenv import load_dotenv
from sqlmodel import create_engine, Session

# 加载 .env 里的 DATABASE_URL
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL not found in .env file")

# 创建全局唯一的 engine
engine = create_engine(DATABASE_URL)

# 定义一个获取 session 的工具函数，这在 FastAPI 中非常常用
def get_session():
    with Session(engine) as session:
        yield session