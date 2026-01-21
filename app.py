import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import pytz

st.set_page_config(page_title="北美精选股监控", layout="wide")

# --- 【1. 时区处理】 ---
# 设多伦多时间为“最后更新时间”.
toronto_tz = pytz.timezone('America/Toronto')
now_toronto = datetime.now(toronto_tz)
time_str = now_toronto.strftime('%Y-%m-%d %H:%M:%S')

st.title("📊 北美多市场实时看板")
st.caption(f"最后更新时间 est: {time_str}")

# --- 【2. 侧边栏配置】 ---
st.sidebar.header("🔍 查询与排序配置")
# 日期选择
selected_date = st.sidebar.date_input("选择查询日期:", now_toronto.date())
is_today = selected_date == now_toronto.date()

# 默认股票
default_tickers = "AQN.TO, BCE.TO, CEMX.TO, COIN.NE, CRM.NE, CU.TO, ILLM.TO, LIF.NE, XSP.TO, VGRO.TO, UNH.NE, SHOP.TO, T.TO, MSTR.NE, NOWS.NE, AMD, AMZN, AVGO, COIN, COST, CRM, GOOG, LULU, META, MSFT, MSTR, NFLX, NOW, NVDA, PLTR, SHOP, SMCI, TSLA, UNH"
tickers_raw = st.sidebar.text_area("股票:", default_tickers, height=120)

# 多级排序设置
st.sidebar.subheader("🔢多级排序设置")
sort_col_1 = st.sidebar.selectbox("第一排序指标", ["涨跌幅", "货币", "成交量", "代码"], index=0)
sort_col_2 = st.sidebar.selectbox("第二排序指标", ["代码", "涨跌幅", "成交量", "货币"], index=0)
sort_order = st.sidebar.radio("排序方式", ["降序", "升序"], horizontal=True)
is_ascending = True if sort_order == "升序" else False

if st.sidebar.button("🚀 获取并排序数据"):
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
                     # 历史逻辑：获取指定日期的数据
                    hist = stock.history(start=selected_date - timedelta(days=5), end=selected_date + timedelta(days=1))
                    if len(hist) < 2: continue
                    curr_price = hist['Close'].iloc[-1]
                    prev_close = hist['Close'].iloc[-2]
                    vol = hist['Volume'].iloc[-1]                

                # --- 【3. 涨跌幅计算逻辑】 ---
                change = ((curr_price - prev_close) / prev_close * 100) if prev_close else 0
                currency = "加币" if any(s in t for s in [".TO", ".V", ".NE"]) else "美金"
                vol_str = f"{vol/1e6:.2f}M" if vol >= 1e6 else f"{vol/1e3:.2f}K"

                # --- 【核心新增：生成跳转链接】 ---
                # 构建 Yahoo Finance 的跳转 URL
                chart_url = f"https://finance.yahoo.com/quote/{t}"


                data_results.append({
                    "代码": t,
                    "跳转链接": chart_url,
                    "当前最新价/当日收盘价": round(curr_price, 3),
                    "货币": currency,
                    "涨跌幅": round(change, 2),
                    "成交量": vol,  # 这里存数值以便排序
                    "成交量(显)": vol_str
                })
            except: 
                continue

    if data_results:
        # --- 核心：执行多列排序 ---
        df = pd.DataFrame(data_results)
        df = df.sort_values(
            by=[sort_col_1, sort_col_2], 
            ascending=[is_ascending, is_ascending]
        )




        # --- 【4. 热力柱状图：零点金黄色】 ---
        st.subheader("🔥 市场表现分布")
        fig = px.bar(
            df, x="代码", y="涨跌幅", color="涨跌幅",
            color_continuous_scale=[
                [0, "#FF0000"],      # 下跌：红色
                [0.5, "#FFD700"],    # 零轴：金黄色
                [1, "#00FF00"]       # 上涨：绿色
            ],
            range_color=[-4, 4],     
            text_auto='.2f'
        )
        fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

        st.divider()



        # --- 【5. 数据表格 】 ---
        st.subheader(f"📋 详细行情 (点击代码可查看图表): {sort_col_1} > {sort_col_2} ({sort_order})")
        
        # 涨跌幅颜色函数
        def style_change(val):
            if isinstance(val, (int, float)):
                if val > 0.1: return 'color: #00FF00; font-weight: bold'
                if val < -0.1: return 'color: #FF4B4B; font-weight: bold'
                return 'color: #FFD700; font-weight: bold'
            return ''

        # 配置表格：简化 LinkColumn 配置以修复 TypeError
        st.dataframe(
            df.style.applymap(style_change, subset=['涨跌幅']),
            column_config={
                "跳转链接": st.column_config.LinkColumn(
                    "代码 (点击看图)",
                    help="点击跳转到 Yahoo Finance 查看实时图表",
                    # 我们直接让“跳转链接”这一列显示成股票代码的名字
                    display_text="https://finance\.yahoo\.com/quote/(.*)" 
                ),
                "当前最新价/当日收盘价": st.column_config.NumberColumn("价格", format="%.3f"),
                "货币": st.column_config.TextColumn("货币"),
                "涨跌幅": st.column_config.NumberColumn("涨跌幅 (%)", format="%.2f%%"),
                "成交量": st.column_config.TextColumn("成交量"),
                "代码": None, "成交量": None # 隐藏原始排序列
            },
            use_container_width=True,
            height=800,
            hide_index=True
        )

        # 强制右对齐 CSS
        st.markdown("""
            <style>
            [data-testid="stDataFrame"] td { text-align: right !important; }
            [data-testid="stDataFrame"] th { text-align: right !important; }
            </style>
            """, unsafe_allow_html=True)
    else:
        st.error("无法抓取数据，请重试。")
