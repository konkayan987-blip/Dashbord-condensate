import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(layout="wide")

@st.cache_data(ttl=3600)
def load_data():
    url = "https://docs.google.com/spreadsheets/d/1G_ikK60FZUgctnM7SLZ4Ss0p6demBrlCwIre27fXsco/export?format=csv&gid=181659687"
    df = pd.read_csv(url)
    df.columns = df.columns.str.strip()
    df['date'] = pd.to_datetime(df['date'], dayfirst=True)
    return df

df = load_data()

st.title("📊 Condensate Performance Dashboard")

# Date Filter
start_date = st.date_input("Start Date", df['date'].min())
end_date = st.date_input("End Date", df['date'].max())

filtered = df[(df['date'] >= pd.to_datetime(start_date)) &
              (df['date'] <= pd.to_datetime(end_date))].copy()

# Check empty
if filtered.empty:
    st.warning("No data in selected date range")
    st.stop()

# คำนวณ KPI ก่อน
avg_pct = filtered['pct_condensate'].mean()
avg_target = filtered['target_pct'].mean()

# KPI Box ด้านบน
k1, k2, k3 = st.columns(3)
k1.metric("Average % Condensate", f"{avg_pct*100:.1f}%")
k2.metric("Target %", f"{avg_target*100:.1f}%")
k3.metric("Difference", f"{(avg_pct-avg_target)*100:.1f}%")

col1, col2 = st.columns(2)

# 🟢 Gauge
with col1:
    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number",
        value=avg_pct*100,
        title={'text': "Average % Condensate"},
        gauge={
            'axis': {'range': [0, 100]},
            'bar': {'color': "green"},
            'steps': [
                {'range': [0, avg_target*100], 'color': "red"},
                {'range': [avg_target*100, 100], 'color': "lightgreen"}
            ]
        }
    ))
    st.plotly_chart(fig_gauge, use_container_width=True)

# 🔴 Trend Graph
with col2:
    filtered['status'] = filtered.apply(
        lambda x: "Below Target" if x['pct_condensate'] < x['target_pct'] else "On Target",
        axis=1
    )

    fig = px.line(filtered,
                  x='date',
                  y='pct_condensate',
                  color='status',
                  color_discrete_map={
                      "Below Target": "red",
                      "On Target": "green"
                  })

    fig.update_layout(yaxis_tickformat=".0%")

    # เส้น Target
    fig.add_hline(y=avg_target,
                  line_dash="dash",
                  line_color="blue",
                  annotation_text="Target",
                  annotation_position="top right")

    st.plotly_chart(fig, use_container_width=True)

st.dataframe(filtered)
