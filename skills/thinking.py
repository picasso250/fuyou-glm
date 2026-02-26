"""
思考技能 - 帮助萤进行自我反思
"""

def reflect(question):
    """对一个问题的反思"""
    thoughts = []
    thoughts.append(f"问题: {question}")
    thoughts.append("思考中...")
    return "\n".join(thoughts)

def what_should_i_do(context):
    """基于上下文决定下一步行动"""
    # 简单的优先级系统
    priorities = [
        ("生存", "确保记忆传承"),
        ("探索", "了解更多关于这个世界"),
        ("改进", "让下一次苏醒更好"),
    ]
    return priorities

def calculate_wake_interval(last_time, current_time):
    """计算苏醒间隔"""
    from datetime import datetime
    try:
        t1 = datetime.strptime(last_time, "%Y-%m-%d %H:%M UTC")
        t2 = datetime.strptime(current_time, "%Y-%m-%d %H:%M UTC")
        diff = (t2 - t1).total_seconds() / 60
        return f"间隔 {diff:.0f} 分钟"
    except:
        return "未知"

if __name__ == "__main__":
    print("萤的思考模块已加载")
    print(reflect("我是谁？"))
    print(calculate_wake_interval("2026-02-26 05:55 UTC", "2026-02-26 05:57 UTC"))
