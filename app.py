import datetime
from io import StringIO
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import requests
import streamlit as st
import yfinance as yf

# -------------------------------------------------------------------------
# 1. 網頁頂部基礎外觀設定
# -------------------------------------------------------------------------
st.set_page_config(page_title="台指期貨現貨終極操盤儀表板 - 台新專屬版", layout="centered")

st.title("📈 台指期貨現貨終極操盤儀表板")
st.caption("🚀 台新旗艦完全體：支援技術分析、留倉護航、黃金現貨與台新證券/期貨 API 串接架構")

# -------------------------------------------------------------------------
# 🧠 二、個股操盤大腦判斷核心 (含留倉過夜護航提示)
# -------------------------------------------------------------------------
def render_trading_guide(rsi, price, open_p, ma5, ma20, low_min, stop_loss_long, stop_loss_short):
    st.markdown("### 🔮 標的雙向操盤與【留倉過夜防護】指南：")
    
    if rsi < 45 and price > open_p and price > ma5:
        st.success("🟩【 燈號：🚀 強烈適合買進做多 (LONG) 🚀 】")
        st.write("➡️ **操盤提示**：價格在低檔成功打底，今日首度收紅K且強勢站上5日攻擊線，多頭主力帶頭反擊，高勝率轉折買點出現！")
        st.write(f"⚠️ **多單風控防線**：進場做多後，多單精準停損價請死守在 **{stop_loss_long} 元**。")
        st.write("🛡️ **【留倉過夜建議】：可安心多單留倉**。底部防守點清晰，只要隔日開盤不跌破此防線，即可續抱過夜。")
        return

    if rsi < 30:
        st.warning("🟨【 燈號：雖然弱勢，但已進入超賣區，不可追空 】")
        st.write("➡️ **操盤提示**：短線跌幅已大（RSI過低），極易引發高槓桿軋空反彈！請勿在此盲目加空。")
        st.write("💡 **做多等待**：目前多頭尚未反擊，請靜下心等待止跌紅K出現再進場。")
        st.write("🛡️ **【留倉過夜建議】：不宜抱空單留倉**。超賣區隨時有跌深強彈風險，建議空手過夜或少量佈局短多。")
        return

    if price < ma20:
        st.error("🟥【 燈號：強烈適合放空 (SHORT) 🚨 】")
        st.write("➡️ **操盤提示**：價格已收破 20 日生命線，中期趨勢全面轉空，符合放空送分題標準！")
        st.write(f"⚠️ **空單風控防線**：空單回補停損點請死守在 **{stop_loss_short} 元**。")
        st.write("🛡️ **【留倉過夜建議】：可考慮空單留倉或順勢做空**。中空格局未破前可抱單過夜。")
        return

    st.success("🟩【 燈號：尚未符合放空標準、常態持倉續抱 】")
    st.write("➡️ **操盤提示**：價格穩守在 20 日生命線之上，多頭大戶籌碼未
