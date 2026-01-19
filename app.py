import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title="北美34只精选股看板", layout="wide")

# 自定义 CSS 样式，让表格更漂亮
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stDataFrame { border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

st.title("📊 北美市场多维度实时看板")
st.caption(f"最后更新: {datetime.now().strftime('%H:%M:%S')} | 涵盖美股、TSX、CDR")

# 侧边栏：这里已经修正了 VGRO.TO
default_tickers = "AQN.TO, BCE.TO, CEMX.TO, COIN.NE, CRM.NE, CU.TO, ILLM.TO, LIF.NE, XSP.TO, VGRO.TO, UNH.NE, SHOP.TO, T.TO, MSTR.NE, NOWS.NE, AMD, AMZN, AVGO, COIN, COST, CRM, GOOG, LULU, META, MSFT, MSTR, NFLX, NOW, NVDA, PLTR, SHOP, SMCI, TSLA, UNH"
tickers_raw = st.sidebar.text_area("监控名单 (34只):", default_tickers, height=200)

if st.sidebar.button("🚀 刷新全量数据"):
    tickers = [t.strip().upper() for t in tickers_raw.split(",") if t.strip()]
    
    data_results = []
    
    with st.spinner('正在同步全球市场数据...'):
        for t in tickers:
            try:
                stock = yf.Ticker(t)
                # 获取价格和基础信息
                fast = stock.fast_info
                hist = stock.history(period="60d") # 获取历史用于计算MACD
                
                if hist.empty: continue
                
                # 1. 价格与涨跌幅
                current_p = hist['Close'].iloc[-1]
                prev_p = hist['Close'].iloc[-2]
                change = ((current_p - prev_p) / prev_p) * 100
                
                # 2. 计算简易 MACD
                exp1 = hist['Close'].ewm(span=12, adjust=False).mean()
                exp2 = hist['Close'].ewm(span=26, adjust=False).mean()
                macd_line = exp1 - exp2
                signal_line = macd_line.ewm(span=9, adjust=False).mean()
                macd_status = "↗️ 看多" if macd_line.iloc[-1] > signal_line.iloc[-1] else "↘️ 看空"
                
                # 3. 统一成交量单位
                vol = fast['last_volume']
                if vol >= 1e6:
                    vol_str = f"{vol/1e6:.2f} M"
                elif vol >= 1e3:
                    vol_str = f"{vol/1e3:.2f} K"
                else:
                    vol_str = str(vol)

                data_results.append({
                    "股票代码": t,
                    "当前价格": round(current_p, 2),
                    "今日涨跌": round(change, 2), # 用于绘制表格内柱状图
                    "MACD趋势": macd_status,
                    "市盈率(PE)": stock.info.get('forwardPE', 'N/A'),
                    "成交量": vol_str,
                    "原始成交量": vol # 隐藏列，用于排序
                })
            except:
                continue

    if data_results:
        df = pd.DataFrame(data_results)
        
        # 按照涨跌幅排序
        df = df.sort_values("今日涨跌", ascending=False)

        # 核心呈现：将分布图合并到清单中
        st.subheader("📋 实时数据综合清单 (含涨跌趋势)")
        
        st.dataframe(
            df,
            column_config={
                "今日涨跌": st.column_config.ProgressColumn(
                    "今日涨跌幅度 (%)",
                    help="当日价格变动百分比",
                    format="%.2f %%",
                    min_value=-5, # 涨跌幅显示范围
                    max_value=5,
                ),
                "当前价格": st.column_config.NumberColumn(format="$ %.2f"),
                "市盈率(PE)": st.column_config.NumberColumn(format="%.2f"),
                "原始成交量": None, # 隐藏这一列
            },
            use_container_width=True,
            height=1000
        )
        
        # 底部提供一个小型的热力统计
        st.divider()
        c1, c2 = st.columns(2)
        with c1:
            up_count = len(df[df['今日涨跌'] > 0])
            st.metric("今日上涨家数", f"{up_count} 只", delta=f"{up_count - 17}")
        with c2:
            st.write("💡 提示：点击表头可以按价格、PE或涨跌幅进行快速排序。")
            
    else:
        st.warning("未能获取到数据，请点击左侧按钮重试。")
else:
    st.info("👈 请在左侧确认 34 只股票代码后，点击【刷新全量数据】按钮。")
    
