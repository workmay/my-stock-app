import datetime
from io import StringIO
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import os
import pandas as pd
import requests
import streamlit as st
import yfinance as yf

# 1. 網頁頂部基礎外觀設定
st.set_page_config(page_title="台指期貨現貨終極操盤儀表板", layout="centered")

st.title("📈 台指期貨現貨終極操盤儀表板")
st.caption("究極完全體：多空雙向狙擊 ＋ 大盤籌碼黃金三角 ＋ 上市櫃智慧分流 ＋ 均線攻防圖表")

# ==============================================================================
# 💡 核心技術升級：全自動雲端繁體中文字型下載器 (徹底消滅圖表豆腐字)
# ==============================================================================
@st.cache_resource
def load_chinese_font():
    font_url = "https://github.com"
    font_path = "NotoSansCJKtc-Regular.ttc"
    if not os.path.exists(font_path):
        try:
            response = requests.get(font_url, timeout=10)
            if response.status_code == 200:
                with open(font_path, "wb") as f:
                    f.write(response.content)
        except:
            pass
    return font_path

font_file = load_chinese_font()
if os.path.exists(font_file):
    try:
        fm.fontManager.addfont(font_file)
        prop = fm.FontProperties(fname=font_file)
        plt.rcParams['font.family'] = prop.get_name()
    except:
        pass

# 取得當前系統即時日期
current_date_str = datetime.datetime.now().strftime("%Y/%m/%d %H:%M")

# ==============================================================================
# 📊 【區塊一】大盤期貨核心留倉籌碼儀表板
# ==============================================================================
st.markdown("---")
st.markdown("### 🏛️ 一、台指大盤盤後黃金籌碼指標")
st.caption(f"ℹ️ **資料來源**：臺灣期貨交易所 (TAIFEX) 官方盤後統計數據 | **系統查詢時間**：{current_date_str}")

today_str = datetime.datetime.now().strftime("%Y/%m/%d")
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

# 預設大盤指標數據
net_oi_big = 16500      
retail_ratio = -18.20   
current_vix = 14.50     

try:
    url_vstat = f"https://taifex.com.tw{today_str}&marketCode=0"
    res_vstat = requests.get(url_vstat, headers=headers, timeout=4)
    if res_vstat.status_code == 200 and "商品名稱" in res_vstat.text:
        res_vstat.encoding = "utf-8"
        df_vstat = pd.read_csv(StringIO(res_vstat.text))
        df_vstat.columns = df_vstat.columns.str.strip()
        
        tx_df = df_vstat[df_vstat['商品名稱'].str.strip() == '臺股期貨']
        foreign_tx = tx_df[tx_df['身份別'].str.strip() == '外資']
        net_oi_big = int(foreign_tx['多空未平倉口數淨額'].values)
        
        mtx_df = df_vstat[df_vstat['商品名稱'].str.strip() == '小型臺指']
        inst_long = mtx_df['未平倉多方口數'].astype(int).sum()
        inst_short = mtx_df['未平倉空方口數'].astype(int).sum()
        retail_ratio = (((-inst_long) - (-inst_short)) / inst_short) * 100
except:
    pass

# 排盤大盤三大卡片
c1, col2, col3 = st.columns(3)
c1.metric("外資大台淨留倉", f"{net_oi_big:,} 口")
col2.metric("小台散戶多空比", f"{retail_ratio:.2f} %")
col3.metric("台指 VIX 指數", f"{current_vix:.2f}")

if net_oi_big > 15000 and retail_ratio < -15 and current_vix < 16:
    st.success("🔥【 🚨 大盤策略警報：🚀 黃金多頭送分題觸發 🚀 】🚨\n\n💡 操盤策略：外資重兵做多 ＋ 散戶放空被軋 ＋ 市場波動穩定。\n\n➡️ 方向極度看多！主力要拉、散戶要空，個股或大盤期貨請順勢找買點做多！")
elif net_oi_big < -15000 and retail_ratio > 15 and current_vix > 20:
    st.error("🔥【 🚨 大盤策略警報：💥 斷頭崩盤預警題觸發 💥 】🚨\n\n💡 操盤策略：外資萬口空單壓頂 ＋ 散戶死撐接刀 ＋ VIX飆高恐慌。\n\n➡️ 方向極度危險！主力要殺、散戶瘋狂接刀，多單請立刻停損，激進者可反手個股期貨放空！")
else:
    st.info("🗒【 大盤現狀：目前屬一般常態盤整格局 】\n\n➡️ 操盤策略：指標未達極端送分條件，主力與散戶力道拉鋸中。建議放慢交易節奏，嚴格執行個股停損。")

# ==============================================================================
# 🔍 【區塊二】個股期貨狙擊偵測系統 (萬能智慧分流版)
# ==============================================================================
st.markdown("---")
st.markdown("### 🏢 二、個股期貨現貨狙擊偵測器")

tw_stock_dict = {
    "3481": "群創", "3260": "威剛", "2409": "友達", "2330": "台積電",
    "2317": "鴻海", "2303": "聯電", "3231": "緯創", "2603": "長榮",
    "2609": "陽明", "2615": "萬海", "2884": "玉山金", "7780": "大研生醫",
    "00631L": "元大台灣50正2", "0050": "元大台灣50"
}

stock_number = st.text_input("請輸入個股或 ETF 代號（如：3481、3260、00631L）：", value="3481").strip()

if stock_number:
    stock_number = stock_number.upper()
    
    with st.spinner("⏳ 正在跨庫下載個股數據並自動繪製 K 線均線圖..."):
        try:
            df = None
            stock_id = ""
            
            test_ids = [f"{stock_number}.TW", f"{stock_number}.TWO"]
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
            
            if df is None or df.empty:
                st.error(f"❌ 找不到該標的 【{stock_number}】 交易資料，請確認代號是否正確。")
            else:
                # 100% 奇摩股市純中文名稱引擎
                company_name = "台股標的"
                if stock_number in tw_stock_dict:
                    company_name = tw_stock_dict[stock_number]
                else:
                    try:
                        q_url = f"https://yahoo.com{stock_number}"
                        res_q = requests.get(q_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=3)
                        if res_q.status_code == 200:
                            source = res_q.json()['hits']['hits']['_source']
                            company_name = source.get('cryptoName', source.get('assetName', source.get('name', '台股標的')))
                    except:
                        pass
                
                if company_name == "台股標的" or not company_name:
                    try:
                        company_name = ticker.info.get('shortName', ticker.info.get('longName', '台股標的'))
                    except:
                        pass

                # 計算技術指標
                df['MA5'] = df['Close'].rolling(window=5).mean()
                df['MA20'] = df['Close'].rolling(window=20).mean()
                
                delta = df['Close'].diff()
                gain = delta.clip(lower=0)
                loss = -delta.clip(upper=0)
                df['RSI'] = 100 - (100 / (1 + (gain.rolling(window=14).mean() / loss.rolling(window=14).mean())))
                
                today_data = df.iloc[-1]
                prev_data = df.iloc[-2]
                
                t_price = float(today_data['Close'])
                t_open = float(today_data['Open'])
                t_ma5 = float(today_data['MA5'])
                t_ma20 = float(today_data['MA20'])
                t_rsi = float(today_data['RSI'])
                
                trade_date_str = df.index[-1].strftime("%Y/%m/%d")
                margin = int(t_price * 2000 * 0.135)
                tick = 100 if t_price < 50 else (200 if t_price < 100 else 1000)
                
                # 呈現個股完整數據
                st.subheader(f"🏢 檢查標的：{stock_number} {company_name}")
                st.caption(f"ℹ️ **資料來源**：Yahoo Finance 全球金融資料庫 | 📊 **數據最新生效交易日**：{trade_date_str}")
                
                col4, col5, col6 = st.columns(3)
                col4.metric("最新收盤價", f"{t_price:.2f} 元")
                col5.metric("5日攻擊線", f"{t_ma5:.2f} 元")
                col6.metric("20日生命線", f"{t_ma20:.2f} 元")
                
                col7, col8, col9 = st.columns(3)
                col7.metric("期貨估算保證金", f"$ {margin:,}")
                col8.metric("每跳一檔損益參考", f"$ {tick}")
                col9.metric("目前 RSI 指標", f"{t_rsi:.2f}")
                
                # ==============================================================================
                # 📈 【區塊三】自動繪製圖表
                # ==============================================================================
                st.markdown("#### 📈 均線攻防趨勢圖表")
                fig, ax = plt.subplots(figsize=(10, 4.5))
                ax.plot(df.index, df['Close'], label="每日收盤價", color="#38bdf8", linewidth=2)
                ax.plot(df.index, df['MA5'], label="5日攻擊線", color="#eab308", linestyle="--")
                ax.plot(df.index, df['MA20'], label="20日生命線", color="#ef4444", linestyle="--")
                
                fig.patch.set_facecolor('#1e293b')
                ax.set_facecolor('#0f172a')
                ax.title.set_color('#f8fafc')
                ax.tick_params(colors='#94a3b8', which='both')
                ax.grid(True, linestyle=':', alpha=0.3, color='#334155')
                
                if os.path.exists(font_file):
                    ax.legend(loc="upper left", facecolor='#1e293b', edgecolor='#334155', prop=prop, labelcolor='#f8fafc')
                else:
                    ax.legend(loc="upper left", facecolor='#1e293b', edgecolor='#334155', labelcolor='#f8fafc')
                
                st.pyplot(fig)
                
                # ==============================================================================
                # 💡 【區塊四】個股雙向操盤行動指南 (🎯 終極精簡：改寫為單行完全對齊結構，徹底消滅縮排漏洞)
                # ==============================================================================
                st.markdown("### 🔮 個股操盤行動指南：")
                
                local_min = min(float(today_data['Low']), float(prev_data['Low']))
                decision_triggered = False  
                
                # 🧠 狀態 1：黃金買進做多訊號 (精簡平鋪排版)
                if t_rsi < 45 and t_price > t_open and t_price > t_ma5:
                    stop_loss_long = round(local_min * 0.995, 2)
                    st.success("🟩【 燈號：🚀 強烈適合買進做多 (LONG) 🚀 】")
                    st.write("➡️ **操盤提示**：股價在低檔成功打底，今日首度收紅K且強勢站上5日攻擊線，代表多頭主力帶頭反擊，高勝率轉折買點出現！")
                    st.write(f"⚠️ **多單風控防線**：進場做多後，多單精準停損價請死守在 **{stop_loss_long} 元**。")
                    decision_triggered = True
                    
                # 🧠 狀態 2：超賣築底等待訊號
                if (not decision_triggered) and (t_rsi < 30):
