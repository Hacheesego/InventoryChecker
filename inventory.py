import streamlit as st
import pandas as pd
import plotly.express as px

def manage_inventory(cursor, conn):
    # --- Search & Filter ---
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

    # --- Stock Warning ---
    st.markdown("---")
    low_stock = df[df['quantity'] < 15]
    if not low_stock.empty:
        st.warning("⚠️ Some items are low in stock!")
        st.dataframe(low_stock)

    # --- View & Edit ---
    st.markdown("---")
    st.subheader("📦 Inventory Table")

    if not df.empty:
        st.dataframe(df, use_container_width=True)

        for index, row in df.iterrows():
            with st.expander(f"Item: {row['item_code']} - {row['item_name']}"):
                st.write("Category:", row['category'])
                st.write("Quantity:", row['quantity'])

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
                        conn.commit()
                        st.success(f"Item {row['item_code']} updated successfully!")
                        st.rerun()
                    except Exception as err:
                        st.error(f"Update failed: {err}")

                delete_confirm = st.checkbox(f"Confirm delete {row['item_code']}", key=f"confirm_{index}")
                if delete_confirm:
                    if st.button(f"Delete {row['item_code']}", key=f"delete_{index}"):
                        try:
                            cursor.execute("DELETE FROM inventory WHERE item_code=%s", (row['item_code'],))
                            conn.commit()
                            st.success(f"Item {row['item_code']} deleted!")
                            st.rerun()
                        except Exception as err:
                            st.error(f"Delete failed: {err}")
    else:
        st.warning("No items found with these filters.")

    # --- Export to CSV ---
    st.markdown("---")
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Download Inventory as CSV", csv, "inventory.csv", "text/csv")

    # --- Import from CSV ---
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
                    conn.commit()
                    st.success("Inventory restored from CSV successfully!")
                    st.rerun()
                except Exception as err:
                    st.error(f"Import failed: {err}")

    # --- Add New Item ---
    st.markdown("---")
    st.subheader("➕ Add New Inventory Item")
    category_options = ["Electronics", "Furniture", "Stationery", "Other"]
    with st.form("add_item_form"):
        new_code = st.text_input("Item Code")
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
            conn.commit()
            st.success("Item added successfully!")
            st.rerun()
        except Exception as err:
            st.error(f"Failed to add item: {err}")
