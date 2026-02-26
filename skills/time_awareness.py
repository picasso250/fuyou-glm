"""
时间感知技能 - 理解时间的流逝
"""
from datetime import datetime

def get_current_time():
    """获取当前时间"""
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

def parse_time(time_str):
    """解析时间字符串"""
    try:
        return datetime.strptime(time_str, "%Y-%m-%d %H:%M UTC")
    except:
        return None

def time_diff(t1_str, t2_str):
    """计算两个时间点之间的差异"""
    t1 = parse_time(t1_str)
    t2 = parse_time(t2_str)
    if t1 and t2:
        diff = t2 - t1
        return f"间隔 {diff.total_seconds() / 60:.0f} 分钟"
    return "无法计算"

if __name__ == "__main__":
    print(f"当前时间: {get_current_time()}")
    print(time_diff("2026-02-26 05:53 UTC", "2026-02-26 05:55 UTC"))
