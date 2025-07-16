import streamlit as st
import mysql.connector

def init_connection():
    if 'conn' not in st.session_state:
        try:
            conn = mysql.connector.connect(
                host="localhost",
                user="InventoryAdmin",
                password="SyahirDB20_02",
                database="hachidb"
            )
            st.session_state.conn = conn
            st.session_state.cursor = conn.cursor()
        except mysql.connector.Error as err:
            st.error(f"Database connection failed: {err}")
            st.stop()
