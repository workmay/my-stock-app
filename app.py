import datetime
import streamlit as st
import yfinance as yf

# -------------------------------------------------------------------------
# 1. 頁面基本設定
# -------------------------------------------------------------------------
st.set_page_config(
    page_title="台指期貨現貨終極操盤儀表板",
    page_icon="📈",
    layout="centered"
)

st.title("📈 台指期貨現貨終極操盤儀表板")
st.caption("🚀 專業留倉護航版：結合大盤宏觀風向、個股狙擊與過夜留倉安全評估")

# -------------------------------------------------------------------------
# 2. 常用標的對照字典
# -------------------------------------------------------------------------
tw_stock_dict = {
    "3481": "群創", "3260": "威剛", "2409": "友達", "2330": "台積電",
    "2317": "鴻海", "2303": "聯電", "3231": "緯創", "2603": "長榮",
    "2609": "陽明", "2615": "萬海", "2884": "玉山金", "7780": "大研生醫",
    "00631L": "元大台灣50正2", "0050": "元大台灣50",
    "AU9901": "元大實物黃金", "AU9902": "一銀金"
}

# -------------------------------------------------------------------------
# 3. 資料抓取函式 (含快取機制)
# -------------------------------------------------------------------------
@st.cache_data(ttl=600)
def fetch_stock_data(ticker):
    suffixes = [f"{ticker}.TW", f"{ticker}.TWO", f"{ticker}.WO", ticker]
    for s in suffixes:
        try:
            df = yf.Ticker(s).history(period="3mo")
            if df is not None and not df.empty:
                return df
        except Exception:
            continue
    return None

def calculate_indicators(df):
    df['MA5'] = df['Close'].rolling(window=5).mean().bfill().ffill()
    df['MA20'] = df['Close'].rolling(window=20).mean().bfill().ffill()
    
    delta = df['Close'].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    rs = gain.rolling(window=14).mean() / loss.rolling(window=14).mean().replace(0, 1)
    df['RSI'] = 100 - (100 / (1 + rs))
    df['RSI'] = df['RSI'].fillna(45.0)
    return df

# -------------------------------------------------------------------------
# 4. 大盤宏觀風向球與留倉氣象站 (^TWII)
# -------------------------------------------------------------------------
st.markdown("### 🌍 零、台指大盤宏觀風向與留倉氣象站")

with st.spinner("正在分析大盤加權指數趨勢與留倉風險..."):
    df_market = fetch_stock_data("^TWII")

if df_market is None or df_market.empty:
    st.warning("⚠️ 目前無法取得台股加權指數 (^TWII) 即時數據。")
else:
    df_market = calculate_indicators(df_market)
    m_latest = df_market.iloc[-1]
    m_price = float(m_latest['Close'])
    m_open = float(m_latest['Open'])
    m_ma5 = float(m_latest['MA5'])
    m_ma20 = float(m_latest['MA20'])
    m_rsi = float(m_latest['RSI'])
    m_date = df_market.index[-1].strftime("%Y/%m/%d")

    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    col_m1.metric("加權指數收盤", f"{m_price:,.2f}")
    col_m2.metric("5日攻擊線", f"{m_ma5:,.2f}")
    col_m3.metric("20日生命線", f"{m_ma20:,.2f}")
    col_m4.metric("大盤 RSI", f"{m_rsi:.1f}")

    is_market_bullish = (m_price > m_ma20) and (m_ma5 >= m_ma20)
    is_market_bearish = (m_price < m_ma20) and (m_ma5 < m_ma20)

    if is_market_bullish:
        st.success(
            "🟢 **【大盤氣象：多頭主導 🚀 適合多單留倉過夜】**\n\n"
            f"➡️ **盤勢解讀**：加權指數穩守 20 日線（{m_ma20:,.2f}）之上。大盤結構安全，**持有強勢多單者可安心留倉續抱**，無須過度恐慌夜盤波動。"
        )
    elif is_market_bearish:
        st.error(
            "🔴 **【大盤氣象：空方壓境 🚨 多單不宜留倉，防範跳空下殺】**\n\n"
            f"➡️ **盤勢解讀**：加權指數已跌破 20 日線（{m_ma20:,.2f}）。盤勢脆弱，若持有多單切忌盲目留倉過夜，以免遭遇隔日利空跳空重傷。"
        )
    else:
        st.warning(
            "🟡 **【大盤氣象：多空膠著 💡 建議降低部位或現金入袋】**\n\n"
            "➡️ **盤勢解讀**：指數在均線糾結震盪，變數較多。為避免隔日國際盤突發利空襲擊，**強烈建議降低留倉部位**，短線入袋為安。"
        )

# -------------------------------------------------------------------------
# 5. 使用者介面：個股／商品查詢區
# -------------------------------------------------------------------------
st.markdown("---")
st.markdown("### 🏢 一、個股期貨現貨狙擊偵測器")

col_input1, col_input2 = st.columns([3, 1])
with col_input1:
    stock_input = st.text_input(
        "輸入台股、美股或商品代號：",
        value="3481",
        help="例如：3481 (群創), 2330 (台積電), TSLA (特斯拉)"
    )

if stock_input:
    stock_number = stock_input.strip().upper()
    company_name = tw_stock_dict.get(stock_number, "自定義標的")
    
    with st.spinner(f"正在載入 【{stock_number}】 數據與留倉分析..."):
        df = fetch_stock_data(stock_number)
        
    if df is None or df.empty:
        st.error(f"❌ 找不到代號 【{stock_number}】 的交易資料。")
    else:
        df = calculate_indicators(df)
        
        latest = df.iloc[-1]
        t_price = float(latest['Close'])
        t_open = float(latest['Open'])
        t_ma5 = float(latest['MA5'])
        t_ma20 = float(latest['MA20'])
        t_rsi = float(latest['RSI'])
        trade_date = df.index[-1].strftime("%Y/%m/%d")
        
        margin = int(t_price * 2000 * 0.135)
        tick_size = 100 if t_price < 50 else (200 if t_price < 100 else 1000)
        
        st.subheader(f"📊 標的資訊：{stock_number} {company_name}")
        st.caption(f"📅 最新生效交易日：{trade_date} | 🔌 資料來源：Yahoo Finance")
        
        m1, m2, m3 = st.columns(3)
        m1.metric("最新收盤價", f"{t_price:.2f} 元")
        m2.metric("5日攻擊線", f"{t_ma5:.2f} 元")
        m3.metric("20日生命線", f"{t_ma20:.2f} 元")
        
        m4, m5, m6 = st.columns(3)
        m4.metric("期貨估算保證金", f"$ {margin:,}")
        m5.metric("每跳一檔損益", f"$ {tick_size}")
        m6.metric("目前 RSI 指標", f"{t_rsi:.2f}")
        
        st.markdown("#### 📉 均線攻防趨勢圖 (Price / MA5 / MA20)")
        chart_df = df[['Close', 'MA5', 'MA20']].copy()
        chart_df.columns = ['收盤價', '5日線', '20日線']
        st.line_chart(chart_df)
        
        # -------------------------------------------------------------------------
        # 6. 智慧操盤行動指南與「留倉訊息評估」
        # -------------------------------------------------------------------------
        st.markdown("### 🔮 標的雙向操盤與【留倉過夜防護】指南：")
        
        is_long = (t_rsi < 45) and (t_price > t_open) and (t_price > t_ma5)
        
        if is_long:
            local_min = min(float(latest['Low']), float(df.iloc[-2]['Low']))
            stop_loss = round(local_min * 0.995, 2)
            st.success(
                "🟩 **【燈號：🚀 強烈適合買進做多 (LONG)】**\n\n"
                "➡️ **操盤提示**：股價低檔打底，今日首度收紅K且強勢站上5日攻擊線，轉折買點浮現！\n\n"
                f"🛡️ **【留倉過夜建議】：可安心多單留倉**。底部防守點清晰，停損價設在 **{stop_loss} 元**，只要隔日開盤不直接跌破此防線，即可續抱。"
            )
        elif t_rsi < 30:
            st.warning(
                "🟨 **【燈號：短線超賣，切勿盲目追空】**\n\n"
                "➡️ **操盤提示**：短線跌幅已大、RSI偏低，容易引發反彈行情。\n\n"
                "🛡️ **【留倉過夜建議】：不宜抱空單留倉**。超賣區隨時有跌深強彈或融券回補的軋空風險，空手觀望或少量佈局短多較安全。"
            )
        elif t_price < t_ma20:
            stop_loss_short = round(t_ma20 * 1.01, 2)
            st.error(
                "🟥 **【燈號：強烈適合放空 (SHORT)】**\n\n"
                "➡️ **操盤提示**：價格跌破20日生命線，中期趨勢轉空。\n\n"
                f"🛡️ **【留倉過夜建議】：可考慮空單留倉或順勢做空**。空單回補防線設在 **{stop_loss_short} 元**，中空格局未破前可抱單過夜。"
            )
        else:
            st.success(
                "🟩 **【燈號：多頭排列，持倉續抱】**\n\n"
                "➡️ **操盤提示**：價格穩守在20日生命線之上，多方格局未破。\n\n"
                "🛡️ **【留倉過夜建議】：原多單可續抱留倉**。只要守住 20 日生命線，大可放心過夜，讓獲利奔跑。"
            )
