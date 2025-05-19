import streamlit as st
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# MongoDB connection
def get_database():
    # Use your MongoDB connection string from environment variables
    MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
    
    # Create a new client and connect to the server
    client = MongoClient(
        MONGODB_URI,
        server_api=ServerApi('1'),
        tls=True,
        tlsAllowInvalidCertificates=True,  # Only use this in development
        retryWrites=True,
        w='majority',
        connectTimeoutMS=30000,
        socketTimeoutMS=30000,
        serverSelectionTimeoutMS=5000  # Fail fast if can't connect
    )
    
    # Test the connection with more detailed error handling
    try:
        # The ping command is cheap and does not require auth
        client.admin.command('ping')
        print("Pinged your deployment. You successfully connected to MongoDB!")
    except Exception as e:
        error_msg = f"MongoDB connection error: {str(e)}\n"
        error_msg += "Please check the following:\n"
        error_msg += "1. Your MongoDB Atlas connection string\n"
        error_msg += "2. Your network connection\n"
        error_msg += "3. MongoDB Atlas IP whitelist settings\n"
        error_msg += "4. MongoDB user permissions"
        print(error_msg)
        raise Exception(error_msg)
    
    return client["lab_survey"]

def save_responses(responses):
    try:
        db = get_database()
        responses["submitted_at"] = datetime.utcnow()
        
        # Add a try-except block specifically for the insert operation
        try:
            result = db.responses.insert_one(responses)
            if result.inserted_id:
                st.success("Successfully saved to database!")
                return True
            else:
                st.error("Failed to save to database: No document was inserted")
                return False
                
        except Exception as insert_error:
            st.error(f"Error saving to database: {str(insert_error)}")
            st.error("Please check your MongoDB connection and try again.")
            return False
            
    except Exception as e:
        st.error(f"Database connection error: {str(e)}")
        st.error("Please check your MongoDB connection string and network settings.")
        return False

def contact_page():
    # Load existing data if available
    contact_data = st.session_state.contact_info
    
    with st.form("contact_form"):
        st.markdown("### Contact Information")
        
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Full Name", 
                              value=contact_data.get("name", ""), 
                              key="name")
        with col2:
            email = st.text_input("Email Address", 
                               value=contact_data.get("email", ""), 
                               key="email")
            
        org_col1, org_col2 = st.columns([2, 1])
        with org_col1:
            organization = st.text_input("Organization", 
                                      value=contact_data.get("organization", ""), 
                                      key="org")
        with org_col2:
            org_type = st.selectbox(
                "Type",
                ["", "University/College", "Corporate", "Government", "Non-Profit", "Other"],
                index=["", "University/College", "Corporate", "Government", "Non-Profit", "Other"].index(
                    contact_data.get("org_type", "")
                ) if contact_data.get("org_type") else 0,
                key="org_type"
            )
        
        submit_col1, submit_col2 = st.columns([1, 1])
        with submit_col1:
            if st.form_submit_button("Next"):
                if not all([name, email, organization, org_type]):
                    st.warning("Please fill in all required fields.")
                else:
                    st.session_state.contact_info = {
                        "name": name,
                        "email": email,
                        "organization": organization,
                        "org_type": org_type
                    }
                    st.session_state.page = "lab_request"
                    st.rerun()

def lab_request_page():
    # Load existing data if available
    lab_data = st.session_state.lab_request
    
    # Parse learning objectives from existing data
    existing_objectives = lab_data.get("learning_objectives", [])
    cert = any("Certification" in obj for obj in existing_objectives)
    hands_on = any("Hands-On" in obj for obj in existing_objectives)
    assessment = any("Assessment" in obj for obj in existing_objectives)
    workshop = any("Workshop" in obj for obj in existing_objectives)
    other_obj = any("Other:" in obj for obj in existing_objectives)
    other_obj_text = next((obj.replace("Other: ", "") for obj in existing_objectives if "Other:" in obj), "")
    
    with st.form("lab_request_form"):
        st.markdown("### Lab Request Details")
        
        # First row: Lab name and type
        col1, col2 = st.columns([2, 1])
        with col1:
            lab_name = st.text_input("Lab Name", 
                                  value=lab_data.get("lab_name", ""), 
                                  key="lab_name")
        with col2:
            lab_type = st.selectbox(
                "Type",
                ["Instructional", "Self-Paced", "Assessment", "Other"],
                index=["Instructional", "Self-Paced", "Assessment", "Other"].index(
                    lab_data.get("lab_type", "Instructional")
                ) if lab_data.get("lab_type") else 0,
                key="lab_type"
            )
        
        # Second row: Persistence and Duration
        col1, col2 = st.columns(2)
        with col1:
            persistence = st.radio(
                "Persistence",
                ["Persistent", "Non-Persistent"],
                index=0 if lab_data.get("persistence") == "Persistent" else 1,
                key="persistence",
                help="Persistent saves work between sessions, Non-Persistent resets each time"
            )
        with col2:
            duration = st.selectbox(
                "Duration",
                ["1 hour", "4 hours", "1 day", "1 week", "Custom"],
                index=["1 hour", "4 hours", "1 day", "1 week", "Custom"].index(
                    lab_data.get("duration", "1 hour")
                ) if lab_data.get("duration") else 0,
                key="duration"
            )
        
        # Learning Objectives
        st.markdown("**Learning Objectives**")
        objectives_cols = st.columns(3)
        with objectives_cols[0]:
            cert = st.checkbox("Certification", value=cert, key="obj_cert")
            hands_on = st.checkbox("Hands-On", value=hands_on, key="obj_hands_on")
        with objectives_cols[1]:
            assessment = st.checkbox("Assessment", value=assessment, key="obj_assessment")
            workshop = st.checkbox("Workshop", value=workshop, key="obj_workshop")
        with objectives_cols[2]:
            other_obj = st.checkbox("Other", value=other_obj, key="obj_other")
            other_obj_text = st.text_input(
                "Other (specify)", 
                value=other_obj_text,
                key="obj_other_text", 
                label_visibility="collapsed"
            )
        
        # Complexity and Developer
        col1, col2 = st.columns(2)
        with col1:
            complexity = st.radio(
                "Complexity",
                ["Beginner", "Intermediate", "Advanced"],
                index=["Beginner", "Intermediate", "Advanced"].index(
                    lab_data.get("complexity", "Beginner")
                ) if lab_data.get("complexity") else 0,
                key="complexity"
            )
        with col2:
            developer = st.radio(
                "Developer",
                ["ACI", "Customer SME", "Joint"],
                index=["ACI", "Customer SME", "Joint"].index(
                    lab_data.get("developer", "ACI")
                ) if lab_data.get("developer") else 0,
                key="developer"
            )
        
        # Target Date
        target_date = st.date_input(
            "Target Completion Date", 
            value=datetime.strptime(lab_data.get("target_date"), "%Y-%m-%d").date() 
                if lab_data.get("target_date") else datetime.now().date(),
            key="target_date"
        )
        
        # Navigation buttons
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            if st.form_submit_button("Back"):
                st.session_state.page = "contact"
                st.rerun()
        with col2:
            if st.form_submit_button("Next"):
                # Collect learning objectives
                learning_objectives = []
                if cert: learning_objectives.append("Certification")
                if hands_on: learning_objectives.append("Hands-On")
                if assessment: learning_objectives.append("Assessment")
                if workshop: learning_objectives.append("Workshop")
                if other_obj and other_obj_text:
                    learning_objectives.append(f"Other: {other_obj_text}")
                
                if not all([lab_name, lab_type, persistence, duration]):
                    st.warning("Please fill in all required fields.")
                else:
                    st.session_state.lab_request = {
                        "lab_name": lab_name,
                        "lab_type": lab_type,
                        "persistence": persistence,
                        "duration": duration,
                        "learning_objectives": learning_objectives,
                        "complexity": complexity,
                        "developer": developer,
                        "target_date": target_date.isoformat()
                    }
                    st.session_state.page = "hardware"
                    st.rerun()

def hardware_page():
    with st.form("hardware_form"):
        st.markdown("### Hardware Requirements")
        
        # System Counts Section
        st.markdown("**System Counts**")
        col1, col2, col3 = st.columns(3)
        with col1:
            total_systems = st.number_input(
                "Total Number of Systems",
                min_value=1,
                step=1,
                key="total_systems"
            )
        with col2:
            pre_installed = st.number_input(
                "Pre-installed (How Many?)",
                min_value=0,
                step=1,
                key="pre_installed"
            )
        with col3:
            boot_iso = st.number_input(
                "Boot from ISO (How Many?)",
                min_value=0,
                step=1,
                key="boot_iso"
            )
        
        # CPU Configuration
        st.markdown("**CPU Configuration**")
        cpu_per_system = st.radio(
            "CPU Cores per System",
            ["2", "4", "8", "16", "Varies by System (specify below)"],
            key="cpu_per_system"
        )
        
        if cpu_per_system == "Varies by System (specify below)":
            cpu_notes = st.text_area("Specify CPU requirements per system:", key="cpu_notes")
        
        # RAM Configuration
        st.markdown("**Memory Configuration**")
        ram_col1, ram_col2 = st.columns([1, 3])
        with ram_col1:
            ram_per_system = st.radio(
                "RAM per System",
                ["2GB", "4GB", "8GB", "16GB", "Other (specify)"],
                key="ram_per_system"
            )
        
        # Storage Configuration
        st.markdown("**Storage Configuration**")
        col1, col2 = st.columns(2)
        with col1:
            hdd_partitions = st.number_input(
                "Number of Partitions per System",
                min_value=1,
                max_value=10,
                step=1,
                key="hdd_partitions"
            )
        with col2:
            hdd_size = st.selectbox(
                "Hard Drive Space per Partition",
                ["20GB", "40GB", "60GB", "100GB", "200GB", "Other (specify)"],
                key="hdd_size"
            )
        
        # Additional Hardware Features
        st.markdown("**Additional Hardware Features**")
        col1, col2 = st.columns(2)
        with col1:
            cd_rom = st.radio(
                "CD-ROM Required",
                ["Yes", "No"],
                key="cd_rom"
            )
        with col2:
            nested_virt = st.multiselect(
                "Nested Virtualization Required",
                ["GNS3", "Hyper-V", "Docker", "Other"],
                key="nested_virt"
            )
        
        # Systems by OS
        st.markdown("**Systems by OS**")
        
        # Windows Systems
        st.markdown("**Windows Systems**")
        windows_systems = []
        windows_cols = st.columns(3)
        with windows_cols[0]:
            win10 = st.number_input("Windows 10", min_value=0, step=1, key="win10")
            if win10 > 0:
                windows_systems.append({"version": "Windows 10", "count": win10})
        with windows_cols[1]:
            win11 = st.number_input("Windows 11", min_value=0, step=1, key="win11")
            if win11 > 0:
                windows_systems.append({"version": "Windows 11", "count": win11})
        with windows_cols[2]:
            win_server = st.number_input("Windows Server", min_value=0, step=1, key="win_server")
            if win_server > 0:
                windows_systems.append({"version": "Windows Server", "count": win_server})
        other_win = st.text_input("Other Windows versions (specify version and count):", key="other_win")
        
        # Linux Systems
        st.markdown("**Linux Systems**")
        linux_systems = []
        linux_cols = st.columns(3)
        with linux_cols[0]:
            ubuntu = st.number_input("Ubuntu", min_value=0, step=1, key="ubuntu")
            if ubuntu > 0:
                linux_systems.append({"distro": "Ubuntu", "count": ubuntu})
        with linux_cols[1]:
            centos = st.number_input("CentOS", min_value=0, step=1, key="centos")
            if centos > 0:
                linux_systems.append({"distro": "CentOS", "count": centos})
        with linux_cols[2]:
            kali = st.number_input("Kali Linux", min_value=0, step=1, key="kali")
            if kali > 0:
                linux_systems.append({"distro": "Kali Linux", "count": kali})
        other_linux = st.text_input("Other Linux distros (specify distro and count):", key="other_linux")
        
        # Other Systems
        st.markdown("**Other Systems**")
        other_systems = []
        other_cols = st.columns(2)
        with other_cols[0]:
            openvas = st.number_input("OpenVAS", min_value=0, step=1, key="openvas")
            if openvas > 0:
                other_systems.append({"name": "OpenVAS", "count": openvas})
            vyos = st.number_input("VyOS", min_value=0, step=1, key="vyos")
            if vyos > 0:
                other_systems.append({"name": "VyOS", "count": vyos})
        with other_cols[1]:
            pfsense = st.number_input("pfSense", min_value=0, step=1, key="pfsense")
            if pfsense > 0:
                other_systems.append({"name": "pfSense", "count": pfsense})
            other_os = st.text_input("Other (specify):", key="other_os")
        
        # Network Requirements
        st.markdown("**Network Requirements**")
        
        # Network Type
        network_type = st.radio(
            "Network Type",
            ["Stand-Alone", "Server/Client", "Peer-to-Peer", "Domain"],
            key="network_type"
        )
        
        # Network Configuration
        net_cols = st.columns(2)
        with net_cols[0]:
            num_subnets = st.number_input(
                "Number of Subnets",
                min_value=1,
                step=1,
                key="num_subnets"
            )
        with net_cols[1]:
            internet_access = st.radio(
                "Internet Access",
                ["Yes", "No"],
                key="internet_access"
            )
        
        # Other Requirements
        st.markdown("**Other Requirements**")
        other_reqs = st.text_area(
            "Any specialized requirements not listed in the previous sections:",
            key="other_reqs",
            height=80,
            help="Please specify any additional requirements or special configurations needed"
        )
        
        # Notes - Increased height to 100px to meet minimum requirements
        notes = st.text_area(
            "Additional Notes or Comments",
            key="hardware_notes",
            height=100
        )
        
        # Navigation buttons
        col1, col2, col3 = st.columns([1, 1, 2])
        
        # Single form submission handler
        submitted = st.form_submit_button("Submit Survey")
        back_clicked = st.form_submit_button("Back")
        
        if back_clicked:
            st.session_state.page = "lab_request"
            st.rerun()
            
        if submitted:
            # Process Windows systems
            if 'other_win' in locals() and other_win:
                windows_systems.append({"version": f"Other: {other_win}", "count": 1})
            
            # Process Linux systems
            if 'other_linux' in locals() and other_linux:
                linux_systems.append({"distro": f"Other: {other_linux}", "count": 1})
            
            # Process other OS
            if 'other_os' in locals() and other_os:
                other_systems.append({"name": f"Other: {other_os}", "count": 1})
            
            # Get cpu_notes if it exists
            cpu_notes_value = cpu_notes if 'cpu_notes' in locals() else ""
            
            hardware_info = {
                "system_counts": {
                    "total_systems": total_systems,
                    "pre_installed": pre_installed,
                    "boot_iso": boot_iso
                },
                "cpu_config": {
                    "cores_per_system": cpu_per_system,
                    "notes": cpu_notes_value if cpu_per_system == "Varies by System (specify below)" else ""
                },
                "memory_config": {
                    "ram_per_system": ram_per_system
                },
                "storage_config": {
                    "partitions_per_system": hdd_partitions if 'hdd_partitions' in locals() else 1,
                    "partition_size": hdd_size if 'hdd_size' in locals() else ""
                },
                "additional_features": {
                    "cd_rom": cd_rom == "Yes" if 'cd_rom' in locals() else False,
                    "nested_virtualization": nested_virt if 'nested_virt' in locals() else False
                },
                "systems_by_os": {
                    "windows": windows_systems if 'windows_systems' in locals() else [],
                    "linux": linux_systems if 'linux_systems' in locals() else [],
                    "other": other_systems if 'other_systems' in locals() else []
                },
                "network_requirements": {
                    "network_type": network_type,
                    "number_of_subnets": num_subnets,
                    "internet_access": internet_access == "Yes"
                },
                "other_requirements": other_reqs,
                "notes": notes
            }
            
            # Store hardware info in session state and go to summary
            st.session_state.hardware_info = hardware_info
            st.session_state.page = "summary"
            st.rerun()

def confirmation_page():
    st.header("Thank You!")
    st.balloons()
    st.success("Your survey has been submitted successfully!")
    
    if st.button("Submit Another Response"):
        # Clear session state and start over
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.session_state.page = "contact"
        st.rerun()

def format_systems_list(systems, key_name):
    if not systems:
        return "None"
    return ", ".join([f"{item[key_name]} (x{item['count']})" for item in systems])

def summary_page():
    st.title("Review Your Submission")
    st.write("Please review all the information below before submitting.")
    
    # Add custom CSS for better button styling
    st.markdown("""
    <style>
    .edit-button {
        border: 1px solid #4CAF50 !important;
        color: white !important;
        background-color: #4CAF50 !important;
        padding: 0.5rem 1rem !important;
        border-radius: 4px !important;
        margin: 0.5rem 0 !important;
        font-size: 0.9rem !important;
    }
    .edit-button:hover {
        background-color: #45a049 !important;
    }
    .nav-button {
        margin: 5px !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Helper function to create edit button
    def create_edit_button(section):
        button_key = f"edit_{section.lower().replace(' ', '_')}"
        if st.button(f"✏️ Edit {section}", 
                   key=button_key,
                   help=f"Click to edit {section}",
                   use_container_width=True,
                   type="primary" if section == "Contact Information" else "secondary"):
            st.session_state.edit_section = section
            st.session_state.from_summary = True
            st.session_state._rerun = True
            
    # Contact Information
    with st.expander("Contact Information", expanded=True):
        contact = st.session_state.contact_info
        col1, col2 = st.columns([4, 1])
        with col1:
            st.write(f"**Name:** {contact.get('name', '')}")
            st.write(f"**Email:** {contact.get('email', '')}")
            st.write(f"**Organization:** {contact.get('organization', '')}")
            st.write(f"**Organization Type:** {contact.get('org_type', '')}")
        with col2:
            create_edit_button("Contact Information")
    
    # Lab Request Details
    with st.expander("Lab Request Details", expanded=True):
        lab = st.session_state.lab_request
        col1, col2 = st.columns([4, 1])
        with col1:
            st.write(f"**Lab Name:** {lab.get('lab_name', '')}")
            st.write(f"**Lab Type:** {lab.get('lab_type', '')}")
            st.write(f"**Persistence:** {lab.get('persistence', '')}")
            st.write(f"**Duration:** {lab.get('duration', '')}")
            st.write(f"**Complexity:** {lab.get('complexity', '')}")
            st.write(f"**Developer:** {lab.get('developer', '')}")
            
            st.write("**Learning Objectives:**")
            for obj in lab.get('learning_objectives', []):
                st.write(f"- {obj}")
        with col2:
            create_edit_button("Lab Request")
    
    # Hardware Requirements
    with st.expander("Hardware Requirements", expanded=True):
        hw = st.session_state.hardware_info
        col1, col2 = st.columns([4, 1])
        with col1:
            st.write("**System Counts:**")
            st.write(f"- Total Systems: {hw.get('system_counts', {}).get('total_systems', 0)}")
            st.write(f"- Pre-installed: {hw.get('system_counts', {}).get('pre_installed', 0)}")
            st.write(f"- Boot from ISO: {hw.get('system_counts', {}).get('boot_iso', 0)}")
            
            st.write("**CPU Configuration:**")
            st.write(f"- Cores per System: {hw.get('cpu_config', {}).get('cores_per_system', '')}")
            if hw.get('cpu_config', {}).get('notes'):
                st.write(f"  - Notes: {hw['cpu_config']['notes']}")
            
            st.write("**Memory Configuration:**")
            st.write(f"- RAM per System: {hw.get('memory_config', {}).get('ram_per_system', '')}")
            
            st.write("**Storage Configuration:**")
            st.write(f"- Partitions per System: {hw.get('storage_config', {}).get('partitions_per_system', '')}")
            st.write(f"- Partition Size: {hw.get('storage_config', {}).get('partition_size', '')}")
            
            st.write("**Windows Systems:**")
            for win in hw.get('systems_by_os', {}).get('windows', []):
                st.write(f"- {win.get('version', '')}: {win.get('count', 0)}")
                
            st.write("**Linux Systems:**")
            for linux in hw.get('systems_by_os', {}).get('linux', []):
                st.write(f"- {linux.get('distro', '')}: {linux.get('count', 0)}")
                
            st.write("**Other Systems:**")
            for other in hw.get('systems_by_os', {}).get('other', []):
                st.write(f"- {other.get('name', '')}: {other.get('count', 0)}")
            
            st.write("**Network Requirements:**")
            st.write(f"- Network Type: {hw.get('network_requirements', {}).get('network_type', '')}")
            st.write(f"- Number of Subnets: {hw.get('network_requirements', {}).get('number_of_subnets', '')}")
            st.write(f"- Internet Access: {'Yes' if hw.get('network_requirements', {}).get('internet_access', False) else 'No'}")
            
            if hw.get('other_requirements'):
                st.write("**Other Requirements:**")
                st.write(hw['other_requirements'])
                
            if hw.get('notes'):
                st.write("**Notes:**")
                st.write(hw['notes'])
        with col2:
            create_edit_button("Hardware")
    
    # Handle edit section navigation
    if hasattr(st.session_state, 'edit_section'):
        # Add a small delay to ensure the button click is processed
        import time
        time.sleep(0.1)  # Small delay to ensure state is updated
        
        if st.session_state.edit_section == "Contact Information":
            st.session_state.page = "contact"
        elif st.session_state.edit_section == "Lab Request":
            st.session_state.page = "lab_request"
        elif st.session_state.edit_section == "Hardware":
            st.session_state.page = "hardware"
        
        # Mark that we're coming from the summary page
        st.session_state.from_summary = True
        
        # Clear the edit section and force a rerun
        section = st.session_state.edit_section
        del st.session_state.edit_section
        st.session_state._rerun = True
        st.rerun()
    
    # Navigation section at the bottom of the summary page
    st.markdown("---")
    
    # Create two columns for the buttons
    col1, col2 = st.columns([1, 2])
    
    with col1:
        if st.button("← Back to Hardware", 
                    key="back_to_hardware",
                    use_container_width=True):
            st.session_state.page = "hardware"
            st.session_state.from_summary = False
            st.rerun()
            
    with col2:
        if st.button("✅ Submit Survey", 
                    key="submit_survey",
                    type="primary",
                    use_container_width=True):
            # Combine all data
            response = {
                "contact_info": st.session_state.contact_info,
                "lab_request": st.session_state.lab_request,
                "hardware_info": st.session_state.hardware_info,
                "submitted_at": datetime.utcnow()
            }
            
            # Save to MongoDB
            if save_responses(response):
                st.session_state.page = "confirmation"
                st.rerun()

def initialize_session_state():
    if "contact_info" not in st.session_state:
        st.session_state.contact_info = {}
    if "lab_request" not in st.session_state:
        st.session_state.lab_request = {}
    if "hardware_info" not in st.session_state:
        st.session_state.hardware_info = {}

def main():
    st.set_page_config(
        page_title="Lab Setup Survey",
        page_icon="🔬",
        layout="centered"
    )
    
    # Initialize session state variables
    initialize_session_state()
    
    # Custom CSS for compact form layout
    st.markdown("""
    <style>
        .main .block-container {
            padding: 0.5rem 0.5rem !important;
            max-width: 700px !important;
        }
        .stForm {
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            padding: 1rem;
            margin: 0.5rem 0;
        }
        .stButton>button {
            width: 100%;
            padding: 0.25rem 0.5rem;
            font-size: 0.9rem;
        }
        .stProgress > div > div > div > div {
            background-color: #4CAF50;
            height: 4px !important;
        }
        .stTextInput>div>div>input, 
        .stTextArea>div>div>textarea,
        .stSelectbox>div>div>div>div,
        .stNumberInput>div>div>input {
            border-radius: 4px;
            border: 1px solid #ccc;
            padding: 0.25rem 0.5rem;
            font-size: 0.9rem;
            min-height: 30px;
        }
        .stTextArea>div>div>textarea {
            min-height: 60px !important;
        }
        .stRadio > div {
            gap: 0.5rem;
            font-size: 0.9rem;
        }
        .stMultiSelect > div > div > div > div {
            padding: 0.25rem 0.5rem;
        }
        .stDateInput>div>div>input {
            padding: 0.25rem 0.5rem;
            font-size: 0.9rem;
        }
        h1 {
            font-size: 1.5rem !important;
            margin: 0.5rem 0 0.5rem 0 !important;
        }
        h2, h3, h4 {
            margin: 0.75rem 0 0.5rem 0 !important;
        }
        .stMarkdown p {
            margin: 0.25rem 0 !important;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Initialize session state
    if "page" not in st.session_state:
        st.session_state.page = "contact"
    
    # Show progress bar
    pages = ["contact", "lab_request", "hardware", "summary", "confirmation"]
    progress = (pages.index(st.session_state.page) + 1) / len(pages)
    st.progress(progress)
    
    # Display current page
    if st.session_state.page == "contact":
        contact_page()
    elif st.session_state.page == "lab_request":
        lab_request_page()
    elif st.session_state.page == "hardware":
        hardware_page()
    elif st.session_state.page == "summary":
        summary_page()
    elif st.session_state.page == "confirmation":
        confirmation_page()

if __name__ == "__main__":
    main()
