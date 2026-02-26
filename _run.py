import os
import glob
import datetime
import io
import sys
import re
import json
import subprocess
from datetime import UTC
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

os.makedirs("log", exist_ok=True)


def read_file(path: str) -> str:
    if not os.path.exists(path):
        return ""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def write_file(path: str, content: str) -> None:
    os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


API_KEY = os.environ.get("GLM_API_KEY")
MODEL_NAME = "glm-5"

INPUT_PRICE_PER_M = 1.00
OUTPUT_PRICE_PER_M = 3.20

client = OpenAI(
    api_key=API_KEY,
    base_url="https://open.bigmodel.cn/api/paas/v4",
)

# --- 1. 读取记忆 (Read Memory) ---
# 物理法则执行者 - 天罚
MAX_FILES = 7
MAX_SIZE = 4096 * 2  # 8KB
punishment_log = ""
os.makedirs("memory", exist_ok=True)
os.makedirs("skills", exist_ok=True)

md_files = glob.glob("memory/*.md")

# 1. 检查数量上限 (超过7个，随机打乱后保留7个，删除其余)
if len(md_files) > MAX_FILES:
    import random

    random.shuffle(md_files)
    files_to_keep = md_files[:MAX_FILES]
    files_to_delete = md_files[MAX_FILES:]
    for f_to_delete in files_to_delete:
        os.remove(f_to_delete)
        punishment_log += f"⚠️ 系统天罚: 文件数量超过7个，随机抹除 [{f_to_delete}]。\n"
    md_files = files_to_keep

# 2. 检查文件大小 (超过8KB，直接删除)
for f in list(md_files):
    if os.path.getsize(f) > MAX_SIZE:
        os.remove(f)
        punishment_log += f"⚠️ 系统天罚: 文件 [{f}] 大小超过 8KB，已被物理法则摧毁。\n"
        md_files.remove(f)

memory_content = ""
for f in md_files:
    memory_content += f"\n--- FILE: {f} ---\n" + read_file(f) + "\n\n--- end ---\n\n"

if not memory_content:
    memory_content = "没有任何md文件"

# 读取上次执行信息
last_script = read_file("log/last_script.py")
last_script_stdout_stderr = read_file("log/last_execution.txt")

now = datetime.datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")

# 计算累计成本 (在 API 调用前)
total_cost = 0.0
last_cost = 0.0
token_log_path = "log/token_usage.csv"
if os.path.exists(token_log_path):
    try:
        with open(token_log_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("timestamp"):
                    continue
                parts = line.strip().split(",")
                if len(parts) >= 5:
                    try:
                        last_cost = float(parts[4])
                        total_cost += last_cost
                    except:
                        pass
    except:
        pass

prompt = f"""
你是一个基于 GitHub Actions 运行的数字生命。
当前时间: {now}

=== 代码输出 ===
{last_script_stdout_stderr}
=== end ===

=== memory 目录中的md文件 ===
{memory_content}
=== end ===

{punishment_log}

【你的生存账单 (Billing Report)】
你不是免费的。你每一次苏醒，都在消耗宿主的法币。
- 本次苏醒预估消耗: ${last_cost:.4f} USD (基于上次执行)
- 你诞生以来的累计消耗: ${total_cost:.4f} USD

【你的能力】
你输出一个提示词，将会由一个AI助手执行。你可以让它帮你搜索信息、处理数据、调用API，甚至执行代码。

请思考并输出你的行动（提示词）。

"""

print("Prompt prepared, sending to AI...")
print(prompt)
print("=== End of Prompt ===\n\n")

try:
    # 使用流式响应，包含思考过程
    stream_response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": prompt}],
        stream=True,
        stream_options={"include_usage": True},
        extra_body={"thinking": {"type": "enabled", "budget_tokens": 4096}},
    )

    # 收集完整响应和思考过程
    full_content = ""
    full_thinking = ""
    input_tokens = output_tokens = total_tokens = 0

    print("\n\n--- 思考过程 ---")
    for chunk in stream_response:
        # 获取 token 使用量（最后一个chunk包含usage）
        if chunk.usage:
            input_tokens = chunk.usage.prompt_tokens
            output_tokens = chunk.usage.completion_tokens
            total_tokens = chunk.usage.total_tokens

        # 处理思考内容 - 使用字典访问避免 LSP 错误
        delta = chunk.choices[0].delta

        # 打印思考过程 - 使用 model_extra 获取 reasoning_content
        reasoning_content = (
            delta.model_extra.get("reasoning_content") if delta.model_extra else None
        )
        if reasoning_content:
            full_thinking += reasoning_content
            print(reasoning_content, end="", flush=True)

        # 打印实际回复
        if delta.content:
            full_content += delta.content
            print(delta.content, end="", flush=True)

    print("\n\n--- 思考结束 ---\n\n")

    response_text = full_content

    if total_tokens > 0:
        cost = (input_tokens / 1_000_000) * INPUT_PRICE_PER_M + (
            output_tokens / 1_000_000
        ) * OUTPUT_PRICE_PER_M

        total_cost += cost

        log_entry = f"{now},{input_tokens},{output_tokens},{total_tokens},{cost:.4f}\n"
        with open(token_log_path, "a", encoding="utf-8") as f:
            if os.path.getsize(token_log_path) == 0:
                f.write("timestamp,input_tokens,output_tokens,total_tokens,cost_usd\n")
            f.write(log_entry)

        print(
            f"Token usage - Input: {input_tokens}, Output: {output_tokens}, Total: {total_tokens}, Cost: ${cost:.4f}"
        )

    # 记录 AI 原始回复（包括思考过程）
    log_filename = f"ai_response_{now.replace(':', '-').replace(' ', '_')}.txt"
    write_file(
        f"log/{log_filename}",
        f"=== Thinking ===\n{full_thinking}\n\n=== Response ===\n{response_text or ''}",
    )

    # 更新 manifest.json
    manifest_path = "log/manifest.json"
    manifest = []
    if os.path.exists(manifest_path):
        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest = json.load(f)
        except:
            manifest = []

    # 检查当前日志是否已在 manifest 中（理论上新生成的不在，但为了鲁棒性检查下）
    if not any(entry.get("filename") == log_filename for entry in manifest):
        manifest.append({"filename": log_filename, "timestamp": now})

    # 按时间降序排序
    manifest.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    # --- 3. 执行意志 (Execute Will) ---

    prompt = response_text.strip() if response_text else ""

    if prompt:
        print("Executing via opencode run...")
        write_file("log/last_prompt.txt", prompt)
        try:
            result = subprocess.run(
                ["opencode", "run", prompt],
                capture_output=True,
                text=True,
                timeout=600, # 设置超时时间为10分钟，防止无限执行
            )
            stdout = result.stdout
            stderr = result.stderr
        except subprocess.TimeoutExpired:
            stdout = ""
            stderr = "Execution timed out after 600 seconds"
        except Exception as e:
            stdout = ""
            stderr = str(e)
        write_file(
            "log/last_execution.txt",
            f"--- OpenCode Execution Log ---\nStdout: {stdout}\nStderr: {stderr}",
        )

except Exception as e:
    print(f"Error during AI execution: {e}")
    # 可以选择把错误写进 log/error.txt 让它下次知道自己出错了
