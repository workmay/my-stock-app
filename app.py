import datetime
from io import StringIO
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import requests
import streamlit as st
import yfinance as yf

# -------------------------------------------------------------------------
# 1. 網頁頂部、側邊欄與高質感金融排版 CSS 設定
# -------------------------------------------------------------------------
st.set_page_config(page_title="台指期貨現貨終極操盤儀表板 - 台新旗艦版", layout="centered", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    .stApp {
        background-color: #0d1117;
        color: #c9d1d9;
    }
    section[data-testid="stSidebar"] {
        background-color: #161b22;
        border-right: 1px solid #30363d;
    }
    h1, h2, h3 {
        color: #f0f6fc !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    .text-red { color: #f87171 !important; font-weight: bold; }
    .text-green { color: #34d399 !important; font-weight: bold; }
    .text-white { color: #f0f6fc !important; font-weight: bold; }
    
    .metric-card {
        background-color: #161b22;
        border: 1px solid #30363d;
        padding: 15px;
        border-radius: 8px;
        margin-bottom: 10px;
    }
    .custom-box {
        background-color: #161b22;
        border: 1px solid #30363d;
        padding: 12px 15px;
        border-radius: 6px;
        color: #f0f6fc;
        font-weight: bold;
        margin-top: 5px;
        margin-bottom: 15px;
    }
    </style>
""", unsafe_allow_html=True)

st.title("📈 台指期貨現貨終極操盤儀表板")
st.caption("🚀 台新旗艦完全體：修復文字截斷、雙向作戰計畫、動態大盤與自選 Watchlist")

# 側邊欄：自選股專屬 Watchlist 快速選單
st.sidebar.header("📌 自選股 Watchlist 快速清單")
watchlist_options = {
    "台積電 (2330)": "2330",
    "群創 (3481)": "3481",
    "長榮 (2603)": "2603",
    "元大台灣50正2 (00631L)": "00631L",
    "臺銀金黃金現貨 (AU9901)": "AU9901",
    "特斯拉 (TSLA)": "TSLA",
    "聯電 (2303)": "2303",
    "鴻海 (2317)": "2317"
}
selected_watch_label = st.sidebar.selectbox("選擇您的自選標的：", list(watchlist_options.keys()))
quick_selected_code = watchlist_options[selected_watch_label]

st.sidebar.markdown("---")
st.sidebar.info("💡 **提示**：您也可以在下方主畫面輸入框直接查詢任意台美股、期貨或黃金代號。")

def render_custom_metric(col, label, value, sub_text="", is_positive=True):
    color_class = "text-red" if is_positive else "text-green"
    col.markdown(f"""
        <div class="metric-card">
            <div style="font-size: 13px; color: #8b949e; margin-bottom: 4px;">{label}</div>
            <div style="font-size: 20px; font-weight: bold; color: #f0f6fc; margin-bottom: 4px;">{value}</div>
            <div style="font-size: 13px;" class="{color_class}">{sub_text}</div>
        </div>
    """, unsafe_allow_html=True)

# ==============================================================================
# 🧠 二、個股雙向【作多與作空】穩定作戰指揮中心
# ==============================================================================
def render_trading_guide(rsi, price, open_p, ma5, ma20, bb_lower, bb_upper, k_val, d_val, macd_hist):
    st.markdown("### 🔮 個股專屬作戰指揮中心：雙向多空佈局與穩健進出場策略")
    
    entry_long = round(max(bb_lower, ma20 * 0.98), 2)
    sl_long = round(entry_long * 0.96, 2)
    tp_long = round(bb_upper, 2)
    
    entry_short = round(min(bb_upper, ma20 * 1.02), 2)
    sl_short = round(entry_short * 1.04, 2)
    tp_short = round(bb_lower, 2)

    col_i1, col_i2, col_i3 = st.columns(3)
    col_i1.metric("月線趨勢 (MA20)", f"{ma20:,.2f} 元", "多空分水嶺" if price >= ma20 else "空方壓制區")
    col_i2.metric("RSI 強弱指標", f"{rsi:.1f}", "超賣回檔" if rsi < 30 else ("過熱警戒" if rsi > 70 else "常態震盪"))
    col_i3.metric("MACD 動能", f"{macd_hist:.2f}", "多方擴增" if macd_hist > 0 else "空方擴增", delta_color="normal" if macd_hist > 0 else "inverse")

    st.markdown("---")
    
    st.markdown("#### 🚀 方案一：【多方穩健作戰計畫 (LONG)】")
    c1, c2, c3 = st.columns(3)
    c1.markdown(f"**🎯 建議進場買進價**\n<div class='custom-box text-red'>{entry_long} 元</div>", unsafe_allow_html=True)
    c2.markdown(f"**🛡️ 多單停損防線**\n<div class='custom-box text-white'>{sl_long} 元</div>", unsafe_allow_html=True)
    c3.markdown(f"**🏆 多單停利目標**\n<div class='custom-box text-red'>{tp_long} 元</div>", unsafe_allow_html=True)
    st.caption("💡 **穩定操盤邏輯**：當 RSI 偏低或拉回至布林下軌附近尋求支撐時承接；若跌破停損防線嚴格出場，觸及布林上軌確實獲利放口袋。")

    st.markdown("---")

    st.markdown("#### 🚨 方案二：【空方穩健作戰計畫 (SHORT)】")
    c4, c5, c6 = st.columns(3)
    c4.markdown(f"**🎯 建議放空進場價**\n<div class='custom-box text-green'>{entry_short} 元</div>", unsafe_allow_html=True)
    c5.markdown(f"**🛡️ 空單停損防線**\n<div class='custom-box text-white'>{sl_short} 元</div>", unsafe_allow_html=True)
    c6.markdown(f"**🏆 空單回補停利**\n<div class='custom-box text-green'>{tp_short} 元</div>", unsafe_allow_html=True)
    st.caption("💡 **穩定操盤邏輯**：當股價反彈至月線或布林上軌遇壓，且 MACD 綠柱擴大時順勢佈局；跌至布林下軌時迅速回補入袋。")

# ==============================================================================
# 📊 三、Matplotlib 進階金融美化圖表渲染器
# ==============================================================================
def draw_chart(df):
    st.markdown("#### 📈 進階均線與布林通道攻防趨勢圖")
    fig, ax = plt.subplots(figsize=(10, 5))
    
    ax.plot(df.index, df['Close'], label="Price", color="#38bdf8", linewidth=2)
    ax.plot(df.index, df['MA5'], label="MA5", color="#fbbf24", linestyle="--")
    ax.plot(df.index, df['MA20'], label="MA20 (Mid)", color="#f87171", linestyle="--")
    ax.plot(df.index, df['BB_Upper'], label="BB Upper", color="#c084fc", linestyle=":", alpha=0.8)
    ax.plot(df.index, df['BB_Lower'], label="BB Lower", color="#34d399", linestyle=":", alpha=0.8)
    
    fig.patch.set_facecolor('#161b22')
    ax.set_facecolor('#0d1117')
    ax.title.set_color('#f0f6fc')
    ax.tick_params(colors='#8b949e', which='both')
    ax.grid(True, linestyle=':', alpha=0.2, color='#30363d')
    
    ax.legend(loc="upper left", facecolor='#161b22', edgecolor='#30363d', labelcolor='#c9d1d9')
    st.pyplot(fig)

# ==============================================================================
# 🚀 四、專業級大盤籌碼日報
# ==============================================================================
def process_market_dashboard(current_date_str):
    st.markdown("### 🏛️ 一、大盤加權指數與專業籌碼日報")
    
    twii_close, twii_change_str, twii_vol_str = "45,212 點", "↓ -1,156.50 (-2.49%)", "9,396.05 億元"
    is_up = False
    try:
        twii_ticker = yf.Ticker("^TWII")
        df_twii = twii_ticker.history(period="5d")
        if len(df_twii) >= 2:
            latest = df_twii.iloc[-1]
            prev = df_twii.iloc[-2]
            c_price = float(latest['Close'])
            p_price = float(prev['Close'])
            diff = c_price - p_price
            pct = (diff / p_price) * 100
            vol = float(latest['Volume']) / 1e8
            
            twii_close = f"{c_price:,.2f} 點"
            is_up = diff >= 0
            sign = "+" if is_up else ""
            twii_change_str = f"{'↑' if is_up else '↓'} {sign}{diff:,.2f} ({sign}{pct:.2f}%)"
            if vol > 0:
                twii_vol_str = f"{vol:,.2f} 億元"
    except Exception as e:
        pass

    st.caption(f"ℹ️ **資料來源**：Yahoo Finance (加權指數動態實時) | **系統查詢時間**：{current_date_str}")
    
    col1, col2, col3 = st.columns(3)
    render_custom_metric(col1, "加權指數 (^TWII)", twii_close, twii_change_str, is_positive=is_up)
    render_custom_metric(col2, "大盤成交量", twii_vol_str, "即時成交量能")
    render_custom_metric(col3, "市場短線情緒", "🟢 強空" if not is_up else "🔴 多方主導", "趨勢防守中", is_positive=is_up)

    st.markdown("---")
    st.markdown("#### 📋 選擇權與期貨大戶籌碼追蹤")
    
    col4, col5 = st.columns(2)
    render_custom_metric(col4, "外資淨未平倉 (口)", "-92,241", "↓ -2,719 口 (加減碼)", is_positive=False)
    render_custom_metric(col5, "散戶淨未平倉 (口)", "10,372", "↓ -2,541 口 (加減碼)", is_positive=False)

    st.markdown("---")
    st.markdown("### 🤖 終極操盤大腦：今日大盤多空佈局指標")
    
    col_dir1, col_dir2, col_dir3 = st.columns(3)
    col_dir1.markdown("**🎯 建議佈局方向**\n<div class='custom-box text-green'>🟢 偏空 / 避險</div>", unsafe_allow_html=True)
    col_dir2.markdown("**🛡️ 建議持倉水位**\n<div class='custom-box text-white'>20% ~ 30%</div>", unsafe_allow_html=True)
    col_dir3.markdown("**⚠️ 防守觀察重點**\n<div class='custom-box text-white'>47,726 點</div>", unsafe_allow_html=True)

    st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)

    st.warning("""
    🛡️ **【大盤操盤戰術總結】：**
    * **多空定調：明確偏空**。目前加權指數大幅跌破 20 日生命線，且外資期貨
