import streamlit as st
import json
import os
from datetime import datetime
import pandas as pd
from data_manager import DataManager
from utils import format_currency, calculate_member_summary, get_payment_status_color

# Admin password - can be overridden with environment variable
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin123')

# Initialize data manager
@st.cache_resource
def get_data_manager():
    return DataManager()

def main():
    st.set_page_config(
        page_title="Subscription Cost-Sharing Manager",
        page_icon="💰",
        layout="wide"
    )
    
    st.title("💰 Subscription Cost-Sharing Manager")
    
    # Initialize data manager
    dm = get_data_manager()
    
    # Initialize session state
    if 'selected_year' not in st.session_state:
        st.session_state.selected_year = datetime.now().year
    
    if 'view_mode' not in st.session_state:
        st.session_state.view_mode = 'member'
    
    if 'admin_authenticated' not in st.session_state:
        st.session_state.admin_authenticated = False
    
    # Load data for current year
    data = dm.load_data(st.session_state.selected_year)
    
    # Sidebar for year selection and settings
    with st.sidebar:
        st.header("View Mode")
        
        # View mode selector
        view_options = ["👤 Member View", "🔧 Admin View"]
        selected_view = st.radio(
            "Select View:",
            view_options,
            index=0 if st.session_state.view_mode == 'member' else 1,
            key="view_selector"
        )
        
        # Handle admin authentication
        if "Admin" in selected_view:
            if not st.session_state.admin_authenticated:
                admin_password = st.text_input("Admin Password:", type="password", key="admin_password")
                if st.button("Login as Admin"):
                    # Check password (can be configured via ADMIN_PASSWORD environment variable)
                    if admin_password == ADMIN_PASSWORD:
                        st.session_state.admin_authenticated = True
                        st.session_state.view_mode = 'admin'
                        st.success("Admin access granted!")
                        st.rerun()
                    else:
                        st.error("Incorrect password!")
                st.info("Enter admin password to access edit features.")
                st.session_state.view_mode = 'member'
            else:
                st.session_state.view_mode = 'admin'
                if st.button("Logout from Admin"):
                    st.session_state.admin_authenticated = False
                    st.session_state.view_mode = 'member'
                    st.rerun()
        else:
            st.session_state.view_mode = 'member'
        
        st.divider()
        st.header("Settings")
        
        # Year selection
        st.subheader("Year Selection")
        available_years = dm.get_available_years()
        if not available_years:
            available_years = [datetime.now().year]
        
        selected_year = st.selectbox(
            "Select Year:",
            options=sorted(available_years, reverse=True),
            index=0 if st.session_state.selected_year in available_years else 0
        )
        
        if selected_year != st.session_state.selected_year:
            st.session_state.selected_year = selected_year
            st.rerun()
        
        # Add new year (Admin only)
        if st.session_state.view_mode == 'admin':
            new_year = st.number_input(
                "Add New Year:",
                min_value=2020,
                max_value=2030,
                value=datetime.now().year,
                step=1
            )
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Add Year"):
                    if new_year not in available_years:
                        dm.create_year_data(new_year)
                        st.success(f"Year {new_year} added!")
                        st.rerun()
                    else:
                        st.warning("Year already exists!")
            
            with col2:
                if st.button("Copy from Previous") and len(available_years) > 1:
                    prev_year = max([y for y in available_years if y < selected_year], default=None)
                    if prev_year:
                        dm.copy_members_from_year(prev_year, selected_year)
                        st.success(f"Members copied from {prev_year}!")
                        st.rerun()
        
        st.divider()
        
        # Subscription settings
        st.subheader("Subscription Settings")
        settings = data.get('settings', {})
        
        if st.session_state.view_mode == 'admin':
            total_price = st.number_input(
                "Total Monthly Price:",
                min_value=0.0,
                value=settings.get('total_price', 100.0),
                step=0.01,
                format="%.2f"
            )
            
            max_slots = st.number_input(
                "Maximum Slots:",
                min_value=1,
                value=settings.get('max_slots', 10),
                step=1
            )
            
            if st.button("Save Settings"):
                dm.update_settings(selected_year, total_price, max_slots)
                st.success("Settings saved!")
                st.rerun()
        else:
            st.info(f"Total Monthly Price: ${settings.get('total_price', 100.0):.2f}")
            st.info(f"Maximum Slots: {settings.get('max_slots', 10)}")
        
        st.divider()
        
        # Monthly reminders for current month
        st.subheader("📢 Payment Reminders")
        current_month = datetime.now().strftime("%b")
        
        # Reload data to get current payments
        reminder_data = dm.load_data(selected_year)
        reminder_members = reminder_data.get('members', [])
        reminder_payments = reminder_data.get('payments', {})
        
        if reminder_members:
            unpaid_members = []
            for member in reminder_members:
                member_payments = reminder_payments.get(member, {})
                if not member_payments.get(current_month, False):
                    unpaid_members.append(member)
            
            if unpaid_members and selected_year == datetime.now().year:
                st.warning(f"⚠️ {current_month} - {len(unpaid_members)} member(s) haven't paid yet:")
                for member in unpaid_members:
                    st.write(f"• {member}")
            elif selected_year == datetime.now().year:
                st.success(f"✅ All members have paid for {current_month}!")
            else:
                st.info(f"Viewing archived year {selected_year}")
    
    # Main content area - adjust tabs based on view mode
    if st.session_state.view_mode == 'admin':
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["👥 Members", "📅 Payments", "📊 Summary", "📈 Dashboard", "📜 History", "💾 Backup"])
    else:
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["👥 Members", "📊 Summary", "📈 Dashboard", "📜 History", "💾 Backup"])
    
    # Reload data after potential changes
    data = dm.load_data(selected_year)
    settings = data.get('settings', {'total_price': 100.0, 'max_slots': 10})
    members = data.get('members', [])
    payments = data.get('payments', {})
    
    with tab1:
        if st.session_state.view_mode == 'admin':
            st.header(f"Manage Members - {selected_year}")
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                # Add new member
                st.subheader("Add New Member")
                new_member_name = st.text_input("Member Name:")
                if st.button("Add Member") and new_member_name.strip():
                    if new_member_name.strip() not in members:
                        dm.add_member(selected_year, new_member_name.strip())
                        st.success(f"Added {new_member_name}!")
                        st.rerun()
                    else:
                        st.warning("Member already exists!")
            
            with col2:
                st.subheader("Current Members")
                if members:
                    for member in members:
                        col_name, col_remove = st.columns([3, 1])
                        with col_name:
                            st.write(f"👤 {member}")
                        with col_remove:
                            if st.button("🗑️", key=f"remove_{member}"):
                                dm.remove_member(selected_year, member)
                                st.success(f"Removed {member}!")
                                st.rerun()
                else:
                    st.info("No members added yet.")
        else:
            st.header(f"Members - {selected_year}")
            st.subheader("Current Members")
            if members:
                for member in members:
                    st.write(f"👤 {member}")
            else:
                st.info("No members added yet.")
    
    # Payments tab (Admin only)
    if st.session_state.view_mode == 'admin':
        with tab2:
            st.header(f"Payment Tracking - {selected_year}")
            
            if not members:
                st.warning("Please add members first in the Members tab.")
            else:
                # Bulk payment registration
                st.subheader("Bulk Payment Registration")
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    bulk_member = st.selectbox("Select Member:", members, key="bulk_member")
                with col2:
                    bulk_months = st.number_input("Number of Months:", min_value=1, max_value=12, value=1, key="bulk_months")
                with col3:
                    start_month = st.selectbox("Starting Month:", 
                                             ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                                              "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"], key="start_month")
                with col4:
                    if st.button("Register Bulk Payment"):
                        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
                        start_idx = months.index(start_month)
                        for i in range(bulk_months):
                            month_idx = (start_idx + i) % 12
                            month = months[month_idx]
                            dm.update_payment(selected_year, bulk_member, month, True)
                        st.success(f"Registered {bulk_months} months for {bulk_member} starting from {start_month}!")
                        st.rerun()
                
                st.divider()
                
                # Monthly payment tracking
                st.subheader("Monthly Payment Status")
                
                months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
                
                # Create payment status table
                payment_data = []
                for member in members:
                    row = {"Member": member}
                    member_payments = payments.get(member, {})
                    
                    for month in months:
                        paid = member_payments.get(month, False)
                        row[month] = "✅" if paid else "❌"
                    
                    # Calculate summary
                    months_paid = sum(1 for month in months if member_payments.get(month, False))
                    price_per_slot = settings['total_price'] / len(members) if members else 0
                    amount_paid = months_paid * price_per_slot
                    amount_owed = (12 - months_paid) * price_per_slot
                    payment_rate = (months_paid / 12) * 100
                    
                    row["Months Paid"] = months_paid
                    row["Amount Paid"] = format_currency(amount_paid)
                    row["Amount Owed"] = format_currency(amount_owed)
                    
                    # Add status indicator
                    if payment_rate == 100:
                        row["Status"] = "🟢 Paid"
                    elif payment_rate >= 50:
                        row["Status"] = "🟡 Partial"
                    else:
                        row["Status"] = "🔴 Behind"
                    
                    payment_data.append(row)
                
                if payment_data:
                    df = pd.DataFrame(payment_data)
                    
                    # Apply styling
                    def highlight_status(val):
                        if "🟢" in str(val):
                            return 'background-color: #d4edda; color: #155724'
                        elif "🟡" in str(val):
                            return 'background-color: #fff3cd; color: #856404'
                        elif "🔴" in str(val):
                            return 'background-color: #f8d7da; color: #721c24'
                        return ''
                    
                    styled_df = df.style.map(highlight_status, subset=['Status'])
                    st.dataframe(styled_df, width='stretch')
                    
                    # Individual month toggles
                    st.subheader("Toggle Individual Payments")
                    selected_member = st.selectbox("Select Member:", members, key="toggle_member")
                    
                    cols = st.columns(6)
                    member_payments = payments.get(selected_member, {})
                    
                    for i, month in enumerate(months):
                        with cols[i % 6]:
                            current_status = member_payments.get(month, False)
                            new_status = st.checkbox(
                                month, 
                                value=current_status,
                                key=f"toggle_{selected_member}_{month}"
                            )
                            if new_status != current_status:
                                dm.update_payment(selected_year, selected_member, month, new_status)
                                st.rerun()
    
    # Summary tab - adjust tab number based on view mode
    summary_tab = tab2 if st.session_state.view_mode == 'member' else tab3
    with summary_tab:
        st.header(f"Individual Summaries - {selected_year}")
        
        if not members:
            st.warning("Please add members first in the Members tab.")
            return
        
        price_per_slot = settings['total_price'] / len(members) if members else 0
        
        for member in members:
            member_payments = payments.get(member, {})
            summary = calculate_member_summary(member_payments, price_per_slot)
            
            # Determine status
            if summary['payment_rate'] == 100:
                status_icon = "🟢"
                status_text = "Paid"
            elif summary['payment_rate'] >= 50:
                status_icon = "🟡"
                status_text = "Partial"
            else:
                status_icon = "🔴"
                status_text = "Behind"
            
            with st.expander(f"{status_icon} {member} - {status_text}"):
                member_payments = payments.get(member, {})
                summary = calculate_member_summary(member_payments, price_per_slot)
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Months Paid", summary['months_paid'])
                with col2:
                    st.metric("Amount Paid", format_currency(summary['amount_paid']))
                with col3:
                    st.metric("Amount Owed", format_currency(summary['amount_owed']))
                with col4:
                    st.metric("Payment Rate", f"{summary['payment_rate']:.1f}%")
                
                # Monthly breakdown
                st.subheader("Monthly Breakdown")
                months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
                month_data = []
                for month in months:
                    paid = member_payments.get(month, False)
                    month_data.append({
                        "Month": month,
                        "Status": "✅ Paid" if paid else "❌ Unpaid",
                        "Amount": format_currency(price_per_slot) if paid else format_currency(0)
                    })
                
                df = pd.DataFrame(month_data)
                st.dataframe(df, width='stretch')
    
    # Dashboard tab - adjust tab number based on view mode
    dashboard_tab = tab3 if st.session_state.view_mode == 'member' else tab4
    with dashboard_tab:
        st.header(f"Overall Dashboard - {selected_year}")
        
        if not members:
            st.warning("Please add members first in the Members tab.")
            return
        
        # CSV Export
        from utils import export_data_to_csv
        csv_data = export_data_to_csv(data)
        st.download_button(
            label="📥 Export to CSV",
            data=csv_data,
            file_name=f"subscription_report_{selected_year}.csv",
            mime="text/csv",
            help="Download yearly report as CSV file"
        )
        
        st.divider()
        
        price_per_slot = settings['total_price'] / len(members) if members else 0
        
        # Calculate overall statistics
        total_possible = len(members) * 12 * price_per_slot
        total_paid = 0
        total_months_paid = 0
        
        for member in members:
            member_payments = payments.get(member, {})
            months_paid = sum(1 for month in ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"] if member_payments.get(month, False))
            total_months_paid += months_paid
            total_paid += months_paid * price_per_slot
        
        total_outstanding = total_possible - total_paid
        
        # Display metrics
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric("Total Members", len(members))
        with col2:
            st.metric("Monthly Price", format_currency(settings['total_price']))
        with col3:
            st.metric("Price per Slot", format_currency(price_per_slot))
        with col4:
            st.metric("Total Received", format_currency(total_paid))
        with col5:
            st.metric("Total Outstanding", format_currency(total_outstanding))
        
        st.divider()
        
        # Progress bars
        if total_possible > 0:
            payment_percentage = (total_paid / total_possible) * 100
            st.subheader(f"Overall Payment Progress: {payment_percentage:.1f}%")
            st.progress(payment_percentage / 100)
        
        st.divider()
        
        # Member comparison chart
        st.subheader("Member Payment Comparison")
        
        member_data = []
        for member in members:
            member_payments = payments.get(member, {})
            months_paid = sum(1 for month in ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"] if member_payments.get(month, False))
            amount_paid = months_paid * price_per_slot
            amount_owed = (12 - months_paid) * price_per_slot
            payment_rate = (months_paid / 12) * 100
            
            # Determine status
            if payment_rate == 100:
                status = "🟢 Paid"
            elif payment_rate >= 50:
                status = "🟡 Partial"
            else:
                status = "🔴 Behind"
            
            member_data.append({
                "Member": member,
                "Status": status,
                "Months Paid": months_paid,
                "Amount Paid": format_currency(amount_paid),
                "Amount Owed": format_currency(amount_owed),
                "Payment Rate": f"{payment_rate:.1f}%"
            })
        
        if member_data:
            df = pd.DataFrame(member_data)
            
            # Apply styling to status column
            def highlight_status(val):
                if "🟢" in str(val):
                    return 'background-color: #d4edda; color: #155724'
                elif "🟡" in str(val):
                    return 'background-color: #fff3cd; color: #856404'
                elif "🔴" in str(val):
                    return 'background-color: #f8d7da; color: #721c24'
                return ''
            
            styled_df = df.style.map(highlight_status, subset=['Status'])
            st.dataframe(styled_df, width='stretch')
            
            # Bar chart of payment rates
            payment_rates = [float(row["Payment Rate"].replace("%", "")) for row in member_data]
            chart_df = pd.DataFrame({
                "Member": [row["Member"] for row in member_data],
                "Payment Rate": payment_rates
            })
            st.bar_chart(chart_df.set_index("Member")["Payment Rate"])
    
    # History tab - adjust tab number based on view mode
    history_tab = tab4 if st.session_state.view_mode == 'member' else tab5
    with history_tab:
        st.header(f"Payment History - {selected_year}")
        
        # Filter options
        col1, col2 = st.columns([2, 1])
        
        with col1:
            filter_member = st.selectbox(
                "Filter by Member:",
                ["All"] + members,
                key="history_filter"
            )
        
        with col2:
            limit = st.number_input(
                "Show last N entries:",
                min_value=10,
                max_value=1000,
                value=50,
                step=10
            )
        
        # Get payment history
        member_filter = None if filter_member == "All" else filter_member
        history = dm.get_payment_history(selected_year, member_filter, limit)
        
        if history:
            st.subheader(f"Recent Payment Changes ({len(history)} entries)")
            
            # Display history as a table
            history_data = []
            for entry in history:
                timestamp = entry.get("timestamp", "")
                try:
                    # Format timestamp
                    dt = datetime.fromisoformat(timestamp)
                    formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S")
                except:
                    formatted_time = timestamp
                
                action_icon = "✅" if entry.get("action") == "marked_paid" else "❌"
                
                history_data.append({
                    "Timestamp": formatted_time,
                    "Member": entry.get("member", ""),
                    "Month": entry.get("month", ""),
                    "Action": f"{action_icon} {entry.get('action', '').replace('_', ' ').title()}",
                    "Old Status": "Paid" if entry.get("old_status") else "Unpaid",
                    "New Status": "Paid" if entry.get("new_status") else "Unpaid"
                })
            
            df = pd.DataFrame(history_data)
            st.dataframe(df, width='stretch')
            
            # Export history to CSV
            import io
            csv_buffer = io.StringIO()
            df.to_csv(csv_buffer, index=False)
            csv_data = csv_buffer.getvalue()
            
            st.download_button(
                label="📥 Export History to CSV",
                data=csv_data,
                file_name=f"payment_history_{selected_year}.csv",
                mime="text/csv",
                help="Download payment history as CSV file"
            )
        else:
            st.info("No payment history recorded yet. Payment changes will appear here.")
    
    # Backup tab - adjust tab number based on view mode
    if st.session_state.view_mode == 'member':
        backup_tab = tab5
    else:
        backup_tab = tab6
    
    with backup_tab:
        st.header("💾 Backup & Restore" if st.session_state.view_mode == 'admin' else "💾 Backup")
        
        st.subheader("Create Backup")
        st.write("Download a complete backup of all your subscription data across all years.")
        
        # Create backup and download directly
        backup_json = dm.create_full_backup()
        
        st.download_button(
            label="📥 Download Full Backup",
            data=backup_json,
            file_name=f"subscription_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            help="Download complete backup of all data",
            type="primary"
        )
        
        # Restore functionality (Admin only)
        if st.session_state.view_mode == 'admin':
            st.divider()
            
            st.subheader("Restore from Backup")
            st.write("Upload a previously created backup file to restore your data.")
            st.warning("⚠️ Warning: This will overwrite existing data for the years in the backup file.")
            
            uploaded_file = st.file_uploader(
                "Choose backup file:",
                type=['json'],
                help="Upload a backup JSON file"
            )
            
            if uploaded_file is not None:
                try:
                    backup_content = uploaded_file.read().decode('utf-8')
                    
                    if st.button("🔄 Restore from Backup", type="primary"):
                        success, message = dm.restore_from_backup(backup_content)
                        
                        if success:
                            st.success(f"✅ {message}")
                            st.info("Please refresh the page to see the restored data.")
                            if st.button("🔄 Refresh Page"):
                                st.rerun()
                        else:
                            st.error(f"❌ {message}")
                except Exception as e:
                    st.error(f"Error reading backup file: {str(e)}")

if __name__ == "__main__":
    main()
