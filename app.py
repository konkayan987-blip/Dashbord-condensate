import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(layout="wide")

@st.cache_data(ttl=300)
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

    # ✅ สร้าง Status ตั้งแต่ตอนโหลดข้อมูลเลย เพื่อป้องกัน SettingWithCopyWarning
    if 'pct_condensate' in df.columns and 'target_pct' in df.columns:
        df['status'] = df.apply(
            lambda x: "Below Target" if x['pct_condensate'] < x['target_pct'] else "On Target",
            axis=1
        )
    return df

# โหลดข้อมูล
df = load_data()

st.title("📊 Condensate Performance Dashboard")

# ==========================================
# 🎛️ PROFESSIONAL SIDEBAR FILTER
# ==========================================
st.sidebar.header("🔎 Filter Panel")

# 1. Date Range Filter (แก้ปัญหา Error ตอนกดเลือกวัน)
min_date = df['date'].min()
max_date = df['date'].max()

date_selection = st.sidebar.date_input(
    "Select Date Range",
    value=(min_date, max_date), # ใช้ tuple สำหรับค่า default
    min_value=min_date,
    max_value=max_date
)

# ตรวจสอบว่าเลือกวันที่ครบ 2 วันหรือยัง (Start & End)
if len(date_selection) != 2:
    st.warning("⚠️ Please select both Start Date and End Date.")
    st.stop()
else:
    start_date, end_date = date_selection

# 2. Boiler Filter
if 'boiler' in df.columns:
    boiler_list = df['boiler'].unique().tolist()
    selected_boiler = st.sidebar.multiselect(
        "Select Boiler",
        boiler_list,
        default=boiler_list
    )
else:
    selected_boiler = None

# 3. Status Filter
if 'status' in df.columns:
    status_list = df['status'].unique().tolist()
    selected_status = st.sidebar.multiselect(
        "Select Status",
        status_list,
        default=status_list
    )
else:
    selected_status = None

# ==========================================
# 🔄 APPLY FILTERS (รวบยอดทำทีเดียว)
# ==========================================
filtered = df.copy()

# กรองวันที่
filtered = filtered[
    (filtered['date'] >= pd.to_datetime(start_date)) &
    (filtered['date'] <= pd.to_datetime(end_date))
]

# กรอง Boiler
if selected_boiler is not None:
    filtered = filtered[filtered['boiler'].isin(selected_boiler)]

# กรอง Status
if selected_status is not None:
    filtered = filtered[filtered['status'].isin(selected_status)]

# แสดงจำนวนข้อมูล
st.sidebar.markdown("---")
st.sidebar.write(f"📌 Records Selected: {len(filtered)}")

# ปุ่ม Refresh Data
if st.sidebar.button("🔁 Refresh Data"):
    st.cache_data.clear()
    st.rerun()

# ตรวจสอบว่ามีข้อมูลหลังการกรองหรือไม่
if filtered.empty:
    st.warning("⚠️ No data matching selected filters.")
    st.stop()

# ==========================================
# 📈 KPIs & CHARTS
# ==========================================
# คำนวณ KPI
avg_pct = filtered['pct_condensate'].mean()
avg_target = filtered['target_pct'].mean()

# KPI Box ด้านบน
k1, k2, k3 = st.columns(3)
k1.metric("Average % Condensate", f"{avg_pct*100:.1f}%")
k2.metric("Target %", f"{avg_target*100:.1f}%")
k3.metric("Difference", f"{(avg_pct-avg_target)*100:.1f}%")

col1, col2 = st.columns(2)

# 🟢 Gauge Chart
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
    fig = px.line(filtered,
                  x='date',
                  y='pct_condensate',
                  color='status',
                  color_discrete_map={
                      "Below Target": "red",
                      "On Target": "green"
                  },
                  markers=True) # เพิ่ม marker จุดบนเส้นให้อ่านง่ายขึ้น

    fig.update_layout(yaxis_tickformat=".0%")

    # เส้น Target
    fig.add_hline(y=avg_target,
                  line_dash="dash",
                  line_color="blue",
                  annotation_text="Average Target",
                  annotation_position="top right")

    st.plotly_chart(fig, use_container_width=True)

# ==========================================
# 📊 DATAFRAME & DOWNLOAD
# ==========================================
st.markdown("### 📋 Filtered Data")
st.dataframe(filtered, use_container_width=True)

# Download Button
csv = filtered.to_csv(index=False).encode('utf-8')
st.download_button(
    label="📥 Download Filtered Data (CSV)",
    data=csv,
    file_name="condensate_filtered.csv",
    mime="text/csv",
)
