
import streamlit as st
import pandas as pd
import plotly.express as px

# Load data
df = pd.read_csv('user_data.csv', parse_dates=['signup_date', 'last_active_date'])

# Derived fields
df['signup_week'] = df['signup_date'].dt.to_period('W').apply(lambda r: r.start_time)
df['retained'] = (df['last_active_date'] - df['signup_date']).dt.days > 7

# Page setup
st.set_page_config(page_title="User Behavior Analytics", layout="wide")
st.title("📊 User Behavior Analytics Dashboard")

# Sidebar
st.sidebar.header("Filter")

# A/B Test Group Filter
selected_group = st.sidebar.selectbox("Select A/B Test Group", options=["All", "A", "B"])
if selected_group != "All":
    df = df[df['ab_group'] == selected_group]

# Date Range Filter
start_date, end_date = st.sidebar.date_input(
    "Signup Date Range",
    [df['signup_date'].min(), df['signup_date'].max()]
)
df = df[(df['signup_date'] >= pd.to_datetime(start_date)) & (df['signup_date'] <= pd.to_datetime(end_date))]

# Session Count Filter
min_sessions = st.sidebar.slider("Minimum Sessions", 1, int(df['session_count'].max()), 1)
df = df[df['session_count'] >= min_sessions]

# Retention Filter
only_retained = st.sidebar.checkbox("Only show retained users")
if only_retained:
    df = df[df['retained']]

# Summary metrics in columns
col1, col2, col3 = st.columns(3)
col1.metric("👥 Total Users", len(df))
col2.metric("📈 Avg. Sessions", f"{df['session_count'].mean():.2f}")
col3.metric("🔁 Retention Rate", f"{df['retained'].mean() * 100:.2f}%")

st.markdown("---")

# Weekly signup trend chart
st.subheader("📅 Weekly Signup Trend")
weekly_signups = df.groupby('signup_week').size().reset_index(name='signups')
fig = px.line(
    weekly_signups,
    x='signup_week',
    y='signups',
    markers=True,
    title="Weekly Signups Over Time",
    labels={'signup_week': 'Week', 'signups': 'Number of Signups'},
    template="plotly_white"
)
st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# Retention by A/B group chart with insights
if selected_group == "All":
    st.subheader("🔁 Retention Rate by A/B Group")
    retention_by_group = df.groupby('ab_group')['retained'].mean().reset_index()
    retention_by_group['retained'] = retention_by_group['retained'] * 100
    fig2 = px.bar(
        retention_by_group,
        x='ab_group',
        y='retained',
        color='ab_group',
        labels={'ab_group': 'Group', 'retained': 'Retention Rate (%)'},
        title="Retention Comparison Between A/B Groups",
        text=retention_by_group['retained'].round(2),
        template="plotly_white"
    )
    fig2.update_traces(textposition='outside')
    fig2.update_yaxes(range=[0, 100])
    st.plotly_chart(fig2, use_container_width=True)

    # Generate insight
    a_ret = retention_by_group[retention_by_group['ab_group'] == 'A']['retained'].values[0]
    b_ret = retention_by_group[retention_by_group['ab_group'] == 'B']['retained'].values[0]
    diff = round(a_ret - b_ret, 2)

    if diff > 0:
        st.success(f"✅ Group A has {diff}% higher retention than Group B. Feature A may be more effective.")
    elif diff < 0:
        st.warning(f"⚠️ Group B has {abs(diff)}% higher retention than Group A. Consider exploring why Feature B performs better.")
    else:
        st.info("ℹ️ Retention is equal across both groups.")

st.markdown("---")

# Data preview
st.subheader("📋 Raw Data Preview")
st.dataframe(df.round(2).head(10), use_container_width=True)
