"""ShamIn — Streamlit Dashboard."""
import streamlit as st

st.set_page_config(
    page_title="ShamIn — SYP/USD Forecaster",
    page_icon="📊",
    layout="wide",
)

st.title("📊 ShamIn — SYP/USD Exchange Rate Forecaster")
st.markdown("نظام ذكي لتوقع سعر صرف الليرة السورية مقابل الدولار الأمريكي")

st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Predictions", "Events", "Performance", "Alerts"])

if page == "Predictions":
    st.header("Exchange Rate Predictions")
    st.info("Prediction dashboard will be available after model training (Phase 5+)")

elif page == "Events":
    st.header("Classified Events")
    st.info("Events timeline will be available after event classification (Phase 2)")

elif page == "Performance":
    st.header("Model Performance")
    st.info("Performance metrics will be available after model evaluation (Phase 6)")

elif page == "Alerts":
    st.header("Alert Rules")
    st.info("Alert configuration will be available after monitoring setup (Phase 9)")
