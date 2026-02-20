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
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML", "disable_web_page_preview": False}
    requests.post(url, json=payload, timeout=10)

def get_news_brief():
    try:
        url = "https://finance.naver.com/item/news_news.naver?code=005930"
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(url, headers=headers)
        res.encoding = 'cp949'
        soup = BeautifulSoup(res.text, 'html.parser')
        news_items = soup.select('.title a')
        
        filtered = []
        # 주가 영향력이 큰 키워드 중심 추출
        important_keys = ['특징주', '실적', '외인', '매수', '반도체', 'HBM', '전망', '공급']
        for news in news_items:
            title = news.get_text().strip()
            link = "https://finance.naver.com" + news['href']
            if any(k in title for k in important_keys):
                filtered.append(f"<b>• {title}</b>\n  🔗 <a href='{link}'>뉴스보기</a>")
            if len(filtered) >= 4: break
        return "📰 <b>주요 뉴스 체크</b>\n" + "\n\n".join(filtered)
    except:
        return "📰 뉴스 정보를 가져오지 못했습니다."

def get_market_data():
    try:
        # 1. 해외 증시 (지수 및 주요 종목 확장)
        tickers = {
            "^SOX": "필라델피아 반도체",
            "NVDA": "엔비디아",
            "TSM": "TSMC",
            "^IXIC": "나스닥"
        }
        us_stats = []
        sox_chg = 0
        for sym, name in tickers.items():
            t = yf.Ticker(sym)
            h = t.history(period="2d")
            if len(h) < 2: continue
            curr = h['Close'].iloc[-1]
            prev = h['Close'].iloc[-2]
            chg = ((curr - prev) / prev) * 100
            if sym == "^SOX": sox_chg = chg
            icon = "🔺" if chg > 0 else "🔹"
            us_stats.append(f"{icon} {name}: {chg:+.2f}%")

        # 2. 삼성전자 상세 데이터 (거래량 추가)
        s = yf.Ticker("005930.KS")
        s_h = s.history(period="2d")
        curr_p = s_h['Close'].iloc[-1]
        prev_p = s_h['Close'].iloc[-2]
        chg_p = curr_p - prev_p
        chg_r = (chg_p / prev_p) * 100
        vol = s_h['Volume'].iloc[-1]
        
        # 3. 외인/기관 수급 (네이버 금융 실시간 데이터)
        res = requests.get("https://finance.naver.com/item/frgn.naver?code=005930", headers={'User-Agent': 'Mozilla/5.0'})
        soup = BeautifulSoup(res.text, 'html.parser')
        row = soup.select('table.type2 tr')[3] 
        tds = row.select('td')
        f_net = tds[6].get_text().strip() 
        i_net = tds[5].get_text().strip() 

        # 메시지 구성
        msg = "🌍 <b>글로벌 반도체 현황</b>\n" + "\n".join(us_stats) + "\n\n"
        msg += f"🇰🇷 <b>삼성전자 데이터</b>\n"
        msg += f"현재가: <b>{int(curr_p):,}원</b> ({chg_r:+.2f}%)\n"
        msg += f"전일대비: {int(chg_p):+,d}원\n"
        msg += f"거래량: {int(vol):,d}주\n\n"
        msg += f"📊 <b>최근 수급 현황</b>\n"
        msg += f"외인: {f_net} / 기관: {i_net}\n\n"
        
        # 분석 전략 추가
        strategy = "💡 <b>오늘의 전략:</b> "
        if sox_chg > 1.0: strategy += "미 증시 강세로 '적극 매수' 유효 🚀"
        elif sox_chg < -1.0: strategy += "하방 압력 우려, '보수적 대응' 필요 ⚠️"
        else: strategy += "박스권 횡보 예상, '관망 후 대응' ⚖️"
        
        return msg + strategy
    except Exception as e:
        return f"❌ 데이터 분석 중 오류: {e}"

if __name__ == "__main__":
    now = datetime.utcnow() + timedelta(hours=9)
    hour = now.hour
    
    m_data = get_market_data()
    n_data = get_news_brief()
    
    title = "☀️ <b>[장 시작 전 브리핑]</b>" if hour < 12 else "🌙 <b>[장 마감 후 브리핑]</b>"
    final_msg = f"{title} ({now.strftime('%m/%d')})\n\n{m_data}\n\n{n_data}"
    
    send_message(final_msg)
