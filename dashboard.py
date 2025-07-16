import streamlit as st
import pandas as pd
import plotly.express as px
from fpdf import FPDF

def admin_dashboard():
    cursor = st.session_state.cursor

    # --- Category Charts ---
    cursor.execute("SELECT category, COUNT(*) FROM inventory GROUP BY category")
    category_data = cursor.fetchall()
    df_category = pd.DataFrame(category_data, columns=["Category", "Count"])

    col1, col2 = st.columns(2)
    with col1:
        st.bar_chart(df_category.set_index("Category"))
    with col2:
        pie_fig = px.pie(df_category, names="Category", values="Count", title="Inventory Distribution")
        st.plotly_chart(pie_fig, use_container_width=True)

    # --- Inventory Table with Search/Filter ---
    st.markdown("---")
    st.subheader("🔍 Search & Filter Inventory")
    search_term = st.text_input("Search by Item Code or Name")
    cursor.execute("SELECT DISTINCT category FROM inventory")
    categories = [row[0] for row in cursor.fetchall()]
    categories.insert(0, "All")
    selected_category = st.selectbox("Filter by Category", categories)

    query = "SELECT * FROM inventory"
    conditions = []
    if search_term:
        conditions.append(f"(item_code LIKE '%{search_term}%' OR item_name LIKE '%{search_term}%')")
    if selected_category != "All":
        conditions.append(f"category = '{selected_category}'")
    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    cursor.execute(query)
    results = cursor.fetchall()
    df = pd.DataFrame(results, columns=['item_code', 'item_name', 'category', 'quantity'])

    # --- View Inventory ---
    st.markdown("---")
    st.subheader("📦 Inventory Table")

    if not df.empty:
        st.dataframe(df, use_container_width=True)

    for index, row in df.iterrows():
        with st.expander(f"Item: {row['item_code']} - {row['item_name']}"):
            st.write("Category:", row['category'])
            st.write("Quantity:", row['quantity'])

            # --- Update Form ---
            with st.form(f"update_form_{index}"):
                new_name = st.text_input("Update Name", value=row['item_name'], key=f"name_{index}")
                new_category = st.text_input("Update Category", value=row['category'], key=f"cat_{index}")
                new_quantity = st.number_input("Update Quantity", value=row['quantity'], min_value=0, step=1, key=f"qty_{index}")
                update_submit = st.form_submit_button("Update")

                if update_submit:
                    try:
                        cursor.execute(
                            "UPDATE inventory SET item_name=%s, category=%s, quantity=%s WHERE item_code=%s",
                            (new_name, new_category, new_quantity, row['item_code'])
                        )
                        st.session_state.conn.commit()
                        st.success(f"Item {row['item_code']} updated successfully!")
                        st.rerun()
                    except Exception as err:
                        st.error(f"Update failed: {err}")

            # --- Delete Form ---
            with st.form(f"delete_form_{index}"):
                st.markdown("#### ⚠️ Delete Item")
                delete_confirm = st.checkbox(f"Confirm delete {row['item_code']}", key=f"confirm_{index}")
                delete_submit = st.form_submit_button("Delete", type="primary")

                if delete_confirm and delete_submit:
                    try:
                        cursor.execute(
                            "INSERT INTO inventory_history (item_code, item_name, category, quantity, action, action_time) VALUES (%s, %s, %s, %s, %s, NOW())",
                            (row['item_code'], row['item_name'], row['category'], row['quantity'], "DELETE")
                        )
                        cursor.execute("DELETE FROM inventory WHERE item_code=%s", (row['item_code'],))
                        st.session_state.conn.commit()
                        st.success(f"Item {row['item_code']} deleted successfully!")
                        st.rerun()
                    except Exception as err:
                        st.error(f"Delete failed: {err}")

    # --- Add New Item ---
    st.markdown("---")
    st.subheader("➕ Add New Inventory Item")
    category_options = ["Electronics", "Furniture", "Consumable", "Other"]
    with st.form("add_item_form"):
        cursor.execute("SELECT item_code FROM inventory ORDER BY item_code DESC LIMIT 1")
        last_code = cursor.fetchone()
        if last_code:
            num = int(last_code[0][1:]) + 1
            new_code = f"A{num:03d}"
        else:
            new_code = "A001"

        st.text_input("Item Code", value=new_code, disabled=True)
        new_name = st.text_input("Item Name")
        new_category = st.selectbox("Category", category_options)
        new_quantity = st.number_input("Quantity", min_value=0, step=1)
        add_submit = st.form_submit_button("Add Item")

        if add_submit:
            try:
                cursor.execute(
                    "INSERT INTO inventory (item_code, item_name, category, quantity) VALUES (%s, %s, %s, %s)",
                    (new_code, new_name, new_category, new_quantity)
                )
                st.session_state.conn.commit()
                st.success("Item added successfully!")
                st.rerun()
            except Exception as err:
                st.error(f"Failed to add item: {err}")

    # --- CSV Export ---
    st.markdown("---")
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Download Inventory as CSV", csv, "inventory.csv", "text/csv")

    # --- CSV Import ---
    st.markdown("---")
    st.subheader("📤 Restore Inventory from CSV File")
    uploaded_file = st.file_uploader("Upload CSV", type=["csv"])
    if uploaded_file is not None:
        df_upload = pd.read_csv(uploaded_file)
        if st.button("⚠️ Import CSV and Replace Inventory"):
            if st.checkbox("Confirm to overwrite existing data"):
                try:
                    cursor.execute("DELETE FROM inventory")
                    for _, row in df_upload.iterrows():
                        cursor.execute(
                            "INSERT INTO inventory (item_code, item_name, category, quantity) VALUES (%s, %s, %s, %s)",
                            (row['item_code'], row['item_name'], row['category'], row['quantity'])
                        )
                    st.session_state.conn.commit()
                    st.success("Inventory restored from CSV successfully!")
                    st.rerun()
                except Exception as err:
                    st.error(f"Import failed: {err}")

    # --- PDF Export ---
    st.markdown("---")
    st.subheader("📄 Export Inventory as PDF")
    if st.button("📥 Download Inventory as PDF"):
        try:
            class PDF(FPDF):
                def header(self):
                    self.set_font("Arial", "B", 12)
                    self.cell(0, 10, "Inventory Report", ln=1, align="C")

                def footer(self):
                    self.set_y(-15)
                    self.set_font("Arial", "I", 8)
                    self.cell(0, 10, f"Page {self.page_no()}", 0, 0, "C")

            pdf = PDF()
            pdf.add_page()
            pdf.set_font("Arial", size=10)

            pdf.set_fill_color(200, 220, 255)
            pdf.cell(40, 10, "Item Code", 1, 0, "C", True)
            pdf.cell(50, 10, "Name", 1, 0, "C", True)
            pdf.cell(40, 10, "Category", 1, 0, "C", True)
            pdf.cell(30, 10, "Quantity", 1, 1, "C", True)

            for _, row in df.iterrows():
                pdf.cell(40, 10, str(row['item_code']), 1)
                pdf.cell(50, 10, str(row['item_name']), 1)
                pdf.cell(40, 10, str(row['category']), 1)
                pdf.cell(30, 10, str(row['quantity']), 1, 1)

            pdf_output = pdf.output(dest='S').encode('latin-1')
            st.download_button("⬇️ Click to Download", data=pdf_output, file_name="inventory_report.pdf", mime="application/pdf")
        except Exception as e:
            st.error(f"PDF generation failed: {e}")

    # --- Inventory Logs ---
    st.markdown("---")
    st.subheader("📜 Inventory Update History")
    cursor.execute("SELECT * FROM inventory_logs ORDER BY timestamp DESC")
    log_data = cursor.fetchall()
    df_logs = pd.DataFrame(log_data, columns=[
        "Log ID", "Item Code", "Action", "Old Name", "New Name",
        "Old Category", "New Category", "Old Qty", "New Qty", "Timestamp", "User"
    ])
    st.dataframe(df_logs, use_container_width=True)

    # --- Inventory History ---
    st.markdown("---")
    st.subheader("🕘 Inventory History Log (Deletions Only)")
    try:
        cursor.execute("SELECT item_code, item_name, category, quantity, action, action_time FROM inventory_history ORDER BY action_time DESC")
        history_data = cursor.fetchall()
        if history_data:
            df_history = pd.DataFrame(history_data, columns=["Item Code", "Name", "Category", "Quantity", "Action", "Time"])
            st.dataframe(df_history, use_container_width=True)
        else:
            st.info("No history records found.")
    except Exception as err:
        st.error(f"Failed to fetch history: {err}")
        