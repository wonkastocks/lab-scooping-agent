import streamlit as st
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from datetime import datetime
import os
from dotenv import load_dotenv

# Set page config - must be the first Streamlit command
st.set_page_config(
    page_title="Lab Scooping Agent",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for styling
st.markdown("""
    <style>
        /* Main header with ACI logo */
        .main-header {
            display: flex;
            align-items: center;
            background-color: #1e40af;
            color: white;
            padding: 0.5rem 2rem;
            margin: -2rem -2rem 2rem -2rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }

        .header-title {
            font-size: 1.5rem;
            font-weight: 600;
            margin: 0;
        }
        
        /* Main background and text colors */
        .stApp {
            background-color: #f8fafc;
            color: #1e293b;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
            font-size: 0.9rem;
            line-height: 1.5;
            padding: 1.5rem;
        }
        
        /* Headers */
        h1 {
            color: #1e40af;
            font-weight: 600;
            font-size: 1.75rem;
            margin: 0 0 1rem 0;
        }
        
        h2 {
            color: #1e40af;
            font-weight: 600;
            font-size: 1.5rem;
            margin: 1.5rem 0 1rem 0;
        }
        
        h3 {
            color: #1e40af;
            font-weight: 600;
            font-size: 1.25rem;
            margin: 1.25rem 0 0.75rem 0;
        }
        
        h4, h5, h6 {
            color: #1e40af;
            font-weight: 600;
            font-size: 1.1rem;
            margin: 1rem 0 0.5rem 0;
        }
        
        /* Buttons */
        .stButton>button {
            background-color: #2563eb;
            color: white;
            border-radius: 6px;
            border: none;
            padding: 0.5rem 1.25rem;
            font-weight: 500;
            font-size: 0.9rem;
            transition: all 0.2s;
        }
        
        .stButton>button:hover {
            background-color: #1d4ed8;
            transform: translateY(-1px);
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        /* Form elements */
        .stTextInput>div>div>input, 
        .stTextArea>div>div>textarea,
        .stSelectbox>div>div>div>div,
        .stNumberInput>div>div>input,
        .stDateInput>div>div>input {
            border: 1px solid #cbd5e1;
            border-radius: 6px;
            padding: 0.5rem 0.75rem;
            font-size: 0.9rem;
        }
        
        /* Form labels */
        label {
            font-size: 0.9rem;
            font-weight: 500;
            margin-bottom: 0.25rem;
            display: block;
        }
        
        /* Cards and containers */
        .stExpander {
            background-color: white;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 1rem;
            margin-bottom: 1rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        }
        
        /* Adjust expander header */
        .stExpander .st-emotion-cache-sh2krr p {
            font-size: 1rem;
            margin: 0;
        }
        
        /* Adjust expander content */
        .stExpander .st-emotion-cache-1p1nwyz {
            padding: 0.75rem 0 0 0;
        }
        
        /* Section headers */
        .stMarkdown h2 {
            color: #1e40af;
            border-bottom: 2px solid #dbeafe;
            padding-bottom: 0.5rem;
            margin: 1.25rem 0 0.75rem 0;
            font-size: 1.4rem;
        }
        
        /* Tables */
        table {
            border-collapse: separate;
            border-spacing: 0;
            width: 100%;
            border-radius: 8px;
            overflow: hidden;
            font-size: 0.85rem;
        }
        
        th, td {
            border: 1px solid #e2e8f0;
            padding: 0.5rem 0.75rem;
            text-align: left;
            line-height: 1.4;
        }
        
        th {
            background-color: #eff6ff;
            color: #1e40af;
            font-weight: 600;
            font-size: 0.9rem;
        }
        
        /* Custom classes */
        .highlight-box {
            background-color: #eff6ff;
            border-left: 4px solid #3b82f6;
            padding: 1rem;
            margin: 1rem 0;
            border-radius: 0 8px 8px 0;
            color: #1e40af;
            font-size: 0.9rem;
        }
        
        /* Back to Review button */
        .stButton>button[data-testid="baseButton-secondary"] {
            background-color: #2563eb;
            color: white;
            border: none;
        }
        
        .stButton>button[data-testid="baseButton-secondary"]:hover {
            background-color: #1d4ed8;
            color: white;
        }
    </style>
""", unsafe_allow_html=True)

# Load environment variables
load_dotenv()

# MongoDB connection
def get_database():
    MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
    client = MongoClient(
        MONGODB_URI,
        server_api=ServerApi('1'),
        tls=True,
        tlsAllowInvalidCertificates=True,
        retryWrites=True,
        w='majority',
        connectTimeoutMS=30000,
        socketTimeoutMS=30000,
        serverSelectionTimeoutMS=5000
    )
    try:
        client.admin.command('ping')
    except Exception as e:
        st.error(f"MongoDB connection error: {str(e)}")
        raise
    return client["lab_survey"]

def save_responses(responses):
    try:
        db = get_database()
        responses["submitted_at"] = datetime.utcnow()
        result = db.responses.insert_one(responses)
        if result.inserted_id:
            return True
        return False
    except Exception as e:
        st.error(f"Error saving to database: {str(e)}")
        return False

# Contact Page
def contact_page():
    # Add back to review button if coming from review
    if st.session_state.get('from_review', False):
        if st.button("← Back to Review", key="back_to_review_contact", type="primary"):
            st.session_state.page = "review"
            st.rerun()
    
    st.title("Contact Information")
    
    with st.form("contact_form"):
        st.markdown("### Primary Contact")
        
        # Name
        col1, col2 = st.columns(2)
        with col1:
            first_name = st.text_input("First Name*", value="John")
        with col2:
            last_name = st.text_input("Last Name*", value="Doe")
        
        # Contact Info
        email = st.text_input("Email*", value="john.doe@example.com")
        organization = st.text_input("Organization*", value="ACME Corp")
        
        # Organization Type
        org_type = st.selectbox(
            "Type of Organization*",
            ["", "Educational Institution", "Enterprise", "Government", "Non-Profit", "Other"],
            index=2  # Pre-select Enterprise
        )
        
        submitted = st.form_submit_button("Next: Course Request", type="primary")
        
        if submitted:
            if not all([first_name, last_name, email, organization, org_type]):
                st.error("Please fill in all required fields (marked with *)")
            else:
                st.session_state.contact_info = {
                    "first_name": first_name,
                    "last_name": last_name,
                    "email": email,
                    "organization": organization,
                    "org_type": org_type
                }
                st.session_state.from_review = False
                st.session_state.page = "course_request"
                st.rerun()

# Course Request Page
def course_request_page():
    # Add back to review button if coming from review
    if st.session_state.get('from_review', False):
        if st.button("← Back to Review", key="back_to_review_course", type="primary"):
            st.session_state.page = "review"
            st.rerun()
    
    st.title("Course Request")
    
    with st.form("course_form"):
        st.markdown("### Course Details")
        
        course_name = st.text_input("Course Name*", value="Advanced Cloud Infrastructure")
        
        col1, col2 = st.columns(2)
        with col1:
            duration_options = ["", "3 months", "6 months", "9 months", "12 months", "18 months", "24 months", "Custom"]
            course_duration = st.selectbox(
                "Course Duration*",
                duration_options,
                index=4  # Pre-select 12 months
            )
            
            # If Custom is selected, show a text input for custom duration
            if course_duration == "Custom":
                custom_duration = st.text_input(
                    "Specify custom duration (e.g., '2 weeks', '1 month', etc.)*",
                    value="6 weeks"
                )
                if custom_duration:
                    course_duration = f"Custom: {custom_duration}"
        with col2:
            num_labs = st.number_input("Number of Labs*", min_value=1, step=1, value=3)
        
        developer = st.radio(
            "Who will develop the labs?*",
            ["ACI", "Customer SME", "Joint Development"],
            index=0  # Pre-select ACI
        )
        
        description = st.text_area(
            "Brief Description of Course*",
            value="This course covers advanced cloud infrastructure concepts including virtualization, networking, and security."
        )
        
        st.markdown("### Learning Objectives")
        certification = st.checkbox("Certification Support", value=True)
        hands_on = st.checkbox("Hands-On Exercises", value=True)
        assessment = st.checkbox("Assessment/Testing", value=True)
        other_objectives = st.text_input(
            "Other Objectives (please specify)",
            value="Real-world scenario based labs"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            submitted = st.form_submit_button("Next: Lab Details", type="primary")
        
        if submitted:
            if not all([course_name, course_duration, developer, description]):
                st.error("Please fill in all required fields (marked with *)")
            elif not any([certification, hands_on, assessment, other_objectives]):
                st.error("Please select at least one learning objective")
            else:
                st.session_state.course_info = {
                    "course_name": course_name,
                    "course_duration": course_duration,
                    "num_labs": num_labs,
                    "developer": developer,
                    "description": description,
                    "objectives": {
                        "certification": certification,
                        "hands_on": hands_on,
                        "assessment": assessment,
                        "other": other_objectives if other_objectives else None
                    },
                    "labs": [{} for _ in range(num_labs)]
                }
                st.session_state.from_review = False
                st.session_state.page = "lab_details"
                st.session_state.current_lab = 1
                st.rerun()

# Lab Details Page
def lab_details_page():
    # Add back to review button if coming from review
    if st.session_state.get('from_review', False):
        if st.button("← Back to Review", key="back_to_review_lab", type="primary"):
            st.session_state.page = "review"
            st.rerun()
    
    num_labs = st.session_state.course_info["num_labs"]
    
    # Main form container with title
    with st.container():
        st.title(f"Lab Configuration ({st.session_state.current_lab} of {num_labs})")
        st.markdown("*Complete the details for this lab below*")
        
        # Regular form elements
        lab_name = st.text_input(
            f"Name of Lab {st.session_state.current_lab}*",
            value=f"Lab {st.session_state.current_lab}: Cloud Infrastructure Setup",
            key=f"lab_name_{st.session_state.current_lab}"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            lab_type = st.radio(
                "Type of Lab*",
                ["Instructional", "Self-Paced"],
                index=0,  # Pre-select Instructional
                key=f"lab_type_{st.session_state.current_lab}"
            )
        with col2:
            persistence = st.radio(
                "Persistence*",
                ["Non-Persistent (Default, Fresh instance each time)", "Persistent (Work saved)"],
                index=0,  # Default to Non-Persistent
                key=f"persistence_{st.session_state.current_lab}"
            )
        
        if "Persistent" in persistence:
            duration = st.session_state.course_info["course_duration"]
            st.info(f"Lab will be persistent for the course duration: {duration}")
        
        complexity = st.selectbox(
            "Complexity Level*",
            options=["", "Beginner", "Intermediate", "Advanced"],
            index=2,  # Pre-select Intermediate
            key=f"complexity_{st.session_state.current_lab}"
        )
        
        # Set default completion date to 30 days from now
        from datetime import datetime, timedelta
        default_date = datetime.now() + timedelta(days=30)
        completion_date = st.date_input(
            "Requested Completion Date*",
            value=default_date,
            key=f"completion_date_{st.session_state.current_lab}"
        )
        
        # VM Configuration Section - Collapsible
        with st.expander("### Virtual Machine Configurations", expanded=True):
            # Initialize num_vms in session state if not exists
            if 'num_vms' not in st.session_state:
                st.session_state.num_vms = 2  # Default to 2 VMs
            
            # Number input for VM count
            col1, col2 = st.columns([3, 1])
            with col1:
                new_num_vms = st.number_input(
                    "Number of VMs Required*",
                    min_value=1,
                    max_value=20,
                    step=1,
                    value=st.session_state.num_vms,
                    key="num_vms_input",
                    help="Hit 'Update' at the bottom to change the number of VMs required for this lab"
                )
            
            # Update the VM count if changed
            if new_num_vms != st.session_state.num_vms:
                st.session_state.num_vms = new_num_vms
                st.rerun()
            
            # Add a note about the auto-update
            st.markdown("**<span style='font-size: 14px;'>The number of VMs will change after you press the update button below</span>**", unsafe_allow_html=True)
            
            # Store VM details for this lab
            vms = []
            
            # Default VM configurations
            default_vms = [
                {
                    "os": "Ubuntu 20.04",
                    "role": "Web Server",
                    "cpus": 2,
                    "ram": 4,
                    "drives": [50],
                    "network_type": "NAT"
                },
                {
                    "os": "Windows Server 2019",
                    "role": "Database Server",
                    "cpus": 4,
                    "ram": 8,
                    "drives": [100, 50],
                    "network_type": "Bridged"
                }
            ]
            
            # Display all VM configurations
            st.markdown("---")  # Visual separator
            for i in range(1, st.session_state.num_vms + 1):
                # Add a visual separator between VMs
                if i > 1:
                    st.markdown("---")
                
                st.markdown(f"#### VM {i} Configuration")
                
                # Get default values if available
                default_vm = default_vms[i-1] if i <= len(default_vms) else {
                    "os": "Ubuntu 20.04",
                    "role": "",
                    "cpus": 2,
                    "ram": 4,
                    "drives": [50],
                    "network_type": "NAT"
                }
                
                # VM Details
                col1, col2 = st.columns(2)
                with col1:
                    os = st.selectbox(
                        f"Operating System (VM {i})*",
                        ["", "Windows 10", "Windows Server 2019", "Ubuntu 20.04", "CentOS 8", "Other"],
                        index=["", "Windows 10", "Windows Server 2019", "Ubuntu 20.04", "CentOS 8", "Other"].index(default_vm["os"]) if default_vm["os"] in ["", "Windows 10", "Windows Server 2019", "Ubuntu 20.04", "CentOS 8", "Other"] else 0,
                        key=f"os_{i}"
                    )
                with col2:
                    role = st.text_input(
                        f"Role (e.g., Web Server, Database) (VM {i})*",
                        value=default_vm["role"],
                        key=f"role_{i}"
                    )
                
                # Resources
                col1, col2 = st.columns(2)
                with col1:
                    cpus = st.number_input(
                        f"Number of vCPUs (VM {i})*",
                        min_value=1,
                        value=default_vm["cpus"],
                        step=1,
                        key=f"cpus_{i}"
                    )
                with col2:
                    ram = st.number_input(
                        f"RAM (GB) (VM {i})*",
                        min_value=1,
                        value=default_vm["ram"],
                        step=1,
                        key=f"ram_{i}"
                    )
                
                # Storage
                st.markdown("**Storage Configuration**")
                num_drives = st.number_input(
                    f"Number of Hard Drives (VM {i})*",
                    min_value=1,
                    value=len(default_vm["drives"]),
                    step=1,
                    key=f"num_drives_{i}"
                )
                
                # Dynamic drive size inputs
                drive_sizes = []
                for j in range(1, num_drives + 1):
                    default_size = default_vm["drives"][j-1] if j <= len(default_vm["drives"]) else 50
                    drive_size = st.number_input(
                        f"  - Drive {j} Size (GB) (VM {i})*",
                        min_value=10,
                        value=default_size,
                        step=10,
                        key=f"drive_{i}_{j}_size"
                    )
                    drive_sizes.append(drive_size)
                
                # Network
                st.markdown("**Network Configuration**")
                network_type = st.selectbox(
                    f"Network Type (VM {i})*",
                    ["NAT", "Bridged", "Host-only", "Internal"],
                    index=["NAT", "Bridged", "Host-only", "Internal"].index(default_vm["network_type"]) if default_vm["network_type"] in ["NAT", "Bridged", "Host-only", "Internal"] else 0,
                    key=f"vm_network_type_{i}"  # Changed key to be more specific
                )
                
                # Add VM to list
                vms.append({
                    "os": os,
                    "role": role,
                    "cpus": cpus,
                    "ram": ram,
                    "drives": drive_sizes,
                    "network_type": network_type
                })
        
        # Network Requirements (outside VM expander)
        st.markdown("### Network Requirements")
        network_type = st.radio(
            "Network Type*",
            ["Stand-Alone", "Server/Client", "Peer-to-Peer", "Domain"],
            key=f"lab_network_type_{st.session_state.current_lab}"  # Changed key to be more specific
        )
        
        num_subnets = st.number_input(
            "Number of Subnets*",
            min_value=1,
            value=1,
            step=1,
            key=f"num_subnets_{st.session_state.current_lab}"
        )
        
        internet_access = st.checkbox("Internet Access Required")
        
        # Other Requirements
        st.markdown("### Other Requirements")
        special_requirements = st.text_area(
            "Any specialized requirements not listed above"
        )
        
    # Navigation buttons
    col1, col2, col3 = st.columns([1, 1, 1])
    
    # Check if all required VM fields are filled
    all_vms_filled = all([
        lab_name,
        completion_date,
        all([vm.get('os') for vm in vms])  # Check if all VMs have an OS selected
    ])
    
    # Helper function to save lab info
    def save_lab_info():
        return {
            "lab_name": lab_name,
            "lab_type": lab_type,
            "persistence": persistence,
            "complexity": complexity,
            "completion_date": completion_date.isoformat(),
            "vms": vms,
            "network_type": network_type,
            "num_subnets": num_subnets,
            "internet_access": internet_access,
            "special_requirements": special_requirements if special_requirements else None
        }
    
    # Previous/Back button
    with col1:
        if st.session_state.get('from_review', False):
            if st.button("← Back to Review", type="secondary"):
                st.session_state.page = "review"
                st.rerun()
        else:
            if st.button("Previous"):
                st.session_state.page = "course_request"
                st.rerun()
    
    # Update button
    with col2:
        if st.button("Update"):
            # Save current lab details without moving to the next page
            lab_info = save_lab_info()
            
            # Update the current lab in the session state
            lab_index = st.session_state.current_lab - 1
            if len(st.session_state.course_info["labs"]) > lab_index:
                st.session_state.course_info["labs"][lab_index] = lab_info
            else:
                st.session_state.course_info["labs"].append(lab_info)
            
            st.rerun()
    
    # Next/Review button with lab counter
    with col3:
        # Create a container for the button and counter
        button_col, counter_col = st.columns([5, 2])
        
        with button_col:
            next_button_text = "Next" if st.session_state.current_lab < num_labs else "Review"
            if all_vms_filled:
                if st.button(next_button_text, type="primary", use_container_width=True):
                    # Save current lab details
                    lab_info = save_lab_info()
                    
                    # Update or add to labs list
                    lab_index = st.session_state.current_lab - 1
                    if len(st.session_state.course_info["labs"]) > lab_index:
                        st.session_state.course_info["labs"][lab_index] = lab_info
                    else:
                        st.session_state.course_info["labs"].append(lab_info)
                    
                    # Move to next lab or to review
                    if st.session_state.current_lab < num_labs:
                        st.session_state.current_lab += 1
                    else:
                        st.session_state.from_review = False
                        st.session_state.page = "review"
                    st.rerun()
            else:
                if st.button(next_button_text, disabled=True, use_container_width=True):
                    pass  # Disabled button
                st.warning("Please complete all required fields")
        
        # Add the lab counter (e.g., "2/3" or "3/3")
        with counter_col:
            st.markdown(
                f"<div style='height: 38px; display: flex; align-items: center; justify-content: center; background: #f0f2f6; border-radius: 0.5rem;'>"
                f"<span style='font-size: 0.9rem; font-weight: 600; color: #4b5563;'>{st.session_state.current_lab} of {num_labs}</span>"
                f"</div>",
                unsafe_allow_html=True
            )

# Review Page
def review_page():
    st.title("Review Your Submission")
    
    # Contact Information Section
    col1, col2 = st.columns([5, 1])
    with col1:
        st.markdown("## 👤 Contact Information")
    with col2:
        st.write("")
        if st.button("✏️ Edit", key="edit_contact_btn"):
            st.session_state.page = "contact"
            st.session_state.from_review = True
            st.rerun()
    
    contact = st.session_state.contact_info
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Name**")
        st.write(f"{contact['first_name']} {contact['last_name']}")
        
        st.markdown("**Email**")
        st.write(contact['email'])
    
    with col2:
        st.markdown("**Organization**")
        st.write(contact['organization'])
        
        st.markdown("**Organization Type**")
        st.write(contact['org_type'])
    
    st.markdown("---")
    
    # Course Information Section
    col1, col2 = st.columns([5, 1])
    with col1:
        st.markdown("## 📚 Course Information")
    with col2:
        st.write("")
        if st.button("✏️ Edit", key="edit_course_btn"):
            st.session_state.page = "course_request"
            st.session_state.from_review = True
            st.rerun()
    
    course = st.session_state.course_info
    objectives = course["objectives"]
    
    st.markdown(f"**Course Name:** {course['course_name']}")
    st.markdown(f"**Duration:** {course['course_duration']}")
    st.markdown(f"**Developer:** {course['developer']}")
    
    st.markdown("**Learning Objectives:**")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"- Certification Support: {'✅' if objectives.get('certification') else '❌'}")
        st.markdown(f"- Hands-On Exercises: {'✅' if objectives.get('hands_on') else '❌'}")
    with col2:
        st.markdown(f"- Assessment/Testing: {'✅' if objectives.get('assessment') else '❌'}")
        if objectives.get('other'):
            st.markdown(f"- {objectives['other']}")
    
    st.markdown("---")
    
    # Lab Details Section
    col1, col2 = st.columns([5, 1])
    with col1:
        st.markdown("## 🔬 Lab Details")
    with col2:
        st.write("")
        if st.button("✏️ Edit", key="edit_labs_btn"):
            st.session_state.page = "lab_details"
            st.session_state.current_lab = 1
            st.session_state.from_review = True
            st.rerun()
    
    for i, lab in enumerate(course["labs"], 1):
        with st.expander(f"🔍 Lab {i}: {lab.get('lab_name', 'Unnamed Lab')}", expanded=False):
            # Lab Info
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown("**Type**")
                st.write(lab.get('lab_type', 'N/A'))
            with col2:
                st.markdown("**Persistence**")
                st.write(lab.get('persistence', 'N/A'))
            with col3:
                st.markdown("**Complexity**")
                st.write(lab.get('complexity', 'N/A'))
            
            st.markdown("**Requested Completion:**")
            st.write(lab.get('completion_date', 'Not specified'))
            
            # VMs Section
            st.markdown("**Virtual Machines:**")
            for j, vm in enumerate(lab.get('vms', []), 1):
                with st.container():
                    st.markdown(f"**VM {j}:** {vm.get('role', 'Unspecified Role')}")
                    
                    col1, col2 = st.columns([1, 2])
                    with col1:
                        st.markdown(f"- **OS:** {vm.get('os', 'N/A')}")
                        st.markdown(f"- **CPUs:** {vm.get('cpus', 'N/A')}")
                        st.markdown(f"- **RAM:** {vm.get('ram', 'N/A')} GB")
                    with col2:
                        drives = ', '.join([f"{d}GB" for d in vm.get('drives', [])]) or 'N/A'
                        st.markdown(f"- **Storage:** {drives}")
                        st.markdown(f"- **Network:** {vm.get('network_type', 'N/A')}")
                
                if j < len(lab.get('vms', [])):
                    st.markdown("---")
    
    # Submit Form
    st.markdown("---")
    if st.button("✅ Submit Request", type="primary", use_container_width=True):
        # Combine all data
        submission = {
            "contact_info": st.session_state.contact_info,
            "course_info": st.session_state.course_info,
            "submitted_at": datetime.utcnow()
        }
        
        # Save to database
        if save_responses(submission):
            st.session_state.page = "confirmation"
            st.rerun()
        else:
            st.error("Failed to save submission. Please try again.")

# Confirmation Page
def confirmation_page():
    st.title("Thank You!")
    st.balloons()
    st.success("Your lab request has been submitted successfully.")
    st.info("Our team will review your request and get back to you soon.")
    
    if st.button("Start New Request"):
        # Reset the session state
        st.session_state.clear()
        st.session_state.page = "contact"
        st.rerun()

# Initialize Session State
def initialize_session_state():
    if "page" not in st.session_state:
        st.session_state.page = "contact"
    
    # Initialize empty dictionaries for form data
    if "contact_info" not in st.session_state:
        st.session_state.contact_info = {}
    
    if "course_info" not in st.session_state:
        st.session_state.course_info = {}

# Main App
def main():
    # Initialize session state
    initialize_session_state()
    
    # Hide Streamlit menu and footer
    hide_streamlit_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .viewerBadge_container__1QSob {display: none;}
    </style>
    """
    st.markdown(hide_streamlit_style, unsafe_allow_html=True)
    
    # Add simple header with title only
    st.markdown("""
    <div class="main-header">
        <h1 class="header-title">Product Submission Request</h1>
    </div>
    """, unsafe_allow_html=True)
    
    # Page routing
    if st.session_state.page == "contact":
        contact_page()
    elif st.session_state.page == "course_request":
        course_request_page()
    elif st.session_state.page == "lab_details":
        lab_details_page()
    elif st.session_state.page == "review":
        review_page()
    elif st.session_state.page == "confirmation":
        confirmation_page()
    else:
        contact_page()  # Default to contact page

if __name__ == "__main__":
    main()
