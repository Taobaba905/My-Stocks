import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title="北美34只精选股看板", layout="wide")

st.title("📊 北美多市场实时看板")
st.caption(f"最后更新: {datetime.now().strftime('%H:%M:%S')} | 配色方案：绿涨 / 红跌 / 零轴深灰")

# 侧边栏：配置中心
default_tickers = "AQN.TO, BCE.TO, CEMX.TO, COIN.NE, CRM.NE, CU.TO, ILLM.TO, LIF.NE, XSP.TO, VGRO.TO, UNH.NE, SHOP.TO, T.TO, MSTR.NE, NOWS.NE, AMD, AMZN, AVGO, COIN, COST, CRM, GOOG, LULU, META, MSFT, MSTR, NFLX, NOW, NVDA, PLTR, SHOP, SMCI, TSLA, UNH"
tickers_raw = st.sidebar.text_area("监控名单:", default_tickers, height=150)

if st.sidebar.button("🚀 刷新全量数据"):
    tickers = [t.strip().upper() for t in tickers_raw.split(",") if t.strip()]
    data_results = []
    
    with st.spinner('正在同步数据...'):
        for t in tickers:
            try:
                stock = yf.Ticker(t)
                fast = stock.fast_info
                hist = stock.history(period="5d")
                if hist.empty: continue
                
                # 计算涨跌
                current_p = hist['Close'].iloc[-1]
                prev_p = hist['Close'].iloc[-2]
                change = ((current_p - prev_p) / prev_p) * 100
                
                # 格式化成交量
                vol = fast['last_volume']
                vol_str = f"{vol/1e6:.2f}M" if vol >= 1e6 else f"{vol/1e3:.2f}K"

                data_results.append({
                    "代码": t,
                    "价格": round(current_p, 2),
                    "涨跌幅(%)": round(change, 2),
                    "PE": stock.info.get('forwardPE', 'N/A'),
                    "成交量": vol_str,
                    "raw_vol": vol
                })
            except: continue

    if data_results:
        df = pd.DataFrame(data_results).sort_values("涨跌幅(%)", ascending=False)

        # --- 1. 重新设计的渐变热力图 ---
        st.subheader("🔥 今日涨跌幅分布")
        
        # 构建自定义颜色渐变：红色(跌) -> 深灰(0) -> 绿色(涨)
        # 这种色标确保 0 附近是深灰色
        custom_color_scale = [
            [0.0, "rgb(150, 0, 0)"],    # 深红
            [0.4, "rgb(255, 100, 100)"], # 浅红
            [0.5, "rgb(60, 60, 60)"],    # 深灰 (中间点)
            [0.6, "rgb(100, 255, 100)"], # 浅绿
            [1.0, "rgb(0, 150, 0)"]     # 深绿
        ]

        fig = px.bar(
            df, x="代码", y="涨跌幅(%)", color="涨跌幅(%)",
            color_continuous_scale=custom_color_scale,
            range_color=[-4, 4], # 设定正负4%为颜色极限
            text_auto='.2f'
        )
        # 优化图表样式
        fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

        st.divider()

        # --- 2. 实时数据清单 ---
        st.subheader("📋 详细数据清单")
        
        # 定义表格配色函数
        def color_text(val):
            if isinstance(val, (int, float)):
                if val > 0.1: return 'color: #00FF00; font-weight: bold' # 亮绿
                if val < -0.1: return 'color: #FF4B4B; font-weight: bold' # 亮红
                return 'color: #808080' # 灰色
            return ''

        st.dataframe(
            df.style.applymap(color_text, subset=['涨跌幅(%)']),
            column_config={
                "涨跌幅(%)": st.column_config.NumberColumn(format="%.2f%%"),
                "价格": st.column_config.NumberColumn(format="$ %.2f"),
                "raw_vol": None
            },
            use_container_width=True,
            height=800
        )
    else:
        st.error("数据抓取失败，请检查网络。")
