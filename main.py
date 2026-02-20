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
        s_h = s_ticker.history(period="3d")
        curr_p, prev_p = s_h['Close'].iloc[-1], s_h['Close'].iloc[-2]
        chg_r = ((curr_p - prev_p) / prev_p) * 100
        vol = s_h['Volume'].iloc[-1]
        s_date = s_h.index[-1].strftime('%m/%d')
        
        # 3. 상세 수급 (개인/프로그램 추가)
        f_net, i_net, p_net, prg_net = "집계중", "집계중", "집계중", "집계중"
        try:
            res = requests.get("https://finance.naver.com/item/frgn.naver?code=005930", headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
            soup = BeautifulSoup(res.text, 'html.parser')
            rows = soup.select('table.type2 tr[onmouseover]')
            if rows:
                tds = rows[0].select('td')
                p_net = tds[4].get_text().strip()   # 개인
                i_net = tds[5].get_text().strip()   # 기관
                f_net = tds[6].get_text().strip()   # 외인
            
            # 프로그램 수급 별도 추출
            res_prg = requests.get("https://finance.naver.com/item/frgn.naver?code=005930", headers={'User-Agent': 'Mozilla/5.0'})
            soup_prg = BeautifulSoup(res_prg.text, 'html.parser')
            prg_td = soup_prg.select('.inner_sub table tr td span')
            if len(prg_td) > 1:
                prg_net = prg_td[1].get_text().strip()
        except: pass

        msg = f"🌍 <b>글로벌 증시 ({us_date})</b>\n" + "\n".join(us_stats) + "\n\n"
        msg += f"🇰🇷 <b>삼성전자 현황 ({s_date})</b>\n"
        msg += f"현재가: <b>{int(curr_p):,}원</b> ({chg_r:+.2f}%)\n"
        msg += f"거래량: {int(vol):,d}주\n\n"
        msg += f"📊 <b>최근 상세 수급</b>\n"
        msg += f"👤 개인: {p_net} / 🏢 기관: {i_net}\n"
        msg += f"👤 외인: {f_net} / 💻 프로그램: {prg_net}\n\n"
        
        # 4. 상세 전략 내용 보강
        strategy = "💡 <b>상세 전략 분석</b>\n"
        if sox_chg > 1.2:
            strategy += "미 반도체 지수의 강력한 상승으로 국내 소부장 종목들의 동반 상승이 예상됩니다. 외인 매수세 유입 시 전고점 돌파를 시도할 가능성이 높으므로 긍정적인 대응을 추천합니다. 🚀"
        elif sox_chg < -1.2:
            strategy += "미 증시의 하락 압력이 거셉니다. 특히 반도체 중심의 매물이 출회되었으므로, 장 초반 변동성에 유의하며 분할 매수 관점에서 보수적으로 접근하는 것이 유리합니다. ⚠️"
        elif abs(sox_chg) <= 0.5:
            strategy += "글로벌 증시가 뚜렷한 방향성 없이 관망세에 진입했습니다. 국내 증시 또한 수급 주체 간의 눈치보기가 예상되므로, 단기 대응보다는 주요 지지선을 확인하며 긴 호흡으로 대응하세요. ⚖️"
        else:
            strategy += "시장 흐름이 중립적입니다. 개별 뉴스에 따른 종목별 장세가 예상되므로 삼성전자의 실시간 수급 추이를 확인하며 대응하시기 바랍니다. 🔍"
        
        return msg + strategy
    except Exception as e:
        return f"⚠️ 데이터 분석 중 오류: {str(e)}"

if __name__ == "__main__":
    now = datetime.utcnow() + timedelta(hours=9)
    m_data = get_market_data()
    n_data = get_news_brief()
    
    title = f"☀️ <b>삼성전자 장 시작 전 브리핑</b>" if now.hour < 12 else f"🌙 <b>삼성전자 장 마감 후 브리핑</b>"
    final_msg = f"{title} ({now.strftime('%m/%d %H:%M')})\n\n{m_data}\n\n{n_data}"
    
    send_message(final_msg)
