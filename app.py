import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import pytz

st.set_page_config(page_title="北美精选股看板-跨日涨跌", layout="wide")

# --- 时区处理 ---
toronto_tz = pytz.timezone('America/Toronto')
now_toronto = datetime.now(toronto_tz)

st.title("📊 北美多市场行情看板")
st.caption("计算逻辑：选今天(最新-昨收)/昨收；选历史(当日收-前日收)/前日收")

# --- 侧边栏：配置中心 ---
st.sidebar.header("查询配置")

# 1. 日期选择
selected_date = st.sidebar.date_input("选择查询日期:", now_toronto.date())
is_today = selected_date == now_toronto.date()

# 2. 股票名单
default_tickers = "AQN.TO, BCE.TO, CEMX.TO, COIN.NE, CRM.NE, CU.TO, ILLM.TO, LIF.NE, XSP.TO, VGRO.TO, UNH.NE, SHOP.TO, T.TO, MSTR.NE, NOWS.NE, AMD, AMZN, AVGO, COIN, COST, CRM, GOOG, LULU, META, MSFT, MSTR, NFLX, NOW, NVDA, PLTR, SHOP, SMCI, TSLA, UNH"
tickers_raw = st.sidebar.text_area("监控名单:", default_tickers, height=150)

if st.sidebar.button("🚀 获取行情数据"):
    tickers = [t.strip().upper() for t in tickers_raw.split(",") if t.strip()]
    data_results = []
    
    with st.spinner('正在计算跨日涨跌幅...'):
        for t in tickers:
            try:
                stock = yf.Ticker(t)
                
                if is_today:
                    # --- 逻辑：(当前最新价 - 昨日收盘价) / 昨日收盘价 ---
                    f = stock.fast_info
                    curr_price = f['last_price']
                    prev_close = f['previous_close']
                else:
                    # --- 历史逻辑：(该日收盘 - 前日收盘) / 前日收盘 ---
                    # 获取该日期及之前的数据（多取几天以防遇到周末）
                    start_search = selected_date - timedelta(days=5)
                    end_search = selected_date + timedelta(days=1)
                    hist = stock.history(start=start_search, end=end_search)
                    
                    if len(hist) < 2:
                        continue
                        
                    # 最后一列是选定日，倒数第二列是前一个交易日
                    curr_price = hist['Close'].iloc[-1]
                    prev_close = hist['Close'].iloc[-2]

                # 计算跨日涨跌幅
                if prev_close and prev_close != 0:
                    change = ((curr_price - prev_close) / prev_close) * 100
                else:
                    change = 0.0
                
                # 货币识别
                is_cad = any(suffix in t for suffix in [".TO", ".V", ".NE"])
                currency = "加币" if is_cad else "美金"

                data_results.append({
                    "代码": t,
                    "最新价格": curr_price,
                    "昨日收盘": prev_close,
                    "显示价格": f"{curr_price:.2f} {currency}",
                    "跨日涨跌幅(%)": round(change, 2)
                })
            except:
                continue

    if data_results:
        df = pd.DataFrame(data_results).sort_values("跨日涨跌幅(%)", ascending=False)

        # --- 1. 热力柱状图 ---
        title_suffix = "今日实时跨日表现" if is_today else f"{selected_date} 历史跨日表现"
        st.subheader(f"🔥 {title_suffix}")
        
        fig = px.bar(
            df, x="代码", y="跨日涨跌幅(%)", color="跨日涨跌幅(%)",
            color_continuous_scale=[[0, "#FF0000"], [0.5, "#404040"], [1, "#00FF00"]],
            range_color=[-4, 4], 
            text_auto='.2f'
        )
        fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

        st.divider()

        # --- 2. 详细数据清单 (全部靠右) ---
        st.subheader("📋 详细行情清单")
        
        def style_color(val):
            if isinstance(val, (int, float)):
                if val > 0.05: return 'color: #00FF00; font-weight: bold'
                if val < -0.05: return 'color: #FF4B4B; font-weight: bold'
            return 'color: #888888'

        st.dataframe(
            df.style.applymap(style_color, subset=['跨日涨跌幅(%)']),
            column_config={
                "显示价格": st.column_config.TextColumn("当前/当日收盘", width="medium"),
                "昨日收盘": st.column_config.NumberColumn("前一收盘", format="%.2f"),
                "跨日涨跌幅(%)": st.column_config.NumberColumn("跨日涨跌幅", format="%.2f%%"),
                "最新价格": None # 隐藏
            },
            use_container_width=True,
            height=800,
            hide_index=True
        )

        # 强制 CSS：全部靠右对齐
        st.markdown("""
            <style>
            [data-testid="stDataFrame"] td { text-align: right !important; }
            [data-testid="stDataFrame"] th { text-align: right !important; }
            </style>
            """, unsafe_allow_html=True)
    else:
        st.error(f"未能抓取到 {selected_date} 的有效数据。")
