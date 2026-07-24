import streamlit as st
from supabase import create_client, Client
import pandas as pd
from datetime import datetime
import hashlib

# Supabase Setup
SUPABASE_URL = "https://yccutkrmflxapwtjngep.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InljY3V0a3JtZmx4YXB3dGpuZ2VwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODQ4NDM5MzEsImV4cCI6MjEwMDQxOTkzMX0.DsWCR0tYq895So5oJWD7Jwia_HRVxO09Y9rv2_Wns9w"

supabase_client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="Fuel Tracker", layout="wide", initial_sidebar_state="expanded")

# Custom CSS for beautiful interface
st.markdown("""
<style>
    * {
        margin: 0;
        padding: 0;
        box-sizing: border-box;
    }
    body {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        background-color: #f5f5f5;
    }
    .sidebar .sidebar-content {
        background-color: #2c3e50;
    }
    .metric-card {
        background: white;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #3498db;
        margin: 10px 0;
    }
    .form-section {
        background: white;
        padding: 20px;
        border-radius: 10px;
        margin: 15px 0;
    }
    .form-section-title {
        color: #3498db;
        font-weight: bold;
        margin-bottom: 15px;
        font-size: 16px;
    }
    .btn-success {
        background-color: #27ae60;
        color: white;
    }
    .btn-danger {
        background-color: #e74c3c;
        color: white;
    }
    .category-badge {
        padding: 5px 10px;
        border-radius: 20px; 
        font-size: 12px;
        font-weight: bold;
    }
    .category-purchase {
        background-color: #3498db;
        color: white;
    }
    .category-issue {
        background-color: #f39c12;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# Session State
if 'user' not in st.session_state:
    st.session_state.user = None

# LOGIN PAGE
if st.session_state.user is None:
    st.title(" Fuel Tracker")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<h2 style='text-align: center;'>Login to your account</h2>", unsafe_allow_html=True)
        
        username = st.text_input("Username", key="login_user")
        password = st.text_input("Password", type="password", key="login_pass")
        
        if st.button("Login", use_container_width=True, key="login_btn"):
            try:
                response = supabase_client.table('users').select('*').eq('username', username).execute()
                
                if response.data and len(response.data) > 0:
                    user = response.data[0]
                    if user['password'] == password:
                        st.session_state.user = user
                        st.success("Login successful!")
                        st.rerun()
                    else:
                        st.error("Invalid credentials")
                else:
                    st.error("Invalid credentials")
            except Exception as e:
                st.error(f"Error: {str(e)}")

# MAIN APP
else:
    # Sidebar
    with st.sidebar:
        st.title(" Fuel Tracker")
        st.write(f"**User:** {st.session_state.user['username']}")
        st.write(f"**Role:** {st.session_state.user['role']}")
        st.markdown("---")
        
        if st.button("Logout", use_container_width=True):
            st.session_state.user = None
            st.rerun()
        
        st.markdown("---")
        page = st.radio("Menu", [" Dashboard", " Fuel Entry", " Reports", " Users", " Password"])
    
    # DASHBOARD PAGE
    if page == " Dashboard":
        st.title("Dashboard")
        st.write("Real-time stock tracking by fuel type")
        
        try:
            entries = supabase_client.table('fuel_entries').select('*').execute()
            entries_data = entries.data if entries.data else []
            
            # Calculate stats
            diesel_entries = [e for e in entries_data if e['fuel_type'] == 'Diesel']
            petrol_entries = [e for e in entries_data if e['fuel_type'] == 'Petrol']
            
            for fuel_type, fuel_entries in [('DIESEL', diesel_entries), ('PETROL', petrol_entries)]:
                old_stock = fuel_entries[0]['opening_stock'] if fuel_entries and fuel_entries[0]['opening_stock'] else 0
                purchased = sum([e['quantity'] for e in fuel_entries if e['transaction_type'] == 'Purchase' and e['quantity']])
                allocated = sum([e['issue_quantity'] for e in fuel_entries if e['transaction_type'] == 'Issue' and e['issue_quantity']])
                total = old_stock + purchased - allocated
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric(f"{fuel_type} Total", f"{total:.2f}L")
                with col2:
                    st.metric("Old Stock", f"{old_stock:.2f}L")
                with col3:
                    st.metric("Purchased", f"+{purchased:.2f}L")
                with col4:
                    st.metric("Allocated", f"-{allocated:.2f}L")
            
            st.markdown("---")
            st.subheader(" Recent Entries")
            search = st.text_input("Search Slip No, Vehicle, Fuel Type...")
            
            if search:
                filtered = [e for e in entries_data if search.lower() in str(e).lower()]
            else:
                filtered = entries_data[:10]
            
            if filtered:
                df = pd.DataFrame(filtered)
                st.dataframe(df, use_container_width=True)
            else:
                st.info("No entries found")
                
        except Exception as e:
            st.error(f"Error: {e}")
    
    # FUEL ENTRY PAGE
    elif page == " Fuel Entry":
        st.title("Add Fuel Entry")
        st.write("Record PURCHASE or ISSUE transactions")
        
        tab1, tab2 = st.tabs([" Purchase Fuel", " Issue to Vehicle"])
        
        with tab1:
            st.markdown("<div class='form-section'>", unsafe_allow_html=True)
            st.markdown("<div class='form-section-title'> Transaction Details</div>", unsafe_allow_html=True)
            
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
            
            st.markdown("</div>", unsafe_allow_html=True)
            st.markdown("<div class='form-section'>", unsafe_allow_html=True)
            st.markdown("<div class='form-section-title'> Quantity & Cost</div>", unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                quantity = st.number_input("Quantity (L) *", min_value=0.0, step=0.01, key="qty_purchase")
            with col2:
                rate = st.number_input("Rate (per L)", min_value=0.0, step=0.01, key="rate_purchase")
            with col3:
                amount = quantity * rate
                st.metric("Amount (₹)", f"{amount:.2f}")
            
            st.markdown("</div>", unsafe_allow_html=True)
            st.markdown("<div class='form-section'>", unsafe_allow_html=True)
            st.markdown("<div class='form-section-title'> Vendor</div>", unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            with col1:
                vendor_name = st.text_input("Vendor Name", key="vendor_name_p")
            with col2:
                vendor_location = st.text_input("Vendor Location", key="vendor_loc_p")
            
            st.markdown("</div>", unsafe_allow_html=True)
            st.markdown("<div class='form-section'>", unsafe_allow_html=True)
            st.markdown("<div class='form-section-title'> Approvals</div>", unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            with col1:
                approved_by = st.text_input("Approved By", key="approved_p")
            with col2:
                remarks = st.text_input("Remarks", key="remarks_p")
            
            st.markdown("</div>", unsafe_allow_html=True)
            
            if st.button(" Save Purchase", use_container_width=True, key="save_purchase"):
                try:
                    supabase_client.table('fuel_entries').insert({
                        'slip_no': slip_no,
                        'transaction_type': 'Purchase',
                        'fuel_type': fuel_type,
                        'date': datetime.now().strftime("%Y-%m-%d"),
                        'opening_stock': opening_stock,
                        'quantity': quantity,
                        'rate': rate,
                        'amount': amount,
                        'vendor_name': vendor_name,
                        'vendor_location': vendor_location,
                        'approved_by': approved_by,
                        'remarks': remarks
                    }).execute()
                    st.success(" Entry saved!")
                except Exception as e:
                    st.error(f"Error: {e}")
        
        with tab2:
            st.markdown("<div class='form-section'>", unsafe_allow_html=True)
            st.markdown("<div class='form-section-title'> Transaction Details</div>", unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            with col1:
                slip_no = st.text_input("Slip No *", key="slip_issue")
            with col2:
                fuel_type = st.selectbox("Fuel Type *", ["Diesel", "Petrol"], key="fuel_issue")
            
            st.markdown("</div>", unsafe_allow_html=True)
            st.markdown("<div class='form-section'>", unsafe_allow_html=True)
            st.markdown("<div class='form-section-title'> Vehicle Information</div>", unsafe_allow_html=True)
            
            vehicle_no = st.text_input("Vehicle No *", key="vehicle_no")
            vin_no = st.text_input("VIN No", key="vin_no")
            registration_no = st.text_input("Registration No", key="reg_no")
            model_no = st.text_input("Model No", key="model_no")
            allocated_to = st.selectbox("Allocated To", ["Demo Car", "Assigned Car", "Customer Car", "Loaner Car", "Other"], key="allocated")
            
            st.markdown("</div>", unsafe_allow_html=True)
            st.markdown("<div class='form-section'>", unsafe_allow_html=True)
            st.markdown("<div class='form-section-title'> Odometer & Distance</div>", unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                opening_odo = st.number_input("Opening Odometer", min_value=0.0, step=0.01, key="opening_odo")
            with col2:
                closing_odo = st.number_input("Closing Odometer", min_value=0.0, step=0.01, key="closing_odo")
            with col3:
                km_run = closing_odo - opening_odo
                st.metric("KM Run", f"{km_run:.2f}")
            
            st.markdown("</div>", unsafe_allow_html=True)
            st.markdown("<div class='form-section'>", unsafe_allow_html=True)
            st.markdown("<div class='form-section-title'> Issue Quantity & Mileage</div>", unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            with col1:
                issue_quantity = st.number_input("Issue Quantity (L) *", min_value=0.0, step=0.01, key="issue_qty")
            with col2:
                if issue_quantity > 0:
                    mileage = km_run / issue_quantity
                    st.metric("Mileage (KM/L)", f"{mileage:.2f}")
                else:
                    mileage = 0
            
            st.markdown("</div>", unsafe_allow_html=True)
            st.markdown("<div class='form-section'>", unsafe_allow_html=True)
            st.markdown("<div class='form-section-title'> Recipient & Approval</div>", unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            with col1:
                recipient_name = st.text_input("Recipient Name", key="recipient_name")
            with col2:
                receiver_name = st.text_input("Receiver Name", key="receiver_name")
            
            col1, col2 = st.columns(2)
            with col1:
                approved_by = st.text_input("Approved By", key="approved_i")
            with col2:
                remarks = st.text_input("Remarks", key="remarks_i")
            
            st.markdown("</div>", unsafe_allow_html=True)
            
            if st.button(" Save Issue", use_container_width=True, key="save_issue"):
                try:
                    supabase_client.table('fuel_entries').insert({
                        'slip_no': slip_no,
                        'transaction_type': 'Issue',
                        'fuel_type': fuel_type,
                        'date': datetime.now().strftime("%Y-%m-%d"),
                        'vehicle_no': vehicle_no,
                        'vin_no': vin_no,
                        'registration_no': registration_no,
                        'model_no': model_no,
                        'allocated_to': allocated_to,
                        'opening_odometer': opening_odo,
                        'closing_odometer': closing_odo,
                        'km_run': km_run,
                        'issue_quantity': issue_quantity,
                        'mileage': mileage,
                        'recipient_name': recipient_name,
                        'receiver_name': receiver_name,
                        'approved_by': approved_by,
                        'remarks': remarks
                    }).execute()
                    st.success(" Entry saved!")
                except Exception as e:
                    st.error(f"Error: {e}")
    
    # REPORTS PAGE
    elif page == " Reports":
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
        
        if st.button(" Filter", use_container_width=True):
            try:
                entries = supabase_client.table('fuel_entries').select('*').execute()
                if entries.data:
                    df = pd.DataFrame(entries.data)
                    
                    if fuel_filter != "All":
                        df = df[df['fuel_type'] == fuel_filter]
                    if type_filter != "All":
                        df = df[df['transaction_type'] == type_filter]
                    
                    st.dataframe(df, use_container_width=True)
                else:
                    st.info("No entries")
            except Exception as e:
                st.error(f"Error: {e}")
    
    # USERS PAGE
    elif page == "👥 Users":
        st.title("Manage Users")
        
        st.subheader(" Create New User")
        col1, col2, col3 = st.columns(3)
        with col1:
            new_username = st.text_input("Username", key="new_user")
        with col2:
            new_password = st.text_input("Password", type="password", key="new_pass")
        with col3:
            new_role = st.selectbox("Role", ["User", "Admin"], key="new_role")
        
        if st.button("Create User", use_container_width=True):
            try:
                supabase_client.table('users').insert({
                    'username': new_username,
                    'password': new_password,
                    'role': new_role
                }).execute()
                st.success(" User created!")
            except Exception as e:
                st.error(f"Error: {e}")
        
        st.subheader("👥 All Users")
        try:
            users = supabase_client.table('users').select('*').execute()
            if users.data:
                df = pd.DataFrame(users.data)
                st.dataframe(df[['username', 'role', 'created_at']], use_container_width=True)
        except Exception as e:
            st.error(f"Error: {e}")
    
    # PASSWORD PAGE
    elif page == " Password":
        st.title("Change Password")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            old_password = st.text_input("Old Password", type="password", key="old_pass")
            new_password = st.text_input("New Password", type="password", key="new_password")
            confirm_password = st.text_input("Confirm Password", type="password", key="confirm_pass")
            
            if st.button("Update Password", use_container_width=True):
                if new_password != confirm_password:
                    st.error("Passwords do not match")
                else:
                    try:
                        response = supabase_client.table('users').select('*').eq('username', st.session_state.user['username']).execute()
                        if response.data and response.data[0]['password'] == old_password:
                            supabase_client.table('users').update({
                                'password': new_password
                            }).eq('id', st.session_state.user['id']).execute()
                            st.success(" Password changed!")
                        else:
                            st.error("Old password incorrect")
                    except Exception as e:
                        st.error(f"Error: {e}")