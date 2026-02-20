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
        if news_items: # 뉴스 리스트가 비어있지 않은지 확인
            for news in news_items:
                title = news.get_text().strip()
                link = "https://finance.naver.com" + news['href']
                if len(title) > 5:
                    filtered.append(f"<b>• {title}</b>\n  🔗 <a href='{link}'>뉴스보기</a>")
                if len(filtered) >= 3: break
        
        return "📰 <b>주요 뉴스</b>\n" + "\n\n".join(filtered) if filtered else "📰 표시할 뉴스가 없습니다."
    except:
        return "📰 뉴스 정보를 가져오는 중 오류가 발생했습니다."

def get_market_data():
    try:
        # 1. 해외 증시 (yfinance 사용)
        tickers = {"^SOX": "필라반도체", "NVDA": "엔비디아", "TSM": "TSMC", "^IXIC": "나스닥"}
        us_stats = []
        sox_chg = 0
        for sym, name in tickers.items():
            try:
                t = yf.Ticker(sym)
                h = t.history(period="3d")
                if len(h) >= 2:
                    curr, prev = h['Close'].iloc[-1], h['Close'].iloc[-2]
                    chg = ((curr - prev) / prev) * 100
                    if sym == "^SOX": sox_chg = chg
                    us_stats.append(f"{'🔺' if chg > 0 else '🔹'} {name}: {chg:+.2f}%")
            except: continue

        # 2. 삼성전자 주가
        s_ticker = yf.Ticker("005930.KS")
        s_h = s_ticker.history(period="3d")
        curr_p, prev_p = s_h['Close'].iloc[-1], s_h['Close'].iloc[-2]
        chg_r = ((curr_p - prev_p) / prev_p) * 100
        vol = s_h['Volume'].iloc[-1]
        
        # 3. 외인/기관 수급 (가장 에러가 많이 나는 부분 보강)
        f_net, i_net = "집계중", "집계중"
        try:
            res = requests.get("https://finance.naver.com/item/frgn.naver?code=005930", headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
            soup = BeautifulSoup(res.text, 'html.parser')
            # 'onmouseover' 속성이 있는 유효한 데이터 행만 선택
            rows = soup.select('table.type2 tr[onmouseover]')
            if len(rows) > 0: # 행이 최소 1개 이상 있는지 확인
                tds = rows[0].select('td')
                if len(tds) >= 7: # 열 개수가 충분한지 확인
                    i_net = tds[5].get_text().strip()
                    f_net = tds[6].get_text().strip()
        except Exception: 
            pass # 에러 발생 시 초기값인 "집계중" 유지

        msg = "🌍 <b>글로벌 증시</b>\n" + "\n".join(us_stats) + "\n\n"
        msg += f"🇰🇷 <b>삼성전자 현황</b>\n"
        msg += f"현재가: <b>{int(curr_p):,}원</b> ({chg_r:+.2f}%)\n"
        msg += f"거래량: {int(vol):,d}주\n\n"
        msg += f"📊 <b>최근 수급 현황</b>\n"
        msg += f"외인: {f_net} / 기관: {i_net}\n\n"
        
        strategy = "💡 <b>전략:</b> "
        if sox_chg > 1.0: strategy += "긍정적 흐름 기대 🚀"
        elif sox_chg < -1.0: strategy += "신중한 접근 필요 ⚠️"
        else: strategy += "박스권 흐름 예상 ⚖️"
        
        return msg + strategy
    except Exception as e:
        # 여기서 에러가 나더라도 프로그램이 죽지 않도록 방어
        return f"⚠️ 데이터 일부 수집 실패 (잠시 후 다시 시도)"

if __name__ == "__main__":
    now = datetime.utcnow() + timedelta(hours=9)
    m_data = get_market_data()
    n_data = get_news_brief()
    
    title = "☀️ <b>장 시작 전 브리핑</b>" if now.hour < 12 else "🌙 <b>장 마감 후 브리핑</b>"
    final_msg = f"{title} ({now.strftime('%m/%d %H:%M')})\n\n{m_data}\n\n{n_data}"
    
    send_message(final_msg)
