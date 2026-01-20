import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import datetime
import pytz  # 导入时区库

st.set_page_config(page_title="北美精选股看板", layout="wide")

# --- 时区处理：强制设为多伦多/美东时间 ---
toronto_tz = pytz.timezone('America/Toronto')
now_toronto = datetime.now(toronto_tz)
time_str = now_toronto.strftime('%Y-%m-%d %H:%M:%S')

st.title("📊 北美多市场实时看板")
st.caption(f"最后更新 (多伦多时间/EST): {time_str} | 绿涨 / 红跌 / 零轴深灰")

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
                
                # --- 货币识别 ---
                is_cad = any(suffix in t for suffix in [".TO", ".V", ".NE"])
                currency = "加币" if is_cad else "美金"
                
                # 成交量单位
                vol = f['last_volume']
                vol_str = f"{vol/1e6:.2f}M" if vol >= 1e6 else f"{vol/1e3:.2f}K"

                data_results.append({
                    "代码": t,
                    "价格": curr,
                    "货币": currency,
                    "显示价格": f"{curr:.2f} {currency}", # 合并显示
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

        # --- 2. 详细数据清单 (强制右对齐) ---
        st.subheader("📋 详细行情数据表")
        
        def style_change(val):
            if isinstance(val, (int, float)):
                if val > 0.1: return 'color: #00FF00; font-weight: bold'
                if val < -0.1: return 'color: #FF4B4B; font-weight: bold'
            return 'color: #888888'

        # 使用 column_config 确保数字和表头靠右
        st.dataframe(
            df.style.applymap(style_change, subset=['涨跌幅(%)']),
            column_config={
                "代码": st.column_config.TextColumn("代码"),
                "显示价格": st.column_config.TextColumn(
                    "最新价格", 
                    help="美股显示美金，加股显示加币",
                    width="medium",
                ),
                "涨跌幅(%)": st.column_config.NumberColumn(format="%.2f%%"),
                "PE": st.column_config.NumberColumn("PE (预测)"),
                "成交量": st.column_config.TextColumn("成交量"),
                "价格": None, # 隐藏原始数值列
                "货币": None  # 隐藏货币说明列
            },
            use_container_width=True,
            height=800,
            hide_index=True
        )
        
        # 强制 CSS 补丁：让所有单元格（包括表头）内容靠右
        st.markdown("""
            <style>
            /* 针对表格内容靠右 */
            [data-testid="stDataFrame"] td { text-align: right !important; }
            /* 针对表格表头靠右 */
            [data-testid="stDataFrame"] th { text-align: right !important; }
            </style>
            """, unsafe_allow_html=True)

    else:
        st.error("未发现数据，请检查网络。")
