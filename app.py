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
st.caption("🚀 全新優化版：高穩定度、即時均線與智慧操盤燈號")

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
# 3. 資料抓取函式 (含快取機制，防止逾時與白畫面)
# -------------------------------------------------------------------------
@st.cache_data(ttl=600)
def fetch_stock_data(ticker):
    # 嘗試不同的後綴組合
    suffixes = [f"{ticker}.TW", f"{ticker}.TWO", f"{ticker}.WO", ticker]
    for s in suffixes:
        try:
            df = yf.Ticker(s).history(period="3mo")
            if df is not None and not df.empty:
                return df
        except Exception:
            continue
    return None

# -------------------------------------------------------------------------
# 4. 使用者介面：輸入區
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
    
    # 抓取資料
    with st.spinner(f"正在從 Yahoo Finance 載入 【{stock_number}】 歷史資料..."):
        df = fetch_stock_data(stock_number)
        
    if df is None or df.empty:
        st.error(f"❌ 找不到代號 【{stock_number}】 的交易資料，請確認代號是否正確。")
    else:
        # 計算技術指標 (MA5, MA20, RSI)
        df['MA5'] = df['Close'].rolling(window=5).mean().bfill().ffill()
        df['MA20'] = df['Close'].rolling(window=20).mean().bfill().ffill()
        
        delta = df['Close'].diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        rs = gain.rolling(window=14).mean() / loss.rolling(window=14).mean().replace(0, 1)
        df['RSI'] = 100 - (100 / (1 + rs))
        df['RSI'] = df['RSI'].fillna(45.0)
        
        # 取得最新一筆交易日數據
        latest = df.iloc[-1]
        t_price = float(latest['Close'])
        t_open = float(latest['Open'])
        t_ma5 = float(latest['MA5'])
        t_ma20 = float(latest['MA20'])
        t_rsi = float(latest['RSI'])
        trade_date = df.index[-1].strftime("%Y/%m/%d")
        
        # 風控與期貨參數估算
        margin = int(t_price * 2000 * 0.135)
        tick_size = 100 if t_price < 50 else (200 if t_price < 100 else 1000)
        
        # 顯示標的標頭
        st.subheader(f"📊 標的資訊：{stock_number} {company_name}")
        st.caption(f"📅 最新生效交易日：{trade_date} | 🔌 資料來源：Yahoo Finance")
        
        # 數據指標卡片排版
        m1, m2, m3 = st.columns(3)
        m1.metric("最新收盤價", f"{t_price:.2f} 元")
        m2.metric("5日攻擊線", f"{t_ma5:.2f} 元")
        m3.metric("20日生命線", f"{t_ma20:.2f} 元")
        
        m4, m5, m6 = st.columns(3)
        m4.metric("期貨估算保證金", f"$ {margin:,}")
        m5.metric("每跳一檔損益", f"$ {tick_size}")
        m6.metric("目前 RSI 指標", f"{t_rsi:.2f}")
        
        # 繪製趨勢圖
        st.markdown("#### 📉 均線攻防趨勢圖 (Price / MA5 / MA20)")
        chart_df = df[['Close', 'MA5', 'MA20']].copy()
        chart_df.columns = ['收盤價', '5日線', '20日線']
        st.line_chart(chart_df)
        
        # -------------------------------------------------------------------------
        # 5. 智慧操盤指南與燈號
        # -------------------------------------------------------------------------
        st.markdown("### 🔮 標的雙向操盤行動指南：")
        
        is_long = (t_rsi < 45) and (t_price > t_open) and (t_price > t_ma5)
        
        if is_long:
            local_min = min(float(latest['Low']), float(df.iloc[-2]['Low']))
            stop_loss = round(local_min * 0.995, 2)
            st.success(
                "🟩 **【燈號：🚀 強烈適合買進做多 (LONG)】**\n\n"
                "➡️ **操盤提示**：股價低檔打底，今日首度收紅K且強勢站上5日攻擊線，轉折買點浮現！\n\n"
                f"⚠️ **多單風控防線**：建議停損價設在 **{stop_loss} 元**。"
            )
        elif t_rsi < 30:
            st.warning(
                "🟨 **【燈號：短線超賣，切勿盲目追空】**\n\n"
                "➡️ **操盤提示**：短線跌幅已大、RSI偏低，容易引發反彈行情。\n\n"
                "💡 **操作建議**：靜待止跌紅K出現再考慮進場做多。"
            )
        elif t_price < t_ma20:
            stop_loss_short = round(t_ma20 * 1.01, 2)
            st.error(
                "🟥 **【燈號：強烈適合放空 (SHORT)】**\n\n"
                "➡️ **操盤提示**：價格跌破20日生命線，中期趨勢轉空。\n\n"
                f"⚠️ **空單風控防線**：建議回補停損價設在 **{stop_loss_short} 元**。"
            )
        else:
            st.success(
                "🟩 **【燈號：多頭排列，持倉續抱】**\n\n"
                "➡️ **操盤提示**：價格穩守在20日生命線之上，多方格局未破，現有部位可續抱。"
            )
