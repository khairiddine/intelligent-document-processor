import streamlit as st
import requests
import json
import os
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")

# Configure page
st.set_page_config(
    page_title="DocuAI - Intelligent Document Processing",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for professional UI
st.markdown("""
<style>
    /* Main theme colors */
    :root {
        --primary-color: #6366f1;
        --secondary-color: #8b5cf6;
        --success-color: #10b981;
        --danger-color: #ef4444;
        --warning-color: #f59e0b;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Custom card styling */
    .custom-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        color: white;
        margin-bottom: 2rem;
    }
    
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.08);
        border-left: 4px solid #6366f1;
        transition: transform 0.2s;
        color: #1e293b !important;
    }
    
    .metric-card p, .metric-card span, .metric-card div {
        color: #1e293b !important;
    }
    
    .metric-card strong {
        color: #6366f1 !important;
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.12);
    }
    
    /* Enhanced buttons */
    .stButton>button {
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.3s;
        border: none;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    
    /* File uploader styling */
    .uploadedFile {
        border-radius: 10px;
        border: 2px dashed #6366f1;
        padding: 2rem;
        background: #f8fafc;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1e293b 0%, #334155 100%);
    }
    
    [data-testid="stSidebar"] .stMarkdown {
        color: white;
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #f1f5f9;
        border-radius: 10px;
        padding: 5px;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 10px 20px;
        font-weight: 600;
    }
    
    /* Success/Error messages */
    .stSuccess, .stError, .stWarning, .stInfo {
        border-radius: 10px;
        padding: 1rem;
        font-weight: 500;
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        background: #f8fafc;
        border-radius: 8px;
        font-weight: 600;
    }
    
    /* Metric styling */
    [data-testid="stMetricValue"] {
        font-size: 2rem;
        font-weight: 700;
        color: #6366f1;
    }
    
    /* Progress bar */
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #6366f1 0%, #8b5cf6 100%);
    }
</style>
""", unsafe_allow_html=True)

# Session state for auth
if 'token' not in st.session_state:
    st.session_state.token = None
if 'user' not in st.session_state:
    st.session_state.user = None

def api_request(method, endpoint, data=None, files=None):
    """Make API request with auth"""
    headers = {}
    if st.session_state.token:
        headers['Authorization'] = f"Bearer {st.session_state.token}"
    
    url = f"{API_BASE_URL}{endpoint}"
    
    if method == "GET":
        response = requests.get(url, headers=headers)
    elif method == "POST":
        if files:
            response = requests.post(url, headers=headers, files=files, data=data)
        else:
            headers['Content-Type'] = 'application/json'
            response = requests.post(url, headers=headers, json=data)
    
    return response

def login_page():
    """Login/Register Page with Professional Design"""
    
    # Hero Section
    st.markdown("""
        <div class="custom-card">
            <h1 style="margin:0; font-size: 3rem;">🤖 DocuAI</h1>
            <p style="margin:0.5rem 0 0 0; font-size: 1.3rem; opacity: 0.95;">
                Intelligent Document Processing Platform
            </p>
            <p style="margin:0.3rem 0 0 0; opacity: 0.85;">
                Powered by AI Agents • Azure OpenAI • CrewAI
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    # Center the login form
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        tab1, tab2 = st.tabs(["🔑 Sign In", "📝 Create Account"])
        
        with tab1:
            st.markdown("### Welcome Back")
            st.markdown("Enter your credentials to access your dashboard")
            
            with st.form("login_form"):
                email = st.text_input("📧 Email Address", placeholder="you@example.com")
                password = st.text_input("🔒 Password", type="password", placeholder="••••••••")
                
                col_btn1, col_btn2 = st.columns([3, 1])
                with col_btn1:
                    submit = st.form_submit_button("🚀 Sign In", use_container_width=True, type="primary")
                
                if submit:
                    if email and password:
                        with st.spinner("🔐 Authenticating..."):
                            response = api_request("POST", "/auth/login", {
                                "email": email,
                                "password": password
                            })
                            
                            if response.status_code == 200:
                                data = response.json()
                                st.session_state.token = data['access_token']
                                st.session_state.user = data['user']
                                st.success("✅ Login successful! Redirecting...")
                                st.balloons()
                                st.rerun()
                            else:
                                try:
                                    error_msg = response.json().get('detail', 'Unknown error')
                                except:
                                    error_msg = response.text if response.text else f"Error {response.status_code}"
                                st.error(f"❌ {error_msg}")
                    else:
                        st.warning("⚠️ Please fill in all fields")
        
        with tab2:
            st.markdown("### Create New Account")
            st.markdown("Join us and start processing documents with AI")
            
            with st.form("register_form"):
                full_name = st.text_input("👤 Full Name", placeholder="John Doe")
                email = st.text_input("📧 Email Address", placeholder="you@example.com", key="reg_email")
                password = st.text_input("🔒 Password", type="password", placeholder="••••••••", key="reg_password")
                
                submit = st.form_submit_button("✨ Create Account", use_container_width=True, type="primary")
                
                if submit:
                    if email and password and full_name:
                        with st.spinner("📝 Creating your account..."):
                            response = api_request("POST", "/auth/register", {
                                "email": email,
                                "password": password,
                                "full_name": full_name
                            })
                            
                            if response.status_code == 200:
                                data = response.json()
                                st.session_state.token = data['access_token']
                                st.session_state.user = data['user']
                                st.success("✅ Account created successfully!")
                                st.balloons()
                                st.rerun()
                            else:
                                try:
                                    error_msg = response.json().get('detail', 'Unknown error')
                                except:
                                    error_msg = response.text if response.text else f"Error {response.status_code}"
                                st.error(f"❌ {error_msg}")
                    else:
                        st.warning("⚠️ Please fill in all fields")
    
    # Features section
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
            <div class="metric-card">
                <h3 style="color: #6366f1; margin:0;">🎯 Accurate</h3>
                <p style="margin:0.5rem 0 0 0; color: #64748b;">
                    98%+ accuracy with Azure Document Intelligence
                </p>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
            <div class="metric-card">
                <h3 style="color: #6366f1; margin:0;">⚡ Fast</h3>
                <p style="margin:0.5rem 0 0 0; color: #64748b;">
                    Process documents in under 30 seconds
                </p>
            </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
            <div class="metric-card">
                <h3 style="color: #6366f1; margin:0;">🔒 Secure</h3>
                <p style="margin:0.5rem 0 0 0; color: #64748b;">
                    Enterprise-grade security with Supabase
                </p>
            </div>
        """, unsafe_allow_html=True)

def main_app():
    """Main Application with Enhanced Sidebar"""
    
    # Enhanced Sidebar
    with st.sidebar:
        st.markdown("""
            <div style="text-align: center; padding: 1rem 0;">
                <h1 style="color: white; margin:0; font-size: 2rem;">🤖 DocuAI</h1>
                <p style="color: rgba(255,255,255,0.7); margin:0.5rem 0 0 0; font-size: 0.9rem;">
                    AI-Powered Processing
                </p>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # User info card
        st.markdown(f"""
            <div style="background: rgba(255,255,255,0.1); padding: 1rem; border-radius: 10px; margin-bottom: 1.5rem;">
                <p style="color: rgba(255,255,255,0.6); margin:0; font-size: 0.85rem;">Logged in as</p>
                <p style="color: white; margin:0.3rem 0 0 0; font-weight: 600;">
                    👤 {st.session_state.user.get('full_name', st.session_state.user['email'])}
                </p>
                <p style="color: rgba(255,255,255,0.8); margin:0.2rem 0 0 0; font-size: 0.85rem;">
                    {st.session_state.user['email']}
                </p>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("### 📍 Navigation")
        page = st.radio(
            "Select Page",
            ["📤 Upload Document", "📊 Document History", "⚙️ Settings"],
            label_visibility="collapsed"
        )
        
        st.markdown("<br><br>", unsafe_allow_html=True)
        
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.token = None
            st.session_state.user = None
            st.rerun()
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("""
            <div style="text-align: center; color: rgba(255,255,255,0.5); font-size: 0.75rem;">
                <p>Powered by CrewAI & Azure</p>
                <p>© 2025 DocuAI</p>
            </div>
        """, unsafe_allow_html=True)
    
    # Main content routing
    if page == "📤 Upload Document":
        upload_page()
    elif page == "📊 Document History":
        history_page()
    elif page == "⚙️ Settings":
        settings_page()

def upload_page():
    """Upload and Process Document with Enhanced UI"""
    
    # Page header
    st.markdown("""
        <h1 style="color: #1e293b; margin-bottom: 0.5rem;">📤 Upload & Process Document</h1>
        <p style="color: #64748b; margin-bottom: 2rem;">Upload your invoice, receipt, or purchase order for AI-powered extraction</p>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1], gap="large")
    
    with col1:
        # Upload section with enhanced styling
        st.markdown("""
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                        padding: 1.5rem; border-radius: 15px; margin-bottom: 1.5rem;">
                <h3 style="color: white; margin: 0;">📁 Select Your Document</h3>
                <p style="color: rgba(255,255,255,0.9); margin: 0.5rem 0 0 0; font-size: 0.95rem;">
                    Drag and drop or click to browse
                </p>
            </div>
        """, unsafe_allow_html=True)
        
        uploaded_file = st.file_uploader(
            "Choose a document",
            type=['pdf', 'png', 'jpg', 'jpeg'],
            label_visibility="collapsed"
        )
        
        if uploaded_file:
            # File info card
            file_size_kb = uploaded_file.size / 1024
            file_size_mb = file_size_kb / 1024
            
            st.markdown(f"""
                <div style="background: #f0fdf4; border-left: 4px solid #10b981; 
                            padding: 1.5rem; border-radius: 10px; margin: 1rem 0;">
                    <h4 style="color: #059669; margin: 0;">✅ File Ready</h4>
                    <p style="margin: 0.8rem 0 0 0; color: #064e3b;">
                        <strong>📄 Name:</strong> {uploaded_file.name}<br>
                        <strong>📊 Size:</strong> {file_size_mb:.2f} MB ({file_size_kb:.1f} KB)<br>
                        <strong>📝 Type:</strong> {uploaded_file.type}
                    </p>
                </div>
            """, unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Process button (moved outside columns to avoid nesting error)
            if st.button("🚀 Process with AI Agents", type="primary", use_container_width=True):
                # Upload phase
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                status_text.markdown("**📤 Uploading document...**")
                progress_bar.progress(20)
                
                files = {'file': (uploaded_file.name, uploaded_file.getvalue())}
                response = api_request("POST", "/documents/upload", files=files)
                
                if response.status_code == 200:
                    doc_data = response.json()
                    progress_bar.progress(40)
                    status_text.markdown("**✅ Upload successful!**")
                    
                    # Processing phase
                    status_text.markdown("**🤖 AI Agents analyzing document...**")
                    progress_bar.progress(60)
                    
                    process_response = api_request("POST", "/documents/process?auto_approve=true", {
                        "document_id": doc_data['id']
                    })
                    
                    progress_bar.progress(90)
                    
                    if process_response.status_code == 200:
                        result = process_response.json()
                        progress_bar.progress(100)
                        status_text.markdown("**✨ Processing complete!**")
                        
                        st.success("🎉 Document processed successfully!")
                        st.balloons()
                        
                        # Debug: Show raw response
                        with st.expander("🔍 Debug: Raw API Response"):
                            st.json(result)
                        
                        # Display results
                        st.markdown("<br>", unsafe_allow_html=True)
                        st.markdown("""
                            <h2 style="color: #1e293b; border-bottom: 3px solid #6366f1; 
                                       padding-bottom: 0.5rem; margin-bottom: 1.5rem;">
                                📋 Extraction Results
                            </h2>
                        """, unsafe_allow_html=True)
                        
                        # Safely access data with fallbacks
                        data = result.get('result_data', {})
                        doc_type = result.get('document_type', 'unknown')
                        
                        # Key metrics with enhanced cards
                        col_a, col_b, col_c = st.columns(3)
                        
                        with col_a:
                            st.markdown(f"""
                                <div class="metric-card" style="text-align: center;">
                                    <p style="color: #64748b; margin: 0; font-size: 0.9rem;">Document Type</p>
                                    <h2 style="color: #6366f1; margin: 0.5rem 0; font-size: 1.8rem;">
                                        {doc_type.upper()}
                                    </h2>
                                    <p style="margin: 0;">📄</p>
                                </div>
                            """, unsafe_allow_html=True)
                        
                        with col_b:
                            amount = data.get('total_amount', 0)
                            if amount is None:
                                amount = 0
                            st.markdown(f"""
                                <div class="metric-card" style="text-align: center;">
                                    <p style="color: #64748b; margin: 0; font-size: 0.9rem;">Total Amount</p>
                                    <h2 style="color: #10b981; margin: 0.5rem 0; font-size: 1.8rem;">
                                        ${amount:.2f}
                                    </h2>
                                    <p style="margin: 0;">💰</p>
                                </div>
                            """, unsafe_allow_html=True)
                        
                        with col_c:
                            confidence = data.get('confidence_score', 0)
                            if confidence is None:
                                confidence = 0
                            confidence_pct = confidence * 100
                            st.markdown(f"""
                                <div class="metric-card" style="text-align: center;">
                                    <p style="color: #64748b; margin: 0; font-size: 0.9rem;">Confidence</p>
                                    <h2 style="color: #8b5cf6; margin: 0.5rem 0; font-size: 1.8rem;">
                                        {confidence_pct:.1f}%
                                    </h2>
                                    <p style="margin: 0;">🎯</p>
                                </div>
                            """, unsafe_allow_html=True)
                        
                        st.markdown("<br>", unsafe_allow_html=True)
                        
                        # Vendor information
                        vendor = data.get('vendor', {})
                        if not vendor or vendor == {}:
                            vendor = {
                                'name': data.get('vendor_name', 'N/A'),
                                'address': data.get('vendor_address', 'N/A'),
                                'phone': data.get('vendor_phone', 'N/A')
                            }
                        
                        vendor_name = vendor.get('name') or data.get('vendor_name') or 'N/A'
                        vendor_address = vendor.get('address') or data.get('vendor_address') or 'N/A'
                        vendor_phone = vendor.get('phone') or data.get('vendor_phone') or data.get('phone') or 'N/A'
                        
                        st.markdown("""
                            <h3 style="color: #1e293b; margin-top: 2rem;">🏢 Vendor Information</h3>
                        """, unsafe_allow_html=True)
                        
                        st.markdown(f"""
                            <div class="metric-card">
                                <p><strong style="color: #6366f1;">Company Name:</strong> {vendor_name}</p>
                                <p><strong style="color: #6366f1;">Address:</strong> {vendor_address}</p>
                                <p><strong style="color: #6366f1;">Contact:</strong> {vendor_phone}</p>
                            </div>
                        """, unsafe_allow_html=True)
                        
                        # Line items
                        line_items = data.get('line_items', []) or data.get('items', [])
                        
                        if line_items and len(line_items) > 0:
                            st.markdown("<br>", unsafe_allow_html=True)
                            st.markdown("""
                                <h3 style="color: #1e293b;">🛒 Line Items</h3>
                            """, unsafe_allow_html=True)
                            
                            for idx, item in enumerate(line_items, 1):
                                description = item.get('description') or item.get('item_description') or item.get('name') or 'N/A'
                                quantity = item.get('quantity') or item.get('qty') or 0
                                unit_price = item.get('unit_price') or item.get('price') or item.get('rate') or 0
                                total = item.get('total') or item.get('amount') or (quantity * unit_price)
                                
                                st.markdown(f"""
                                    <div class="metric-card" style="margin-bottom: 0.8rem;">
                                        <strong style="color: #6366f1;">Item {idx}:</strong> {description}<br>
                                        <span style="color: #64748b;">
                                            Quantity: {quantity} × ${unit_price:.2f} = 
                                            <strong style="color: #10b981;">${total:.2f}</strong>
                                        </span>
                                    </div>
                                """, unsafe_allow_html=True)
                        else:
                            st.markdown("<br>", unsafe_allow_html=True)
                            st.info("ℹ️ No line items found in this document")
                        
                        # Full JSON data
                        st.markdown("<br>", unsafe_allow_html=True)
                        with st.expander("🔍 View Complete Extraction Data (JSON)"):
                            st.json(data)
                    else:
                        progress_bar.empty()
                        status_text.empty()
                        try:
                            error_msg = process_response.json().get('detail', 'Unknown error')
                        except:
                            error_msg = process_response.text if process_response.text else f"Error {process_response.status_code}"
                        st.error(f"❌ Processing failed: {error_msg}")
                else:
                    progress_bar.empty()
                    status_text.empty()
                    try:
                        error_msg = response.json().get('detail', 'Unknown error')
                    except:
                        error_msg = response.text if response.text else f"Error {response.status_code}"
                    st.error(f"❌ Upload failed: {error_msg}")
    
    with col2:
        # Info panel
        st.markdown("""
            <div style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); 
                        padding: 1.5rem; border-radius: 15px; color: white; margin-bottom: 1rem;">
                <h3 style="margin: 0;">ℹ️ Quick Info</h3>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
            <div class="metric-card">
                <h4 style="color: #6366f1; margin-top: 0;">📄 Supported Documents</h4>
                <ul style="color: #1e293b; line-height: 1.8;">
                    <li><strong>Invoices</strong> - Sales & purchase invoices</li>
                    <li><strong>Receipts</strong> - Payment receipts</li>
                    <li><strong>Purchase Orders</strong> - PO documents</li>
                </ul>
            </div>
        """, unsafe_allow_html=True)

def history_page():
    """Document History with Enhanced UI"""
    
    st.markdown("""
        <h1 style="color: #1e293b; margin-bottom: 0.5rem;">📊 Document Processing History</h1>
        <p style="color: #64748b; margin-bottom: 2rem;">View all your processed documents and their results</p>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([3, 1, 1])
    with col3:
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()
    
    with st.spinner("📂 Loading your documents..."):
        response = api_request("GET", "/documents/history?limit=50")
        
        if response.status_code == 200:
            documents = response.json()
            
            if documents:
                # Summary stats
                total_docs = len(documents)
                total_amount = sum(doc.get('amount', 0) for doc in documents if doc.get('amount'))
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.markdown(f"""
                        <div class="metric-card" style="text-align: center;">
                            <p style="color: #64748b; margin: 0; font-size: 0.85rem;">Total Documents</p>
                            <h2 style="color: #6366f1; margin: 0.5rem 0;">{total_docs}</h2>
                            <p style="margin: 0;">📄</p>
                        </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    st.markdown(f"""
                        <div class="metric-card" style="text-align: center;">
                            <p style="color: #64748b; margin: 0; font-size: 0.85rem;">Total Value</p>
                            <h2 style="color: #10b981; margin: 0.5rem 0;">${total_amount:.2f}</h2>
                            <p style="margin: 0;">💰</p>
                        </div>
                    """, unsafe_allow_html=True)
                
                with col3:
                    completed = sum(1 for doc in documents if doc['status'] == 'completed')
                    st.markdown(f"""
                        <div class="metric-card" style="text-align: center;">
                            <p style="color: #64748b; margin: 0; font-size: 0.85rem;">Completed</p>
                            <h2 style="color: #8b5cf6; margin: 0.5rem 0;">{completed}</h2>
                            <p style="margin: 0;">✅</p>
                        </div>
                    """, unsafe_allow_html=True)
                
                with col4:
                    pending = sum(1 for doc in documents if doc['status'] in ['pending', 'processing'])
                    st.markdown(f"""
                        <div class="metric-card" style="text-align: center;">
                            <p style="color: #64748b; margin: 0; font-size: 0.85rem;">Pending</p>
                            <h2 style="color: #f59e0b; margin: 0.5rem 0;">{pending}</h2>
                            <p style="margin: 0;">⏳</p>
                        </div>
                    """, unsafe_allow_html=True)
                
                st.markdown("<br><br>", unsafe_allow_html=True)
                
                # Documents list
                for doc in documents:
                    # Status badge color
                    status_colors = {
                        'completed': '#10b981',
                        'processing': '#f59e0b',
                        'pending': '#64748b',
                        'failed': '#ef4444'
                    }
                    status_color = status_colors.get(doc['status'], '#64748b')
                    
                    # Document type icon
                    type_icons = {
                        'invoice': '📄',
                        'receipt': '🧾',
                        'purchase_order': '📦'
                    }
                    doc_type = doc.get('document_type') or ''
                    doc_icon = type_icons.get(doc_type.lower() if doc_type else '', '📄')
                    
                    with st.expander(
                        f"{doc_icon} **{doc['filename']}** - " + 
                        f"<span style='color: {status_color};'>●</span> {doc['status'].upper()}",
                        expanded=False
                    ):
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            doc_type_display = (doc.get('document_type') or 'Unknown').upper()
                            st.markdown(f"""
                                <div class="metric-card">
                                    <p style="color: #64748b; margin: 0; font-size: 0.85rem;">Document Info</p>
                                    <p style="margin: 0.5rem 0 0 0;">
                                        <strong>Type:</strong> {doc_type_display}<br>
                                        <strong>Status:</strong> <span style="color: {status_color};">{doc['status'].upper()}</span>
                                    </p>
                                </div>
                            """, unsafe_allow_html=True)
                        
                        with col2:
                            st.markdown(f"""
                                <div class="metric-card">
                                    <p style="color: #64748b; margin: 0; font-size: 0.85rem;">Financial Details</p>
                                    <p style="margin: 0.5rem 0 0 0;">
                                        <strong>Amount:</strong> <span style="color: #10b981;">${doc.get('amount', 0):.2f}</span><br>
                                        <strong>Vendor:</strong> {doc.get('vendor', 'N/A')}
                                    </p>
                                </div>
                            """, unsafe_allow_html=True)
                        
                        with col3:
                            upload_date = doc['upload_timestamp'][:10] if doc.get('upload_timestamp') else 'N/A'
                            st.markdown(f"""
                                <div class="metric-card">
                                    <p style="color: #64748b; margin: 0; font-size: 0.85rem;">Dates</p>
                                    <p style="margin: 0.5rem 0 0 0;">
                                        <strong>Uploaded:</strong> {upload_date}<br>
                                        <strong>ID:</strong> <code style="font-size: 0.75rem;">{doc['id'][:8]}...</code>
                                    </p>
                                </div>
                            """, unsafe_allow_html=True)
                        
                        st.markdown("<br>", unsafe_allow_html=True)
                        
                        if st.button(f"🔍 View Full Details", key=f"view_{doc['id']}", use_container_width=True):
                            with st.spinner("Loading details..."):
                                detail_response = api_request("GET", f"/documents/{doc['id']}/result")
                                if detail_response.status_code == 200:
                                    result_data = detail_response.json()
                                    
                                    st.markdown("<br>", unsafe_allow_html=True)
                                    st.markdown("""
                                        <h3 style="color: #6366f1; border-bottom: 2px solid #e2e8f0; 
                                                   padding-bottom: 0.5rem; margin-bottom: 1rem;">
                                            📋 Complete Extraction Details
                                        </h3>
                                    """, unsafe_allow_html=True)
                                    
                                    # Get the extraction data
                                    data = result_data.get('result_data', {})
                                    
                                    # Debug: Show the actual data structure
                                    st.markdown("""
                                        <div style="background: #fef3c7; padding: 1rem; border-radius: 8px; margin-bottom: 1rem;">
                                            <strong>🐛 Debug Info:</strong> Expand "Show Raw JSON" below to see the actual data structure
                                        </div>
                                    """, unsafe_allow_html=True)
                                    
                                    # Key Metrics Row
                                    metric_col1, metric_col2, metric_col3 = st.columns(3)
                                    
                                    with metric_col1:
                                        doc_type = result_data.get('document_type', 'unknown')
                                        st.markdown(f"""
                                            <div class="metric-card" style="text-align: center;">
                                                <p style="color: #64748b; margin: 0; font-size: 0.85rem;">Document Type</p>
                                                <h3 style="color: #6366f1; margin: 0.5rem 0;">{doc_type.upper()}</h3>
                                                <p style="margin: 0;">📄</p>
                                            </div>
                                        """, unsafe_allow_html=True)
                                    
                                    with metric_col2:
                                        total_amt = data.get('total_amount', 0) or 0
                                        st.markdown(f"""
                                            <div class="metric-card" style="text-align: center;">
                                                <p style="color: #64748b; margin: 0; font-size: 0.85rem;">Total Amount</p>
                                                <h3 style="color: #10b981; margin: 0.5rem 0;">${total_amt:.2f}</h3>
                                                <p style="margin: 0;">💰</p>
                                            </div>
                                        """, unsafe_allow_html=True)
                                    
                                    with metric_col3:
                                        confidence = (data.get('confidence_score', 0) or 0) * 100
                                        st.markdown(f"""
                                            <div class="metric-card" style="text-align: center;">
                                                <p style="color: #64748b; margin: 0; font-size: 0.85rem;">Confidence Score</p>
                                                <h3 style="color: #8b5cf6; margin: 0.5rem 0;">{confidence:.1f}%</h3>
                                                <p style="margin: 0;">🎯</p>
                                            </div>
                                        """, unsafe_allow_html=True)
                                    
                                    st.markdown("<br>", unsafe_allow_html=True)
                                    
                                    # Document Details Section
                                    detail_col1, detail_col2 = st.columns(2)
                                    
                                    with detail_col1:
                                        st.markdown("""
                                            <h4 style="color: #6366f1; margin-bottom: 0.5rem;">🏢 Vendor Information</h4>
                                        """, unsafe_allow_html=True)
                                        
                                        # Try different possible field names for vendor
                                        vendor = data.get('vendor', {})
                                        if not vendor or vendor == {}:
                                            vendor = {
                                                'name': data.get('vendor_name', 'N/A'),
                                                'address': data.get('vendor_address', 'N/A'),
                                                'phone': data.get('vendor_phone', 'N/A')
                                            }
                                        
                                        vendor_name = vendor.get('name') or data.get('vendor_name') or 'N/A'
                                        vendor_address = vendor.get('address') or data.get('vendor_address') or 'N/A'
                                        vendor_phone = vendor.get('phone') or data.get('vendor_phone') or data.get('phone') or 'N/A'
                                        
                                        st.markdown(f"""
                                            <div class="metric-card">
                                                <p style="margin: 0.3rem 0;"><strong style="color: #6366f1;">Company:</strong> {vendor_name}</p>
                                                <p style="margin: 0.3rem 0;"><strong style="color: #6366f1;">Address:</strong> {vendor_address}</p>
                                                <p style="margin: 0.3rem 0;"><strong style="color: #6366f1;">Phone:</strong> {vendor_phone}</p>
                                            </div>
                                        """, unsafe_allow_html=True)
                                    
                                    with detail_col2:
                                        st.markdown("""
                                            <h4 style="color: #6366f1; margin-bottom: 0.5rem;">📅 Document Information</h4>
                                        """, unsafe_allow_html=True)
                                        
                                        invoice_num = data.get('invoice_number', 'N/A')
                                        invoice_date = data.get('invoice_date', 'N/A')
                                        due_date = data.get('due_date', 'N/A')
                                        
                                        st.markdown(f"""
                                            <div class="metric-card">
                                                <p style="margin: 0.3rem 0;"><strong style="color: #6366f1;">Invoice #:</strong> {invoice_num}</p>
                                                <p style="margin: 0.3rem 0;"><strong style="color: #6366f1;">Invoice Date:</strong> {invoice_date}</p>
                                                <p style="margin: 0.3rem 0;"><strong style="color: #6366f1;">Due Date:</strong> {due_date}</p>
                                            </div>
                                        """, unsafe_allow_html=True)
                                    
                                    # Line Items Section
                                    line_items = data.get('line_items', []) or data.get('items', [])
                                    
                                    if line_items and len(line_items) > 0:
                                        st.markdown("<br>", unsafe_allow_html=True)
                                        st.markdown("""
                                            <h4 style="color: #6366f1; margin-bottom: 0.5rem;">🛒 Line Items</h4>
                                        """, unsafe_allow_html=True)
                                        
                                        for idx, item in enumerate(line_items, 1):
                                            description = item.get('description') or item.get('item_description') or item.get('name') or 'N/A'
                                            quantity = item.get('quantity') or item.get('qty') or 0
                                            unit_price = item.get('unit_price') or item.get('price') or item.get('rate') or 0
                                            total = item.get('total') or item.get('amount') or (quantity * unit_price)
                                            
                                            st.markdown(f"""
                                                <div class="metric-card" style="margin-bottom: 0.8rem;">
                                                    <div style="display: flex; justify-content: space-between; align-items: start;">
                                                        <div style="flex: 1;">
                                                            <strong style="color: #6366f1;">Item {idx}:</strong> {description}<br>
                                                            <span style="color: #64748b; font-size: 0.9rem;">
                                                                Qty: {quantity} × ${unit_price:.2f}
                                                            </span>
                                                        </div>
                                                        <div style="text-align: right;">
                                                            <strong style="color: #10b981; font-size: 1.1rem;">${total:.2f}</strong>
                                                        </div>
                                                    </div>
                                                </div>
                                            """, unsafe_allow_html=True)
                                    else:
                                        st.markdown("<br>", unsafe_allow_html=True)
                                        st.info("ℹ️ No line items found in this document")
                                    
                                    # Totals Section
                                    if data.get('subtotal') or data.get('tax_amount'):
                                        st.markdown("<br>", unsafe_allow_html=True)
                                        st.markdown("""
                                            <h4 style="color: #6366f1; margin-bottom: 0.5rem;">💵 Financial Summary</h4>
                                        """, unsafe_allow_html=True)
                                        
                                        subtotal = data.get('subtotal', 0) or 0
                                        tax = data.get('tax_amount', 0) or 0
                                        total = data.get('total_amount', 0) or 0
                                        
                                        st.markdown(f"""
                                            <div class="metric-card">
                                                <div style="display: flex; justify-content: space-between; margin: 0.3rem 0;">
                                                    <span style="color: #64748b;">Subtotal:</span>
                                                    <strong>${subtotal:.2f}</strong>
                                                </div>
                                                <div style="display: flex; justify-content: space-between; margin: 0.3rem 0;">
                                                    <span style="color: #64748b;">Tax:</span>
                                                    <strong>${tax:.2f}</strong>
                                                </div>
                                                <div style="border-top: 2px solid #e2e8f0; margin: 0.5rem 0; padding-top: 0.5rem;">
                                                    <div style="display: flex; justify-content: space-between;">
                                                        <span style="color: #6366f1; font-weight: 600;">Total:</span>
                                                        <strong style="color: #10b981; font-size: 1.2rem;">${total:.2f}</strong>
                                                    </div>
                                                </div>
                                            </div>
                                        """, unsafe_allow_html=True)
                                    
                                    # Raw JSON as text (not nested expander)
                                    st.markdown("<br>", unsafe_allow_html=True)
                                    st.markdown("""
                                        <details>
                                            <summary style="cursor: pointer; color: #6366f1; font-weight: 600; padding: 0.5rem;">
                                                🔍 Click to view Raw JSON Data
                                            </summary>
                                        </details>
                                    """, unsafe_allow_html=True)
                                    if st.checkbox("Show Raw JSON", key=f"json_{doc['id']}"):
                                        st.json(result_data)
                                else:
                                    st.error("❌ Failed to load details")
            else:
                st.markdown("""
                    <div style="text-align: center; padding: 4rem 2rem; background: #f8fafc; 
                                border-radius: 15px; border: 2px dashed #cbd5e1;">
                        <h2 style="color: #64748b;">📭 No Documents Yet</h2>
                        <p style="color: #94a3b8; margin: 1rem 0 2rem 0;">
                            Upload your first document to get started with AI-powered extraction
                        </p>
                    </div>
                """, unsafe_allow_html=True)
        else:
            st.error("❌ Failed to load document history. Please try again.")

def settings_page():
    """Settings Page with Enhanced UI"""
    
    st.markdown("""
        <h1 style="color: #1e293b; margin-bottom: 0.5rem;">⚙️ Settings & Configuration</h1>
        <p style="color: #64748b; margin-bottom: 2rem;">Manage your account and view system information</p>
    """, unsafe_allow_html=True)
    
    # User Profile Section
    st.markdown("""
        <h3 style="color: #6366f1; border-bottom: 2px solid #e2e8f0; padding-bottom: 0.5rem;">
            👤 User Profile
        </h3>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("""
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                        width: 120px; height: 120px; border-radius: 50%; 
                        display: flex; align-items: center; justify-content: center;
                        margin: 1rem auto;">
                <span style="font-size: 4rem;">👤</span>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        user_info = st.session_state.user
        st.markdown(f"""
            <div class="metric-card" style="margin-top: 1rem;">
                <p style="margin: 0;"><strong style="color: #6366f1;">Full Name:</strong> {user_info.get('full_name', 'N/A')}</p>
                <p style="margin: 0.5rem 0;"><strong style="color: #6366f1;">Email:</strong> {user_info['email']}</p>
                <p style="margin: 0.5rem 0;"><strong style="color: #6366f1;">User ID:</strong> <code>{user_info['id']}</code></p>
                <p style="margin: 0.5rem 0 0 0;"><strong style="color: #6366f1;">Member Since:</strong> {user_info.get('created_at', 'N/A')[:10]}</p>
            </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # API Configuration Section
    st.markdown("""
        <h3 style="color: #6366f1; border-bottom: 2px solid #e2e8f0; padding-bottom: 0.5rem;">
            🔗 API Configuration
        </h3>
    """, unsafe_allow_html=True)
    
    st.markdown(f"""
        <div class="metric-card">
            <p style="margin: 0;"><strong style="color: #6366f1;">Backend URL:</strong></p>
            <code style="background: #f1f5f9; padding: 0.5rem 1rem; border-radius: 5px; 
                        display: block; margin-top: 0.5rem; color: #1e293b;">
                {API_BASE_URL}
            </code>
            <p style="margin: 1rem 0 0 0; color: #64748b; font-size: 0.9rem;">
                ✅ Connection status: <strong style="color: #10b981;">Active</strong>
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # System Information
    st.markdown("""
        <h3 style="color: #6366f1; border-bottom: 2px solid #e2e8f0; padding-bottom: 0.5rem;">
            💻 System Information
        </h3>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
            <div class="metric-card">
                <h4 style="color: #6366f1; margin-top: 0;">🤖 AI Technologies</h4>
                <ul style="color: #64748b; line-height: 2;">
                    <li><strong>CrewAI:</strong> Multi-agent orchestration</li>
                    <li><strong>Azure OpenAI:</strong> GPT-4o for classification</li>
                    <li><strong>Azure Document Intelligence:</strong> Data extraction</li>
                    <li><strong>Phoenix:</strong> Tracing & monitoring</li>
                </ul>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
            <div class="metric-card">
                <h4 style="color: #6366f1; margin-top: 0;">🔧 Infrastructure</h4>
                <ul style="color: #64748b; line-height: 2;">
                    <li><strong>Backend:</strong> FastAPI (Python)</li>
                    <li><strong>Database:</strong> Supabase PostgreSQL</li>
                    <li><strong>Storage:</strong> Supabase Storage</li>
                    <li><strong>Frontend:</strong> Streamlit</li>
                </ul>
            </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # Actions
    st.markdown("""
        <h3 style="color: #6366f1; border-bottom: 2px solid #e2e8f0; padding-bottom: 0.5rem;">
            🎯 Quick Actions
        </h3>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📊 View History", use_container_width=True):
            st.session_state.page = "📊 Document History"
            st.rerun()
    
    with col2:
        if st.button("📤 Upload Document", use_container_width=True, type="primary"):
            st.session_state.page = "📤 Upload Document"
            st.rerun()
    
    with col3:
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.rerun()
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # Footer info
    st.markdown("""
        <div style="text-align: center; padding: 2rem; background: #f8fafc; 
                    border-radius: 15px; margin-top: 2rem;">
            <p style="color: #64748b; margin: 0;">
                <strong>DocuAI Platform</strong> v1.0.0
            </p>
            <p style="color: #94a3b8; margin: 0.5rem 0 0 0; font-size: 0.9rem;">
                Powered by AI • Built with ❤️ • © 2025
            </p>
        </div>
    """, unsafe_allow_html=True)

# Main app logic
if st.session_state.token:
    main_app()
else:
    login_page()
