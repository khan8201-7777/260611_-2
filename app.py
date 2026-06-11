import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta

st.set_page_config(page_title="주식 대시보드", page_icon="📈", layout="wide")

STOCKS = {
    "애플 (AAPL)": "AAPL",
    "마이크로소프트 (MSFT)": "MSFT",
    "엔비디아 (NVDA)": "NVDA",
    "구글 (GOOGL)": "GOOGL",
    "아마존 (AMZN)": "AMZN",
    "메타 (META)": "META",
    "테슬라 (TSLA)": "TSLA",
    "삼성전자 (005930.KS)": "005930.KS",
    "SK하이닉스 (000660.KS)": "000660.KS",
    "TSMC (TSM)": "TSM",
}

st.title("📈 글로벌 주식 대시보드")
st.markdown("10개 주요 종목의 실시간 주가 데이터를 시각화합니다.")

period_map = {"1주": "7d", "1개월": "1mo", "3개월": "3mo", "6개월": "6mo", "1년": "1y"}
selected_period_label = st.sidebar.selectbox("조회 기간", list(period_map.keys()), index=2)
period = period_map[selected_period_label]

@st.cache_data(ttl=300)
def fetch_all(period):
    tickers = list(STOCKS.values())
    data = {}
    info_list = []

    for name, ticker in STOCKS.items():
        try:
            t = yf.Ticker(ticker)
            hist = t.history(period=period)
            if hist.empty:
                continue
            data[ticker] = hist["Close"]

            latest = hist["Close"].iloc[-1]
            prev = hist["Close"].iloc[-2] if len(hist) > 1 else latest
            change_pct = (latest - prev) / prev * 100

            info_list.append({
                "종목명": name,
                "티커": ticker,
                "현재가": latest,
                "전일대비(%)": change_pct,
                "52주 최고": hist["Close"].max(),
                "52주 최저": hist["Close"].min(),
            })
        except Exception:
            continue

    df_info = pd.DataFrame(info_list)
    df_prices = pd.DataFrame(data)
    return df_info, df_prices

with st.spinner("주식 데이터를 불러오는 중..."):
    df_info, df_prices = fetch_all(period)

# 요약 카드
st.subheader("📊 종목 현황")
cols = st.columns(5)
for i, row in df_info.iterrows():
    col = cols[i % 5]
    delta_color = "🟢" if row["전일대비(%)"] >= 0 else "🔴"
    col.metric(
        label=row["종목명"].split("(")[0].strip(),
        value=f"{row['현재가']:,.2f}",
        delta=f"{row['전일대비(%)']:+.2f}%",
    )

st.divider()

# 주가 추이 차트
st.subheader("📉 주가 추이")
selected_names = st.multiselect(
    "종목 선택 (복수 선택 가능)",
    options=list(STOCKS.keys()),
    default=list(STOCKS.keys())[:5],
)
selected_tickers = [STOCKS[n] for n in selected_names if STOCKS[n] in df_prices.columns]

if selected_tickers:
    fig = go.Figure()
    for ticker in selected_tickers:
        name = [k for k, v in STOCKS.items() if v == ticker][0].split("(")[0].strip()
        # 정규화 (첫날 기준 100)
        series = df_prices[ticker].dropna()
        normalized = series / series.iloc[0] * 100
        fig.add_trace(go.Scatter(x=normalized.index, y=normalized, mode="lines", name=name))

    fig.update_layout(
        title=f"정규화 주가 추이 (시작일=100, {selected_period_label})",
        xaxis_title="날짜",
        yaxis_title="상대 주가",
        hovermode="x unified",
        height=450,
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )
    st.plotly_chart(fig, use_container_width=True)

st.divider()

col1, col2 = st.columns(2)

with col1:
    st.subheader("📋 상세 데이터")
    display_df = df_info.copy()
    display_df["현재가"] = display_df["현재가"].map("{:,.2f}".format)
    display_df["전일대비(%)"] = display_df["전일대비(%)"].map("{:+.2f}%".format)
    display_df["52주 최고"] = display_df["52주 최고"].map("{:,.2f}".format)
    display_df["52주 최저"] = display_df["52주 최저"].map("{:,.2f}".format)
    st.dataframe(display_df.drop(columns=["티커"]), use_container_width=True, hide_index=True)

with col2:
    st.subheader("📊 등락률 비교")
    if not df_info.empty:
        bar_df = df_info.sort_values("전일대비(%)")
        bar_df["색상"] = bar_df["전일대비(%)"].apply(lambda x: "상승" if x >= 0 else "하락")
        fig2 = px.bar(
            bar_df,
            x="전일대비(%)",
            y=bar_df["종목명"].str.split("(").str[0].str.strip(),
            color="색상",
            color_discrete_map={"상승": "#ef5350", "하락": "#1976d2"},
            orientation="h",
            text=bar_df["전일대비(%)"].map("{:+.2f}%".format),
        )
        fig2.update_layout(height=380, showlegend=False, yaxis_title="", xaxis_title="등락률 (%)")
        st.plotly_chart(fig2, use_container_width=True)

st.caption(f"데이터 출처: Yahoo Finance | 마지막 업데이트: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | 5분마다 자동 갱신")
