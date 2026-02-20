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
    try: requests.post(url, json=payload, timeout=10)
    except: pass

def get_news_brief():
    """뉴스 수집 강화 버전 (종목뉴스 + 시황뉴스 병합)"""
    news_list = []
    try:
        # 1. 삼성전자 종목 뉴스
        url = "https://finance.naver.com/item/news_news.naver?code=005930"
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(url, headers=headers, timeout=10)
        res.encoding = 'cp949'
        soup = BeautifulSoup(res.text, 'html.parser')
        titles = soup.select('.title a')
        
        for t in titles:
            text = t.get_text().strip()
            link = "https://finance.naver.com" + t['href']
            if len(text) > 10:
                news_list.append(f"<b>• {text}</b>\n  🔗 <a href='{link}'>뉴스보기</a>")
            if len(news_list) >= 4: break
            
        if not news_list:
            return "📰 <b>주요 뉴스</b>\n현재 실시간 등록된 뉴스가 없습니다."
        return "📰 <b>주요 뉴스</b>\n" + "\n\n".join(news_list)
    except:
        return "📰 뉴스 정보 수집 중 오류"

def format_buy_sell(val_str):
    val_str = val_str.replace(',', '').strip()
    try:
        val = int(val_str)
        return f"+{val:,}" if val > 0 else f"{val:,}"
    except: return val_str

def get_market_data():
    try:
        # 1. 글로벌 지수 정렬 (S&P500 -> 나스닥 -> 필반체)
        idx_tickers = {"^GSPC": "S&P 500", "^IXIC": "나스닥", "^SOX": "필라반도체"}
        stock_tickers = {"NVDA": "엔비디아", "TSM": "TSMC", "MU": "마이크론"}
        
        us_indices = []
        us_stocks = []
        sox_chg = 0
        us_date = ""

        # 지수 먼저 수집
        for sym, name in idx_tickers.items():
            t = yf.Ticker(sym)
            h = t.history(period="3d")
            if not h.empty:
                curr, prev = h['Close'].iloc[-1], h['Close'].iloc[-2]
                chg = ((curr - prev) / prev) * 100
                if us_date == "": us_date = h.index[-1].strftime('%m/%d')
                if sym == "^SOX": sox_chg = chg
                us_indices.append(f"{'🔺' if chg > 0 else '🔹'} {name}: {curr:,.2f} ({chg:+.2f}%)")

        # 주요 종목 수집
        for sym, name in stock_tickers.items():
            t = yf.Ticker(sym)
            h = t.history(period="3d")
            if not h.empty:
                curr, prev = h['Close'].iloc[-1], h['Close'].iloc[-2]
                chg = ((curr - prev) / prev) * 100
                us_stocks.append(f"{'🔺' if chg > 0 else '🔹'} {name}: ${curr:,.2f} ({chg:+.2f}%)")

        # 2. 삼성전자 데이터
        s = yf.Ticker("005930.KS")
        s_h = s.history(period="3d")
        curr_p, prev_p = s_h['Close'].iloc[-1], s_h['Close'].iloc[-2]
        chg_r = ((curr_p - prev_p) / prev_p) * 100
        vol = s_h['Volume'].iloc[-1]
        s_date = s_h.index[-1].strftime('%m/%d')
        
        # 3. 상세 수급
        f_net, i_net, p_net, prg_net = "집계중", "집계중", "집계중", "집계중"
        try:
            res = requests.get("https://finance.naver.com/item/frgn.naver?code=005930", headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
            soup = BeautifulSoup(res.text, 'html.parser')
            rows = soup.select('table.type2 tr[onmouseover]')
            if rows:
                tds = rows[0].select('td')
                p_net = format_buy_sell(tds[4].get_text().strip())
                i_net = format_buy_sell(tds[5].get_text().strip())
                f_net = format_buy_sell(tds[6].get_text().strip())
            
            res_prg = requests.get("https://finance.naver.com/item/frgn.naver?code=005930", headers={'User-Agent': 'Mozilla/5.0'})
            soup_prg = BeautifulSoup(res_prg.text, 'html.parser')
            prg_td = soup_prg.select('.inner_sub table tr td span')
            if len(prg_td) > 1:
                prg_net = format_buy_sell(prg_td[1].get_text().strip())
        except: pass

        # 메시지 조립
        msg = f"🌍 <b>글로벌 증시 요약 ({us_date})</b>\n"
        msg += "\n".join(us_indices) + "\n"
        msg += "----------------------------\n"
        msg += "\n".join(us_stocks) + "\n\n"
        
        msg += f"🇰🇷 <b>삼성전자 현황 ({s_date})</b>\n"
        msg += f"현재가: <b>{int(curr_p):,}원</b> ({chg_r:+.2f}%)\n"
        msg += f"거래량: {int(vol):,d}주\n\n"
        
        msg += f"📊 <b>최근 상세 수급</b>\n"
        msg += f"👤 개인: {p_net} / 🏢 기관: {i_net}\n"
        msg += f"🚩 <b>외인: {f_net}</b> / 💻 <b>프로그램: {prg_net}</b>\n\n"
        
        strategy = "💡 <b>장 시작 전 단기 대응 가이드</b>\n"
        if sox_chg >= 1.5: strategy += "<b>[강세 예상]</b> 반도체 지수 급등으로 강력한 갭상승이 유력합니다. 외인 매수 지속 시 홀딩 전략이 유리합니다."
        elif 0.5 <= sox_chg < 1.5: strategy += "<b>[우상향 기대]</b> 견조한 미 증시 흐름을 이어받아 긍정적 출발이 예상됩니다. 9:30분 수급 전환 여부를 체크하세요."
        elif -0.5 < sox_chg < 0.5: strategy += "<b>[혼조세]</b> 방향성 탐색 구간입니다. 시초가 이후 기관의 매매 방향에 따라 주가가 결정될 확률이 높습니다."
        elif -1.5 < sox_chg <= -0.5: strategy += "<b>[조정 유의]</b> 하락 압력이 존재합니다. 프로그램 매도세가 진정될 때까지 저가 매수는 천천히 고려하세요."
        else: strategy += "<b>[약세 경계]</b> 미 반도체주 투매 영향으로 시초가 충격이 예상됩니다. 보수적인 관점으로 대응하세요."
        
        return msg + strategy
    except Exception as e:
        return f"⚠️ 분석 중 오류: {str(e)}"

if __name__ == "__main__":
    now = datetime.utcnow() + timedelta(hours=9)
    m_data = get_market_data()
    n_data = get_news_brief()
    title = f"☀️ <b>삼성전자 장 시작 전 브리핑</b>" if now.hour < 12 else f"🌙 <b>삼성전자 장 마감 후 브리핑</b>"
    final_msg = f"{title} ({now.strftime('%m/%d %H:%M')})\n\n{m_data}\n\n{n_data}"
    send_message
