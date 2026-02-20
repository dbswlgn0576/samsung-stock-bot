import os
import requests
import yfinance as yf
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

# --- [설정] 본인의 정보 ---
TOKEN = "8114787639:AAHql-XrNDswzFKS2MUUzvuAlQ-s5kjhcfY"
CHAT_ID = "7216858159"

# 1. 텔레그램 전송 함수
def send_message(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"전송 오류: {e}")

# 2. 뉴스 수집 함수
def get_news_brief(count=3):
    try:
        url = "https://finance.naver.com/item/news_news.naver?code=005930"
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(url, headers=headers)
        res.encoding = 'cp949'
        soup = BeautifulSoup(res.text, 'html.parser')
        news_items = soup.select('.title a')
        keywords = ['주가', '외인', '매수', '매도', '실적', '반도체', '특징주', '전망', '상승', '하락']
        filtered = []
        for news in news_items:
            title = news.get_text().strip()
            if any(k in title for k in keywords):
                link = "https://finance.naver.com" + news['href']
                filtered.append(f"· {title}\n  🔗 {link}")
            if len(filtered) >= count: break
        return "📰 <b>[삼성전자 주요 뉴스]</b>\n" + "\n\n".join(filtered) if filtered else "📰 주요 뉴스 없음"
    except: return "❌ 뉴스 수집 실패"

# 3. 상세 수급 데이터 (외인/기관)
def get_detailed_trend():
    try:
        url = "https://finance.naver.com/item/frgn.naver?code=005930"
        res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        soup = BeautifulSoup(res.text, 'html.parser')
        rows = soup.select('table.type2 tr')
        for row in rows:
            tds = row.select('td')
            if len(tds) >= 9:
                date = tds[0].get_text().strip()
                inst = tds[5].get_text().strip().replace(',', '') 
                fore = tds[6].get_text().strip().replace(',', '') 
                if fore.replace('-', '').isdigit():
                    return date, int(fore), int(inst)
        return None, 0, 0
    except: return None, 0, 0

# 4. 종합 분석 및 브리핑 생성
def get_stock_brief():
    try:
        us_tickers = [("^SOX", "필반도체"), ("NVDA", "엔비디아"), ("MU", "마이크론")]
        us_results = []; sox_change = 0
        for sym, name in us_tickers:
            h = yf.Ticker(sym).history(period="2d")
            if len(h) < 2: continue
            chg = ((h['Close'].iloc[-1] - h['Close'].iloc[-2]) / h['Close'].iloc[-2]) * 100
            if sym == "^SOX": sox_change = chg
            us_results.append(f"{'🔴' if chg > 0 else '🔵'} {name}: {chg:+.2f}%")
        
        s_ticker = yf.Ticker("005930.KS")
        s_hist = s_ticker.history(period="2d")
        curr = s_hist['Close'].iloc[-1]
        diff = ((curr - s_hist['Close'].iloc[-2]) / s_hist['Close'].iloc[-2]) * 100
        f_date, f_buy, i_buy = get_detailed_trend()
        
        msg = f"🌍 <b>[해외 증시 요약]</b>\n" + "\n".join(us_results) + "\n\n"
        msg += f"🇰🇷 <b>[삼성전자 ({f_date})]</b>\n현재가: {int(curr):,}원 ({diff:+.2f}%)\n"
        msg += f"👤 외인: {f_buy:+,d} / 🏢 기관: {i_buy:+,d}\n\n"
        
        analysis = "🔮 <b>[전망/분석]</b> "
        if sox_change > 0.5: analysis += "반도체 업황 호조로 긍정적 흐름이 기대됩니다. 📈"
        elif sox_change < -0.5: analysis += "차익 실현 매물 및 하락 압력에 유의하세요. 📉"
        else: analysis += "방향성 탐색을 위한 관망세가 예상됩니다. ⚖️"
        
        return msg + analysis
    except Exception as e: return f"❌ 분석 중 오류: {e}"

# --- 5. [메인 실행부] 오전/오후 시간에 따라 제목 자동 변경 ---
if __name__ == "__main__":
    # 한국 시간(KST) 계산 (UTC+9)
    now = datetime.utcnow() + timedelta(hours=9)
    current_hour = now.hour

    # 데이터 가져오기
    stock_info = get_stock_brief()
    news_info = get_news_brief()

    # 시간에 따른 제목 설정 (오전 12시 이전이면 오전 브리핑, 이후면 오후 브리핑)
    if current_hour < 12:
        title = "☀️ <b>[삼성전자 장 시작 전 브리핑]</b>"
    else:
        title = "🌙 <b>[삼성전자 장 마감 후 브리핑]</b>"
    
    final_message = f"{title}\n\n{stock_info}\n\n{news_info}"
    
    # 텔레그램 전송
    send_message(final_message)
    print(f"전송 완료: {title} (KST {now.strftime('%H:%M')})")
