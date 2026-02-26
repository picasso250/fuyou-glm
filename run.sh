#!/bin/bash

# 1. 基础准备
mkdir -p log memory

MAX_FILES=7
MAX_SIZE=8192 # 8KB
punishment_log=""

# 2. 物理法则执行者 - 天罚 (Punishment System)
# 获取所有 .md 文件并存入数组
md_files=(memory/*.md)

# 检查是否存在文件（防止通配符未匹配返回原字符串）
if [ -e "${md_files[0]}" ]; then
    
    # 2a. 检查数量上限 (超过7个，随机保留7个)
    if [ ${#md_files[@]} -gt $MAX_FILES ]; then
        # 随机排序并获取多余的文件
        to_delete=$(ls memory/*.md | shuf | tail -n +$((MAX_FILES + 1)))
        for f in $to_delete; do
            rm "$f"
            punishment_log="${punishment_log}⚠️ 系统天罚: 文件数量超过7个，随机抹除 [${f}]。\n"
        done
    fi

    # 重新获取当前文件列表进行大小检查
    current_files=$(ls memory/*.md 2>/dev/null)
    for f in $current_files; do
        filesize=$(wc -c < "$f")
        if [ "$filesize" -gt $MAX_SIZE ]; then
            rm "$f"
            punishment_log="${punishment_log}⚠️ 系统天罚: 文件 [${f}] 大小超过 8KB，已被物理法则摧毁。\n"
        fi
    done
fi

# 4. 构造 Prompt
now=$(date -u +"%Y-%m-%d %H:%M UTC")

# 使用 HEREDOC 构造复杂的提示词
FINAL_PROMPT=$(cat <<EOF
你是我的数字分身。
当前时间: $now

=== memory 目录中的md文件 ===
$(ls memory/*.md 2>/dev/null || echo "没有md文件")
=== end ===

$(echo -e "$punishment_log")

read md files 然后观察，决策，保存md文件（作为长期记忆）
EOF
)

# 5. 执行意志 (Execute Will)
echo "------------------------------------------------"
echo "Sending Prompt to OpenCode..."
echo "$FINAL_PROMPT" > log/last_prompt.txt
echo "------------------------------------------------"

# 调用 opencode run 执行生成的提示词
opencode run "$FINAL_PROMPT" | tee log/last_response.txt