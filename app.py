import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import pytz

st.set_page_config(page_title="北美精选股监控", layout="wide")

# --- 时区处理：多伦多时间 ---
toronto_tz = pytz.timezone('America/Toronto')
now_toronto = datetime.now(toronto_tz)
time_str = now_toronto.strftime('%Y-%m-%d %H:%M:%S')

st.title("📊 北美多市场实时看板")
st.caption(f"最后更新 多伦多东部时间 est: {time_str}")

# --- 侧边栏配置 ---
st.sidebar.header("查询配置")
selected_date = st.sidebar.date_input("选择查询日期:", now_toronto.date())
is_today = selected_date == now_toronto.date()

default_tickers = "AQN.TO, BCE.TO, CEMX.TO, COIN.NE, CRM.NE, CU.TO, ILLM.TO, LIF.NE, XSP.TO, VGRO.TO, UNH.NE, SHOP.TO, T.TO, MSTR.NE, NOWS.NE, AMD, AMZN, AVGO, COIN, COST, CRM, GOOG, LULU, META, MSFT, MSTR, NFLX, NOW, NVDA, PLTR, SHOP, SMCI, TSLA, UNH"
tickers_raw = st.sidebar.text_area("监控名单:", default_tickers, height=150)

if st.sidebar.button("🚀 获取行情数据"):
    tickers = [t.strip().upper() for t in tickers_raw.split(",") if t.strip()]
    data_results = []
    
    with st.spinner('同步数据中...'):
        for t in tickers:
            try:
                stock = yf.Ticker(t)
                
                if is_today:
                    f = stock.fast_info
                    curr_price = f['last_price']
                    prev_close = f['previous_close']
                    vol = f['last_volume']
                else:
                    # 历史模式：取选定日及前5天确保跨越周末
                    hist = stock.history(start=selected_date - timedelta(days=5), end=selected_date + timedelta(days=1))
                    if len(hist) < 2: continue
                    curr_price = hist['Close'].iloc[-1]
                    prev_close = hist['Close'].iloc[-2]
                    vol = hist['Volume'].iloc[-1]

                # 计算涨跌幅
                change = ((curr_price - prev_close) / prev_close * 100) if prev_close else 0
                
                # 货币与成交量单位
                currency = "加币" if any(s in t for s in [".TO", ".V", ".NE"]) else "美金"
                vol_str = f"{vol/1e6:.2f}M" if vol >= 1e6 else f"{vol/1e3:.2f}K"

                data_results.append({
                    "代码": t,
                    "当前最新价/当日收盘价": round(curr_price, 4),
                    "货币": currency,
                    "涨跌幅": round(change, 3),
                    "成交量": vol_str
                })
            except:
                continue

    if data_results:
        df = pd.DataFrame(data_results).sort_values("涨跌幅", ascending=False)

        # --- 1. 热力柱状图 ---
        fig = px.bar(
            df, x="代码", y="涨跌幅", color="涨跌幅",
            color_continuous_scale=[[0, "#FF0000"], [0.5, "#404040"], [1, "#00FF00"]],
            range_color=[-4, 4], text_auto='.2f'
        )
        fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

        st.divider()

        # --- 2. 精简版数据清单 ---
        st.subheader("📋 实时详情清单")
        
        def style_change(val):
            if isinstance(val, (int, float)):
                if val > 0.05: return 'color: #00FF00; font-weight: bold'
                if val < -0.05: return 'color: #FF4B4B; font-weight: bold'
            return 'color: #888888'

        st.dataframe(
            df.style.applymap(style_change, subset=['涨跌幅']),
            column_config={
                "代码": st.column_config.TextColumn("代码"),
                "当前最新价/当日收盘价": st.column_config.NumberColumn("当前最新价/当日收盘价", format="%.4f"),
                "货币": st.column_config.TextColumn("货币"),
                "涨跌幅": st.column_config.NumberColumn("涨跌幅 (%)", format="%.2f%%"),
                "成交量": st.column_config.TextColumn("成交量"),
            },
            use_container_width=True,
            height=800,
            hide_index=True
        )

        # 强制 CSS：表头和单元格全部靠右
        st.markdown("""
            <style>
            [data-testid="stDataFrame"] td { text-align: right !important; }
            [data-testid="stDataFrame"] th { text-align: right !important; }
            </style>
            """, unsafe_allow_html=True)
    else:
        st.error("无数据返回。")
