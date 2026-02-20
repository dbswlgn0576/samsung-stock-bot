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
        requests.post(url, json=payload, timeout=10)
    except: pass

def get_news_brief():
    """삼성전자 관련 핵심 뉴스만 추출 (관련 없으면 출력 안 함)"""
    try:
        url = "https://finance.naver.com/item/news_news.naver?code=005930"
        res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        res.encoding = 'cp949'
        soup = BeautifulSoup(res.text, 'html.parser')
        titles = soup.select('.title a')
        
        filtered = []
        keywords = ['삼성', '반도체', 'HBM', '파운드리', 'D램', '초격차']
        for t in titles:
            txt = t.get_text().strip()
            # 관련 키워드 포함 시에만 추가
            if any(k in txt for k in keywords):
                txt_esc = txt.replace('<', '&lt;').replace('>', '&gt;')
                link = "https://finance.naver.com" + t['href']
                filtered.append(f"<b>• {txt_esc}</b>\n  🔗 <a href='{link}'>뉴스보기</a>")
            if len(filtered) >= 3: break
            
        if not filtered: return "" # 관련 뉴스 없으면 아예 섹션 삭제
        return "📰 <b>주요 뉴스</b>\n" + "\n\n".join(filtered) + "\n\n"
    except: return ""

def format_num(val_str):
    """숫자에 + 기호 및 콤마 추가"""
    val_str = val_str.replace(',', '').strip()
    try:
        val = int(val_str)
        return f"+{val:,}" if val > 0 else f"{val:,}"
    except: return val_str

def get_market_data():
    try:
        # 1. 글로벌 증시 (S&P500 -> 나스닥 -> 필반체 -> 종목 순)
        tickers = {"^GSPC": "S&P 500", "^IXIC": "나스닥", "^SOX": "필라반도체", "NVDA": "엔비디아", "TSM": "TSMC", "MU": "마이크론"}
        us_stats = []
        sox_chg, us_date = 0, ""
        
        for sym, name in tickers.items():
            t = yf.Ticker(sym)
            h = t.history(period="3d")
            if not h.empty:
                curr, prev = h['Close'].iloc[-1], h['Close'].iloc[-2]
                chg = ((curr - prev) / prev) * 100
                if us_date == "": us_date = h.index[-1].strftime('%m/%d')
                if sym == "^SOX": sox_chg = chg
                price_str = f"${curr:,.2f}" if sym not in ["^GSPC", "^IXIC", "^SOX"] else f"{curr:,.2f}"
                us_stats.append(f"{'🔺' if chg > 0 else '🔹'} {name}: {price_str} ({chg:+.2f}%)")

        # 2. 삼성전자 현황
        s_ticker = yf.Ticker("005930.KS")
        s_h = s_ticker.history(period="3d")
        curr_p, prev_p = s_h['Close'].iloc[-1], s_h['Close'].iloc[-2]
        chg_r = ((curr_p - prev_p) / prev_p) * 100
        vol = s_h['Volume'].iloc[-1]
        s_date = s_h.index[-1].strftime('%m/%d')
        
        # 3. 상세 수급
        p_n, i_n, f_n, pr_n = "집계중", "집계중", "집계중", "집계중"
        try:
            res = requests.get("https://finance.naver.com/item/frgn.naver?code=005930", headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
            soup = BeautifulSoup(res.text, 'html.parser')
            rows = soup.select('table.type2 tr[onmouseover]')
            if rows:
                tds = rows[0].select('td')
                p_n, i_n, f_n = format_num(tds[4].text), format_num(tds[5].text), format_num(tds[6].text)
            prg_td = soup.select('.inner_sub table tr td span')
            if len(prg_td) > 1: pr_n = format_num(prg_td[1].text)
        except: pass

        # 메시지 구성 (기존 구성 복원)
        msg = f"🌍 <b>글로벌 증시 ({us_date})</b>\n" + "\n".join(us_stats) + "\n\n"
        msg += f"🇰🇷 <b>삼성전자 현황 ({s_date})</b>\n"
        msg += f"현재가: <b>{int(curr_p):,}원</b> ({chg_r:+.2f}%)\n"
        msg += f"거래량: {int(vol):,d}주\n\n"
        msg += f"📊 <b>최근 상세 수급</b>\n"
        msg += f"👤 개인: {p_n} / 🏢 기관: {i_n}\n"
        msg += f"🚩 <b>외인: {f_n}</b> / 💻 <b>프로그램: {pr_n}</b>\n\n"
        
        # 4. 상세 단기 대응 가이드 복원
        st = "💡 <b>장 시작 전 단기 대응 가이드</b>\n"
        if sox_chg >= 1.5:
            st += "<b>[강세 예상]</b> 필반지수 급등으로 삼성전자 '갭상승' 출발이 유력합니다. 장 초반 외인/프로그램 매수세가 유지된다면 주가 밀림 없이 강한 상승세를 이어갈 확률이 높습니다. 추격 매수보다는 9시 30분까지 수급 유지 여부를 체크하세요."
        elif 0.5 <= sox_chg < 1.5:
            st += "<b>[우상향 기대]</b> 미 반도체주의 견조한 흐름으로 긍정적 출발이 예상됩니다. 프로그램 매수 유입 시 안정적인 흐름이 기대되나, 최근 외인들의 단기 차익 실현 욕구가 강하므로 장중 수급 이탈 여부를 주의 깊게 살피십시오."
        elif -0.5 < sox_chg < 0.5:
            st += "<b>[혼조세/보합]</b> 미 증시 모멘텀이 약합니다. 보합권 출발 후 전일 종가를 지지하는지가 관건입니다. 당일은 방향성 베팅보다는 장중 프로그램 매매 추이에 따른 박스권 단기 매매가 유리한 장세입니다."
        elif -1.5 < sox_chg <= -0.5:
            st += "<b>[조정 유의]</b> 미 증시 하락 여파로 '보수적 대응'이 필요합니다. 장 초반 프로그램 매도세가 집중될 수 있으므로, 지지선 확인 전까지는 성급한 저가 매수보다는 관망하며 장 중반 이후 외인 수급 반전 시점을 노리세요."
        else:
            st += "<b>[약세 경계]</b> 미 반도체주의 투매 현상이 있었습니다. 시초가 하락 압력이 매우 큽니다. 프로그램 매도 폭탄이 우려되므로, 장 초반 투매에 동참하기보다 오후장 수급 진정 여부를 확인하며 보수적으로 대응하시기 바랍니다."
        
        return msg + st
    except Exception as e:
        return f"⚠️ 분석 중 오류: {str(e)}"

if __name__ == "__main__":
    now = datetime.utcnow() + timedelta(hours=9)
    m_data = get_market_data()
    n_data = get_news_brief()
    title = f"☀️ <b>삼성전자 장 시작 전 브리핑</b>" if now.hour < 12 else f"🌙 <b>삼성전자 장 마감 후 브리핑</b>"
    
    # 데이터 합치기 (뉴스가 비어있으면 자동으로 n_data 자리는 건너뜀)
    final_msg = f"{title} ({now.strftime('%m/%d %H:%M')})\n\n{m_data}\n\n{n_data}"
    send_message(final_msg.strip())
