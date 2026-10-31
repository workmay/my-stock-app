import datetime
from io import StringIO
import matplotlib
matplotlib.use('Agg')  # 確保雲端背景安全渲染
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import requests
import streamlit as st
import yfinance as yf

# -------------------------------------------------------------------------
# 1. 網頁頂部基礎外觀設定
# -------------------------------------------------------------------------
st.set_page_config(page_title="台指期貨現貨終極操盤儀表板 - 台新旗艦版", layout="centered")

st.title("📈 台指期貨現貨終極操盤儀表板")
st.caption("🚀 台新旗艦完全體：支援台指大盤即時氣象、全球多資產技術分析、留倉護航與台新 API 串接架構")

# ==============================================================================
# 🧠 二、個股操盤大腦判斷核心 (含詳細留倉過夜護航提示)
# ==============================================================================
def render_trading_guide(rsi, price, open_p, ma5, ma20, low_min, stop_loss_long, stop_loss_short):
    st.markdown("### 🔮 標的雙向操盤與【留倉過夜防護】指南：")
    
    # 狀態 1：買進做多訊號
    if rsi < 45 and price > open_p and price > ma5:
        st.success("🟩【 燈號：🚀 強烈適合買進做多 (LONG) 🚀 】")
        st.write("➡️ **操盤提示**：價格在低檔成功打底，今日首度收紅K且強勢站上5日攻擊線，多頭主力帶頭反擊，高勝率轉折買點出現！")
        st.write(f"⚠️ **多單風控防線**：進場做多後，多單精準停損價請死守在 **{stop_loss_long} 元**（跌破近兩日低點便認輸平倉）。")
        st.write("🛡️ **【留倉過夜建議】：可安心多單留倉**。底部防守點清晰，只要隔日開盤不跌破此防線，即可續抱過夜。")
        return

    # 狀態 2：超賣築底等待訊號
    if rsi < 30:
        st.warning("🟨【 燈號：雖然弱勢，但已進入超賣區，不可追空 】")
        st.write("➡️ **操盤提示**：短線跌幅已大（RSI過低），極易引發高槓桿軋空反彈！請勿在此盲目加空。")
        st.write("💡 **做多等待**：目前多頭尚未反擊（尚未收紅K站上5日線），空手者請靜下心等待止跌紅K出現再進場。")
        st.write("🛡️ **【留倉過夜建議】：不宜抱空單留倉**。超賣區隨時有跌深強彈風險，建議空手過夜或少量佈局短多。")
        return

    # 狀態 3：強烈適合放空訊號
    if price < ma20:
        st.error("🟥【 燈號：強烈適合放空 (SHORT) 🚨 】")
        st.write("➡️ **操盤提示**：價格已收破 20 日生命線，中期趨勢全面轉空，符合放空送分題標準！")
        st.write(f"⚠️ **空單風控防線**：空單回補停損點請死守在 **{stop_loss_short} 元**。")
        st.write("🛡️ **【留倉過夜建議】：可考慮空單留倉或順勢做空**。中空格局未破前可抱單過夜。")
        return

    # 狀態 4：常態橫盤震盪續抱
    st.success("🟩【 燈號：尚未符合放空標準、常態持倉續抱 】")
    st.write("➡️ **操盤提示**：價格穩守在 20 日生命線之上，多頭大戶籌碼未潰散。原本持有的多單可繼續留倉續抱。")
    st.write("🛡️ **【留倉過夜建議】：原多單可續抱留倉**。只要守住 20 日生命線，大可放心過夜。")

# ==============================================================================
# 📊 三、Matplotlib 國際通用操盤英文圖表渲染器 (100% 徹底消滅豆腐字)
# ==============================================================================
def draw_chart(df):
    st.markdown("#### 📈 均線攻防趨勢圖表 (Price / MA5 / MA20)")
    fig, ax = plt.subplots(figsize=(10, 4.5))
    
    ax.plot(df.index, df['Close'], label="Price", color="#38bdf8", linewidth=2)
    ax.plot(df.index, df['MA5'], label="MA5", color="#eab308", linestyle="--")
    ax.plot(df.index, df['MA20'], label="MA20", color="#ef4444", linestyle="--")
    
    fig.patch.set_facecolor('#1e293b')
    ax.set_facecolor('#0f172a')
    ax.title.set_color('#f8fafc')
    ax.tick_params(colors='#94a3b8', which='both')
    ax.grid(True, linestyle=':', alpha=0.3, color='#334155')
    
    ax.legend(loc="upper left", facecolor='#1e293b', edgecolor='#334155', labelcolor='#f8fafc')
    st.pyplot(fig)

# ==============================================================================
# 🚀 四、升級版：透過穩定 Yahoo Finance 抓取台股大盤指數與動態氣象指標
# ==============================================================================
def process_market_dashboard(current_date_str):
    st.markdown("### 🏛️ 一、台指大盤即時氣象與指數動態指標")
    st.caption(f"ℹ️ **資料來源**：Yahoo Finance 全球金融即時連線 (^TWII 台股加權指數) | **系統查詢時間**：{current_date_str}")
    
    twii_close, twii_change, twii_ma20 = 23000.0, 0.0, 23000.0
    try:
        twii = yf.Ticker("^TWII")
        df_twii = twii.history(period="2mo")
        if not df_twii.empty:
            df_twii['MA20'] = df_twii['Close'].rolling(window=20).mean()
            twii_close = float(df_twii['Close'].iloc[-1])
            twii_prev = float(df_twii['Close'].iloc[-2])
            twii_change = ((twii_close - twii_prev) / twii_prev) * 100
            twii_ma20 = float(df_twii['MA20'].iloc[-1])
    except:
        pass

    col1, col2, col3 = st.columns(3)
    col1.metric("台股加權指數", f"{twii_close:,.2f} 點", f"{twii_change:+.2f}%")
    col2.metric("大盤 20日生命線", f"{twii_ma20:,.2f} 點")
    
    # 根據真實大盤與月線距離判定市場氣象
    status_text = ""
    if twii_close > twii_ma20 and twii_change > 0:
        col3.metric("大盤短線多空燈號", "🟢 多頭穩健")
        st.success("🔥【 大盤氣象站：🚀 大盤指數站穩 20 日生命線上方 🚀 】\n\n💡 操盤策略：大盤結構偏多，個股拉回可尋求優質標的佈局，維持正常留倉。")
    elif twii_close < twii_ma20:
        col3.metric("大盤短線多空燈號", "🔴 空頭修正")
        st.error("🔥【 大盤氣象站：🚨 大盤指數已跌破 20 日生命線 🚨 】\n\n💡 操盤策略：盤勢轉趨弱勢修正，大盤空方掌控中！請務必嚴格執行個股停損，降低過夜留倉風險。")
    else:
        col3.metric("大盤短線多空燈號", "🟡 震盪互陳")
        st.info("🗒【 大盤氣象站：目前處於月線附近拉鋸震盪格局 】\n\n➡️ 操盤策略：多空未分勝負，建議放慢交易節奏，嚴格控管資金水位。")

# ==============================================================================
# 🗂️ 五、個股大腦資料安全撈取核心 (萬能轟炸流，支援黃金現貨與全球美股)
# ==============================================================================
def process_stock_dashboard(stock_number):
    tw_stock_dict = {
        "3481": "群創", "3260": "威剛", "2409": "友達", "2330": "台積電",
        "2317": "鴻海", "2303": "聯電", "3231": "緯創", "2603": "長榮",
        "2609": "陽明", "2615": "萬海", "2884": "玉山金", "7780": "大研生醫",
        "00631L": "元大台灣50正2", "0050": "元大台灣50",
        "AU9901": "元大實物黃金", "AU9902": "富邦實物黃金"
    }
    
    df, ticker = None, None
    test_ids = [f"{stock_number}.TW", f"{stock_number}.TWO", stock_number]
    
    for tid in test_ids:
        try:
            ticker_test = yf.Ticker(tid)
            df_test = ticker_test.history(period="3mo")
            if not df_test.empty:
                df, ticker = df_test, ticker_test
                break
        except:
            pass
            
    if df is None or df.empty:
        st.error(f"❌ 找不到該標的 【{stock_number}】 交易資料，請確認代號是否正確。")
        return

    company_name = tw_stock_dict.get(stock_number, "金融標的")
    if company_name == "金融標的":
        try: company_name = ticker.info.get('shortName', ticker.info.get('longName', '金融標的'))
        except: pass

    df['MA5'] = df['Close'].rolling(window=5).mean().bfill().ffill()
    df['MA20'] = df['Close'].rolling(window=20).mean().bfill().ffill()
    
    delta = df['Close'].diff()
    gain, loss = delta.clip(lower=0), -delta.clip(upper=0)
    df['RSI'] = 100 - (100 / (1 + (gain.rolling(window=14).mean().bfill() / loss.rolling(window=14).mean().bfill().replace(0, 1))))
    df['RSI'] =
