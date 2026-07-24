import streamlit as st
import supabase
from supabase import create_client, Client
import pandas as pd
from datetime import datetime
import hashlib

# Supabase credentials
SUPABASE_URL = "https://yccutkrmflxapwtjngep.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InljY3V0a3JtZmx4YXB3dGpuZ2VwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODQ4NDM5MzEsImV4cCI6MjEwMDQxOTkzMX0.DsWCR0tYq895So5oJWD7Jwia_HRVxO09Y9rv2_Wns9w"

# Initialize Supabase client
supabase_client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Page config
st.set_page_config(page_title="Fuel Tracker", layout="wide", initial_sidebar_state="expanded")

# Initialize session state
if 'token' not in st.session_state:
    st.session_state.token = None
if 'user' not in st.session_state:
    st.session_state.user = None

# Helper functions
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def login_user(username, password):
    try:
        response = supabase_client.table('users').select('*').eq('username', username).execute()
        if response.data and len(response.data) > 0:
            user = response.data[0]
            if user['password'] == hash_password(password):
                return user
        return None
    except Exception as e:
        st.error(f"Error: {e}")
        return None

def create_new_user(username, password, role):
    try:
        response = supabase_client.table('users').insert({
            'username': username,
            'password': hash_password(password),
            'role': role
        }).execute()
        return response.data
    except Exception as e:
        st.error(f"Error: {e}")
        return None

def get_fuel_entries():
    try:
        response = supabase_client.table('fuel_entries').select('*').order('date', desc=True).execute()
        return response.data
    except Exception as e:
        st.error(f"Error: {e}")
        return []

def add_fuel_entry(data):
    try:
        response = supabase_client.table('fuel_entries').insert(data).execute()
        return response.data
    except Exception as e:
        st.error(f"Error: {e}")
        return None

def delete_fuel_entry(id):
    try:
        response = supabase_client.table('fuel_entries').delete().eq('id', id).execute()
        return True
    except Exception as e:
        st.error(f"Error: {e}")
        return False

def get_dashboard_stats():
    try:
        entries = get_fuel_entries()
        fuels = ['Diesel', 'Petrol']
        stats = []
        
        for fuel in fuels:
            fuel_entries = [e for e in entries if e['fuel_type'] == fuel]
            old_stock = fuel_entries[0]['opening_stock'] if fuel_entries and fuel_entries[0]['opening_stock'] else 0
            purchased = sum([e['quantity'] for e in fuel_entries if e['transaction_type'] == 'Purchase' and e['quantity']])
            allocated = sum([e['issue_quantity'] for e in fuel_entries if e['transaction_type'] == 'Issue' and e['issue_quantity']])
            total = old_stock + purchased - allocated
            
            stats.append({
                'fuel_type': fuel,
                'old_stock': old_stock,
                'purchased': purchased,
                'allocated': allocated,
                'total_stock': total
            })
        
        return stats
    except Exception as e:
        st.error(f"Error: {e}")
        return []

# LOGIN PAGE
if not st.session_state.token:
    st.title("Fuel Tracker Login")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.subheader("Login to your account")
        
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        
        if st.button("Login", use_container_width=True):
            user = login_user(username, password)
            
            if user:
                st.session_state.token = "logged_in"
                st.session_state.user = user
                st.success("Login successful!")
                st.rerun()
            else:
                st.error("Invalid credentials")

else:
    # MAIN APP
    st.sidebar.title("Fuel Tracker")
    st.sidebar.write(f"**User:** {st.session_state.user['username']}")
    st.sidebar.write(f"**Role:** {st.session_state.user['role']}")
    
    if st.sidebar.button("Logout", use_container_width=True):
        st.session_state.token = None
        st.session_state.user = None
        st.rerun()
    
    # Navigation
    page = st.sidebar.radio("Menu", ["Dashboard", "Fuel Entry", "Reports", "Users", "Password"])
    
    # DASHBOARD PAGE
    if page == "Dashboard":
        st.title("Dashboard")
        st.write("Real-time stock tracking by fuel type")
        
        stats = get_dashboard_stats()
        
        cols = st.columns(len(stats))
        for idx, stat in enumerate(stats):
            with cols[idx]:
                st.metric(
                    label=stat['fuel_type'],
                    value=f"{stat['total_stock']:.2f}L",
                    delta=f"Old: {stat['old_stock']:.2f}L | Purchase: {stat['purchased']:.2f}L | Allocated: {stat['allocated']:.2f}L"
                )
        
        st.subheader("Recent Entries")
        entries = get_fuel_entries()
        if entries:
            df = pd.DataFrame(entries[:10])
            st.dataframe(df[['date', 'transaction_type', 'slip_no', 'fuel_type', 'quantity', 'issue_quantity']], use_container_width=True)
    
    # FUEL ENTRY PAGE
    elif page == "Fuel Entry":
        st.title("Add Fuel Entry")
        st.write("Record PURCHASE or ISSUE transactions")
        
        tab1, tab2 = st.tabs(["Purchase Fuel", "Issue to Vehicle"])
        
        with tab1:
            st.subheader("Purchase Fuel")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                slip_no = st.text_input("Slip No *", key="slip_purchase")
            with col2:
                fuel_type = st.selectbox("Fuel Type *", ["Diesel", "Petrol"], key="fuel_purchase")
            with col3:
                stock_type = st.selectbox("Stock Type *", ["New Stock", "Old Stock"], key="stock_purchase")
            
            opening_stock = None
            if stock_type == "Old Stock":
                opening_stock = st.number_input("Stock Amount (L)", min_value=0.0, step=0.01, key="opening_stock")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                quantity = st.number_input("Quantity (L) *", min_value=0.0, step=0.01, key="qty_purchase")
            with col2:
                rate = st.number_input("Rate (per L)", min_value=0.0, step=0.01, key="rate_purchase")
            with col3:
                amount = quantity * rate
                st.metric("Amount", f"{amount:.2f}")
            
            col1, col2 = st.columns(2)
            with col1:
                vendor_name = st.text_input("Vendor Name", key="vendor_name_p")
            with col2:
                vendor_location = st.text_input("Vendor Location", key="vendor_loc_p")
            
            col1, col2 = st.columns(2)
            with col1:
                approved_by = st.text_input("Approved By", key="approved_p")
            with col2:
                remarks = st.text_input("Remarks", key="remarks_p")
            
            if st.button("Save Purchase", use_container_width=True, key="save_purchase"):
                data = {
                    "slip_no": slip_no,
                    "transaction_type": "Purchase",
                    "fuel_type": fuel_type,
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "opening_stock": opening_stock,
                    "quantity": quantity,
                    "rate": rate,
                    "amount": amount,
                    "vendor_name": vendor_name,
                    "vendor_location": vendor_location,
                    "approved_by": approved_by,
                    "remarks": remarks
                }
                
                response = add_fuel_entry(data)
                if response:
                    st.success("Entry saved!")
                else:
                    st.error("Error saving entry")
        
        with tab2:
            st.subheader("Issue to Vehicle")
            
            col1, col2 = st.columns(2)
            with col1:
                slip_no = st.text_input("Slip No *", key="slip_issue")
            with col2:
                fuel_type = st.selectbox("Fuel Type *", ["Diesel", "Petrol"], key="fuel_issue")
            
            col1, col2, col3, col4, col5 = st.columns(5)
            with col1:
                vehicle_no = st.text_input("Vehicle No *", key="vehicle_no")
            with col2:
                vin_no = st.text_input("VIN No", key="vin_no")
            with col3:
                registration_no = st.text_input("Reg No", key="reg_no")
            with col4:
                model_no = st.text_input("Model No", key="model_no")
            with col5:
                allocated_to = st.selectbox("Allocated To", ["Demo Car", "Assigned Car", "Customer Car", "Loaner Car", "Other"], key="allocated")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                opening_odo = st.number_input("Opening Odometer", min_value=0.0, step=0.01, key="opening_odo")
            with col2:
                closing_odo = st.number_input("Closing Odometer", min_value=0.0, step=0.01, key="closing_odo")
            with col3:
                km_run = closing_odo - opening_odo
                st.metric("KM Run", f"{km_run:.2f}")
            
            col1, col2 = st.columns(2)
            with col1:
                issue_quantity = st.number_input("Issue Quantity (L) *", min_value=0.0, step=0.01, key="issue_qty")
            with col2:
                if issue_quantity > 0:
                    mileage = km_run / issue_quantity
                    st.metric("Mileage (KM/L)", f"{mileage:.2f}")
                else:
                    mileage = 0
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                recipient_name = st.text_input("Recipient Name", key="recipient_name")
            with col2:
                receiver_name = st.text_input("Receiver Name", key="receiver_name")
            with col3:
                approved_by = st.text_input("Approved By", key="approved_i")
            with col4:
                remarks = st.text_input("Remarks", key="remarks_i")
            
            if st.button("Save Issue", use_container_width=True, key="save_issue"):
                data = {
                    "slip_no": slip_no,
                    "transaction_type": "Issue",
                    "fuel_type": fuel_type,
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "vehicle_no": vehicle_no,
                    "vin_no": vin_no,
                    "registration_no": registration_no,
                    "model_no": model_no,
                    "allocated_to": allocated_to,
                    "opening_odometer": opening_odo,
                    "closing_odometer": closing_odo,
                    "km_run": km_run,
                    "issue_quantity": issue_quantity,
                    "mileage": mileage,
                    "recipient_name": recipient_name,
                    "receiver_name": receiver_name,
                    "approved_by": approved_by,
                    "remarks": remarks
                }
                
                response = add_fuel_entry(data)
                if response:
                    st.success("Entry saved!")
                else:
                    st.error("Error saving entry")
    
    # REPORTS PAGE
    elif page == "Reports":
        st.title("Reports & Export")
        st.write("View, filter, and export transactions")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            fuel_filter = st.selectbox("Fuel Type", ["All", "Diesel", "Petrol"])
        with col2:
            type_filter = st.selectbox("Transaction Type", ["All", "Purchase", "Issue"])
        with col3:
            date_from = st.date_input("From Date")
        with col4:
            date_to = st.date_input("To Date")
        
        if st.button("Filter", use_container_width=True):
            entries = get_fuel_entries()
            if entries:
                df = pd.DataFrame(entries)
                
                if fuel_filter != "All":
                    df = df[df['fuel_type'] == fuel_filter]
                if type_filter != "All":
                    df = df[df['transaction_type'] == type_filter]
                
                st.dataframe(df, use_container_width=True)
    
    # USERS PAGE
    elif page == "Users":
        st.title("Manage Users")
        
        st.subheader("Create New User")
        col1, col2, col3 = st.columns(3)
        with col1:
            new_username = st.text_input("Username")
        with col2:
            new_password = st.text_input("Password", type="password")
        with col3:
            new_role = st.selectbox("Role", ["User", "Admin"])
        
        if st.button("Create User", use_container_width=True):
            response = create_new_user(new_username, new_password, new_role)
            if response:
                st.success("User created!")
            else:
                st.error("Error creating user")
        
        st.subheader("All Users")
        try:
            users = supabase_client.table('users').select('*').execute()
            if users.data:
                df = pd.DataFrame(users.data)
                st.dataframe(df[['username', 'role', 'created_at']], use_container_width=True)
        except Exception as e:
            st.error(f"Error: {e}")
    
    # PASSWORD PAGE
    elif page == "Password":
        st.title("Change Password")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            old_password = st.text_input("Old Password", type="password")
            new_password = st.text_input("New Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            
            if st.button("Update Password", use_container_width=True):
                if new_password != confirm_password:
                    st.error("Passwords do not match")
                else:
                    try:
                        user = login_user(st.session_state.user['username'], old_password)
                        if user:
                            supabase_client.table('users').update({
                                'password': hash_password(new_password)
                            }).eq('id', st.session_state.user['id']).execute()
                            st.success("Password changed!")
                        else:
                            st.error("Old password incorrect")
                    except Exception as e:
                        st.error(f"Error: {e}")