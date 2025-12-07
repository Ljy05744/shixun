"""
数据库操作模块
"""

import sqlite3
from datetime import datetime
from typing import List, Dict, Any, Optional


def get_db_connection():
    """获取数据库连接"""
    conn = sqlite3.connect('tasks.db')
    conn.row_factory = sqlite3.Row  # 返回字典格式
    return conn


def init_database():
    """初始化数据库表"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # 创建任务表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            status TEXT NOT NULL DEFAULT 'pending',
            due_date DATE,
            priority INTEGER DEFAULT 3,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 创建索引
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_status ON tasks(status)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_due_date ON tasks(due_date)')

    conn.commit()
    conn.close()
    print("✅ 数据库初始化完成")


def get_all_tasks(status: Optional[str] = None) -> List[Dict[str, Any]]:
    """获取所有任务"""
    conn = get_db_connection()
    cursor = conn.cursor()

    if status:
        cursor.execute(
            "SELECT * FROM tasks WHERE status = ? ORDER BY created_at DESC",
            (status,)
        )
    else:
        cursor.execute("SELECT * FROM tasks ORDER BY created_at DESC")

    tasks = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return tasks


def get_task_by_id(task_id: int) -> Optional[Dict[str, Any]]:
    """根据ID获取任务"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def create_task(task_data: Dict[str, Any]) -> Dict[str, Any]:
    """创建新任务"""
    print(f"🔧 开始创建任务: {task_data['title']}")

    conn = get_db_connection()
    cursor = conn.cursor()

    print(f"📝 执行SQL插入...")
    cursor.execute('''
        INSERT INTO tasks (title, description, status, due_date, priority)
        VALUES (?, ?, ?, ?, ?)
    ''', (
        task_data['title'],
        task_data.get('description', ''),
        task_data.get('status', 'pending'),
        task_data.get('due_date'),
        task_data.get('priority', 3)
    ))

    print(f"💾 提交事务...")
    conn.commit()

    task_id = cursor.lastrowid
    print(f"🆔 获取任务ID: {task_id}")

    if not task_id:
        print("❌ 错误: 无法获取 lastrowid")
        conn.close()
        raise Exception("无法获取任务ID")

    # 获取刚创建的任务
    print(f"🔍 查询刚创建的任务 ID={task_id}...")
    cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
    row = cursor.fetchone()

    if not row:
        print(f"❌ 错误: 查询不到任务 ID={task_id}")
        # 检查表中是否有数据
        cursor.execute("SELECT COUNT(*) as count FROM tasks")
        count = cursor.fetchone()['count']
        print(f"📊 表中总任务数: {count}")

        # 列出所有任务
        cursor.execute("SELECT id, title FROM tasks")
        all_tasks = cursor.fetchall()
        print(f"📋 所有任务: {all_tasks}")

    conn.close()

    if row:
        result = dict(row)
        print(f"✅ 任务创建成功: ID={result['id']}, 标题={result['title']}")
        return result
    else:
        print("❌ 任务创建失败")
        raise Exception("任务创建后查询失败")


def update_task(task_id: int, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """更新任务"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # 检查任务是否存在
    cursor.execute("SELECT id FROM tasks WHERE id = ?", (task_id,))
    if not cursor.fetchone():
        conn.close()
        return None

    # 构建更新语句
    set_clauses = []
    values = []

    for key, value in update_data.items():
        if value is not None:
            set_clauses.append(f"{key} = ?")
            values.append(value)

    if not set_clauses:
        conn.close()
        return None

    # 添加更新时间
    set_clauses.append("updated_at = CURRENT_TIMESTAMP")

    # 执行更新
    values.append(task_id)
    sql = f"UPDATE tasks SET {', '.join(set_clauses)} WHERE id = ?"
    cursor.execute(sql, values)
    conn.commit()

    # 获取更新后的任务
    updated_task = get_task_by_id(task_id)
    conn.close()
    return updated_task


def delete_task(task_id: int) -> bool:
    """删除任务"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    deleted = cursor.rowcount > 0

    conn.commit()
    conn.close()
    return deleted


def get_task_stats() -> Dict[str, Any]:
    """获取任务统计信息"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) as total FROM tasks")
    total = cursor.fetchone()['total']

    cursor.execute("SELECT COUNT(*) as completed FROM tasks WHERE status = 'completed'")
    completed = cursor.fetchone()['completed']

    cursor.execute("SELECT COUNT(*) as pending FROM tasks WHERE status = 'pending'")
    pending = cursor.fetchone()['pending']

    cursor.execute("SELECT COUNT(*) as in_progress FROM tasks WHERE status = 'in_progress'")
    in_progress = cursor.fetchone()['in_progress']

    cursor.execute("SELECT COUNT(*) as overdue FROM tasks WHERE due_date < DATE('now') AND status != 'completed'")
    overdue = cursor.fetchone()['overdue']

    # 新增：优先级统计
    cursor.execute("SELECT priority, COUNT(*) as count FROM tasks GROUP BY priority ORDER BY priority")
    priority_stats = {}
    for row in cursor.fetchall():
        priority_stats[f"priority_{row['priority']}"] = row['count']

    # 新增：高优先级任务统计（优先级1-2）
    cursor.execute("SELECT COUNT(*) as high_priority FROM tasks WHERE priority <= 2")
    high_priority = cursor.fetchone()['high_priority']

    conn.close()

    return {
        "total": total,
        "completed": completed,
        "pending": pending,
        "in_progress": in_progress,
        "overdue": overdue,
        "completion_rate": round((completed / total * 100) if total > 0 else 0, 1),
        # 新增字段
        "priority_distribution": priority_stats,
        "high_priority_tasks": high_priority
    }