iimport os
import requests
import yfinance as yf
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

# --- [설정] ---
TOKEN = "8114787639:AAHql-XrNDswzFKS2MUUzvuAlQ-s5kjhcfY"
CHAT_ID = "7216858159"

def send_message(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML", "disable_web_page_preview": True}
    requests.post(url, json=payload, timeout=10)

def get_news_brief():
    try:
        url = "https://finance.naver.com/item/news_news.naver?code=005930"
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(url, headers=headers, timeout=10)
        res.encoding = 'cp949'
        soup = BeautifulSoup(res.text, 'html.parser')
        news_items = soup.select('.title a')
        filtered = []
        if news_items:
            for news in news_items:
                title = news.get_text().strip()
                link = "https://finance.naver.com" + news['href']
                if len(title) > 5:
                    filtered.append(f"<b>• {title}</b>\n  🔗 <a href='{link}'>뉴스보기</a>")
                if len(filtered) >= 3: break
        return "📰 <b>주요 뉴스</b>\n" + "\n\n".join(filtered) if filtered else "📰 표시할 뉴스가 없습니다."
    except:
        return "📰 뉴스 정보 수집 중"

def get_market_data():
    try:
        # 1. 글로벌 증시 (S&P 500 추가 및 달러 표시)
        tickers = {"^GSPC": "S&P 500", "^SOX": "필라반도체", "NVDA": "엔비디아", "TSM": "TSMC", "^IXIC": "나스닥"}
        us_stats = []
        sox_chg = 0
        us_date = ""
        for sym, name in tickers.items():
            try:
                t = yf.Ticker(sym)
                h = t.history(period="3d")
                if not h.empty:
                    curr, prev = h['Close'].iloc[-1], h['Close'].iloc[-2]
                    chg = ((curr - prev) / prev) * 100
                    if us_date == "": us_date = h.index[-1].strftime('%m/%d')
                    if sym == "^SOX": sox_chg = chg
                    
                    price_str = f"${curr:,.2f}" if sym != "^SOX" and sym != "^IXIC" and sym != "^GSPC" else f"{curr:,.2f}"
                    us_stats.append(f"{'🔺' if chg > 0 else '🔹'} {name}: {price_str} ({chg:+.2f}%)")
            except: continue

        # 2. 삼성전자 주가
        s_ticker = yf.Ticker("005930.KS")
        s_h
