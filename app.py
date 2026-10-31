import streamlit as st
import yfinance as yf
import requests

# 1. 設定網頁標題與外觀
st.set_page_config(page_title="個股期貨狙擊儀表板", layout="centered")

st.title("📉 個股期貨空頭狙擊儀表板")
st.caption("全方位相容版：完美支援一般股票、ETF、槓桿/反向基金 (如 00631L) 100% 查詢")

# 2. 自由輸入文字框
stock_number = st.text_input("⌨️ 請輸入台股代號（個股、ETF 皆可，如：3481、3260、00631L）：", value="3481", max_chars=10)

if stock_number:
    # 統一轉成大寫並去除空白
    stock_number = stock_number.strip().upper()
    
    with st.spinner("⏳ 雲端後台正在跨庫連線下載並精算數據..."):
        try:
            df = None
            stock_id = ""
            
            # 💡 核心超級升級：【個股與 ETF 萬用自動分流偵測】
            # 建立多種可能的 Yahoo 代號排列組合進行轟炸測試，直到成功拿到資料為止
            test_ids = [
                f"{stock_number}.TW",   # 組合一：上市股票/上市ETF (例如 00631L.TW)
                f"{stock_number}.TWO"   # 組合二：上櫃股票/上櫃ETF
            ]
            
            # 如果使用者自己打了點（例如打 2330.TW），直接保留
            if "." in stock_number:
                test_ids = [stock_number]
                
            for tid in test_ids:
                ticker_test = yf.Ticker(tid)
                df_test = ticker_test.history(period="3mo")
                if not df_test.empty:
                    df = df_test
                    stock_id = tid
                    ticker = ticker_test
                    break
            
            # 判斷最後是否成功拿到 K 線數據
            if df is None or df.empty:
                st.error(f"❌ 找不到該標的 【{stock_number}】 交易資料，請確認代號是否正確。")
            else:
                # 💡 中文名稱抓取：優先直連台灣 Yahoo 奇摩股市 API 通道
                company_name = "台股標的"
                try:
                    q_url = f"https://yahoo.com{stock_number}"
                    res_q = requests.get(q_url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}, timeout=3)
                    if res_q.status_code == 200:
                        q_data = res_q.json()
                        hits = q_data.get('hits', {}).get('hits', [])
                        if hits:
                            source = hits[0].get('_source', {})
                            company_name = source.get('cryptoName', source.get('assetName', source.get('name', '台股標的')))
                except:
                    pass
                
                # 保底萬用備援機制
                if company_name == "台股標的" or not company_name:
                    try:
                        company_name = ticker.info.get('shortName', ticker.info.get('longName', '台股標的'))
                    except:
                        pass

                # 計算技術指標
                df['MA20'] = df['Close'].rolling(window=20).mean()
                delta = df['Close'].diff()
                gain = delta.clip(lower=0)
                loss = -delta.clip(upper=0)
                df['RSI'] = 100 - (100 / (1 + (gain.rolling(window=14).mean() / loss.rolling(window=14).mean())))
                
                today = df.iloc[-1]
                t_price = float(today['Close'])
                t_ma20 = float(today['MA20'])
                t_rsi = float(today['RSI'])
                
                # 期貨保證金計算 (注意：ETF期貨規格可能與一般個股期不同，此處維持標準一口2張股票價值作參考估算)
                margin = int(t_price * 2000 * 0.135)
                tick = 100 if t_price < 50 else (200 if t_price < 100 else 1000)
                stop_loss = round(t_ma20 * 1.01, 2)
                
                # 4. 漂亮呈現網頁畫面
                st.subheader(f"🏢 檢查標的：{stock_number} {company_name}")
                
                col1, col2, col3 = st.columns(3)
                col1.metric("最新收盤價", f"{t_price:.2f} 元")
                col2.metric("20日生命線", f"{t_ma20:.2f} 元")
                col3.metric("目前 RSI 值", f"{t_rsi:.2f}")
                
                col4, col5, col6 = st.columns(3)
                col4.metric("期貨估算保證金", f"$ {margin:,}")
                col5.metric("每跳一檔損益參考", f"$ {tick}")
                col6.metric("空單精準回補價", f"{stop_loss} 元")
                
                st.markdown("---")
                st.markdown("### 🔮 終極操盤行動指南：")
                
                # 5. 策略亮燈判定
                if t_rsi < 30:
                    st.warning("🟨【 燈號：雖然弱勢，但已進入超賣區，不可追空 】")
                    st.write("➡️ **操盤提示**：短線跌幅已大（RSI過低），極易引發高槓桿軋空反彈！請勿在此盲目加空。")
                elif t_price < t_ma20:
                    st.error(f"🟥【 燈號：強烈適合放空 (SHORT) 🚨 】")
                    st.write(f"➡️ **操盤提示**：價格已收破20日生命線，中期趨勢全面轉空，符合放空送分題標準！多單或空單回補防守點請死守在 {stop_loss} 元。")
                else:
                    st.success("🟩【 燈號：尚未符合放空標準、暫時觀望 】")
                    st.write("➡️ **操盤提示**：價格穩守在生命線之上，多頭大戶籌碼未潰散，此處放空容易被軋，請勿盲目摸頂放空！")
                    
        except Exception as e:
            st.error(f"數據加載失敗: {str(e)}")
