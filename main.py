import os
import requests
import yfinance as yf
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

# --- [설정] ---
TOKEN = "8114787639:AAHql-XrNDswzFKS2MUUzvuAlQ-s5kjhcfY"
CHAT_ID = "7216858159"

def send_message(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}
    res = requests.post(url, json=payload, timeout=10)
    print(f"Telegram Response: {res.status_code}") # 실행 로그에서 확인 가능

def get_news_brief():
    try:
        url = "https://finance.naver.com/item/news_news.naver?code=005930"
        res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        res.encoding = 'cp949'
        soup = BeautifulSoup(res.text, 'html.parser')
        titles = soup.select('.title a')
        news_list = []
        for t in titles[:3]: # 상위 3개만
            txt = t.get_text().strip().replace('<', '&lt;').replace('>', '&gt;')
            link = "https://finance.naver.com" + t['href']
            news_list.append(f"• {txt}\n  🔗 <a href='{link}'>뉴스보기</a>")
        return "📰 <b>주요 뉴스</b>\n" + "\n\n".join(news_list) if news_list else "📰 뉴스 없음"
    except: return "📰 뉴스 수집 오류"

def format_num(val_str):
    try:
        val = int(val_str.replace(',', ''))
        return f"+{val:,}" if val > 0 else f"{val:,}"
    except: return val_str

def get_market_data():
    # 지수 순서: S&P500 -> 나스닥 -> 필반체
    indices = {"^GSPC": "S&P 500", "^IXIC": "나스닥", "^SOX": "필라반도체"}
    stocks = {"NVDA": "엔비디아", "TSM": "TSMC", "MU": "마이크론"}
    
    us_indices, us_stocks, sox_chg, us_date = [], [], 0, ""
    
    for sym, name in indices.items():
        h = yf.Ticker(sym).history(period="2d")
        if not h.empty:
            curr, prev = h['Close'].iloc[-1], h['Close'].iloc[-2]
            chg = ((curr - prev) / prev) * 100
            if sym == "^SOX": sox_chg = chg
            us_date = h.index[-1].strftime('%m/%d')
            us_indices.append(f"{'🔺' if chg > 0 else '🔹'} {name}: {curr:,.2f} ({chg:+.2f}%)")

    for sym, name in stocks.items():
        h = yf.Ticker(sym).history(period="2d")
        if not h.empty:
            curr = h['Close'].iloc[-1]
            prev = h['Close'].iloc[-2]
            chg = ((curr - prev) / prev) * 100
            us_stocks.append(f"{'🔺' if chg > 0 else '🔹'} {name}: ${curr:,.2f} ({chg:+.2f}%)")

    # 삼성전자 수급 (네이버)
    res = requests.get("https://finance.naver.com/item/frgn.naver?code=005930", headers={'User-Agent': 'Mozilla/5.0'})
    soup = BeautifulSoup(res.text, 'html.parser')
    rows = soup.select('table.type2 tr[onmouseover]')
    p_net, i_net, f_net = "0", "0", "0"
    if rows:
        tds = rows[0].select('td')
        p_net, i_net, f_net = format_num(tds[4].text), format_num(tds[5].text), format_num(tds[6].text)
    
    # 메시지 구성
    m = f"🌍 <b>글로벌 증시 ({us_date})</b>\n" + "\n".join(us_indices) + "\n"
    m += "----------------------------\n" + "\n".join(us_stocks) + "\n\n"
    m += f"📊 <b>최근 상세 수급</b>\n👤 개인: {p_net} / 🏢 기관: {i_net}\n"
    m += f"🚩 <b>외인: {f_net}</b>\n\n"
    
    strategy = "💡 <b>단기 대응 가이드</b>\n"
    if sox_chg >= 1.0: strategy += "강세 흐름입니다. 외인 매수세 유지 시 적극 대응하세요. 🚀"
    elif sox_chg <= -1.0: strategy += "하락 압력이 큽니다. 보수적으로 관망하세요. ⚠️"
    else: strategy += "보합권 장세입니다. 수급 변화를 주시하세요. ⚖️"
    
    return m + strategy

if __name__ == "__main__":
    now = datetime.utcnow() + timedelta(hours=9)
    final_msg = f"☀️ <b>삼성전자 장 시작 전 브리핑</b> ({now.strftime('%m/%d %H:%M')})\n\n"
    final_msg += get_market_data() + "\n\n" + get_news_brief()
    send_message(final_msg)
