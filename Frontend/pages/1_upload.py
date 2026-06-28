# Frontend/pages/1_Upload.py
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import streamlit as st
import tempfile
from backend.agents.orchestrator import run_finsight_pipeline
from components.styles import inject_styles

st.set_page_config(page_title="Upload | FinSight", page_icon="📤", layout="wide")
inject_styles()

st.markdown('<div class="section-header"><h1>Upload Your Bank Statement</h1></div>',
            unsafe_allow_html=True)
st.caption("Supported formats: CSV · PDF  ·  Your data is processed locally and never stored")

st.write("")

tab1, tab2 = st.tabs(["📁  Upload File", "🔍  Try with Sample Data"])

with tab1:
    st.write("")

    # Drag-and-drop visual overlay (activates on dragover)
    st.markdown("""
    <div id="drop-overlay" style="display:none; position:fixed; inset:0; z-index:9999;
         background:rgba(30,94,255,0.08); backdrop-filter:blur(2px);
         border:3px dashed #1E5EFF; border-radius:20px; pointer-events:none;">
      <div style="position:absolute; top:50%; left:50%; transform:translate(-50%,-50%);
           text-align:center; color:#1E5EFF;">
        <div style="font-size:56px; line-height:1;">📂</div>
        <div style="font-size:22px; font-weight:700; margin-top:12px;">Drop your file here</div>
        <div style="font-size:14px; color:#6B8EFF; margin-top:6px;">CSV or PDF accepted</div>
      </div>
    </div>

    <script>
    (function() {
      let dragCount = 0;
      const overlay = document.getElementById('drop-overlay');

      document.addEventListener('dragenter', function(e) {
        dragCount++;
        if (overlay) overlay.style.display = 'block';
      });

      document.addEventListener('dragleave', function(e) {
        dragCount--;
        if (dragCount <= 0) {
          dragCount = 0;
          if (overlay) overlay.style.display = 'none';
        }
      });

      document.addEventListener('drop', function(e) {
        dragCount = 0;
        if (overlay) overlay.style.display = 'none';
      });

      document.addEventListener('dragover', function(e) {
        e.preventDefault();
      });
    })();
    </script>
    """, unsafe_allow_html=True)

    # Instructional hint above uploader
    st.markdown("""
    <div style="display:flex; align-items:center; gap:10px; margin-bottom:10px;">
      <span style="font-size:28px;">📥</span>
      <div>
        <div style="font-weight:700; font-size:15px; color:#1E293B;">Drag & drop your file anywhere on this page</div>
        <div style="font-size:13px; color:#64748B; margin-top:2px;">Or click below to browse — CSV and PDF supported</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    uploaded = st.file_uploader(
        "Drop your bank statement here or click to browse",
        type=["csv", "pdf"],
        label_visibility="visible"
    )

    if uploaded:
        st.markdown(f"""
        <div class="upload-success">
          <span style="font-size:22px">✅</span>
          <div>
            <strong>{uploaded.name}</strong> is ready<br>
            <span style="font-size:13px;color:#64748B">{uploaded.size / 1024:.1f} KB uploaded</span>
          </div>
        </div>""", unsafe_allow_html=True)
        st.write("")

        if st.button("Analyze Statement →", type="primary"):
            suffix = ".pdf" if uploaded.name.endswith(".pdf") else ".csv"
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(uploaded.read())
                tmp_path = tmp.name
            with st.spinner("Running 5 AI agents on your statement…"):
                try:
                    result = run_finsight_pipeline(tmp_path)
                    st.session_state["result"] = result
                    st.success("✅  Analysis complete! Redirecting to dashboard…")
                    st.switch_page("pages/2_Dashboard.py")
                except Exception as e:
                    st.error(f"Something went wrong: {str(e)}")
                    st.caption("Check that your file matches the format shown above.")
                finally:
                    if os.path.exists(tmp_path):
                        os.unlink(tmp_path)

with tab2:
    st.write("")
    st.markdown("""
    <div class="advice-box">
      <strong style="font-size:15px">🔍  Live demo — no upload needed</strong><br>
      <span style="color:#374151;font-size:14px">
        This runs the complete 5-agent analysis on a realistic sample Indian bank statement.
        You'll see everything FinSight produces — spending breakdown, health score,
        savings opportunities, and a personalized action plan.
      </span>
    </div>""", unsafe_allow_html=True)

    st.write("")

    # Preview of sample data
    with st.expander("👀  Preview sample data"):
        import pandas as pd
        sample_preview = {
            "Date": ["01-05-2024", "02-05-2024", "03-05-2024", "05-05-2024", "07-05-2024"],
            "Description": ["Salary Credit", "Zomato Order", "Netflix", "Amazon Purchase", "Petrol Bunk"],
            "Amount": [25000, 450, 649, 1299, 2000],
            "Type": ["Credit", "Debit", "Debit", "Debit", "Debit"],
        }
        st.dataframe(pd.DataFrame(sample_preview), hide_index=True, use_container_width=True)
        st.caption("…and more transactions across food, transport, utilities, and entertainment.")

    st.write("")
    if st.button("Run Demo Analysis →", type="primary"):
        with st.spinner("Running full analysis on sample data…"):
            sample_path = os.path.abspath(
                os.path.join(os.path.dirname(__file__), "../../backend/data/sample_statements.csv"))
            try:
                result = run_finsight_pipeline(sample_path)
                st.session_state["result"] = result
                st.switch_page("pages/2_Dashboard.py")
            except Exception as e:
                st.error(f"Demo error: {str(e)}")

st.divider()
st.markdown('<p style="color:#94A3B8;font-size:13px;text-align:center">🔒 Your data never leaves this session. No accounts, no storage.</p>', unsafe_allow_html=True)