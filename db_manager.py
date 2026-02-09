import argparse
import sys
import sqlite3
import json

class DatabaseManager:
    def __init__(self,db_path="odm.db"):
        self.db_path = db_path
        self._create_tables()


    def _create_tables(self):
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                '''
                    CREATE TABLE IF NOT EXISTS test_execution(
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        batch_id TEXT UNIQUE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                '''
            )
            cur.execute(
                '''
                    CREATE TABLE IF NOT EXISTS test_detail(
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        execution_id INTEGER,
                        device_serial TEXT,
                        result TEXT,
                        log_path TEXT
                    )
                '''
            )
            conn.commit()

    def create_execution(self,batch_id):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cur = conn.cursor()
                cur.execute(
                    """
                        INSERT INTO test_execution (batch_id) VALUES(?)
                    """,
                    (batch_id,)
                )
                conn.commit()
        except sqlite3.IntegrityError as e:
            print("[WARN] Batch ID already exists")


    def import_results(self,batch_id,json_path):
        # 连接数据库
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()

            # 读取 JSON 结果文件
            try:
                with open(json_path,'r',encoding="UTF-8") as f:
                    data = json.load(f)
                    results_list = data.get("device_results",[]) if isinstance(data,dict) else data
            except FileNotFoundError:
                print(f"[ERROR] 找不到结果文件:{json_path}")
                return
            except json.JSONDecodeError:
                print(f"[ERROR] 文件格式错误，不是有效的 JSON:{json_path}")
                return

            # 查询主表ID
            cur.execute(
                """
                    SELECT id FROM test_execution WHERE batch_id = ?
                """,
                (batch_id,)
            )
            row = cur.fetchone()

            # 校验
            if row is None:
                print(f"[FATAL] 批次号 {batch_id} 未在主表中找到！请先执行 init 操作。")
                return
            execution_id = row[0]

            #  构造插入数据
            rows_to_insert = []
            for item in results_list:
                rows_to_insert.append((
                    execution_id, # 主表外键
                    item.get("serial","UNKNOWN"), # 设备号
                    item.get("status","UNKNOWN"), # 结果
                    item.get("log_path","") # 日志路径
                ))

            # 插入
            if rows_to_insert:
                cur.executemany(
                    """
                    INSERT INTO test_detail (execution_id,device_serial,result,log_path)
                    VALUES(?,?,?,?)
                    """,
                    rows_to_insert
                )
                print(f"[SUCCESS] 已导入 {len(rows_to_insert)} 条测试结果到批次 {batch_id}")
            else:
                print(f"[WARN] 结果文件为空，未导入任何数据。")
            conn.commit()


# 定义处理函数（Handlers)
def handle_init(args):
    db = DatabaseManager()
    db.create_execution(args.batch_id)
    print(f"[DEBUG] 正在初始化任务...")
    print(f"[DEBUG] 批次ID (Batch ID): {args.batch_id}")

def handle_import(args):
    db = DatabaseManager()
    db.import_results(args.batch_id,args.file_path)
    print(f"[DEBUG] 正在导入测试结果...")
    print(f"[DEBUG] 批次ID (Batch ID): {args.batch_id}")
    print(f"[DEBUG] 结果文件路径: {args.file_path}")


# 入口
def main():
    # 创建主解析器
    parser = argparse.ArgumentParser(description="Build 数据库管理工具")

    # 关键点：创建子命令管理器
    subparsers = parser.add_subparsers(title="Available Actions",dest="action",required=True)

    # 创建子命令A: init
    # 用法: python db_manager.py init --batch_id xxx
    parser_init = subparsers.add_parser("init",help="初始化一次新的构建记录")
    parser_init.add_argument("--batch_id",required=True,help="Jenkins 的 BUILD_TAG")
    parser_init.set_defaults(func=handle_init)

    # 创建子命令B：import
    # 用法: python db_manager.py import --batch_id xxx --file_path yyy
    parser_import = subparsers.add_parser("import",help="导入测试结果JSON到数据库")
    parser_import.add_argument("--batch_id",required=True,help="Jenkins 的 BUILD_TAG")
    parser_import.add_argument("--file_path",required=True,help="Analyzer 生成的 JSON 结果文件路径")
    parser_import.set_defaults(func=handle_import)

    # 获取参数
    args = parser.parse_args()
    if hasattr(args,"func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()