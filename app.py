import datetime
import streamlit as st
import yfinance as yf

# 1. 網頁頂部最基礎的外觀設定 (極速載入結構)
st.set_page_config(page_title="台指期貨現貨終極操盤儀表板", layout="centered")

st.title("📈 台指期貨現貨終極操盤儀表板")
st.caption("24小時萬能保底版：支援股票、ETF、黃金現貨與美股，假日全天候隨時可用")

# 💡 全局繁體中文強制對照字典 (100% 解決英文、亂碼、台股個股的問題)
tw_stock_dict = {
    "3481": "群創", "3260": "威剛", "2409": "友達", "2330": "台積電",
    "2317": "鴻海", "2303": "聯電", "3231": "緯創", "2603": "長榮",
    "2609": "陽明", "2615": "萬海", "2884": "玉山金", "7780": "大研生醫",
    "00631L": "元大台灣50正2", "0050": "元大台灣50",
    "AU9901": "元大實物黃金", "AU9902": "一銀金 (First Bank Gold)"
}

st.markdown("---")
st.markdown("### 🏢 一、個股期貨現貨狙擊偵測器")

# 🎯 2. 搜尋欄位核心：這個欄位現在是完全獨立的，雲端 3 秒內 100% 絕對會強制浮現！
stock_input = st.text_input("請輸入台股、美股或商品代號（如：3481、3260、AU9902、TSLA）：", value="3481")

if stock_input:
    stock_number = stock_input.strip().upper()
    company_name = tw_stock_dict.get(stock_number, "台股標的")
    
    # 💡 智慧分流測試陣列：假日適用，Yahoo 歷史資料庫 24 小時不打烊
    test_ids = [f"{stock_number}.TW", f"{stock_number}.TWO", f"{stock_number}.WO", stock_number]
    df = None
    
    for tid in test_ids:
        try:
            df_test = yf.Ticker(tid).history(period="3mo")
            if not df_test.empty:
                df = df_test
                break
        except:
            pass
            
    if df is None or df.empty:
        st.error(f"❌ 找不到該標的 【{stock_number}】 交易資料，請確認代號是否正確。")
    else:
        # 計算 5日與20日線
        df['MA5'] = df['Close'].rolling(window=5).mean().bfill().ffill()
        df['MA20'] = df['Close'].rolling(window=20).mean().bfill().ffill()
        
        # 計算 RSI
        delta = df['Close'].diff()
        gain, loss = delta.clip(lower=0), -delta.clip(upper=0)
        df['RSI'] = 100 - (100 / (1 + (gain.rolling(window=14).mean().bfill() / loss.rolling(window=14).mean().bfill().replace(0, 1))))
        df['RSI'] = df['RSI'].fillna(45.0)
        
        today_data = df.iloc[-1]
        t_price = float(today_data['Close'])
        t_open = float(today_data['Open'])
        t_ma5 = float(today_data['MA5'])
        t_ma20 = float(today_data['MA20'])
        t_rsi = float(today_data['RSI'])
        
        trade_date_str = df.index[-1].strftime("%Y/%m/%d")
        margin = int(t_price * 2000 * 0.135)
        tick = 100 if t_price < 50 else (200 if t_price < 100 else 1000)
        
        # 呈現彩色風控卡片
        st.subheader(f"🏢 檢查標的：{stock_number} {company_name}")
        st.caption(f"ℹ️ **資料來源**：Yahoo Finance 歷史資料庫 | 📊 **數據最新生效交易日**：{trade_date_str}")
        
        col1, col2, col3 = st.columns(3)
        col1.metric("最新收盤價", f"{t_price:.2f} 元")
        col2.metric("5日攻擊線", f"{t_ma5:.2f} 元")
        col3.metric("20日生命線", f"{t_ma20:.2f} 元")
        
        col4, col5, col6 = st.columns(3)
        col4.metric("期貨估算保證金", f"$ {margin:,}")
        col5.metric("每跳一檔損益參考", f"$ {tick}")
        col6.metric("目前 RSI 指標", f"{t_rsi:.2f}")
        
        # 💡 使用 Streamlit 內建原生高質感折線圖表 (100% 支援中文、流暢、絕對不產生豆腐字！)
        st.markdown("#### 📈 均線攻防趨勢圖表 (Price / MA5 / MA20)")
        chart_data = df[['Close', 'MA5', 'MA20']].copy()
        chart_data.columns = ['Price', 'MA5', 'MA20']
        st.line_chart(chart_data)
        
        # 操盤指南
        st.markdown("### 🔮 標的雙向操盤行動指南：")
        is_long = (t_rsi < 45) and (t_price > t_open) and (t_price > t_ma5)
        
        if is_long:
            local_min = min(float(today_data['Low']), float(df.iloc[-2]['Low']))
            stop_loss_long = round(local_min * 0.995, 2)
            st.success("🟩【 燈號：🚀 強烈適合買進做多 (LONG) 🚀 】\n\n➡️ **操盤提示**：股價在低檔成功打底，今日首度收紅K且強勢站上5日攻擊線，轉折買點出現！\n\n⚠️ **多單風控防線**：多單精準停損價請死守在 **" + str(stop_loss_long) + " 元**。")
        elif t_rsi < 30:
            st.warning("🟨【 燈號：雖然弱勢，但已進入超賣區，不可追空 】\n\n➡️ **操盤提示**：短線跌幅已大（RSI過低），極易引發高槓桿軋空反彈！請勿在此盲目加空。\n\n💡 **做多等待**：目前多頭尚未反擊，請靜下心等待止跌紅K出現再進場。")
        elif t_price < t_ma20:
            stop_loss_short = round(t_ma20 * 1.01, 2)
            st.error("🟥【 燈號：強烈適合放空 (SHORT) 🚨 】\n\n➡️ **操盤提示**：價格已收破 20 日生命線，中期趨勢全面轉空，符合放空送分題標準！\n\n⚠️ **空單回補防線**：空單回補停損點請死守在 **" + str(stop_loss_short) + " 元**。")
        else:
            st.success("🟩【 燈號：尚未符合放空標準、常態持倉續抱 】\n\n➡️ **操盤提示**：價格穩守在 20 日生命線之上，多頭大戶籌碼未潰散。原本持有的多單可繼續留倉續抱。")
