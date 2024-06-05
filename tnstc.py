import streamlit as st
import sqlite3
from datetime import datetime
import hashlib
import pandas as pd
import pytz
from collections.abc import Iterable  # Importing Iterable from collections.abc


# Helper functions
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def format_date(date_str):
    return datetime.strptime(date_str, '%Y-%m-%d').strftime('%d-%m-%Y')

def get_current_time():
    IST = pytz.timezone('Asia/Kolkata')
    return datetime.now(IST)

def create_database():
    conn = sqlite3.connect('edp_shifts.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS shifts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT,
        branch TEXT,
        staff_name TEXT,
        staff_number TEXT,
        mobile_phone TEXT,
        shift_timing TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        email TEXT,
        role TEXT,
        verified INTEGER DEFAULT 0
    )''')
    c.execute('''CREATE INDEX IF NOT EXISTS idx_staff ON shifts (staff_name, staff_number, mobile_phone)''')
    branches = ['RFT', 'DCN', 'TVK', 'LAL', 'MCR', 'TMF', 'CNT', 'MNP', 'TKI', 'PBR', 'JKM', 'ALR', 'UPM', 'TRR', 'KNM']
    for branch in branches:
        try:
            c.execute('INSERT INTO users (username, password, email, role) VALUES (?, ?, ?, ?)', 
                      (branch, hash_password(branch.lower() + '123'), f"{branch.lower()}@example.com", 'user'))
        except sqlite3.IntegrityError:
            pass
    try:
        c.execute('INSERT INTO users (username, password, email, role) VALUES (?, ?, ?, ?)', 
                  ('admin', hash_password('admin123'), 'admin@example.com', 'admin'))
    except sqlite3.IntegrityError:
        pass
    conn.commit()
    conn.close()

create_database()

def get_db_connection():
    conn = sqlite3.connect('edp_shifts.db')
    conn.row_factory = sqlite3.Row
    return conn

def authenticate_user(username, password):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, hash_password(password)))
    user = c.fetchone()
    conn.close()
    return user

def insert_shift(date, branch, staff_name, staff_number, mobile_phone, shift_timing):
    conn = get_db_connection()
    c = conn.cursor()
    timestamp = get_current_time().strftime('%Y-%m-%d %H:%M:%S')
    c.execute('''
        INSERT INTO shifts (date, branch, staff_name, staff_number, mobile_phone, shift_timing, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (date, branch, staff_name, staff_number, mobile_phone, shift_timing, timestamp))
    conn.commit()
    conn.close()

def fetch_all_shifts():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM shifts ORDER BY date, branch')
    shifts = c.fetchall()
    conn.close()
    return shifts

def fetch_user(username):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE username = ?', (username,))
    user = c.fetchone()
    conn.close()
    return user

def fetch_all_users():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM users ORDER BY username')
    users = c.fetchall()
    conn.close()
    return users

def reset_password(username, new_password):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('UPDATE users SET password = ? WHERE username = ?', (hash_password(new_password), username))
    conn.commit()
    conn.close()

def delete_shift(shift_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('DELETE FROM shifts WHERE id = ?', (shift_id,))
    conn.commit()
    conn.close()

def update_shift(shift_id, date, branch, staff_name, staff_number, mobile_phone, shift_timing):
    conn = get_db_connection()
    c = conn.cursor()
    timestamp = get_current_time().strftime('%Y-%m-%d %H:%M:%S')
    c.execute('''
        UPDATE shifts SET date = ?, branch = ?, staff_name = ?, staff_number = ?, mobile_phone = ?, shift_timing = ?, timestamp = ?
        WHERE id = ?
    ''', (date, branch, staff_name, staff_number, mobile_phone, shift_timing, timestamp, shift_id))
    conn.commit()
    conn.close()

def register_user(username, email, password, role):
    conn = get_db_connection()
    c = conn.cursor()
    try:
        c.execute('INSERT INTO users (username, password, email, role, verified) VALUES (?, ?, ?, ?, ?)', 
                  (username, hash_password(password), email, role, 0))
        conn.commit()
        st.success('User registered successfully!')
    except sqlite3.IntegrityError:
        st.error('Username already exists.')
    finally:
        conn.close()

def verify_user(username):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('UPDATE users SET verified = 1 WHERE username = ?', (username,))
    conn.commit()
    conn.close()

def update_user_role(username, new_role):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('UPDATE users SET role = ? WHERE username = ?', (new_role, username))
    conn.commit()
    conn.close()

def fetch_suggestions():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT DISTINCT staff_name, staff_number, mobile_phone FROM shifts')
    suggestions = c.fetchall()
    conn.close()
    return suggestions

# Streamlit UI setup
st.set_page_config(layout="wide")

title_color = '#1f77b4'
subtitle_color = '#333333'
table_header_color = '#f5f5f5'
table_header_font = 'Arial, sans-serif'
table_data_font = 'Arial, sans-serif'

st.markdown(f'<h1 style="color:{title_color};">Dashboard</h1>', unsafe_allow_html=True)
st.markdown(f'<h3 style="color:{subtitle_color}; font-family:{table_data_font};">'
            'Tamil Nadu State Transport Corporation (KUM) Ltd., Trichy Region</h3>', unsafe_allow_html=True)
st.subheader('EDP Shift Management')

if 'username' not in st.session_state:
    st.session_state['username'] = None

if st.session_state['username'] is None:
    st.header('Login')
    with st.form('login_form'):
        username = st.text_input('Username')
        password = st.text_input('Password', type='password')
        submitted = st.form_submit_button('Login')
        if submitted:
            user = authenticate_user(username, password)
            if user:
                st.session_state['username'] = user['username']
                st.session_state['role'] = user['role']
                st.success(f'Welcome, {user["username"]}!')
                st.rerun()
            else:
                st.error('Invalid username or password.')
else:
    st.sidebar.header(f'Logged in as {st.session_state["username"]}')
    if st.sidebar.button('Logout'):
        st.session_state['username'] = None
        st.session_state['role'] = None
        st.rerun()

    if st.sidebar.checkbox('View Profile'):
        user = fetch_user(st.session_state['username'])
        if user:
            st.sidebar.subheader('Profile Information')
            st.sidebar.text(f'Username: {user["username"]}')
            st.sidebar.text(f'Email: {user["email"]}')
            st.sidebar.text(f'Role: {user["role"]}')
            new_password = st.sidebar.text_input('New Password', type='password')
            if st.sidebar.button('Reset Password'):
                if new_password:
                    reset_password(user['username'], new_password)
                    st.sidebar.success('Password reset successfully!')

    if st.session_state['role'] == 'user':
        st.header('Submit Your Shift')
        suggestions = fetch_suggestions()
        with st.form('shift_form'):
            date = st.date_input('Date', value=datetime.now().date(), help="Select the date of your shift")
            branch = st.session_state['username']
            staff_name = st.text_input('Staff Name')
            staff_number = st.text_input('Staff Number')
            mobile_phone = st.text_input('Mobile Phone')
            shift_timing = st.selectbox('Shift Timing', ['6-2', '8-5', '10-6', '2-10', '5-1', '5-9(DAY/NIGHT)', '10-6(NIGHT)'])
            submitted = st.form_submit_button('Submit')
            if submitted:
                if not (staff_name and staff_number and mobile_phone):
                    st.error('Please fill in all the fields.')
                else:
                    insert_shift(date, branch, staff_name, staff_number, mobile_phone, shift_timing)
                    st.success('Shift data submitted successfully!')

    if st.session_state['role'] == 'admin':
        st.header('Admin View - All Shifts')
        if st.button('Load All Shifts'):
            shifts = fetch_all_shifts()
            if shifts:
                df = pd.DataFrame(shifts, columns=['ID', 'Date', 'Branch', 'Staff Name', 'Staff Number', 'Mobile Phone', 'Shift Timing', 'Timestamp'])
                df['Date'] = pd.to_datetime(df['Date'], errors='coerce').dt.strftime('%d-%m-%Y')
                st.dataframe(df.style.set_table_styles([
                    {'selector': 'th', 'props': [('background-color', table_header_color), ('color', 'black'),
                                                 ('font-family', table_header_font), ('font-weight', 'bold')]},
                    {'selector': 'td', 'props': [('color', 'black'), ('font-family', table_data_font)]},
                    {'selector': 'tr:hover td', 'props': [('background-color', '#e6e6e6')]}
                ]).set_properties(**{'text-align': 'center', 'border-collapse': 'collapse', 'border': '1px solid #cccccc'}))
            else:
                st.write('No shifts found.')

        st.header('Manage Shifts')
        shift_id = st.number_input('Shift ID to edit/delete', min_value=1, step=1)
        action = st.selectbox('Action', ['Select Action', 'Edit Shift', 'Delete Shift'])
        if action == 'Edit Shift':
            with st.form('edit_shift_form'):
                new_date = st.date_input('Date', value=datetime.now().date(), help="Select the date of the shift")
                new_branch = st.text_input('Branch')
                new_staff_name = st.text_input('Staff Name')
                new_staff_number = st.text_input('Staff Number')
                new_mobile_phone = st.text_input('Mobile Phone')
                new_shift_timing = st.selectbox('Shift Timing', ['6-2(DAY)', '8-5(DAY)', '10-6(DAY)', '2-10(DAY)','5-1(DAY/NIGHT)', '5-9(DAY/NIGHT)', '1-9(NIGHT)','10-6(NIGHT)'])
                submitted = st.form_submit_button('Update Shift')
                if submitted:
                    update_shift(shift_id, new_date, new_branch, new_staff_name, new_staff_number, new_mobile_phone, new_shift_timing)
                    st.success('Shift data updated successfully!')

        elif action == 'Delete Shift':
            if st.button('Delete Shift'):
                delete_shift(shift_id)
                st.success('Shift deleted successfully!')

        st.sidebar.subheader('Admin Tools')
        with st.form('register_user_form'):
            st.sidebar.header('Register New User')
            new_username = st.text_input('New Username')
            new_email = st.text_input('New Email')
            new_password = st.text_input('New Password', type='password')
            role = st.selectbox('New User Role', ['user', 'admin'])
            register_submitted = st.form_submit_button('Register')
            if register_submitted:
                register_user(new_username, new_email, new_password, role)

        if st.sidebar.button('Load All Users'):
            users = fetch_all_users()
            if users:
                df_users = pd.DataFrame(users)
                st.sidebar.dataframe(df_users)

        with st.form('edit_user_role_form'):
            st.sidebar.header('Edit User Role')
            username_to_edit = st.text_input('Username to Edit')
            new_role = st.selectbox('New Role', ['user', 'admin'])
            edit_role_submitted = st.form_submit_button('Update Role')
            if edit_role_submitted:
                update_user_role(username_to_edit, new_role)
                st.success(f'Role updated to {new_role} for user { username_to_edit}!')

        with st.form('verify_user_form'):
            st.sidebar.header('Verify User')
            username_to_verify = st.text_input('Username to Verify')
            verify_submitted = st.form_submit_button('Verify')
            if verify_submitted:
                verify_user(username_to_verify)
                st.success(f'User {username_to_verify} verified successfully!')


