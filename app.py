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

    # 🔥 แก้ปัญหา format วันที่หลากหลาย
    df['date'] = pd.to_datetime(
        df['date'],
        format='mixed',
        errors='coerce'
    )

    df = df.dropna(subset=['date'])

    return df

df = load_data()

st.title("📊 Condensate Performance Dashboard")
# ==========================================
# 🎛️ PROFESSIONAL SIDEBAR FILTER
# ==========================================
st.sidebar.header("🔎 Filter Panel")

# Date Range
min_date = df['date'].min()
max_date = df['date'].max()

start_date, end_date = st.sidebar.date_input(
    "Select Date Range",
    [min_date, max_date],
    min_value=min_date,
    max_value=max_date
)

# Boiler Filter (ถ้ามีคอลัมน์ boiler)
if 'boiler' in df.columns:
    boiler_list = df['boiler'].unique().tolist()
    selected_boiler = st.sidebar.multiselect(
        "Select Boiler",
        boiler_list,
        default=boiler_list
    )
else:
    selected_boiler = None

# ==========================================
# APPLY FILTER
# ==========================================
filtered = df[
    (df['date'] >= pd.to_datetime(start_date)) &
    (df['date'] <= pd.to_datetime(end_date))
]

if selected_boiler:
    filtered = filtered[filtered['boiler'].isin(selected_boiler)]

# สร้าง status
filtered['status'] = filtered.apply(
    lambda x: "Below Target" if x['pct_condensate'] < x['target_pct'] else "On Target",
    axis=1
)

# Status Filter
status_list = filtered['status'].unique().tolist()
selected_status = st.sidebar.multiselect(
    "Select Status",
    status_list,
    default=status_list
)

filtered = filtered[filtered['status'].isin(selected_status)]

# แสดงจำนวนข้อมูล
st.sidebar.markdown("---")
st.sidebar.write(f"📌 Records Selected: {len(filtered)}")

# Reset Button
if st.sidebar.button("🔄 Reset Filter"):
    st.rerun()

# ถ้าไม่มีข้อมูล
if filtered.empty:
    st.warning("No data matching selected filters")
    st.stop()
# Date Filter
start_date = st.date_input("Start Date", df['date'].min())
end_date = st.date_input("End Date", df['date'].max())

# แปลงให้แน่ใจว่าเป็น datetime
df['date'] = pd.to_datetime(df['date'], errors='coerce')
df = df.dropna(subset=['date'])

# ✅ สร้าง filtered ตรงนี้
filtered = df[
    (df['date'] >= pd.to_datetime(start_date)) &
    (df['date'] <= pd.to_datetime(end_date))
]

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
# =========================
# 📥 Download Button
# =========================
csv = filtered.to_csv(index=False).encode('utf-8')

st.download_button(
    label="📥 Download Filtered Data",
    data=csv,
    file_name="condensate_filtered.csv",
    mime="text/csv",
)





