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
    except:
        pass

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
    except: return "📰 뉴스 정보 수집 중"

def format_buy_sell(val_str):
    val_str = val_str.replace(',', '').strip()
    try:
        val = int(val_str)
        return f"+{val:,}" if val > 0 else f"{val:,}"
    except: return val_str

def get_market_data():
    try:
        # 1. 글로벌 증시 (마이크론 포함)
        tickers = {"^GSPC": "S&P 500", "^SOX": "필라반도체", "NVDA": "엔비디아", "TSM": "TSMC", "MU": "마이크론", "^IXIC": "나스닥"}
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
                    price_str = f"${curr:,.2f}" if sym not in ["^SOX", "^IXIC", "^GSPC"] else f"{curr:,.2f}"
                    us_stats.append(f"{'🔺' if chg > 0 else '🔹'} {name}: {price_str} ({chg:+.2f}%)")
            except: continue

        # 2. 삼성전자 주가
        s_ticker = yf.Ticker("005930.KS")
        s_h = s_ticker.history(period="3d")
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

        msg = f"🌍 <b>글로벌 증시 ({us_date})</b>\n" + "\n".join(us_stats) + "\n\n"
        msg += f"🇰🇷 <b>삼성전자 현황 ({s_date})</b>\n"
        msg += f"현재가: <b>{int(curr_p):,}원</b> ({chg_r:+.2f}%)\n"
        msg += f"거래량: {int(vol):,d}주\n\n"
        msg += f"📊 <b>최근 상세 수급</b>\n"
        msg += f"👤 개인: {p_net} / 🏢 기관: {i_net}\n"
        msg += f"🚩 <b>외인: {f_net}</b> / 💻 <b>프로그램: {prg_net}</b>\n\n"
        
        # 4. 당일 단기 대응 가이드
        strategy = "💡 <b>장 시작 전 단기 대응 가이드</b>\n"
        if sox_chg >= 1.5:
            strategy += "<b>[강세 예상]</b> 필반지수 급등으로 삼성전자 '갭상승' 출발이 유력합니다. 장 초반 외인/프로그램 매수세 유지 시 강한 탄력이 기대됩니다."
        elif 0.5 <= sox_chg < 1.5:
            strategy += "<b>[우상향 기대]</b> 미 반도체 호조로 긍정적 출발이 예상됩니다. 다만 장중 수급 이탈 여부를 프로그램 추이로 꼭 확인하세요."
        elif -0.5 < sox_chg < 0.5:
            strategy += "<b>[혼조세]</b> 미 증시 모멘텀이 약합니다. 시초가 이후 전일 종가 지지 여부를 확인하며 박스권 대응이 유리합니다."
        elif -1.5 < sox_chg <= -0.5:
            strategy += "<b>[조정 유의]</b> 미 증시 하락으로 시초가 약세 가능성이 큽니다. 성급한 저가 매수보다 수급 진정을 기다리세요."
        else:
            strategy += "<b>[약세 경계]</b> 미 반도체주 투매로 하락 압력이 매우 큽니다. 장 초반 투매 동참보다 오후장 진정 시점을 확인하세요."
        
        return msg + strategy
    except Exception as e:
        return f"⚠️ 분석 중 오류: {str(e)}"

if __name__ == "__main__":
    now = datetime.utcnow() + timedelta(hours=9)
    m_data = get_market_data()
    n_data = get_news_brief()
    title = f"☀️ <b>삼성전자 장 시작 전 브리핑</b>" if now.hour < 12 else f"🌙 <b>삼성전자 장 마감 후 브리핑</b>"
    final_msg = f"{title} ({now.strftime('%m/%d %H:%M')})\n\n{m_data}\n\n{n_data}"
    send_message(final_msg)
