# frontend/pages/1_Upload.py
import sys, os

def _load_parser():
    base = os.path.dirname(__file__)
    search_dirs = [
        base,
        os.path.abspath(os.path.join(base, "..")),
        os.path.abspath(os.path.join(base, "../..")),
        os.path.abspath(os.path.join(base, "../../backend/agents")),  # ← FIXED
        os.path.abspath(os.path.join(base, "../backend/agents")),
    ]
    for d in search_dirs:
        if os.path.exists(os.path.join(d, "statement_parser.py")):
            if d not in sys.path:
                sys.path.insert(0, d)
            break

_load_parser()

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
                os.path.join(os.path.dirname(__file__), "../../backend/data/sample_statements.csv"))
            result = run_finsight_pipeline(sample_path)
            st.session_state["result"] = result
            st.switch_page("pages/2_Dashboard.py")