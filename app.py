import streamlit as st
import tempfile
import os
import zipfile
import time
import threading
import queue
import io
import pandas as pd
import json
from typing import List, Dict, Any, Optional
import base64


import uuid    # Universally Unique Identifier.
from datetime import datetime

from utils.VCDueDiligenceSystem import VCDueDiligenceSystem
system = VCDueDiligenceSystem()


# Mock for the system module (replace with your actual module)
class InvestmentAnalysisSystem:
    def process_files(self, file_paths: List[str]) -> str:
        """
        Process multiple startup data files and return an investment analysis report.
        This is a placeholder - replace with your actual multiagent implementation.
        """
        # Simulating processing time
        time.sleep(10)
        
        # Return a mock report - your actual system would generate real insights
        return f"""
# Investment Opportunity Analysis

## Executive Summary
Analyzed {len(file_paths)} documents related to the startup. The AI agent system has evaluated the business model, team, market opportunity, and financial projections.

## Investment Recommendation
**Decision: PROCEED WITH FURTHER DUE DILIGENCE**

**Confidence Score: 78%**

## Key Strengths
- Strong founding team with relevant industry experience
- Innovative product with clear market differentiation
- Scalable business model with healthy margins
- Demonstrated customer traction with 45% MoM growth

## Risk Factors
- Competitive landscape intensifying with 3 funded competitors
- Cash runway of only 8 months at current burn rate
- Regulatory challenges in 2 target markets
- Key technical milestone delays observed

## Financial Analysis
| Metric | Current | Projected (24mo) | Industry Benchmark |
|--------|---------|------------------|-------------------|
| ARR    | $750K   | $4.5M            | N/A               |
| Gross Margin | 68% | 72%            | 65%               |
| CAC    | $3,200  | $2,800           | $3,500            |
| LTV    | $18,000 | $24,000          | $16,000           |
| Burn Rate | $180K/mo | $230K/mo     | N/A               |

## Market Analysis
- Total Addressable Market (TAM): $8.2B
- Serviceable Available Market (SAM): $2.1B
- Serviceable Obtainable Market (SOM): $210M
- Expected CAGR: 22% over next 5 years

## Recommended Terms
- Pre-money valuation range: $12M-$15M
- Suggested investment: $2.5M-$3.5M
- Ownership target: 18-22%
- Board seat: Yes
- Pro-rata rights: Required

## Next Steps
1. Schedule technical due diligence session
2. Conduct customer reference calls
3. Verify financial projections
4. Evaluate competitive positioning
"""

# Initialize system
# system = InvestmentAnalysisSystem()

class ProcessStatus:
    """Class to track processing status"""
    def __init__(self):
        self.progress = 0.0
        self.status = "Not started"
        self.report = None
        self.files_data = None  # <-- ADD THIS LINE
        self.error = None
        self.analysis_stages = []

def create_unique_temp_dir(base_dir):
    # Get current datetime with microseconds (Python doesn't have built-in nanoseconds)
    now = datetime.now()
    timestamp = now.strftime('%Y%m%d_%H%M%S_%f')  # %f gives microseconds
    
    # Generate random ID
    random_id = str(uuid.uuid4())[:8]  # Using first 8 characters of UUID
    
    # Create folder name
    folder_name = f"extracted_{timestamp}_{random_id}"
    
    # Create full path (adjust base_dir as needed)
    # base_dir = "/root/r3/temp_folder/"  # Current directory, change as needed
    temp_dir = os.path.join(base_dir, folder_name)
    
    # Create the directory
    os.makedirs(temp_dir, exist_ok=True)
    
    return temp_dir

def extract_zip_to_temp(zip_file) -> List[str]:
    """Extract a zip file to a temporary directory and return paths to all files."""
    temp_dir = "/root/r3/temp_folder"
    temp_dir = create_unique_temp_dir("/root/r3/temp_folder")

    file_paths = []
    
    with zipfile.ZipFile(zip_file, 'r') as zip_ref:
        zip_ref.extractall(temp_dir)
        
        for root, _, files in os.walk(temp_dir):
            for file in files:
                if file.startswith(".") or file.startswith("__MACOSX"):
                    continue
                file_paths.append(os.path.join(root, file))
                
    return file_paths

def save_uploaded_file(uploaded_file) -> str:
    """Save an uploaded file to a temporary location and return the path."""
    temp_dir = tempfile.mkdtemp()
    file_path = os.path.join(temp_dir, uploaded_file.name)
    
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
        
    return file_path

def process_files_thread(file_paths: List[str], status_obj: ProcessStatus, result_queue: queue.Queue, analysis_type: str):
    """Thread function to process files and update status dynamically from backend execution."""
    try:
        status_obj.status = "Starting analysis pipeline..."
        status_obj.progress = 0.02

        # Call backend (blocking inside this thread). Expecting 3-tuple: report, files_data, executed_agents
        report, files_data, executed_agents = system.process_files_sync(file_paths, analysis_type=analysis_type)

        # Defensive: ensure executed_agents is a list
        if not isinstance(executed_agents, list):
            try:
                executed_agents = list(executed_agents or [])
            except Exception:
                executed_agents = []

        # Build user-friendly stage strings
        if executed_agents:
            status_obj.analysis_stages = [f"Running {agent.replace('_', ' ').title()} Agent..." for agent in executed_agents]
        else:
            # Fallback: basic single stage if backend returned nothing
            status_obj.analysis_stages = ["Finalizing analysis..."]

        # Show progress iterating over dynamic stages
        total_stages = max(1, len(status_obj.analysis_stages))
        for i, stage in enumerate(status_obj.analysis_stages):
            status_obj.status = stage
            status_obj.progress = (i + 1) / total_stages * 0.95  # cap at 95% until finalization
            time.sleep(0.6)  # small delay so user sees progress update

        # Finalize
        status_obj.progress = 1.0
        status_obj.status = "Analysis complete"
        status_obj.report = report
        status_obj.files_data = files_data
        result_queue.put(report)

    except Exception as e:
        status_obj.error = str(e)
        status_obj.status = "Error"
        print("=== process_files_thread ERROR ===", repr(e))
        result_queue.put(None)



def render_investment_header():
    """Render the application header with investment-themed design"""
    st.markdown("""
    <style>
    .header-container {
        background-color: #0e1117;
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 1rem;
    }
    .header-title {
        color: #ffffff;
        font-size: 2.2rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
    .header-subtitle {
        color: #9fa6b7;
        font-size: 1.2rem;
        font-weight: 400;
    }
    .metric-container {
        background-color: #1e2130;
        padding: 1rem;
        border-radius: 8px;
        margin-top: 1rem;
    }
    .metric-title {
        color: #9fa6b7;
        font-size: 0.9rem;
        font-weight: 600;
        text-transform: uppercase;
    }
    .metric-value {
        color: #ffffff;
        font-size: 1.8rem;
        font-weight: 700;
    }
    .insight-card {
        background-color: #1e2130;
        padding: 1.5rem;
        border-radius: 8px;
        margin-bottom: 1rem;
        border-left: 4px solid #4CAF50;
    }
    .risk-card {
        background-color: #1e2130;
        padding: 1.5rem;
        border-radius: 8px;
        margin-bottom: 1rem;
        border-left: 4px solid #F44336;
    }
    .neutral-card {
        background-color: #1e2130;
        padding: 1.5rem;
        border-radius: 8px;
        margin-bottom: 1rem;
        border-left: 4px solid #2196F3;
    }
    </style>
    <div class="header-container">
        <div class="header-title">🚀 Startup Investment Analysis</div>
        <div class="header-subtitle">AI-powered due diligence and investment decision support</div>
    </div>
    """, unsafe_allow_html=True)

def add_logo_and_branding():
    """Add custom branding elements to the sidebar"""
    st.sidebar.markdown("""
    <style>
    .sidebar-branding {
        text-align: center;
        padding: 1rem 0;
    }
    .sidebar-title {
        font-size: 1.5rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
    .sidebar-subtitle {
        font-size: 1rem;
        color: #9fa6b7;
        margin-bottom: 1.5rem;
    }
    </style>
    <div class="sidebar-branding">
        <div class="sidebar-title">InvestorIQ</div>
        <div class="sidebar-subtitle">AI-Powered Due Diligence</div>
    </div>
    """, unsafe_allow_html=True)

def main():
    st.set_page_config(
        page_title="Startup Investment Analyzer",
        page_icon="🚀",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Add custom CSS for better styling
    st.markdown("""
    <style>
    .stProgress > div > div {
        background-color: #4CAF50;
    }
    .stDownloadButton button {
        background-color: #2196F3;
        color: white;
    }
    .stButton button {
        background-color: #4CAF50;
        color: white;
        font-weight: 600;
        padding: 0.5rem 2rem;
        border-radius: 8px;
    }
    .report-container {
        background-color: #f9f9f9;
        padding: 2rem;
        border-radius: 10px;
        border: 1px solid #e0e0e0;
    }
    </style>
    """, unsafe_allow_html=True)
    
    add_logo_and_branding()
    
    # Sidebar filters and options
    st.sidebar.header("Analysis Configuration")
    
    analysis_type = st.sidebar.selectbox(
        "Analysis Type",
        ["Full Due Diligence", "Quick Assessment", "Financial Review", "Market Analysis", "Team Evaluation"]
    )
    
   
    
    # Initialize session state variables if they don't exist
    if 'processing' not in st.session_state:
        st.session_state.processing = False
    if 'status' not in st.session_state:
        st.session_state.status = ProcessStatus()
    if 'file_paths' not in st.session_state:
        st.session_state.file_paths = []
    if 'report' not in st.session_state:
        st.session_state.report = None
    if 'uploaded_data' not in st.session_state: # <-- ADD THIS
        st.session_state.uploaded_data = None  # <-- ADD THIS
    if 'startup_name' not in st.session_state:
        st.session_state.startup_name = ""
        
    # Custom header
    render_investment_header()
    
    # Main content area
    col1, col2 = st.columns([7, 3])
    
    with col1:
        # Startup information form
        st.header("Startup Information")
        
        startup_name = st.text_input("Startup Name", 
                                     value=st.session_state.startup_name,
                                     placeholder="Enter the startup's name")
        
        if startup_name != st.session_state.startup_name:
            st.session_state.startup_name = startup_name
        
        cols = st.columns(3)
        with cols[0]:
            fundraising_amount = st.text_input("Raising Amount", 
                                              placeholder="e.g. $2.5M")
        with cols[1]:
            valuation = st.text_input("Valuation", 
                                     placeholder="e.g. $15M pre-money")
        with cols[2]:
            founded_year = st.text_input("Founded", 
                                        placeholder="e.g. 2021")
        
        # File uploader section
        st.header("Upload Startup Data")
        st.markdown("""
        Upload relevant documents for the startup. The system supports:
        - Pitch decks (PDF)
        - Financial models/projections (PDF/ZIP)
        - Market research documents (PDF)
        - Team background (PDF)
        - Previous investor updates (PDF)
        - Technical documentation (PDF/ZIP)
        """)
        
        uploaded_files = st.file_uploader(
            "Upload documents for analysis", 
            type=["pdf", "zip"],
            accept_multiple_files=True,
            help="Upload multiple PDFs or a ZIP archive containing all relevant documents."
        )
        
        analyze_button = st.button(
            "🔍 Run Investment Analysis", 
            disabled=st.session_state.processing or not uploaded_files or not startup_name
        )
        
        if analyze_button:
            st.session_state.file_paths = []
            
            # Process each uploaded file
            for uploaded_file in uploaded_files:
                if uploaded_file.name.lower().endswith('.zip'):
                    # For ZIP files, extract them first
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as tmp_file:
                        tmp_file.write(uploaded_file.getbuffer())
                        zip_path = tmp_file.name
                    
                    # Extract zip and get file paths
                    extracted_paths = extract_zip_to_temp(zip_path)
                    st.session_state.file_paths.extend(extracted_paths)
                    os.unlink(zip_path)  # Remove the temporary zip file
                else:
                    # For other files, save them directly
                    file_path = save_uploaded_file(uploaded_file)
                    st.session_state.file_paths.append(file_path)
            
            # Start processing in a separate thread
            st.session_state.processing = True
            st.session_state.status = ProcessStatus()
            st.session_state.report = None
            
            result_queue = queue.Queue()
            thread = threading.Thread(
    target=process_files_thread,
    args=(st.session_state.file_paths, st.session_state.status, result_queue, analysis_type)
)

            thread.daemon = True
            thread.start()
            
            # Force a rerun to start showing progress
            st.rerun()
    
    with col2:
        # Display the document summary
        st.header("Document Summary")
        if uploaded_files:
            st.write(f"**{len(uploaded_files)} documents uploaded**")
            
            # Group files by type
            file_types = {}
            for uploaded_file in uploaded_files:
                file_ext = uploaded_file.name.split('.')[-1].lower()
                if file_ext in file_types:
                    file_types[file_ext] += 1
                else:
                    file_types[file_ext] = 1
            
            # Display file type summary
            st.markdown("**Document Types:**")
            for ext, count in file_types.items():
                st.markdown(f"- {count} {ext.upper()} file{'s' if count > 1 else ''}")
            
            # Display file list in collapsible section
            with st.expander("View Document List"):
                for uploaded_file in uploaded_files:
                    st.markdown(f"- {uploaded_file.name}")
        else:
            st.info("No documents uploaded yet.")
            
            # Sample files suggestion
            with st.expander("Need sample files?"):
                st.markdown("""
                For testing, you can use sample startup documents:
                - Sample pitch deck
                - Financial projections template
                - Market research example
                
                Contact your administrator for access to these templates.
                """)
    
    # Show progress when processing
    if st.session_state.processing:
        status = st.session_state.status
        
        st.markdown("---")
        st.header("Analysis Progress")
        
        # Show progress bar
        progress_bar = st.progress(float(status.progress))
        
        # Display current status
        status_text = st.empty()
        status_text.markdown(f"**Current stage:** {status.status}")
        
        
        # Add a spinner while waiting
        if status.progress < 1.0 and not status.error:
            with st.spinner("Analysis in progress..."):
                # Wait for a moment and then rerun to update progress
                time.sleep(1.0)
                st.rerun()
        else:
            st.session_state.processing = False
            if status.error:
                st.error(f"An error occurred: {status.error}")
            else:
                print(st.session_state.file_paths)
                # file_paths = st.session_state.file_paths
                # report = system.process_files(file_paths)
                st.session_state.report = status.report
                st.session_state.uploaded_data = status.files_data
                st.success("Analysis complete!")
    
    # Display the report when available
    if st.session_state.report:
        st.markdown("---")
        st.header(f"Investment Analysis: {st.session_state.startup_name}")
        
       
            # Render the markdown report
        st.markdown(st.session_state.report)
       
        # Import docx for Word document generation
        from docx import Document
        

        # Example report content (Markdown or plain text)
        report_content = st.session_state.report
        startup_name = st.session_state.startup_name.replace(' ', '_')

        # Let user select format
        file_format = st.selectbox(
            "Choose download format", 
            options=["Markdown (.md)", "Text (.txt)"]
        )

        if file_format == "Markdown (.md)":
            file_name = f"{startup_name}_investment_analysis.md"
            data = report_content  # raw markdown text
            mime = "text/markdown"

        elif file_format == "Text (.txt)":
            file_name = f"{startup_name}_investment_analysis.txt"
            data = report_content  # plain text
            mime = "text/plain"

        # Provide download button
        st.download_button(
            label="📥 Download Full Report",
            data=data,
            file_name=file_name,
            mime=mime
        )

        st.markdown("---") # Add a separator

        # Use an expander to show/hide the raw data
        with st.expander("📄 See Extracted Text from Uploaded Files"):
            if st.session_state.uploaded_data:
                for filename, data in st.session_state.uploaded_data.items():
                    st.subheader(f"Content of: {os.path.basename(filename)}")
                    # Use a text_area inside a container for a scrollable box
                    st.text_area(
                        label=f"Content for {filename}", 
                        value=data.get('content', 'No content was extracted from this file.'),
                        height=400,
                        key=f"textarea_{filename}" # Use a unique key
                    )
            else:
                st.info("No extracted data is available to display.")

if __name__ == "__main__":
    main()