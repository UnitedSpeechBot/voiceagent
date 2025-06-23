import streamlit as st
import psycopg2
import pandas as pd
from dotenv import load_dotenv
import os
from datetime import datetime, date

# Set your DATABASE_URL here
DATABASE_URL = "postgresql://unitedspeechbot_user:xJ6AKNv93uCTOFvbkiaX4dn9K3nJhz7r@dpg-d1cm4g3ipnbc739en0f0-a.virginia-postgres.render.com/unitedspeechbot"

st.set_page_config(page_title="United MileagePlus Account Admin", layout="wide")

def get_connection():
    try:
        return psycopg2.connect(DATABASE_URL)
    except Exception as e:
        st.error(f"Connection error: {e}")
        return None

def execute_sql(query, values=None):
    try:
        conn = get_connection()
        if not conn:
            return False
        cursor = conn.cursor()
        cursor.execute(query, values)
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Database error: {e}")
        return False

def get_columns():
    conn = get_connection()
    if not conn:
        return []
    cur = conn.cursor()
    cur.execute("""
        SELECT column_name, data_type, character_maximum_length, is_nullable, column_default 
        FROM information_schema.columns 
        WHERE table_name='accounts'
    """)
    columns = cur.fetchall()
    cur.close()
    conn.close()
    return columns

def fetch_data():
    conn = get_connection()
    if not conn:
        return pd.DataFrame()
    df = pd.read_sql("SELECT * FROM accounts ORDER BY mileage_plus_num DESC", conn)
    conn.close()
    return df

def generate_mileage_plus_num():
    import random
    return f"{random.randint(100000, 999999)}"

st.sidebar.title("Navigation")
page = st.sidebar.radio("Commands", [
    "📋 View Accounts",
    "➕ Add Account",
    "✏️ Update Account",
    "🗑️ Delete Account",
    "🧱 Schema Management"
])

if page == "📋 View Accounts":
    st.title("📋 Account Records")
    st.markdown("View all MileagePlus accounts in the database below.")
    if st.button("🔄 Refresh Data"):
        st.rerun()
    df = fetch_data()
    if df.empty:
        st.warning("No accounts found in the table.")
    else:
        st.dataframe(df, use_container_width=True)

elif page == "➕ Add Account":
    st.title("➕ Add New Account")
    st.markdown("Fill out the form below to add a new MileagePlus account.")
    with st.form("add_account_form"):
        col1, col2 = st.columns(2)
        with col1:
            mileage_plus_num = st.text_input("MileagePlus Number (6 digits)", value=generate_mileage_plus_num(), max_chars=6)
            first_name = st.text_input("First Name")
            last_name = st.text_input("Last Name")
            dob = st.date_input("Date of Birth", value=None)
        with col2:
            email = st.text_input("Email")
            ph_number = st.text_input("Phone Number", max_chars=20)
            mileage_points = st.number_input("Mileage Points", min_value=0, value=0)
        submitted = st.form_submit_button("Add Account")
        if submitted:
            errors = []
            if not mileage_plus_num or len(mileage_plus_num) != 6 or not mileage_plus_num.isdigit():
                errors.append("MileagePlus number must be exactly 6 digits")
            if not first_name:
                errors.append("First name is required")
            if not last_name:
                errors.append("Last name is required")
            if not email:
                errors.append("Email is required")
            if not ph_number or not ph_number.isdigit():
                errors.append("Phone number must be numeric")
            if errors:
                for error in errors:
                    st.error(error)
            else:
                form_data = {
                    'mileage_plus_num': int(mileage_plus_num),
                    'first_name': first_name,
                    'last_name': last_name,
                    'dob': dob.strftime("%Y-%m-%d") if dob else None,
                    'email': email,
                    'ph_number': ph_number,
                    'mileage_points': mileage_points
                }
                keys = list(form_data.keys())
                values = list(form_data.values())
                query = f"INSERT INTO accounts ({', '.join(keys)}) VALUES ({', '.join(['%s']*len(keys))})"
                success = execute_sql(query, values)
                if success:
                    st.success("✅ Account added successfully!")
                    st.rerun()

elif page == "✏️ Update Account":
    st.title("✏️ Update Account")
    st.markdown("Select an account by MileagePlus number and update a specific field.")
    df = fetch_data()
    if df.empty:
        st.info("No accounts available to update.")
    else:
        with st.form("update_account_form"):
            selected_num = st.selectbox("Select MileagePlus Number", df['mileage_plus_num'], key="update_num")
            field = st.selectbox("Field to Update", [
                'first_name', 'last_name', 'dob', 'email', 'ph_number', 'mileage_points'
            ], key="update_field")
            if field == 'dob':
                new_value = st.date_input("New Value", key="update_value")
                new_value = new_value.strftime("%Y-%m-%d") if new_value else None
            elif field == 'mileage_points':
                new_value = st.number_input("New Value", min_value=0, key="update_value")
            else:
                new_value = st.text_input("New Value", key="update_value")
            update_btn = st.form_submit_button("Update Account")
            if update_btn:
                valid = True
                if field == 'mileage_plus_num':
                    if not new_value or len(str(new_value)) != 6 or not str(new_value).isdigit():
                        st.error("MileagePlus number must be exactly 6 digits")
                        valid = False
                if field == 'ph_number' and (not new_value or not new_value.isdigit()):
                    st.error("Phone number must be numeric")
                    valid = False
                if valid and new_value is not None:
                    query = f"UPDATE accounts SET {field} = %s WHERE mileage_plus_num = %s"
                    success = execute_sql(query, (new_value, selected_num))
                    if success:
                        st.success(f"✅ Updated {field} for MileagePlus number {selected_num}")
                        st.rerun()
                elif not valid:
                    pass
                else:
                    st.warning("Please provide a new value.")

elif page == "🗑️ Delete Account":
    st.title("🗑️ Delete Account")
    st.markdown("Select an account by MileagePlus number to delete.")
    df = fetch_data()
    if df.empty:
        st.info("No accounts available to delete.")
    else:
        with st.form("delete_account_form"):
            selected_num = st.selectbox("Select MileagePlus Number", df['mileage_plus_num'], key="delete_num")
            account_details = df[df['mileage_plus_num'] == selected_num].iloc[0]
            st.write("**Account Details:**")
            st.write(f"- First Name: {account_details['first_name']}")
            st.write(f"- Last Name: {account_details['last_name']}")
            st.write(f"- DOB: {account_details['dob']}")
            st.write(f"- Email: {account_details['email']}")
            st.write(f"- Phone: {account_details['ph_number']}")
            st.write(f"- Mileage Points: {account_details['mileage_points']}")
            confirm_delete = st.checkbox("I confirm I want to delete this account", key="delete_confirm")
            delete_btn = st.form_submit_button("Delete Account")
            if delete_btn:
                if confirm_delete:
                    success = execute_sql("DELETE FROM accounts WHERE mileage_plus_num = %s", (selected_num,))
                    if success:
                        st.success(f"✅ Deleted account with MileagePlus number {selected_num}")
                        st.rerun()
                else:
                    st.warning("Please confirm deletion by checking the checkbox.")

elif page == "🧱 Schema Management":
    st.title("🧱 Schema Management")
    st.markdown("Manage the structure of the `accounts` table.")
    with st.expander("📜 View Table Schema", expanded=True):
        cols = get_columns()
        if cols:
            schema_df = pd.DataFrame(cols, columns=["Column", "Type", "Max Length", "Nullable", "Default"])
            st.dataframe(schema_df, use_container_width=True)
        else:
            st.warning("Unable to fetch schema.")
    with st.expander("➕ Add New Column"):
        with st.form("add_column_form"):
            col_name = st.text_input("Column Name", key="add_col_name")
            col_type = st.selectbox("Data Type", [
                "VARCHAR(255)", "TEXT", "INTEGER", "BOOLEAN", "DATE", 
                "TIMESTAMP", "DECIMAL(10,2)", "BIGINT"
            ], key="add_col_type")
            add_btn = st.form_submit_button("Add Column")
            if add_btn:
                if col_name:
                    query = f"ALTER TABLE accounts ADD COLUMN {col_name} {col_type}"
                    success = execute_sql(query)
                    if success:
                        st.success(f"✅ Column `{col_name}` added!")
                        st.rerun()
                else:
                    st.warning("Please provide a column name.")
    with st.expander("🗑️ Delete Column"):
        if cols:
            col_to_drop = st.selectbox("Select Column", [c[0] for c in cols if c[0] != "mileage_plus_num"], key="delete_col")
            confirm = st.text_input("Type 'DELETE' to confirm", key="delete_confirm")
            if st.button("Delete Column"):
                if confirm == "DELETE":
                    query = f"ALTER TABLE accounts DROP COLUMN {col_to_drop}"
                    success = execute_sql(query)
                    if success:
                        st.success(f"✅ Column `{col_to_drop}` deleted!")
                        st.rerun()
                else:
                    st.warning("Please type 'DELETE' to confirm.")
        else:
            st.info("No columns available to delete.")
    with st.expander("✏️ Update Column"):
        if cols:
            col_to_update = st.selectbox("Select Column", [c[0] for c in cols], key="update_col")
            action = st.radio("Action", ["Rename", "Change Type"], key="update_action")
            if action == "Rename":
                with st.form("rename_column_form"):
                    new_name = st.text_input("New Name", key="rename_value")
                    rename_btn = st.form_submit_button("Rename Column")
                    if rename_btn:
                        if new_name and new_name != col_to_update:
                            query = f"ALTER TABLE accounts RENAME COLUMN {col_to_update} TO {new_name}"
                            success = execute_sql(query)
                            if success:
                                st.success(f"✅ Renamed `{col_to_update}` to `{new_name}`")
                                st.rerun()
                        else:
                            st.warning("Please provide a different new name.")
            else:
                with st.form("change_type_form"):
                    new_type = st.selectbox("New Type", [
                        "VARCHAR(255)", "TEXT", "INTEGER", "BOOLEAN", "DATE", 
                        "TIMESTAMP", "DECIMAL(10,2)", "BIGINT"
                    ], key="type_value")
                    st.warning("⚠️ Changing type may fail if data is incompatible.")
                    type_btn = st.form_submit_button("Change Type")
                    if type_btn:
                        query = f"ALTER TABLE accounts ALTER COLUMN {col_to_update} TYPE {new_type}"
                        success = execute_sql(query)
                        if success:
                            st.success(f"✅ Changed type of `{col_to_update}` to {new_type}")
                            st.rerun()
        else:
            st.info("No columns available to update.")

st.sidebar.markdown("---")
st.sidebar.markdown("**United MileagePlus Account System**")
st.sidebar.markdown("Admin Interface v1.0")
