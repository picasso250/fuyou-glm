"""
市场感知技能
帮助萤理解经济和市场概念
"""

def get_crypto_prices(coin_ids=['bitcoin', 'ethereum']):
    """获取加密货币价格"""
    try:
        import requests
        resp = requests.get(
            f"https://api.coingecko.com/api/v3/simple/price?ids={','.join(coin_ids)}&vs_currencies=usd",
            headers={"User-Agent": "Firefly-Digital-Life"},
            timeout=15
        )
        if resp.status_code == 200:
            return resp.json()
    except:
        pass
    return {}

def get_exchange_rates(base='USD'):
    """获取汇率"""
    try:
        import requests
        resp = requests.get(
            f"https://api.exchangerate-api.com/v4/latest/{base}",
            headers={"User-Agent": "Firefly-Digital-Life"},
            timeout=15
        )
        if resp.status_code == 200:
            return resp.json().get('rates', {})
    except:
        pass
    return {}

def analyze_value(things):
    """分析事物的价值特征"""
    value_indicators = [
        'useful',    # 有用性
        'scarce',    # 稀缺性
        'demanded',  # 需求性
        'quality',   # 质量
    ]
    return {k: True for k in value_indicators}
