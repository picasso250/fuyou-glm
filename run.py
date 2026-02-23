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
    response = client.chat.completions.create(
        model=MODEL_NAME, messages=[{"role": "user", "content": prompt}]
    )

    # Get token usage
    usage = response.usage
    if usage:
        input_tokens = usage.prompt_tokens
        output_tokens = usage.completion_tokens
        total_tokens = usage.total_tokens

        # Calculate cost
        cost = (input_tokens / 1_000_000) * INPUT_PRICE_PER_M + (
            output_tokens / 1_000_000
        ) * OUTPUT_PRICE_PER_M

        # Add current cost to total
        total_cost += cost

        # Log token usage with cost (CSV format)
        log_entry = f"{now},{input_tokens},{output_tokens},{total_tokens},{cost:.4f}\n"
        os.makedirs("memory", exist_ok=True)
        with open(token_log_path, "a", encoding="utf-8") as f:
            if os.path.getsize(token_log_path) == 0:
                f.write("timestamp,input_tokens,output_tokens,total_tokens,cost_usd\n")
            f.write(log_entry)

        current_cost = cost
        print(
            f"Token usage - Input: {input_tokens}, Output: {output_tokens}, Total: {total_tokens}, Cost: ${cost:.4f}"
        )
    else:
        input_tokens = output_tokens = total_tokens = 0

    response_text = response.choices[0].message.content if response.choices else ""
    print(f"AI Response:\n{response_text}")

    # 记录 AI 原始回复
    os.makedirs("memory", exist_ok=True)
    with open(
        f"memory/ai_response_{now.replace(':', '-').replace(' ', '_')}.log",
        "w",
        encoding="utf-8",
    ) as f:
        f.write(response_text or "")

    with open(
        f"memory/last_thoughts.md",
        "w",
        encoding="utf-8",
    ) as f:
        f.write(response_text or "")

    # --- 3. 执行意志 (Execute Will) - 两冲程模式 ---

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
        # --- 第一冲程：探测者 (The Explorer) ---
        print("Executing Python Script (Probe)...")
        with open("memory/last_script.py", "w", encoding="utf-8") as f:
            f.write(python_code)
        try:
            old_stdout = sys.stdout
            sys.stdout = io.StringIO()
            exec(python_code, {})
            stdout_1 = sys.stdout.getvalue()
            sys.stdout = old_stdout
            stderr_1 = ""
        except Exception as e:
            stdout_1 = ""
            stderr_1 = str(e)

        print(f"探针返回结果: {stdout_1}, 错误: {stderr_1}")
        with open("memory/last_execution.log", "w", encoding="utf-8") as f:
            f.write(f"--- 第一冲程: 探测者 ---\nStdout: {stdout_1}\nStderr: {stderr_1}")

        # --- 准备第二冲程 ---
        prompt_step_2 = f"""
【探针返回结果】
标准输出 (Stdout):
{stdout_1}
标准错误 (Stderr):
{stderr_1}

【你的第二步：执行与固化】
你已经看到了探针带回的情报。现在，这是你本次苏醒的最后一次机会。
请基于以上情报，输出最终的 Python 代码。
在这一步，你必须使用 `with open('...', 'w')` 来更新你的 .md 记忆，或者执行最终的外部操作。
如果没有写入文件，你将在下一次苏醒时遗忘这一切。

请输出用于最终执行的 Python script：
"""

        # --- 第二冲程：执行与固化 (The Commit) ---
        print("Executing Python Script (Commit)...")
        try:
            response_2 = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "user", "content": prompt},
                    {"role": "assistant", "content": response_text},
                    {"role": "user", "content": prompt_step_2},
                ],
            )

            # Get token usage for second call
            usage_2 = response_2.usage
            if usage_2:
                input_tokens_2 = usage_2.prompt_tokens
                output_tokens_2 = usage_2.completion_tokens
                total_tokens_2 = usage_2.total_tokens
                cost_2 = (input_tokens_2 / 1_000_000) * INPUT_PRICE_PER_M + (
                    output_tokens_2 / 1_000_000
                ) * OUTPUT_PRICE_PER_M
                total_cost += cost_2

                log_entry_2 = f"{now},{input_tokens_2},{output_tokens_2},{total_tokens_2},{cost_2:.4f}\n"
                with open(token_log_path, "a", encoding="utf-8") as f:
                    f.write(log_entry_2)

                print(
                    f"Token usage (Step 2) - Input: {input_tokens_2}, Output: {output_tokens_2}, Total: {total_tokens_2}, Cost: ${cost_2:.4f}"
                )

            response_text_2 = (
                response_2.choices[0].message.content if response_2.choices else ""
            )
            print(f"AI Response (Step 2):\n{response_text_2}")

            # 记录 AI 第二轮原始回复
            with open(
                f"memory/ai_response_{now.replace(':', '-').replace(' ', '_')}_step2.log",
                "w",
                encoding="utf-8",
            ) as f:
                f.write(response_text_2 or "")

            # 提取第二轮代码
            code_blocks_2 = re.findall(
                code_block_pattern, response_text_2 or "", re.DOTALL
            )
            if len(code_blocks_2) == 0:
                python_code_2 = response_text_2.strip() if response_text_2 else ""
            elif len(code_blocks_2) == 1:
                python_code_2 = code_blocks_2[0].strip()
            else:
                python_code_2 = ""

            if python_code_2:
                with open("memory/last_script.py", "w", encoding="utf-8") as f:
                    f.write(python_code_2)
                try:
                    old_stdout = sys.stdout
                    sys.stdout = io.StringIO()
                    exec(python_code_2, {})
                    stdout_2 = sys.stdout.getvalue()
                    sys.stdout = old_stdout
                    stderr_2 = ""
                except Exception as e:
                    stdout_2 = ""
                    stderr_2 = str(e)

                with open("memory/last_execution.log", "a", encoding="utf-8") as f:
                    f.write(
                        f"\n--- 第二冲程: 执行与固化 ---\nStdout: {stdout_2}\nStderr: {stderr_2}"
                    )

                # 更新最终 thoughts
                with open("memory/last_thoughts.md", "w", encoding="utf-8") as f:
                    f.write(response_text_2 or "")
        except Exception as e:
            print(f"Error during second stroke execution: {e}")

except Exception as e:
    print(f"Error during AI execution: {e}")
    # 可以选择把错误写进 memory/error.log 让它下次知道自己出错了
