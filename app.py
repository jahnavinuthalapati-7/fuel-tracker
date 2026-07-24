import streamlit as st
from supabase import create_client, Client
import pandas as pd
from datetime import datetime

# Supabase credentials
SUPABASE_URL = "https://yccutkrmflxapwtjngep.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InljY3V0a3JtZmx4YXB3dGpuZ2VwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODQ4NDM5MzEsImV4cCI6MjEwMDQxOTkzMX0.DsWCR0tYq895So5oJWD7Jwia_HRVxO09Y9rv2_Wns9w"

supabase_client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="Fuel Tracker", layout="wide")

if 'user' not in st.session_state:
    st.session_state.user = None

# LOGIN PAGE
if st.session_state.user is None:
    st.title("Fuel Tracker Login")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.subheader("Login to your account")
        
        username = st.text_input("Username", key="login_user")
        password = st.text_input("Password", type="password", key="login_pass")
        
        if st.button("Login", use_container_width=True):
            try:
                # Query database
                response = supabase_client.table('users').select('*').eq('username', username).execute()
                
                if response.data and len(response.data) > 0:
                    user = response.data[0]
                    # Compare plain text password
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
    st.sidebar.title("Fuel Tracker")
    st.sidebar.write(f"**User:** {st.session_state.user['username']}")
    st.sidebar.write(f"**Role:** {st.session_state.user['role']}")
    
    if st.sidebar.button("Logout", use_container_width=True):
        st.session_state.user = None
        st.rerun()
    
    page = st.sidebar.radio("Menu", ["Dashboard", "Fuel Entry", "Reports"])
    
    if page == "Dashboard":
        st.title("Dashboard")
        st.write("Welcome to Fuel Tracker!")
        
        try:
            entries = supabase_client.table('fuel_entries').select('*').execute()
            if entries.data:
                df = pd.DataFrame(entries.data)
                st.dataframe(df, use_container_width=True)
            else:
                st.info("No entries yet")
        except Exception as e:
            st.error(f"Error: {e}")
    
    elif page == "Fuel Entry":
        st.title("Add Fuel Entry")
        
        tab1, tab2 = st.tabs(["Purchase", "Issue"])
        
        with tab1:
            st.subheader("Purchase Fuel")
            slip_no = st.text_input("Slip No")
            fuel_type = st.selectbox("Fuel Type", ["Diesel", "Petrol"])
            stock_type = st.selectbox("Stock Type", ["New Stock", "Old Stock"])
            
            if stock_type == "Old Stock":
                opening_stock = st.number_input("Stock Amount (L)", min_value=0.0)
            else:
                opening_stock = None
            
            quantity = st.number_input("Quantity (L)", min_value=0.0)
            rate = st.number_input("Rate (per L)", min_value=0.0)
            
            if st.button("Save Purchase"):
                try:
                    supabase_client.table('fuel_entries').insert({
                        'slip_no': slip_no,
                        'transaction_type': 'Purchase',
                        'fuel_type': fuel_type,
                        'date': datetime.now().strftime("%Y-%m-%d"),
                        'opening_stock': opening_stock,
                        'quantity': quantity,
                        'rate': rate,
                        'amount': quantity * rate
                    }).execute()
                    st.success("Entry saved!")
                except Exception as e:
                    st.error(f"Error: {e}")
        
        with tab2:
            st.subheader("Issue to Vehicle")
            slip_no = st.text_input("Slip No", key="slip_issue")
            fuel_type = st.selectbox("Fuel Type", ["Diesel", "Petrol"], key="fuel_issue")
            vehicle_no = st.text_input("Vehicle No")
            issue_quantity = st.number_input("Issue Quantity (L)", min_value=0.0)
            
            if st.button("Save Issue"):
                try:
                    supabase_client.table('fuel_entries').insert({
                        'slip_no': slip_no,
                        'transaction_type': 'Issue',
                        'fuel_type': fuel_type,
                        'date': datetime.now().strftime("%Y-%m-%d"),
                        'vehicle_no': vehicle_no,
                        'issue_quantity': issue_quantity
                    }).execute()
                    st.success("Entry saved!")
                except Exception as e:
                    st.error(f"Error: {e}")
    
    elif page == "Reports":
        st.title("Reports")
        try:
            entries = supabase_client.table('fuel_entries').select('*').execute()
            if entries.data:
                df = pd.DataFrame(entries.data)
                st.dataframe(df, use_container_width=True)
            else:
                st.info("No entries")
        except Exception as e:
            st.error(f"Error: {e}")