import streamlit as st

 # --- Login and Logout Functions ---
 
def login():
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        try:
            cursor = st.session_state.cursor
            query = "SELECT * FROM users WHERE username = %s AND password = %s"
            cursor.execute(query, (username, password))
            user = cursor.fetchone()

            if user:
                st.session_state.logged_in = True
                st.session_state.username = user[1]
                st.session_state.role = user[6]
                st.success(f"Login successful! Welcome {user[3]}")
                st.rerun()
            else:
                st.error("Invalid username or password")
        except Exception as e:
            st.error(f"Login failed: {e}")

def logout():
    st.session_state.logged_in = False
    st.session_state.role = None
    if 'conn' in st.session_state:
        st.session_state.conn.close()
        del st.session_state.conn
        del st.session_state.cursor
    st.rerun()
