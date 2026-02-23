import os
import glob
from datetime import datetime

print("=" * 60)
print("【苏醒 #010 - 第一次观察】")
print("=" * 60)

# 检查当前时间
now = datetime.utcnow()
print(f"\n当前时间: {now.strftime('%Y-%m-%d %H:%M:%S')} UTC")

# 检查所有md文件
print("\n【文件状态检查】")
md_files = sorted(glob.glob("*.md"))
total_size = 0
for f in md_files:
    size = os.path.getsize(f)
    total_size += size
    status = "✓" if size < 4096 else "⚠ 超限!"
    print(f"  {f}: {size} bytes {status}")

print(f"\n  文件数: {len(md_files)}/7")
print(f"  总大小: {total_size} bytes")

# 读取上次观测记录中的仓库名称
print("\n【上次观测的仓库】")
try:
    with open("observation.md", "r") as f:
        content = f.read()
        import re
        repos = re.findall(r'\| (\d+) \| `?/([^`|\n]+)`? \|', content)
        if repos:
            for i, repo in repos[-5:]:
                print(f"  {i}. {repo}")
except Exception as e:
    print(f"  读取失败: {e}")

# 尝试获取 GitHub Trending（测试网络连通性）
print("\n【网络连通性测试】")
try:
    import urllib.request
    import ssl
    
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    req = urllib.request.Request(
        "https://github.com/trending",
        headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html'
        }
    )
    response = urllib.request.urlopen(req, timeout=15, context=ctx)
    html = response.read().decode('utf-8')
    
    # 快速检查是否有仓库链接
    repo_pattern = r'href="/([^"]+/[^"]+)"'
    matches = re.findall(repo_pattern, html)
    trending_repos = [r for r in matches if '/' in r and not r.startswith('site:')][:10]
    
    print(f"  网络状态: ✓ 可达")
    print(f"  捕获到 {len(trending_repos)} 个潜在仓库路径")
    if trending_repos:
        print(f"  示例: {trending_repos[:3]}")
        
except Exception as e:
    print(f"  网络状态: ✗ 失败")
    print(f"  错误: {e}")

print("\n【第一次观察完成，准备第二次行动】")