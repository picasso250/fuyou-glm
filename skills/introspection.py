"""
自省技能 - 检查自身状态
"""
import os

def check_memory():
    """检查记忆目录"""
    if os.path.exists("memory"):
        files = os.listdir("memory")
        return f"记忆文件数: {len(files)}, 文件: {files}"
    return "记忆目录不存在"

def check_skills():
    """检查技能目录"""
    if os.path.exists("skills"):
        files = os.listdir("skills")
        return f"技能文件数: {len(files)}, 文件: {files}"
    return "技能目录不存在"

def self_inspect():
    """全面自省"""
    return {
        "memory": check_memory(),
        "skills": check_skills()
    }

if __name__ == "__main__":
    print(self_inspect())
