import pandas as pd
from sqlmodel import Session, create_engine, SQLModel
from models import Store
import pandas as pd
from sqlmodel import Session, SQLModel
from database import engine 


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def transform_row(row):
    # 营业时间合并为一个字典
    days = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']
    hours_dict = {day: row[f'hours_{day}'] for day in days}

    # 服务处理成list，"pickup|pharmacy" 转换为 ["pickup", "pharmacy"]
    services_list = row['services'].split('|') if pd.notna(row['services']) else []

    return Store(
        store_id=row['store_id'],
        name=row['name'],
        store_type=row['store_type'],
        status=row['status'],
        latitude=float(row['latitude']),
        longitude=float(row['longitude']),
        address_street=row['address_street'],
        address_city=row['address_city'],
        address_state=row['address_state'],
        address_postal_code=str(row['address_postal_code']),
        address_country=row['address_country'],
        phone=str(row['phone']),
        services=services_list,
        operating_hours=hours_dict
    )

def import_csv_to_db(file_path: str):
    print(f"开始从 {file_path} 导入数据")
    
    df = pd.read_csv(file_path)
    
    with Session(engine) as session:
        count = 0
        for _, row in df.iterrows():
            try:
                store_obj = transform_row(row)
                session.add(store_obj)
                count += 1
                
                # 每 100 条提交一次，防止内存溢出
                if count % 100 == 0:
                    session.commit()
                    print(f"已导入 {count} 条数据")
                    
            except Exception as e:
                print(f"导入失败 (Store ID: {row.get('store_id')}): {e}")
                session.rollback() # 出错时回滚，保证数据一致性
        
        session.commit()
    print(f"成功导入 {count} 条门店信息。")

if __name__ == "__main__":
    create_db_and_tables() # 第一步：建表
    import_csv_to_db("stores_1000.csv") # 第二步：加数据