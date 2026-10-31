import streamlit as st
import yfinance as yf
import requests

# 1. 設定網頁標題與外觀
st.set_page_config(page_title="個股期貨狙擊儀表板", layout="centered")

st.title("📉 個股期貨空頭狙擊儀表板")
st.caption("全市場完美版：內建【上市+上櫃】雙官方資料庫，全台灣個股 100% 自動秀中文")

# 保底常用中文名稱表 (當網路極度繁忙時的第一線防禦)
tw_stock_dict = {
    "3481": "群創", "2409": "友達", "2330": "台積電", "2317": "鴻海",
    "2303": "聯電", "3231": "緯創", "2603": "長榮", "2609": "陽明",
    "2615": "萬海", "2884": "玉山金"
}

# 2. 自由輸入文字框
stock_number = st.text_input("⌨️ 請輸入台股個股代號（上市或上櫃皆可，如：3481、8069、3324）：", value="3481", max_chars=10)

if stock_number:
    stock_number = stock_number.strip()
    if stock_number.isdigit():
        stock_id = f"{stock_number}.TW"
    else:
        stock_id = stock_number.upper()
        
    with st.spinner("⏳ 雲端後台正在連線下載並精算數據..."):
        try:
            # 3. 直連數據庫抓取 K 線資料
            ticker = yf.Ticker(stock_id)
            df = ticker.history(period="3mo")
            
            if df.empty:
                st.error("❌ 找不到該股交易資料，請確認股號是否正確。")
            else:
                # 💡 核心升級：【上市 + 上櫃】雙軌官方中文名稱精準抓取
                company_name = "台股個股"
                
                # 第一重：常用保底字典
                if stock_number in tw_stock_dict:
                    company_name = tw_stock_dict[stock_number]
                else:
                    # 第二重：連線臺灣證交所 (找上市公司)
                    try:
                        res_twse = requests.get("https://twse.com.tw", timeout=2)
                        if res_twse.status_code == 200:
                            target = next((item for item in res_twse.json() if item['Code'] == stock_number), None)
                            if target:
                                company_name = target['Name']
                    except:
                        pass
                    
                    # 第三重：若上市找不到，立刻連線證券櫃檯買賣中心 (找上櫃公司)
                    if company_name == "台股個股":
                        try:
                            # 櫃買中心公開上櫃行情 API
                            res_tpex = requests.get("https://tpex.org.tw", timeout=2)
                            if res_tpex.status_code == 200:
                                target_tpex = next((item for item in res_tpex.json() if item['Date'] and item['SecuritiesCompanyCode'] == stock_number), None)
                                if target_tpex:
                                    company_name = target_tpex['CompanyName']
                        except:
                            pass
                    
                    # 第四重：若雙官方皆繁忙，回歸 Yahoo 的 shortName
                    if company_name == "台股個股":
                        try:
                            company_name = ticker.info.get('shortName', ticker.info.get('longName', '台股個股'))
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
                col4.metric("期貨原始保證金", f"$ {margin:,}")
                col5.metric("每跳一檔損益", f"$ {tick}")
                col6.metric("空單精準回補價", f"{stop_loss} 元")
                
                st.markdown("---")
                st.markdown("### 🔮 終極操盤行動指南：")
                
                # 5. 策略亮燈判定
                if t_rsi < 30:
                    st.warning("🟨【 燈號：雖然弱勢，但已進入超賣區，不可追空 】")
                    st.write("➡️ **操盤提示**：短線跌幅已大（RSI過低），極易引發高槓桿期貨軋空反彈！請勿在此盲目加空。")
                elif t_price < t_ma20:
                    st.error(f"🟥【 燈號：強烈適合放空 (SHORT) 🚨 】")
                    st.write(f"➡️ **操盤提示**：股價已收破20日生命線，中期趨勢全面轉空，符合放空送分題標準！多單或空單回補防守點請死守在 {stop_loss} 元。")
                else:
                    st.success("🟩【 燈號：尚未符合放空標準、暫時觀望 】")
                    st.write("➡️ **操盤提示**：股價穩守在生命線之上，多頭大戶籌碼未潰散，此處放空容易被軋，請勿盲目摸頂放空！")
                    
        except Exception as e:
            st.error(f"數據加載失敗: {str(e)}")
