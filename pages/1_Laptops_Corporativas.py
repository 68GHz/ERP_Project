import streamlit as st
from shared_erp import render_product_page

st.set_page_config(
    page_title="Laptops Corporativas - ERP",
    layout="wide",
    initial_sidebar_state="expanded"
)

render_product_page("PROD-001")

