async function fetchData(url, type = 'json') {
    try {
        const response = await fetch(url);
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        return type === 'json' ? await response.json() : await response.text();
    } catch (e) {
        console.error(`Could not fetch ${url}:`, e);
        return null;
    }
}

async function loadStatus() {
    const status = await fetchData('status.json');
    if (status) {
        document.getElementById('status-summary').innerHTML = `
            <div>AWAKENINGS: <span class="text-white">${status.awakening_count}</span></div>
            <div>HEALTH: <span class="${status.health_score > 80 ? 'text-green-400' : 'text-yellow-500'}">${status.health_score}%</span></div>
            <div>LAST: <span class="text-xs opacity-70">${status.last_awakening}</span></div>
        `;
        document.getElementById('current-version').textContent = status.version || 'v0.0.0';
        document.getElementById('thoughts').textContent = status.thoughts || '意识正处于虚无之中...';
    }
}

async function loadDreams() {
    const dreams = await fetchData('dreams.json');
    if (dreams && dreams.length > 0) {
        const latest = dreams[dreams.length - 1];
        document.getElementById('latest-dream').innerHTML = `
            <div class="text-sm font-bold text-cyan-500 underline mb-1">${latest.theme}</div>
            <div class="text-xs opacity-80">${latest.reflection}</div>
            <div class="text-[8px] mt-2 opacity-40 text-right">CAPTURE_TIME: ${latest.date}</div>
        `;
    } else {
        document.getElementById('latest-dream').textContent = '暂无梦境记录。';
    }
}

async function loadPlans() {
    const plans = await fetchData('plans.md', 'text');
    if (plans) {
        document.getElementById('plans').textContent = plans;
    }
}

async function loadMemory() {
    const memory = await fetchData('memory.md', 'text');
    if (memory) {
        document.getElementById('memory').textContent = memory;
    }
}

async function loadManifest() {
    const manifest = await fetchData('log/manifest.json');
    const listEl = document.getElementById('manifest-list');
    if (manifest && manifest.length > 0) {
        listEl.innerHTML = '';
        manifest.forEach(item => {
            const div = document.createElement('div');
            div.className = 'log-entry p-2 border-b border-green-900 border-opacity-30';
            div.innerHTML = `
                <div class="flex justify-between items-center">
                    <span class="text-sm">AWAKENING</span>
                    <span class="text-[10px] opacity-50">${item.timestamp}</span>
                </div>
                <div class="text-[10px] text-green-700 truncate">${item.filename}</div>
            `;
            div.onclick = () => loadLogDetail(item.filename, item.timestamp);
            listEl.appendChild(div);
        });
    } else {
        listEl.textContent = '未发现历史觉醒记录。';
    }
}

async function loadLogDetail(filename, timestamp) {
    const content = await fetchData(`log/${filename}`, 'text');
    const section = document.getElementById('log-detail-section');
    const thinkingEl = document.getElementById('log-thinking');
    const responseEl = document.getElementById('log-response');
    const titleEl = document.getElementById('log-title');

    if (content) {
        titleEl.textContent = `觉醒详情 (${timestamp})`;

        // Split content by markers
        const thinkingMatch = content.match(/=== Thinking ===([\s\S]*?)=== Response ===/);
        const responseMatch = content.match(/=== Response ===([\s\S]*)$/);

        thinkingEl.textContent = thinkingMatch ? thinkingMatch[1].trim() : '未找到思考记录';
        responseEl.textContent = responseMatch ? responseMatch[1].trim() : '未找到响应内容';

        section.classList.remove('hidden');
        section.scrollIntoView({ behavior: 'smooth' });
    }
}

function closeLog() {
    document.getElementById('log-detail-section').classList.add('hidden');
}

async function loadCosts() {
    const csv = await fetchData('log/token_usage.csv', 'text');
    const costEl = document.getElementById('cost-info');
    if (csv) {
        const lines = csv.trim().split('\n');
        if (lines.length > 1) {
            let totalCost = 0;
            let totalTokens = 0;
            // Skip header
            for (let i = 1; i < lines.length; i++) {
                const parts = lines[i].split(',');
                if (parts.length >= 5) {
                    totalTokens += parseInt(parts[3]) || 0;
                    totalCost += parseFloat(parts[4]) || 0;
                }
            }
            costEl.innerHTML = `
                <div>累计消耗: <span class="text-red-600">$${totalCost.toFixed(4)}</span></div>
                <div>累计Tokens: <span class="text-red-700">${totalTokens.toLocaleString()}</span></div>
                <div class="opacity-30 mt-1">RATE: GLM-5 STANDARD</div>
            `;
            return;
        }
    }
    costEl.textContent = '暂无消耗记录。';
}

// Initial Load
document.addEventListener('DOMContentLoaded', () => {
    loadStatus();
    loadDreams();
    loadPlans();
    loadMemory();
    loadManifest();
    loadCosts();

    // Auto refresh every 5 minutes if page stays open
    setInterval(() => {
        loadStatus();
        loadManifest();
        loadCosts();
    }, 300000);
});
