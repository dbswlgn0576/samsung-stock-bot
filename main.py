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
    try:
        res = requests.post(url, json=payload, timeout=10)
    except: pass

def get_news_brief():
    """삼성전자/반도체 관련 핵심 뉴스만 추출 (없으면 빈 문자열 반환)"""
    try:
        url = "https://finance.naver.com/item/news_news.naver?code=005930"
        res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        res.encoding = 'cp949'
        soup = BeautifulSoup(res.text, 'html.parser')
        titles = soup.select('.title a')
        
        filtered_news = []
        keywords = ['삼성', '반도체', 'HBM', '파운드리']
        
        for t in titles:
            txt = t.get_text().strip()
            # 키워드가 포함된 뉴스만 필터링
            if any(k in txt for k in keywords):
                txt_esc = txt.replace('<', '&lt;').replace('>', '&gt;')
                link = "https://finance.naver.com" + t['href']
                filtered_news.append(f"• {txt_esc}\n  🔗 <a href='{link}'>뉴스보기</a>")
            if len(filtered_news) >= 3: break
            
        if not filtered_news:
            return "" # 관련 뉴스 없으면 빈값 반환
        return "📰 <b>주요 뉴스</b>\n" + "\n\n".join(filtered_news) + "\n\n"
    except: return ""

def format_num(val_str):
    """숫자 기호 간소화 (+/-)"""
    val_str = val_str.replace(',', '').strip()
    try:
        val = int(val_str)
        return f"+{val:,}" if val > 0 else f"{val:,}"
    except: return val_str

def get_market_data():
    try:
        # 1. 글로벌 증시
        tickers = {"^GSPC": "S&P500", "^IXIC": "나스닥", "^SOX": "필반체", "NVDA": "NVDA", "TSM": "TSMC", "MU": "MU"}
        us_data = []
        sox_chg = 0
        us_date = ""
        
        for sym, name in tickers.items():
            t = yf.Ticker(sym)
            h = t.history(period="3d")
            if not h.empty:
                curr, prev = h['Close'].iloc[-1], h['Close'].iloc[-2]
                chg = ((curr - prev) / prev) * 100
                if us_date == "": us_date = h.index[-1].strftime('%m/%d')
                if sym == "^SOX": sox_chg = chg
                p_str = f"${curr:,.1f}" if sym in ["NVDA", "TSM", "MU"] else f"{curr:,.0f}"
                us_data.append(f"{'🔺' if chg > 0 else '🔹'} {name}: {p_str} ({chg:+.2f}%)")

        # 2. 삼성전자 현황
        s_ticker = yf.Ticker("005930.KS")
        s_h = s_ticker.history(period="3d")
        curr_p, vol = s_h['Close'].iloc[-1], s_h['Volume'].iloc[-1]
        chg_r = ((curr_p - s_h['Close'].iloc[-2]) / s_h['Close'].iloc[-2]) * 100
        s_date = s_h.index[-1].strftime('%m/%d')
        
        # 3. 상세 수급 (한 줄 압축 배치)
        p_net, i_net, f_net, prg_net = "0", "0", "0", "0"
        try:
            res = requests.get("https://finance.naver.com/item/frgn.naver?code=005930", headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
            soup = BeautifulSoup(res.text, 'html.parser')
            rows = soup.select('table.type2 tr[onmouseover]')
            if rows:
                tds = rows[0].select('td')
                p_net, i_net, f_net = format_num(tds[4].text), format_num(tds[5].text), format_num(tds[6].text)
            prg_td = soup.select('.inner_sub table tr td span')
            if len(prg_td) > 1: prg_net = format_num(prg_td[1].text)
        except: pass

        msg = f"🌍 <b>글로벌 증시 ({us_date})</b>\n" + "\n".join(us_data) + "\n\n"
        msg += f"🇰🇷 <b>삼성전자 ({s_date})</b>: <b>{int(curr_p):,}원</b> ({chg_r:+.2f}%)\n"
        msg += f"📊 <b>수급(개/기/외/프)</b>\n{p_net} / {i_net} / <b>{f_net}</b> / <b>{prg_net}</b>\n\n"
        
        # 4. 단기 대응 가이드
        strategy = "💡 <b>단기 대응 가이드</b>\n"
        if sox_chg >= 1.5:
            strategy += "<b>[강세]</b> 갭상승 유력. 장 초반 외인/프로그램 매수 유지 시 강한 상승세 기대. 9:30분까지 수급 유지 체크!"
        elif 0.5 <= sox_chg < 1.5:
            strategy += "<b>[우상향]</b> 긍정적 출발 예상. 프로그램 매수 시 안정적이나 외인 차익 실현 주의, 수급 이탈 살필 것."
        elif -0.5 < sox_chg < 0.5:
            strategy += "<b>[보합]</b> 모멘텀 약함. 전일 종가 지지가 관건. 장중 프로그램 추이에 따른 박스권 매매 유리."
        elif -1.5 < sox_chg <= -0.5:
            strategy += "<b>[조정]</b> 보수적 대응. 프로그램 매도 집중 주의. 지지선 확인 전까지 관망, 오후반전 노릴 것."
        else:
            strategy += "<b>[약세]</b> 하락 압력 매우 큼. 프로그램 매도 폭탄 우려. 장 초반 투매 금지, 오후 진정 확인 후 대응."
        
        return msg + strategy
    except Exception as e:
        return f"⚠️ 분석 중 오류: {str(e)}"

if __name__ == "__main__":
    now = datetime.utcnow() + timedelta(hours=9)
    m_data = get_market_data()
    n_data = get_news_brief()
    title = f"☀️ <b>삼성전자 장 시작 전 브리핑</b>" if now.hour < 12 else f"🌙 <b>삼성전자 장 마감 후 브리핑</b>"
    # 뉴스가 있을 때만 합치고, 없으면 뉴스 섹션 제외
    final_msg = f"{title} ({now.strftime('%m/%d %H:%M')})\n\n{m_data}\n\n{n_data}"
    send_message(final_msg.strip())
