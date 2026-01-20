import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title="北美精选股看板", layout="wide")

# 标题与更新时间
st.title("📊 北美多市场实时看板")
st.caption(f"最后更新: {datetime.now().strftime('%H:%M:%S')} | 绿涨 / 红跌 / 零轴深灰")

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
                curr = f['last_price']
                prev = f['previous_close']
                change = ((curr - prev) / prev) * 100
                
                # --- 后缀逻辑与货币识别 ---
                if any(suffix in t for suffix in [".TO", ".V", ".NE"]):
                    currency_label = "加币"
                else:
                    currency_label = "美金"
                
                # 统一成交量单位
                vol = f['last_volume']
                vol_str = f"{vol/1e6:.2f}M" if vol >= 1e6 else f"{vol/1e3:.2f}K"

                data_results.append({
                    "代码": t,
                    "价格": curr,
                    "货币": currency_label,
                    "涨跌幅(%)": round(change, 2),
                    "PE": stock.info.get('forwardPE', 'N/A'),
                    "成交量": vol_str
                })
            except:
                continue

    if data_results:
        df = pd.DataFrame(data_results).sort_values("涨跌幅(%)", ascending=False)

        # --- 1. 绝对配色热力柱状图 ---
        st.subheader("🔥 今日涨跌幅分布")
        fig = px.bar(
            df, x="代码", y="涨跌幅(%)", color="涨跌幅(%)",
            color_continuous_scale=[[0, "#FF0000"], [0.5, "#404040"], [1, "#00FF00"]],
            range_color=[-4, 4], 
            text_auto='.2f'
        )
        fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

        st.divider()

        # --- 2. 实时数据清单 (右对齐与货币标注) ---
        st.subheader("📋 详细行情数据表")
        
        # 定义动态颜色样式
        def style_change(val):
            if isinstance(val, (int, float)):
                if val > 0.1: return 'color: #00FF00; font-weight: bold'
                if val < -0.1: return 'color: #FF4B4B; font-weight: bold'
            return 'color: #888888'

        # 使用 column_config 实现右对齐和格式化
        st.dataframe(
            df.style.applymap(style_change, subset=['涨跌幅(%)']),
            column_config={
                "价格": st.column_config.NumberColumn(
                    "价格 (加币/美金)", 
                    help="根据后缀自动识别货币",
                    format="%.2f",
                    width="medium",
                ),
                "货币": st.column_config.TextColumn("货币", width="small"),
                "涨跌幅(%)": st.column_config.NumberColumn(format="%.2f%%"),
                "代码": st.column_config.TextColumn("代码"),
            },
            use_container_width=True,
            height=800,
            hide_index=True
        )
        
        # 针对 Streamlit 默认表格对齐的 CSS 补丁 (强制价格列内容靠右)
        st.markdown("""
            <style>
            /* 尝试定位表格中的数值列并强制靠右 */
            [data-testid="stTable"] td:nth-child(2), 
            [data-testid="stTable"] th:nth-child(2) {
                text-align: right !important;
            }
            </style>
            """, unsafe_allow_html=True)

    else:
        st.error("未发现数据，请检查网络。")
