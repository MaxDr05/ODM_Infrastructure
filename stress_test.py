import os
import time
import random
import sqlite3
from db_manager import DatabaseManager

DB_PATH = "odm.db"

def generate_fake_data(batch_count=1000,devices_per_batch=50):
    # 0. 确保数据库表已建立
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)  # 删掉旧的，从头开始

    # 初始化建表
    DatabaseManager(DB_PATH)

    devices = [f"device_{i:03d}" for i in range(1,51)]
    statuses = ["SUCCESS","FAIL"]

    print(f"DEBUG: 计划生成 {batch_count} 个批次，每批次 {len(devices)} 台设备")

    print(f"[Phase 1] 开始生成数据...")

    start_time = time.time()
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("BEGIN TRANSACTION;")

        total_inserted = 0

        for i in range(batch_count):
            batch_id = f"stress-test-run-{i}"

            # 1. 插主表
            cur.execute("INSERT INTO test_execution (batch_id) VALUES (?)", (batch_id,))
            execution_id = cur.lastrowid

            # 构造数据
            current_batch_rows = []
            for dev in devices:
                status = random.choices(statuses,weights=[80,20],k=1)[0]
                log_path = f"/app/logs/{batch_id}/{dev}.log"
                current_batch_rows.append((execution_id,dev,status,log_path))

                # 3. 批量写入子表
                if current_batch_rows:
                    cur.executemany(
                        "INSERT INTO test_detail (execution_id, device_serial, result, log_path) VALUES (?, ?, ?, ?)",
                        current_batch_rows
                    )
                    total_inserted += len(current_batch_rows)

                if i == 0:
                    print(
                        f"🔍 DEBUG: 第1个批次已插入，execution_id={execution_id}, 包含 {len(current_batch_rows)} 条子项")

                if i % 100 == 0 and i > 0:
                    print(f"  ...已处理 {i} 个批次 (累计 {total_inserted} 条)")


        conn.commit()
        cur.execute("SELECT count(*) FROM test_detail")
        real_count = cur.fetchone()[0]

    end_time = time.time()
    total_rows = batch_count * devices_per_batch
    print(f"共插入 {total_rows} 条数据。")
    print(f"实际库存: {real_count} (如果这个是0，说明出大问题了)")
    print(f"总耗时: {end_time - start_time:.2f} 秒")

def benchmark_query():
    target_device = "device_043"
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    print(f"\n🔎 [Phase 2] 开始测试查询性能 (设备: {target_device})...")

    # 第一次查询
    start = time.time()
    cur.execute("SELECT * FROM test_detail WHERE device_serial = ? AND result = 'FAIL'", (target_device,))
    rows = cur.fetchall()
    end = time.time()

    duration_ms = (end - start) * 1000
    print(f"命中记录数: {len(rows)} ")
    print(f"️查询耗时: {duration_ms:.4f} ms")

    conn.close()

if __name__ == '__main__':
    # generate_fake_data()

    benchmark_query()


