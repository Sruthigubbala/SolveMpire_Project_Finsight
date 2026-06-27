import streamlit as st

def inject_styles():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=DM+Mono:wght@400;500&display=swap');

    /* ── Global ── */
    html, body, [class*="css"] { font-family: 'Inter', -apple-system, sans-serif !important; }
    .block-container { padding-top: 2.5rem !important; padding-bottom: 4rem !important; max-width: 1200px !important; }
    #MainMenu, footer { visibility: hidden; }
    ::-webkit-scrollbar { width: 5px; }
    ::-webkit-scrollbar-track { background: #F1F5F9; }
    ::-webkit-scrollbar-thumb { background: #CBD5E1; border-radius: 3px; }

    /* ── Hero ── */
    .hero-eyebrow {
        display: inline-flex; align-items: center; gap: 6px;
        font-size: 11px; font-weight: 600; letter-spacing: 0.12em;
        text-transform: uppercase; color: #1E5EFF;
        background: #EEF3FF; border: 1px solid #C7D7FF;
        border-radius: 100px; padding: 5px 14px; margin-bottom: 22px;
    }
    .hero-eyebrow::before { content: ''; display: inline-block; width: 6px; height: 6px; border-radius: 50%; background: #1E5EFF; }
    .hero-title { font-size: 54px; font-weight: 900; color: #0A1628; line-height: 1.12; letter-spacing: -0.035em; margin-bottom: 0; }
    .hero-title .accent { background: linear-gradient(135deg, #1E5EFF 0%, #00C4A1 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }
    .hero-sub { font-size: 18px; color: #64748B; margin-top: 18px; line-height: 1.7; max-width: 560px; }

    /* ── Section headers ── */
    .section-header { display: flex; align-items: center; gap: 12px; margin-bottom: 20px; margin-top: 8px; }
    .section-header::before { content: ''; display: block; width: 4px; height: 22px; background: linear-gradient(180deg, #1E5EFF, #00C4A1); border-radius: 2px; flex-shrink: 0; }
    .section-header h2, .section-header h1 { margin: 0 !important; padding: 0 !important; }

    /* ── Feature/Step Cards ── */
    .step-box { background: #FFFFFF; border: 1px solid #E8EDF5; border-radius: 16px; padding: 28px 22px; text-align: center; transition: box-shadow 0.2s ease, transform 0.2s ease, border-color 0.2s ease; position: relative; overflow: hidden; height: 100%; }
    .step-box::after { content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3px; background: linear-gradient(90deg, #1E5EFF, #00C4A1); opacity: 0; transition: opacity 0.2s ease; }
    .step-box:hover { box-shadow: 0 12px 40px rgba(30,94,255,0.10); transform: translateY(-4px); border-color: #C7D7FF; }
    .step-box:hover::after { opacity: 1; }
    .step-num { font-size: 34px; font-weight: 800; color: #1E5EFF; font-family: 'DM Mono', monospace; line-height: 1; margin-bottom: 12px; }
    .step-box b { font-size: 15px; font-weight: 700; color: #1E293B; }
    .step-box .desc { color: #64748B; font-size: 13px; line-height: 1.65; display: block; margin-top: 8px; }

    /* ── Metric Cards ── */
    [data-testid="stMetric"] { background: #FFFFFF; border: 1px solid #E8EDF5; border-radius: 14px; padding: 18px 20px !important; transition: box-shadow 0.15s ease, border-color 0.15s ease; }
    [data-testid="stMetric"]:hover { box-shadow: 0 6px 20px rgba(30,94,255,0.09); border-color: #C7D7FF; }
    [data-testid="stMetricLabel"] p { font-size: 11px !important; font-weight: 700 !important; letter-spacing: 0.07em !important; text-transform: uppercase !important; color: #94A3B8 !important; }
    [data-testid="stMetricValue"] { font-size: 26px !important; font-weight: 800 !important; color: #0A1628 !important; letter-spacing: -0.02em !important; }

    /* ── Buttons ── */
   /* ── Buttons ── */
.stButton > button {
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
    font-size: 14px !important;
    border-radius: 9px !important;
    padding: 10px 22px !important;
    transition: all 0.2s ease !important;
}

/* Primary Button - Sky Blue */
.stButton > button[kind="primary"] {
    background: #87CEEB !important;
    color: #000000 !important;
    border: 1px solid #6BBDE8 !important;
    box-shadow: 0 4px 12px rgba(135,206,235,0.35) !important;
}

/* Hover Effect */
.stButton > button[kind="primary"]:hover {
    background: #6ECFF6 !important;
    color: #000000 !important;
    border-color: #4FB8E8 !important;
    box-shadow: 0 6px 18px rgba(135,206,235,0.45) !important;
    transform: translateY(-2px) !important;
}.stButton > button:not([kind="primary"]) { background: #FFFFFF !important; border: 1.5px solid #E2E8F0 !important; color: #374151 !important; }
    .stButton > button:not([kind="primary"]):hover { border-color: #1E5EFF !important; color: #1E5EFF !important; box-shadow: 0 3px 12px rgba(30,94,255,0.12) !important; }

    /* ── Text Inputs ── */
    .stTextInput > div > div > input, .stTextArea textarea { font-family: 'Inter', sans-serif !important; font-size: 15px !important; border: 1.5px solid #E2E8F0 !important; border-radius: 10px !important; padding: 12px 16px !important; transition: border-color 0.15s ease, box-shadow 0.15s ease !important; background: #FFFFFF !important; }
    .stTextInput > div > div > input:focus, .stTextArea textarea:focus { border-color: #1E5EFF !important; box-shadow: 0 0 0 3px rgba(30,94,255,0.10) !important; outline: none !important; }

    /* ── File Uploader ── */
    [data-testid="stFileUploader"] {
        border: 2.5px dashed #93C5FD !important;
        border-radius: 20px !important;
        padding: 48px 36px !important;
        background: linear-gradient(135deg, #F0F7FF 0%, #F8FAFC 100%) !important;
        transition: all 0.25s ease !important;
        position: relative !important;
    }
    [data-testid="stFileUploader"]:hover {
        border-color: #1E5EFF !important;
        background: linear-gradient(135deg, #EEF3FF 0%, #F0FDFA 100%) !important;
        box-shadow: 0 0 0 5px rgba(30,94,255,0.08), 0 8px 30px rgba(30,94,255,0.10) !important;
        transform: scale(1.01) !important;
    }
    /* Uploader inner label */
    [data-testid="stFileUploader"] label {
        font-weight: 600 !important;
        font-size: 15px !important;
        color: #1E293B !important;
    }
    /* Browse button inside uploader */
    [data-testid="stFileUploaderDropzoneInstructions"] {
        font-size: 14px !important;
        color: #64748B !important;
    }
    /* Pulsing ring animation on the uploader when idle */
    @keyframes pulse-ring {
        0%   { box-shadow: 0 0 0 0 rgba(30,94,255,0.15); }
        70%  { box-shadow: 0 0 0 10px rgba(30,94,255,0); }
        100% { box-shadow: 0 0 0 0 rgba(30,94,255,0); }
    }
    [data-testid="stFileUploader"] {
        animation: pulse-ring 3s ease-out infinite !important;
    }
    [data-testid="stFileUploader"]:hover {
        animation: none !important;
    }

    /* Drag overlay animation */
    #drop-overlay {
        animation: fadeInOverlay 0.2s ease;
    }
    @keyframes fadeInOverlay {
        from { opacity: 0; }
        to   { opacity: 1; }
    }

    /* ── Tabs ── */
    .stTabs [data-baseweb="tab-list"] { background: #F1F5F9; border-radius: 12px; padding: 5px; gap: 5px; border: none !important; }
    .stTabs [data-baseweb="tab"] { border-radius: 9px !important; font-weight: 500 !important; font-size: 14px !important; padding: 9px 20px !important; color: #64748B !important; border: none !important; }
    .stTabs [aria-selected="true"] { background: #FFFFFF !important; color: #1E5EFF !important; font-weight: 600 !important; box-shadow: 0 1px 6px rgba(0,0,0,0.09) !important; }

    /* ── Expander ── */
    details { border: 1px solid #E8EDF5 !important; border-radius: 12px !important; overflow: hidden !important; margin-bottom: 8px !important; }
    details summary { font-weight: 600 !important; font-size: 14px !important; padding: 14px 18px !important; background: #F8FAFC !important; color: #374151 !important; cursor: pointer !important; }
    details[open] summary { border-bottom: 1px solid #E8EDF5 !important; }

    /* ── Info / Advice Boxes ── */
    .advice-box { background: linear-gradient(135deg, #EEF3FF, #F0FDFA); border: 1px solid #C7D7FF; border-left: 4px solid #1E5EFF; padding: 24px 28px; border-radius: 0 14px 14px 0; font-size: 15px; line-height: 1.85; color: #1E293B; margin-bottom: 16px; }
    .answer-box { background: linear-gradient(135deg, #F0FDF9, #ECFDF5); border: 1px solid #A7F3D0; border-left: 4px solid #00A86B; padding: 22px 26px; border-radius: 0 14px 14px 0; font-size: 15px; line-height: 1.8; color: #1E293B; margin-top: 16px; }
    .warning-box { background: #FFFBEB; border: 1px solid #FDE68A; border-left: 4px solid #F59E0B; padding: 18px 22px; border-radius: 0 12px 12px 0; font-size: 14px; color: #78350F; }
    .info-box { background: #F8FAFC; border: 1px solid #E2E8F0; padding: 20px 24px; border-radius: 12px; font-size: 14px; color: #374151; }

    /* ── Scheme Cards ── */
    .scheme-card { background: #FFFFFF; border: 1.5px solid #E8EDF5; border-radius: 16px; padding: 24px 26px; margin-bottom: 14px; transition: box-shadow 0.2s, border-color 0.2s, transform 0.2s; }
    .scheme-card:hover { box-shadow: 0 10px 36px rgba(30,94,255,0.10); border-color: #C7D7FF; transform: translateY(-2px); }
    .scheme-badge { display: inline-block; font-size: 11px; font-weight: 700; padding: 4px 12px; border-radius: 100px; letter-spacing: 0.05em; text-transform: uppercase; margin-bottom: 12px; }
    .badge-gov  { background: #EEF3FF; color: #1E5EFF; }
    .badge-bank { background: #ECFDF5; color: #00A86B; }
    .badge-mf   { background: #FFF7ED; color: #EA580C; }
    .badge-ins  { background: #FDF2F8; color: #9333EA; }

    /* ── Chat / Q&A ── */
    .chat-user { background: linear-gradient(135deg, #1E5EFF, #0048D9); color: #FFFFFF; padding: 14px 20px; border-radius: 18px 18px 4px 18px; font-size: 15px; margin-bottom: 10px; margin-left: auto; max-width: 80%; box-shadow: 0 4px 14px rgba(30,94,255,0.25); }
    .chat-ai { background: #FFFFFF; border: 1px solid #E8EDF5; color: #1E293B; padding: 18px 22px; border-radius: 4px 18px 18px 18px; font-size: 15px; line-height: 1.78; margin-bottom: 28px; box-shadow: 0 2px 10px rgba(0,0,0,0.06); }
    .chat-empty { text-align: center; padding: 60px 20px; color: #94A3B8; }

    /* ── About Page ── */
    .about-stat { text-align: center; padding: 28px 20px; background: #FFFFFF; border: 1px solid #E8EDF5; border-radius: 16px; }
    .about-stat .stat-val { font-size: 40px; font-weight: 900; color: #1E5EFF; letter-spacing: -0.03em; font-family: 'DM Mono', monospace; }
    .about-stat .stat-label { font-size: 13px; color: #64748B; font-weight: 500; margin-top: 4px; }
    .team-card { background: #FFFFFF; border: 1px solid #E8EDF5; border-radius: 16px; padding: 28px 20px; text-align: center; transition: box-shadow 0.2s, transform 0.2s; }
    .team-card:hover { box-shadow: 0 8px 30px rgba(30,94,255,0.10); transform: translateY(-3px); }
    .tech-pill { display: inline-block; font-size: 12px; font-weight: 600; padding: 5px 13px; border-radius: 100px; margin: 4px; }

    /* ── Progress Bar ── */
    [data-testid="stProgressBar"] > div { background: linear-gradient(90deg, #1E5EFF, #00C4A1) !important; border-radius: 100px !important; }

    /* ── DataFrames ── */
    [data-testid="stDataFrame"] { border: 1px solid #E8EDF5 !important; border-radius: 12px !important; overflow: hidden !important; }

    /* ── Divider ── */
    hr { border: none !important; border-top: 1px solid #F1F5F9 !important; margin: 28px 0 !important; }

    /* ── Code ── */
    code { font-family: 'DM Mono', monospace !important; font-size: 13px !important; background: #F1F5F9 !important; padding: 2px 7px !important; border-radius: 5px !important; color: #374151 !important; }

    /* ── Alerts ── */
    .stAlert { border-radius: 12px !important; font-size: 14px !important; }

    /* ── Typography ── */
    h1 { font-size: 30px !important; font-weight: 800 !important; color: #0A1628 !important; letter-spacing: -0.025em !important; }
    h2 { font-size: 20px !important; font-weight: 700 !important; color: #1E293B !important; letter-spacing: -0.015em !important; }
    h3 { font-size: 16px !important; font-weight: 600 !important; color: #1E293B !important; }
    p, li { color: #374151 !important; line-height: 1.7 !important; }
    .stCaption p { color: #94A3B8 !important; font-size: 13px !important; }
    
    /* ===== Sidebar ===== */
[data-testid="stSidebar"] {
    background: #F8FBFF !important;
    border-right: 1px solid #D6EFFF;
}

/* Navigation Links */
[data-testid="stSidebarNav"] a {
    background: transparent !important;
    color: #2C3E50 !important;
    font-size: 15px !important;
    font-weight: 500 !important;
    border-radius: 10px !important;
    padding: 10px 14px !important;
    margin: 4px 8px !important;
    transition: all 0.3s ease !important;
}

/* Hover */
[data-testid="stSidebarNav"] a:hover {
    background: #87CEEB !important;
    color: #000000 !important;
    transform: translateX(4px);
}

/* Selected Page */
[data-testid="stSidebarNav"] li[data-selected="true"] a {
    background: #87CEEB !important;
    color: #000000 !important;
    font-weight: 700 !important;
    box-shadow: 0 3px 10px rgba(135,206,235,0.4);
}

/* Sidebar Heading */
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
    color: #0A1628 !important;
    font-weight: 700 !important;
}

    /* ── Responsive ── */
    @media (max-width: 768px) { .hero-title { font-size: 34px; } .hero-sub { font-size: 15px; } }
    </style>
    """, unsafe_allow_html=True)