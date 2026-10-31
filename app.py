
import streamlit as st
import yfinance as yf
import datetime

# 1. 設定網頁標題與外觀設定
st.set_page_config(page_title="個股期貨狙擊儀表板", layout="centered")

st.title("📉 個股期貨空頭狙擊儀表板")
st.caption("雲端連網實戰版：支援手機/電腦自由輸入，大戶籌碼與風控一鍵精算")

# 內建常用中文名稱對照表
tw_stock_dict = {
    "3481": "群創", "2409": "友達", "2330": "台積電", "2317": "鴻海",
    "2303": "聯電", "3231": "緯創", "2603": "長榮", "2609": "陽明"
}

# 2. 建立讓使用者「自由輸入」的網頁文字框
stock_number = st.text_input("⌨️ 請輸入台股個股代號：", value="3481", max_chars=4)

if stock_number:
    company_name = tw_stock_dict.get(stock_number, "台股個股")
    stock_id = f"{stock_number}.TW"
    
    with st.spinner("⏳ 雲端後台正在安全連線雅虎數據庫精算中..."):
        try:
            # 3. 雲端後台直接抓取真實數據，完全不透過瀏覽器，100% 不會被阻擋
            ticker = yf.Ticker(stock_id)
            df = ticker.history(period="3mo")
            
            if df.empty:
                st.error("❌ 找不到該股交易資料，請確認股號是否正確。")
            else:
                # 計算指標
                df['MA20'] = df['Close'].rolling(window=20).mean()
                delta = df['Close'].diff()
                gain = delta.clip(lower=0)
                loss = -delta.clip(upper=0)
                df['RSI'] = 100 - (100 / (1 + (gain.rolling(window=14).mean() / loss.rolling(window=14).mean())))
                
                today = df.iloc[-1]
                t_price = float(today['Close'])
                t_ma20 = float(today['MA20'])
                t_rsi = float(today['RSI'])
                
                margin = int(t_price * 2000 * 0.135)
                tick = 100 if t_price < 50 else (200 if t_price < 100 else 1000)
                stop_loss = round(t_ma20 * 1.01, 2)
                
                # 4. 漂亮地在網頁畫面上排版呈現
                st.subheader(f"🏢 檢查標的：{stock_number} {company_name}")
                
                # 第一排卡片：基礎數據
                col1, col2, col3 = st.columns(3)
                col1.metric("最新收盤價", f"{t_price:.2f} 元")
                col2.metric("20日生命線", f"{t_ma20:.2f} 元")
                col3.metric("目前 RSI 值", f"{t_rsi:.2f}")
                
                # 第二排卡片：期貨風控
                col4, col5, col6 = st.columns(3)
                col4.metric("期貨原始保證金", f"$ {margin:,}")
                col5.metric("每跳一檔損益", f"$ {tick}")
                col6.metric("空單精準回補價", f"{stop_loss} 元")
                
                st.markdown("---")
                st.markdown("### 🔮 終極操盤行動指南：")
                
                # 5. 策略亮燈燈號判定
                if t_rsi < 30:
                    st.warning(f"🟨【 燈號：雖然弱勢，但已進入超賣區，不可追空 】\n\n➡️ 操盤提示：短線跌幅已大（RSI過低），極易引發高槓桿期貨軋空反彈！請勿盲目加空。")
                elif t_price < t_ma20:
                    st.error(f"🟥【 燈號：強烈適合放空 (SHORT) 🚨 】\n\n➡️ 操盤提示：股價已收破20日生命線，中期趨勢全面轉空，符合放空送分題標準！空單防守點設在 {stop_loss} 元。")
                else:
                    st.success(f"🟩【 燈號：尚未符合放空標準、暫時觀望 】\n\n➡️ 操盤提示：股價穩守在生命線之上，多頭大戶籌碼未潰散，請勿盲目摸頂放空！")
                    
        except Exception as e:
            st.error(f"數據加載失敗: {str(e)}")
