import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title="34只股票监控助手", layout="wide")

st.title("🚀 我的股票实时监控面板")

# 侧边栏配置
st.sidebar.header("配置中心")
ticker_raw = st.sidebar.text_area(
    "股票代码列表 (已为你格式化):", 
    "AQN.TO, BCE.TO, CEMX.TO, COIN.NE, CRM.NE, CU.TO, ILLM.TO, LIF.NE, XSP.TO, VRGO.TO, UNH.NE, SHOP.TO, T.TO, MSTR.NE, NOWS.NE, AMD, AMZN, AVGO, COIN, COST, CRM, GOOG, LULU, META, MSFT, MSTR, NFLX, NOW, NVDA, PLTR, SHOP, SMCI, TSLA, UNH",
    height=200
)

# 按钮：强制开始抓取
run_button = st.sidebar.button("📊 点击获取/更新数据")

if run_button:
    tickers = [t.strip().upper() for t in ticker_raw.split(",") if t.strip()]
    st.write(f"正在尝试获取 {len(tickers)} 只股票的数据...")
    
    data_list = []
    placeholder = st.empty() # 创建一个动态显示区域
    
    # 逐个抓取，防止整体崩溃
    for t in tickers:
        with st.status(f"正在抓取 {t}...", expanded=False) as status:
            try:
                # 使用较短的 period 提高速度
                tick = yf.Ticker(t)
                # 获取最近两天的价格来计算涨跌
                hist = tick.history(period="2d")
                
                if not hist.empty and len(hist) >= 1:
                    current_price = hist['Close'].iloc[-1]
                    # 如果有前一天的价格就算涨幅，否则显示 0
                    if len(hist) > 1:
                        prev_close = hist['Close'].iloc[-2]
                        change = ((current_price - prev_close) / prev_close) * 100
                    else:
                        change = 0.0
                    
                    # 尝试获取 PE 和 成交量
                    info = tick.fast_info
                    
                    data_list.append({
                        "代码": t,
                        "价格": round(current_price, 2),
                        "涨跌幅(%)": round(change, 2),
                        "成交量": f"{info['last_volume']/1e6:.2f}M" if 'last_volume' in info else "N/A"
                    })
                    status.update(label=f"✅ {t} 完成", state="complete")
                else:
                    status.update(label=f"⚠️ {t} 无数据 (可能是闭市或代码错)", state="error")
            except Exception as e:
                status.update(label=f"❌ {t} 发生错误", state="error")
                continue

    # 抓取完成后显示结果
    if data_list:
        df = pd.DataFrame(data_list)
        
        # 1. 热力图
        st.subheader("🔥 今日涨跌幅分布")
        fig = px.bar(df, x="代码", y="涨跌幅(%)", color="涨跌幅(%)",
                     color_continuous_scale='RdYlGn', 
                     range_color=[-3, 3],
                     text_auto='.2f')
        st.plotly_chart(fig, use_container_width=True)
        
        # 2. 详细列表
        st.subheader("📋 实时数据清单")
        st.dataframe(df, use_container_width=True, height=800)
    else:
        st.error("所有股票都未能获取数据，请检查网络连接或稍后再试。")

else:
    st.info("👈 请点击左侧按钮开始获取实时行情")
