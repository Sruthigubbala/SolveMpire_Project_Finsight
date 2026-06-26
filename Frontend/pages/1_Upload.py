# frontend/pages/1_Upload.py
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import streamlit as st
import tempfile
from backend.agents.orchestrator import run_finsight_pipeline

st.set_page_config(page_title="Upload | FinSight", layout="wide")
st.title("Upload Your Bank Statement")
st.caption("Supported formats: CSV, PDF  ·  Your data is never stored permanently")

tab1, tab2 = st.tabs(["Upload File", "Try with Sample Data"])

with tab1:
    uploaded = st.file_uploader(
        "Drag and drop your bank statement",
        type=["csv", "pdf"],
        label_visibility="collapsed"
    )
    with st.expander("What format should my CSV be?"):
        st.code("""Date,Description,Amount,Type
01-05-2024,Zomato Order,320,Debit
02-05-2024,Salary Credit,25000,Credit
03-05-2024,Netflix,649,Debit""")

    if uploaded:
        st.success(f"✓ {uploaded.name} ready")
        if st.button("Analyze Statement", type="primary"):
            suffix = ".pdf" if uploaded.name.endswith(".pdf") else ".csv"
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(uploaded.read())
                tmp_path = tmp.name
            with st.spinner("Running 5 AI agents on your statement..."):
                try:
                    result = run_finsight_pipeline(tmp_path)
                    st.session_state["result"] = result
                    st.success("Analysis complete!")
                    st.switch_page("pages/2_Dashboard.py")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
                finally:
                    os.unlink(tmp_path)

with tab2:
    st.info("Click below to run the full analysis on a sample bank statement.")
    if st.button("Run Demo Analysis", type="primary"):
        with st.spinner("Analyzing sample data..."):
            sample_path = os.path.abspath(
                os.path.join(os.path.dirname(__file__), "../../backend/data/sample_statement.csv"))
            result = run_finsight_pipeline(sample_path)
            st.session_state["result"] = result
            st.switch_page("pages/2_Dashboard.py")