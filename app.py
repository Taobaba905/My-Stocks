import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import datetime
import pytz

st.set_page_config(page_title="北美精选股看板", layout="wide")

# --- 时区处理：多伦多时间 ---
toronto_tz = pytz.timezone('America/Toronto')
now_toronto = datetime.now(toronto_tz)
time_str = now_toronto.strftime('%Y-%m-%d %H:%M:%S')

st.title("📊 北美多市场实时看板")
st.caption(f"最后更新 (多伦多时间/EST): {time_str} | 算法：(当前价 - 开盘价) / 开盘价")

# 侧边栏配置
default_tickers = "AQN.TO, BCE.TO, CEMX.TO, COIN.NE, CRM.NE, CU.TO, ILLM.TO, LIF.NE, XSP.TO, VGRO.TO, UNH.NE, SHOP.TO, T.TO, MSTR.NE, NOWS.NE, AMD, AMZN, AVGO, COIN, COST, CRM, GOOG, LULU, META, MSFT, MSTR, NFLX, NOW, NVDA, PLTR, SHOP, SMCI, TSLA, UNH"
tickers_raw = st.sidebar.text_area("监控名单:", default_tickers, height=150)

if st.sidebar.button("🚀 刷新全量数据"):
    tickers = [t.strip().upper() for t in tickers_raw.split(",") if t.strip()]
    data_results = []
    
    with st.spinner('正在同步多市场行情...'):
        for t in tickers:
            try:
                stock = yf.Ticker(t)
                f = stock.fast_info
                
                # 获取核心价格数据
                curr = f['last_price']
                open_p = f['open'] # 获取今日开盘价
                
                # --- 新逻辑：当前价减去今日开盘价 ---
                if open_p and open_p != 0:
                    change = ((curr - open_p) / open_p) * 100
                else:
                    change = 0.0
                
                # 货币识别
                is_cad = any(suffix in t for suffix in [".TO", ".V", ".NE"])
                currency = "加币" if is_cad else "美金"
                
                # 成交量单位
                vol = f['last_volume']
                vol_str = f"{vol/1e6:.2f}M" if vol >= 1e6 else f"{vol/1e3:.2f}K"

                data_results.append({
                    "代码": t,
                    "当前价格": curr,
                    "今日开盘": open_p,
                    "显示价格": f"{curr:.2f} {currency}",
                    "日内涨跌幅(%)": round(change, 2),
                    "PE": stock.info.get('forwardPE', 'N/A'),
                    "成交量": vol_str
                })
            except:
                continue

    if data_results:
        df = pd.DataFrame(data_results).sort_values("日内涨跌幅(%)", ascending=False)

        # --- 1. 绝对配色热力柱状图 ---
        st.subheader("🔥 日内波动分布 (相对今日开盘)")
        fig = px.bar(
            df, x="代码", y="日内涨跌幅(%)", color="日内涨跌幅(%)",
            color_continuous_scale=[[0, "#FF0000"], [0.5, "#404040"], [1, "#00FF00"]],
            range_color=[-3, 3], # 日内波动通常比跨日波动小，范围设为3%
            text_auto='.2f'
        )
        fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

        st.divider()

        # --- 2. 详细数据清单 (强制靠右) ---
        st.subheader("📋 详细行情数据表")
        
        def style_change(val):
            if isinstance(val, (int, float)):
                if val > 0.05: return 'color: #00FF00; font-weight: bold'
                if val < -0.05: return 'color: #FF4B4B; font-weight: bold'
            return 'color: #888888'

        st.dataframe(
            df.style.applymap(style_change, subset=['日内涨跌幅(%)']),
            column_config={
                "代码": st.column_config.TextColumn("代码"),
                "显示价格": st.column_config.TextColumn("最新价格", width="medium"),
                "今日开盘": st.column_config.NumberColumn("今日开盘", format="%.2f"),
                "日内涨跌幅(%)": st.column_config.NumberColumn("日内涨跌幅", format="%.2f%%"),
                "PE": st.column_config.NumberColumn("PE"),
                "成交量": st.column_config.TextColumn("成交量"),
                "当前价格": None # 隐藏
            },
            use_container_width=True,
            height=800,
            hide_index=True
        )
        
        # 强制 CSS：表头和内容全部靠右
        st.markdown("""
            <style>
            [data-testid="stDataFrame"] td { text-align: right !important; }
            [data-testid="stDataFrame"] th { text-align: right !important; }
            </style>
            """, unsafe_allow_html=True)

    else:
        st.error("未获取到数据，请重试。")
