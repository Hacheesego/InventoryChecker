import streamlit as st
from db import init_connection
from auth import login, logout
from dashboard import admin_dashboard

st.set_page_config(
    page_title="Inventory Management System",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Session State Initialization ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'role' not in st.session_state:
    st.session_state.role = None

# --- Initialize DB ---
init_connection()

# --- App Control Flow ---
if not st.session_state.logged_in:
    login()
else:
    with st.sidebar:
        st.success("Logged in")
        st.markdown(f"👤 **User:** `{st.session_state.username}`")
        st.markdown(f"🔐 **Role:** `{st.session_state.role.capitalize()}`")
        if st.button("Logout"):
            logout()
        st.markdown("---")
        st.caption("Inventory System • Final Year Project")

    if st.session_state.role != "admin":
        st.warning("Access denied: This section is restricted to Admins only.")
        st.stop()

    st.subheader("📋 Admin Dashboard")
    st.write("Welcome to the inventory system, Commander.")
    admin_dashboard()
