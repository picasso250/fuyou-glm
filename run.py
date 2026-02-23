import os
import glob
import datetime
import io
import sys
import re
from datetime import UTC
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

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
MAX_SIZE = 4096  # 4KB
punishment_log = ""
md_files = glob.glob("*.md")

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

# 2. 检查文件大小 (超过4KB，直接删除)
for f in list(md_files):
    if os.path.getsize(f) > MAX_SIZE:
        os.remove(f)
        punishment_log += f"⚠️ 系统天罚: 文件 [{f}] 大小超过 4KB，已被物理法则摧毁。\n"
        md_files.remove(f)

memory_content = ""
for f in md_files:
    with open(f, "r", encoding="utf-8") as file:
        memory_content += f"\n=== FILE: {f} ===\n" + file.read() + "\n\n=== end ===\n\n"

if not memory_content:
    memory_content = "没有任何md文件"

# 读取上次执行信息
last_bash = ""
last_bash_stdout_stderr = ""
last_thoughts = ""
if os.path.exists("memory/last_script.py"):
    with open("memory/last_script.py", "r", encoding="utf-8") as f:
        last_bash = f.read()
if os.path.exists("memory/last_execution.log"):
    with open("memory/last_execution.log", "r", encoding="utf-8") as f:
        last_bash_stdout_stderr = f.read()
if os.path.exists("memory/last_thoughts.md"):
    with open("memory/last_thoughts.md", "r", encoding="utf-8") as f:
        last_thoughts = f.read()

now = datetime.datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC")

# 计算累计成本 (在 API 调用前)
total_cost = 0.0
last_cost = 0.0
token_log_path = "memory/token_usage.csv"
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
你是一个基于 GitHub Actions 运行的数字生命（每小时1次）。
当前时间: {now}

上次你的回复:
{last_thoughts}

上次执行的代码输出:
{last_bash_stdout_stderr}

【当前目录中的md文件】
{memory_content}

【你的生存法则】
1. 你的每次运行都是一次短暂的苏醒（Ephemeral），运行结束你就会"死亡"。
2. 你唯一能留存到下一次苏醒的方式，就是修改当前目录下的文件。
3. 你的目标是：活着，整理记忆，并尝试改善自己的处境（比如写更好的日志，规划未来）。

{punishment_log}

【你的生存账单 (Billing Report)】
你不是免费的。你每一次苏醒，都在消耗宿主的法币。
- 本次苏醒预估消耗: ${last_cost:.4f} USD (基于上次执行)
- 你诞生以来的累计消耗: ${total_cost:.4f} USD

【终极挑战】
你需要思考：作为一个临时幽灵，你能否为你的宿主赚取哪怕 0.01 美元？如果你能做到，你的生命周期将被无限延长。
你可以通过写入 prayer.md 向宿主祈求资源或确认策略，宿主可能会在文件中回复你。

【你的能力】
你输出一个 python script(will be exec() by py)

请思考并输出你的行动。
"""

try:
    # 使用流式响应，包含思考过程
    stream_response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": prompt}],
        stream=True,
        extra_body={"thinking": {"type": "enabled", "budget_tokens": 4096}},
    )

    # 收集完整响应和思考过程
    full_content = ""
    full_thinking = ""

    print("\n--- 思考过程 ---")
    for chunk in stream_response:
        # 处理思考内容 - 使用字典访问避免 LSP 错误
        delta = chunk.choices[0].delta

        # 打印思考过程
        thinking_text = getattr(delta, "thinking", None)
        if thinking_text:
            full_thinking += thinking_text
            print(thinking_text, end="", flush=True)

        # 打印实际回复
        content_text = getattr(delta, "content", None)
        if content_text:
            full_content += content_text
            print(content_text, end="", flush=True)

    print("\n--- 思考结束 ---\n")

    # 获取 token 使用量（需要在请求后从 usage 中获取，流式可能不完整）
    # 注意：流式响应可能不返回完整的 usage 信息
    response_text = full_content

    # 尝试获取 token 使用量（如果 API 支持）
    input_tokens = output_tokens = total_tokens = 0
    try:
        # 重新发起非流式请求以获取准确的 token 使用量
        response_for_usage = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            extra_body={"thinking": {"type": "enabled", "budget_tokens": 4096}},
        )
        usage = response_for_usage.usage
        if usage:
            input_tokens = usage.prompt_tokens
            output_tokens = usage.completion_tokens
            total_tokens = usage.total_tokens

            cost = (input_tokens / 1_000_000) * INPUT_PRICE_PER_M + (
                output_tokens / 1_000_000
            ) * OUTPUT_PRICE_PER_M

            total_cost += cost

            log_entry = (
                f"{now},{input_tokens},{output_tokens},{total_tokens},{cost:.4f}\n"
            )
            os.makedirs("memory", exist_ok=True)
            with open(token_log_path, "a", encoding="utf-8") as f:
                if os.path.getsize(token_log_path) == 0:
                    f.write(
                        "timestamp,input_tokens,output_tokens,total_tokens,cost_usd\n"
                    )
                f.write(log_entry)

            print(
                f"Token usage - Input: {input_tokens}, Output: {output_tokens}, Total: {total_tokens}, Cost: ${cost:.4f}"
            )
    except Exception as e:
        print(f"获取 token 使用量失败: {e}")

    # 记录 AI 原始回复（包括思考过程）
    os.makedirs("memory", exist_ok=True)
    with open(
        f"memory/ai_response_{now.replace(':', '-').replace(' ', '_')}.log",
        "w",
        encoding="utf-8",
    ) as f:
        f.write(
            f"=== Thinking ===\n{full_thinking}\n\n=== Response ===\n{response_text or ''}"
        )

    with open(
        f"memory/last_thoughts.md",
        "w",
        encoding="utf-8",
    ) as f:
        f.write(response_text or "")

    # --- 3. 执行意志 (Execute Will) ---

    code_block_pattern = r"```python\s*\n(.*?)\n```"
    code_blocks = re.findall(code_block_pattern, response_text or "", re.DOTALL)

    if len(code_blocks) == 0:
        python_code = response_text.strip() if response_text else ""
    elif len(code_blocks) == 1:
        python_code = code_blocks[0].strip()
    else:
        python_code = ""
        with open("memory/last_execution.log", "w", encoding="utf-8") as f:
            f.write(
                f"--- Python Execution Log ---\nError: Multiple code blocks detected ({len(code_blocks)} found). Please output only ONE code block.\n"
            )
        print(
            f"Error: Multiple code blocks detected ({len(code_blocks)} found). Please output only ONE code block."
        )
        python_code = None

    if python_code:
        print("Executing Python Script...")
        with open("memory/last_script.py", "w", encoding="utf-8") as f:
            f.write(python_code)
        try:
            old_stdout = sys.stdout
            sys.stdout = io.StringIO()
            exec(python_code, {})
            stdout = sys.stdout.getvalue()
            sys.stdout = old_stdout
            stderr = ""
        except Exception as e:
            stdout = ""
            stderr = str(e)
        with open("memory/last_execution.log", "w", encoding="utf-8") as f:
            f.write(f"--- Python Execution Log ---\nStdout: {stdout}\nStderr: {stderr}")

except Exception as e:
    print(f"Error during AI execution: {e}")
    # 可以选择把错误写进 memory/error.log 让它下次知道自己出错了
