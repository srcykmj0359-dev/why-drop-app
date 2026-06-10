import os
import re
import json
import html
import time
import hashlib
import traceback
import io
import zipfile
import xml.etree.ElementTree as ET
from urllib.parse import quote
from datetime import datetime
from pathlib import Path

import requests
import pandas as pd
import altair as alt
import streamlit as st
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from openai import OpenAI

try:
    from streamlit_searchbox import st_searchbox
except Exception:
    st_searchbox = None


# =============================
# 환경변수
# =============================
load_dotenv()

def get_config_value(name, default=None):
    """
    로컬에서는 .env, Streamlit Cloud에서는 Secrets 값을 읽는다.
    Streamlit Secrets에 값이 없으면 os.getenv로 fallback한다.
    """
    try:
        if hasattr(st, "secrets") and name in st.secrets:
            return st.secrets.get(name, default)
    except Exception:
        pass

    return os.getenv(name, default)


OPENAI_API_KEY = get_config_value("OPENAI_API_KEY")
NAVER_CLIENT_ID = get_config_value("NAVER_CLIENT_ID")
NAVER_CLIENT_SECRET = get_config_value("NAVER_CLIENT_SECRET")
DART_API_KEY = get_config_value("DART_API_KEY")

# 한국투자증권 Open API
KIS_APP_KEY = get_config_value("KIS_APP_KEY")
KIS_APP_SECRET = get_config_value("KIS_APP_SECRET")
KIS_ENV = str(get_config_value("KIS_ENV", "real")).lower()


# =============================
# Streamlit 설정
# =============================
st.set_page_config(
    page_title="왜빠짐",
    page_icon="📉",
    layout="wide"
)


# =============================
# CSS
# =============================
st.markdown(
    """
<style>

    .splash-screen {
        min-height: 82vh;
        display: flex;
        align-items: center;
        justify-content: center;
        text-align: center;
    }

    .splash-card {
        width: 100%;
        max-width: 520px;
        background: linear-gradient(135deg, #0f172a, #1e293b);
        color: white;
        padding: 46px 34px;
        border-radius: 34px;
        box-shadow: 0 28px 70px rgba(15,23,42,0.28);
        border: 1px solid rgba(255,255,255,0.08);
        animation: splashPop 0.7s ease-out;
    }

    .splash-icon {
        width: 88px;
        height: 88px;
        border-radius: 28px;
        background: linear-gradient(135deg, #fee2e2, #dbeafe);
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 0 auto 18px auto;
        font-size: 2.65rem;
        box-shadow: 0 18px 40px rgba(0,0,0,0.22);
        animation: floatIcon 1.35s ease-in-out infinite;
    }

    .splash-title {
        font-size: 2.7rem;
        font-weight: 950;
        letter-spacing: -1.3px;
        margin-bottom: 8px;
    }

    .splash-subtitle {
        color: #cbd5e1;
        font-size: 1.06rem;
        font-weight: 700;
        margin-bottom: 24px;
        line-height: 1.55;
    }

    .splash-loader {
        width: 100%;
        height: 10px;
        background: rgba(255,255,255,0.12);
        border-radius: 999px;
        overflow: hidden;
        margin-top: 8px;
    }

    .splash-loader-fill {
        height: 10px;
        border-radius: 999px;
        background: linear-gradient(90deg, #2563eb, #7c3aed, #ef4444);
        animation: loadFill 1.55s ease-in-out forwards;
    }

    .splash-note {
        margin-top: 14px;
        color: #94a3b8;
        font-weight: 700;
        font-size: 0.88rem;
    }

    .login-screen {
        min-height: 82vh;
        display: flex;
        align-items: center;
        justify-content: center;
    }

    .login-card {
        width: 100%;
        max-width: 520px;
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 34px;
        padding: 34px;
        box-shadow: 0 24px 60px rgba(15,23,42,0.12);
        text-align: center;
        animation: splashPop 0.55s ease-out;
    }

    .login-logo {
        width: 74px;
        height: 74px;
        border-radius: 24px;
        margin: 0 auto 14px auto;
        display: flex;
        align-items: center;
        justify-content: center;
        background: linear-gradient(135deg, #fee2e2, #dbeafe);
        font-size: 2.1rem;
        box-shadow: 0 12px 30px rgba(0,0,0,0.08);
    }

    .login-title {
        font-size: 2rem;
        font-weight: 950;
        color: #111827;
        letter-spacing: -0.9px;
        margin-bottom: 8px;
    }

    .login-subtitle {
        color: #6b7280;
        font-weight: 700;
        line-height: 1.65;
        margin-bottom: 18px;
    }

    .login-benefit {
        text-align: left;
        background: #f8fafc;
        border: 1px solid #e5e7eb;
        border-radius: 20px;
        padding: 16px;
        color: #334155;
        font-weight: 700;
        line-height: 1.8;
        margin-bottom: 18px;
    }

    .login-small {
        color: #94a3b8;
        font-size: 0.82rem;
        line-height: 1.6;
        margin-top: 12px;
    }

    .top-user-bar {
        display: flex;
        justify-content: flex-end;
        align-items: center;
        gap: 10px;
        margin-bottom: 8px;
        color: #64748b;
        font-size: 0.88rem;
        font-weight: 800;
    }

    @keyframes splashPop {
        from {
            opacity: 0;
            transform: translateY(16px) scale(0.96);
        }
        to {
            opacity: 1;
            transform: translateY(0) scale(1);
        }
    }

    @keyframes floatIcon {
        0%, 100% {
            transform: translateY(0);
        }
        50% {
            transform: translateY(-7px);
        }
    }

    @keyframes loadFill {
        from {
            width: 0%;
        }
        to {
            width: 100%;
        }
    }

    .main {
        background-color: #f6f8fb;
    }

    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1180px;
    }

    .app-title {
        font-size: 2.4rem;
        font-weight: 900;
        color: #111827;
        margin-bottom: 0.2rem;
        letter-spacing: -1px;
    }

    .app-subtitle {
        color: #6b7280;
        font-size: 1.05rem;
        margin-bottom: 1.6rem;
    }

    .section-title {
        font-size: 1.35rem;
        font-weight: 900;
        color: #111827;
        margin-top: 16px;
        margin-bottom: 14px;
        letter-spacing: -0.5px;
    }

    .kpi-card {
        background: linear-gradient(135deg, #ffffff, #f8fbff);
        padding: 20px;
        border-radius: 20px;
        box-shadow: 0 8px 22px rgba(0,0,0,0.05);
        border: 1px solid #e8eef5;
        text-align: center;
        min-height: 112px;
    }

    .kpi-label {
        font-size: 0.92rem;
        color: #6b7280;
        margin-bottom: 12px;
        font-weight: 700;
    }

    .kpi-value {
        font-size: 1.65rem;
        font-weight: 900;
        color: #111827;
        letter-spacing: -0.5px;
    }

    .negative {
        color: #dc2626;
    }

    .positive {
        color: #16a34a;
    }

    .neutral {
        color: #111827;
    }

    .source-small {
        font-size: 0.78rem;
        color: #9ca3af;
        margin-top: 8px;
    }

    .news-card {
        background: white;
        padding: 18px;
        border-radius: 18px;
        border-left: 6px solid #2563eb;
        box-shadow: 0 8px 24px rgba(0,0,0,0.045);
        margin-bottom: 14px;
    }

    .dart-card {
        background: white;
        padding: 18px;
        border-radius: 18px;
        border-left: 6px solid #f59e0b;
        box-shadow: 0 8px 24px rgba(0,0,0,0.045);
        margin-bottom: 14px;
    }

    .card-title {
        font-weight: 900;
        font-size: 1.05rem;
        color: #111827;
        margin-bottom: 8px;
        line-height: 1.45;
    }

    .card-title a {
        color: #111827;
        text-decoration: none;
    }

    .card-title a:hover {
        color: #2563eb;
        text-decoration: underline;
    }

    .card-desc {
        color: #4b5563;
        line-height: 1.65;
        font-size: 0.98rem;
    }

    .card-date {
        color: #9ca3af;
        font-size: 0.82rem;
        margin-top: 8px;
    }

    .ai-summary-card {
        background: linear-gradient(135deg, #111827, #1f2937);
        color: white;
        padding: 26px;
        border-radius: 24px;
        box-shadow: 0 12px 34px rgba(0,0,0,0.15);
        margin-bottom: 18px;
    }

    .ai-summary-title {
        font-size: 0.95rem;
        color: #d1d5db;
        margin-bottom: 10px;
        font-weight: 700;
    }

    .ai-summary-text {
        font-size: 1.32rem;
        font-weight: 900;
        line-height: 1.55;
        letter-spacing: -0.3px;
        margin-bottom: 18px;
    }

    .risk-badge-low {
        display: inline-block;
        background: #dcfce7;
        color: #166534;
        padding: 9px 15px;
        border-radius: 999px;
        font-weight: 900;
        font-size: 0.95rem;
    }

    .risk-badge-mid {
        display: inline-block;
        background: #fef3c7;
        color: #92400e;
        padding: 9px 15px;
        border-radius: 999px;
        font-weight: 900;
        font-size: 0.95rem;
    }

    .risk-badge-high {
        display: inline-block;
        background: #fee2e2;
        color: #991b1b;
        padding: 9px 15px;
        border-radius: 999px;
        font-weight: 900;
        font-size: 0.95rem;
    }

    .reason-card {
        background: white;
        padding: 19px;
        border-radius: 20px;
        border: 1px solid #e5e7eb;
        box-shadow: 0 8px 24px rgba(0,0,0,0.045);
        margin-bottom: 14px;
    }

    .reason-title {
        font-weight: 900;
        font-size: 1.08rem;
        color: #111827;
        margin-bottom: 9px;
        letter-spacing: -0.3px;
    }

    .reason-desc {
        color: #4b5563;
        line-height: 1.65;
        font-size: 0.98rem;
    }

    .keyword-chip {
        display: inline-block;
        background: #eef2ff;
        color: #3730a3;
        padding: 9px 13px;
        border-radius: 999px;
        font-weight: 800;
        margin-right: 8px;
        margin-bottom: 8px;
        font-size: 0.92rem;
    }

    .check-card {
        background: #ffffff;
        padding: 15px 17px;
        border-radius: 16px;
        border: 1px solid #e5e7eb;
        margin-bottom: 10px;
        font-weight: 700;
        color: #374151;
        box-shadow: 0 6px 18px rgba(0,0,0,0.035);
        line-height: 1.55;
    }


    .insight-card {
        background: linear-gradient(135deg, #0f172a, #1e293b);
        color: white;
        padding: 26px;
        border-radius: 24px;
        box-shadow: 0 16px 38px rgba(15,23,42,0.20);
        margin-top: 18px;
        margin-bottom: 18px;
    }

    .insight-label {
        color: #cbd5e1;
        font-size: 0.92rem;
        font-weight: 800;
        margin-bottom: 10px;
    }

    .insight-title {
        font-size: 1.35rem;
        font-weight: 950;
        line-height: 1.5;
        margin-bottom: 16px;
        letter-spacing: -0.4px;
    }

    .mini-chip {
        display: inline-block;
        padding: 8px 12px;
        border-radius: 999px;
        background: rgba(255,255,255,0.12);
        color: #e5e7eb;
        font-weight: 800;
        font-size: 0.88rem;
        margin-right: 8px;
        margin-bottom: 8px;
    }

    .score-wrap {
        background: white;
        padding: 22px;
        border-radius: 22px;
        border: 1px solid #e5e7eb;
        box-shadow: 0 10px 28px rgba(0,0,0,0.055);
        margin-bottom: 18px;
    }

    .score-row {
        margin-bottom: 15px;
    }

    .score-head {
        display: flex;
        justify-content: space-between;
        align-items: center;
        color: #111827;
        font-weight: 900;
        margin-bottom: 7px;
    }

    .score-sub {
        color: #6b7280;
        font-size: 0.84rem;
        font-weight: 700;
    }

    .score-track {
        width: 100%;
        height: 12px;
        background: #eef2f7;
        border-radius: 999px;
        overflow: hidden;
    }

    .score-fill {
        height: 12px;
        border-radius: 999px;
        background: linear-gradient(90deg, #2563eb, #7c3aed);
    }

    .ad-card {
        background: linear-gradient(135deg, #f8fafc, #eef2ff);
        border: 1px dashed #a5b4fc;
        padding: 18px;
        border-radius: 20px;
        margin: 18px 0;
        color: #334155;
        box-shadow: 0 8px 20px rgba(0,0,0,0.035);
    }

    .ad-title {
        font-weight: 950;
        color: #1e293b;
        margin-bottom: 6px;
    }

    .locked-card {
        background: white;
        border: 1px solid #e5e7eb;
        padding: 22px;
        border-radius: 22px;
        box-shadow: 0 10px 28px rgba(0,0,0,0.05);
        margin-top: 18px;
        margin-bottom: 18px;
    }

    .locked-title {
        font-size: 1.15rem;
        font-weight: 950;
        color: #111827;
        margin-bottom: 8px;
    }

    .locked-desc {
        color: #4b5563;
        line-height: 1.7;
        margin-bottom: 14px;
    }

    .premium-card {
        background: linear-gradient(135deg, #fff7ed, #fffbeb);
        border: 1px solid #fed7aa;
        padding: 20px;
        border-radius: 22px;
        box-shadow: 0 10px 24px rgba(0,0,0,0.04);
        margin-top: 12px;
    }








    /* =============================
       V1.1.7 Chart Width Fix
       모바일/PC에서 Altair 차트가 본문 영역을 벗어나지 않도록 제한
    ============================= */
    div[data-testid="stVegaLiteChart"] {
        width: 100% !important;
        max-width: 100% !important;
        overflow: hidden !important;
    }

    div[data-testid="stVegaLiteChart"] > div {
        width: 100% !important;
        max-width: 100% !important;
        overflow: hidden !important;
    }

    div[data-testid="stVegaLiteChart"] svg {
        max-width: 100% !important;
    }

    @media (max-width: 760px) {
        div[data-testid="stVegaLiteChart"] {
            overflow-x: hidden !important;
        }
    }

    /* =============================
       V1.1.6 Beginner Friendly Chart
       초보자용 차트 가독성 개선
    ============================= */
    .beginner-chart-guide {
        background: linear-gradient(135deg, #ffffff, #f8fafc);
        border: 1px solid #e2e8f0;
        border-radius: 22px;
        padding: 15px 16px;
        margin: 10px 0 14px 0;
        box-shadow: 0 10px 26px rgba(15,23,42,0.045);
    }

    .beginner-chart-title {
        color: #0f172a;
        font-size: 1.02rem;
        font-weight: 1000;
        margin-bottom: 6px;
    }

    .beginner-chart-desc {
        color: #475569;
        font-size: 0.84rem;
        font-weight: 760;
        line-height: 1.65;
    }

    .beginner-chart-legend {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin-top: 10px;
    }

    .legend-pill {
        border-radius: 999px;
        padding: 6px 10px;
        font-size: 0.76rem;
        font-weight: 900;
        background: #f1f5f9;
        color: #334155;
        border: 1px solid #e2e8f0;
    }

    .legend-pill.price-up {
        background: #fef2f2;
        color: #b91c1c;
        border-color: #fecaca;
    }

    .legend-pill.price-down {
        background: #eff6ff;
        color: #1d4ed8;
        border-color: #bfdbfe;
    }

    .legend-pill.volume {
        background: #f8fafc;
        color: #475569;
        border-color: #cbd5e1;
    }

    .chart-label-row {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 10px;
        margin: 10px 0 4px 0;
    }

    .chart-label-box {
        background: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 18px;
        padding: 11px 13px;
    }

    .chart-label-title {
        font-size: 0.78rem;
        font-weight: 1000;
        color: #0f172a;
        margin-bottom: 4px;
    }

    .chart-label-desc {
        font-size: 0.74rem;
        font-weight: 760;
        color: #64748b;
        line-height: 1.55;
    }

    @media (max-width: 760px) {
        .chart-label-row {
            grid-template-columns: 1fr !important;
        }

        .beginner-chart-guide {
            padding: 13px 13px !important;
            border-radius: 18px !important;
        }

        .beginner-chart-title {
            font-size: 0.94rem !important;
        }

        .beginner-chart-desc {
            font-size: 0.78rem !important;
        }

        .legend-pill {
            font-size: 0.70rem !important;
            padding: 5px 8px !important;
        }
    }

    /* =============================
       V1.1.5 Premium Search Dropdown UI
       자동완성 후보 리스트 고급화
    ============================= */
    div[role="listbox"] {
        border-radius: 18px !important;
        border: 1px solid #dbeafe !important;
        box-shadow: 0 18px 44px rgba(15, 23, 42, 0.14) !important;
        overflow: hidden !important;
        padding: 6px !important;
        background: #ffffff !important;
    }

    div[role="option"] {
        min-height: 44px !important;
        padding: 12px 14px !important;
        border-radius: 14px !important;
        color: #0f172a !important;
        font-size: 0.92rem !important;
        font-weight: 850 !important;
        letter-spacing: -0.15px !important;
        border-bottom: 1px solid rgba(226, 232, 240, 0.55) !important;
    }

    div[role="option"]:hover,
    div[role="option"][aria-selected="true"] {
        background: linear-gradient(135deg, #eff6ff, #eef2ff) !important;
        color: #1d4ed8 !important;
    }

    div[role="combobox"] {
        border-radius: 15px !important;
    }

    .stock-search-preview {
        background: linear-gradient(135deg, #ffffff, #f8fafc);
        border: 1px solid #e2e8f0;
        border-radius: 22px;
        padding: 13px 15px;
        margin: 8px 0 14px 0;
        box-shadow: 0 10px 26px rgba(15,23,42,0.045);
    }

    .stock-search-preview-title {
        color: #0f172a;
        font-size: 0.88rem;
        font-weight: 1000;
        margin-bottom: 5px;
    }

    .stock-search-preview-desc {
        color: #64748b;
        font-size: 0.78rem;
        font-weight: 760;
        line-height: 1.55;
    }

    @media (max-width: 760px) {
        div[role="option"] {
            min-height: 42px !important;
            padding: 11px 12px !important;
            font-size: 0.84rem !important;
        }

        .stock-search-preview {
            padding: 12px 13px !important;
            border-radius: 18px !important;
        }
    }

    /* =============================
       V1.1.3 Google-like Stock Searchbox
    ============================= */
    .search-helper-card {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 18px;
        padding: 11px 13px;
        color: #475569;
        font-size: 0.80rem;
        font-weight: 780;
        margin: 8px 0 14px 0;
        line-height: 1.55;
    }

    .search-selected-card {
        background: #eff6ff;
        border: 1px solid #bfdbfe;
        border-radius: 18px;
        padding: 11px 13px;
        color: #1e3a8a;
        font-size: 0.84rem;
        font-weight: 900;
        margin: 8px 0 14px 0;
    }

    @media (max-width: 760px) {
        .search-helper-card,
        .search-selected-card {
            font-size: 0.74rem !important;
            border-radius: 16px !important;
            padding: 10px 11px !important;
        }
    }

    /* =============================
       V1.1.0 KIS Free Chart
       차트는 무료 핵심 기능으로 제공
    ============================= */

    .premium-chart-card {
        background: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 24px;
        padding: 18px 18px 14px 18px;
        margin: 14px 0 18px 0;
        box-shadow: 0 14px 34px rgba(15,23,42,0.055);
    }

    .premium-chart-title {
        font-size: 1.05rem;
        font-weight: 1000;
        color: #111827;
        margin-bottom: 4px;
    }

    .premium-chart-sub {
        font-size: 0.82rem;
        font-weight: 780;
        color: #64748b;
        line-height: 1.55;
        margin-bottom: 10px;
    }

    .chart-source-note {
        color: #94a3b8;
        font-size: 0.74rem;
        font-weight: 760;
        margin-top: 8px;
    }

    @media (max-width: 760px) {
        .premium-chart-card {
            padding: 14px 12px 12px 12px !important;
            border-radius: 20px !important;
        }

        .premium-chart-title {
            font-size: 0.96rem !important;
        }

        .premium-chart-sub {
            font-size: 0.76rem !important;
        }
    }

    .chart-info-card {
        background: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 22px;
        padding: 16px 18px;
        margin: 12px 0 16px 0;
        box-shadow: 0 10px 24px rgba(15,23,42,0.045);
    }

    .chart-info-title {
        font-size: 1.02rem;
        font-weight: 1000;
        color: #111827;
        margin-bottom: 6px;
    }

    .chart-info-desc {
        color: #475569;
        font-size: 0.88rem;
        font-weight: 760;
        line-height: 1.65;
    }

    .chart-mini-grid {
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 10px;
        margin-top: 12px;
    }

    .chart-mini-box {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 16px;
        padding: 11px 12px;
    }

    .chart-mini-label {
        color: #64748b;
        font-size: 0.74rem;
        font-weight: 900;
        margin-bottom: 4px;
    }

    .chart-mini-value {
        color: #0f172a;
        font-size: 0.92rem;
        font-weight: 1000;
    }

    @media (max-width: 760px) {
        .chart-mini-grid {
            grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
        }

        .chart-info-card {
            padding: 14px 14px !important;
            border-radius: 20px !important;
        }

        .chart-info-title {
            font-size: 0.96rem !important;
        }

        .chart-info-desc {
            font-size: 0.80rem !important;
        }
    }

    /* =============================
       V0.9.7 PRO Demand Validation
       유료 버튼 클릭 시 무엇이 열리는지 3초 안에 이해시키는 카드
    ============================= */

    .pro-compact-card {
        background: linear-gradient(135deg, #111827, #312e81);
        color: white;
        border-radius: 22px;
        padding: 18px 18px;
        margin: 14px 0 12px 0;
        box-shadow: 0 14px 30px rgba(17,24,39,0.16);
        border: 1px solid rgba(255,255,255,0.10);
    }

    .pro-compact-top {
        display: flex;
        justify-content: space-between;
        gap: 10px;
        align-items: center;
        margin-bottom: 8px;
    }

    .pro-compact-badge {
        display: inline-block;
        background: rgba(250,204,21,0.16);
        color: #fde68a;
        border: 1px solid rgba(250,204,21,0.24);
        border-radius: 999px;
        padding: 6px 10px;
        font-size: 0.74rem;
        font-weight: 950;
        white-space: nowrap;
    }

    .pro-compact-price {
        display: inline-block;
        background: rgba(255,255,255,0.12);
        border: 1px solid rgba(255,255,255,0.14);
        border-radius: 999px;
        padding: 6px 10px;
        font-size: 0.76rem;
        font-weight: 950;
        color: #ffffff;
        white-space: nowrap;
    }

    .pro-compact-title {
        font-size: 1.02rem;
        font-weight: 1000;
        letter-spacing: -0.25px;
        line-height: 1.45;
        margin-bottom: 6px;
    }

    .pro-compact-desc {
        color: #dbeafe;
        font-size: 0.84rem;
        font-weight: 760;
        line-height: 1.6;
    }

    .pro-compact-points {
        display: flex;
        flex-wrap: wrap;
        gap: 7px;
        margin-top: 12px;
    }

    .pro-compact-point {
        background: rgba(255,255,255,0.10);
        border: 1px solid rgba(255,255,255,0.12);
        color: #e5e7eb;
        border-radius: 999px;
        padding: 6px 9px;
        font-size: 0.74rem;
        font-weight: 900;
    }

    .pro-click-guide {
        color: #64748b;
        font-size: 0.78rem;
        font-weight: 760;
        margin-top: -2px;
        margin-bottom: 10px;
        padding-left: 2px;
    }

    @media (max-width: 760px) {
        .pro-compact-card {
            padding: 16px 14px !important;
            border-radius: 20px !important;
        }

        .pro-compact-top {
            align-items: flex-start !important;
            flex-direction: column !important;
            gap: 6px !important;
        }

        .pro-compact-title {
            font-size: 0.96rem !important;
        }

        .pro-compact-desc {
            font-size: 0.78rem !important;
        }

        .pro-compact-point {
            font-size: 0.70rem !important;
            padding: 5px 8px !important;
        }
    }

    .pro-hero-card {
        background: linear-gradient(135deg, #111827, #312e81);
        color: white;
        border-radius: 26px;
        padding: 24px 22px;
        margin: 18px 0 14px 0;
        box-shadow: 0 18px 42px rgba(17,24,39,0.22);
        border: 1px solid rgba(255,255,255,0.10);
    }

    .pro-kicker {
        display: inline-block;
        background: rgba(250,204,21,0.16);
        color: #fde68a;
        border: 1px solid rgba(250,204,21,0.24);
        border-radius: 999px;
        padding: 7px 11px;
        font-size: 0.78rem;
        font-weight: 950;
        margin-bottom: 12px;
    }

    .pro-title {
        font-size: 1.42rem;
        font-weight: 1000;
        letter-spacing: -0.5px;
        margin-bottom: 8px;
        line-height: 1.35;
    }

    .pro-subtitle {
        color: #dbeafe;
        font-size: 0.96rem;
        font-weight: 760;
        line-height: 1.75;
        margin-bottom: 16px;
    }

    .pro-price {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        background: white;
        color: #111827;
        border-radius: 16px;
        padding: 11px 13px;
        font-weight: 1000;
        margin-bottom: 14px;
        box-shadow: 0 10px 24px rgba(0,0,0,0.13);
    }

    .pro-grid {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 10px;
        margin-top: 12px;
    }

    .pro-feature {
        background: rgba(255,255,255,0.10);
        border: 1px solid rgba(255,255,255,0.12);
        border-radius: 18px;
        padding: 13px 13px;
    }

    .pro-feature-title {
        font-size: 0.92rem;
        font-weight: 1000;
        color: #ffffff;
        margin-bottom: 5px;
    }

    .pro-feature-desc {
        font-size: 0.80rem;
        font-weight: 720;
        color: #dbeafe;
        line-height: 1.55;
    }

    .compare-card {
        background: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 24px;
        padding: 20px;
        margin: 14px 0;
        box-shadow: 0 12px 30px rgba(15,23,42,0.06);
    }

    .compare-title {
        font-size: 1.08rem;
        font-weight: 1000;
        color: #111827;
        margin-bottom: 12px;
    }

    .compare-grid {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 12px;
    }

    .compare-box-free {
        border: 1px solid #e5e7eb;
        background: #f8fafc;
        border-radius: 20px;
        padding: 15px;
    }

    .compare-box-pro {
        border: 1px solid #c4b5fd;
        background: linear-gradient(135deg, #faf5ff, #eef2ff);
        border-radius: 20px;
        padding: 15px;
    }

    .compare-head {
        font-weight: 1000;
        color: #111827;
        margin-bottom: 8px;
    }

    .compare-line {
        color: #475569;
        font-size: 0.87rem;
        font-weight: 760;
        line-height: 1.75;
    }

    .pro-detail-card {
        background: linear-gradient(135deg, #fff7ed, #fffbeb);
        border: 1px solid #fed7aa;
        border-radius: 24px;
        padding: 20px;
        margin: 16px 0;
        box-shadow: 0 12px 30px rgba(251,146,60,0.10);
    }

    .pro-detail-title {
        font-size: 1.18rem;
        font-weight: 1000;
        color: #111827;
        margin-bottom: 8px;
    }

    .pro-detail-desc {
        color: #57534e;
        font-weight: 760;
        line-height: 1.7;
        margin-bottom: 12px;
    }

    .pro-proof {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 18px;
        padding: 14px;
        margin: 12px 0;
        color: #334155;
        font-size: 0.88rem;
        font-weight: 760;
        line-height: 1.65;
    }

    .pro-success-card {
        background: #ecfdf5;
        border: 1px solid #bbf7d0;
        color: #166534;
        border-radius: 20px;
        padding: 16px;
        margin: 12px 0;
        font-weight: 900;
        line-height: 1.65;
    }

    @media (max-width: 760px) {
        .pro-hero-card {
            padding: 20px 16px !important;
            border-radius: 24px !important;
        }

        .pro-title {
            font-size: 1.18rem !important;
        }

        .pro-subtitle {
            font-size: 0.86rem !important;
        }

        .pro-grid,
        .compare-grid {
            grid-template-columns: 1fr !important;
        }

        .pro-feature-title {
            font-size: 0.88rem !important;
        }

        .pro-feature-desc,
        .compare-line {
            font-size: 0.78rem !important;
        }
    }

    .deep-section-card {
        background: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 22px;
        padding: 20px;
        margin-bottom: 14px;
        box-shadow: 0 10px 26px rgba(0,0,0,0.045);
    }

    .deep-title {
        font-size: 1.08rem;
        font-weight: 950;
        color: #111827;
        margin-bottom: 8px;
    }

    .deep-desc {
        color: #4b5563;
        line-height: 1.75;
        font-size: 0.98rem;
    }

    .deep-grid {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 12px;
        margin-top: 12px;
    }

    .deep-mini {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 16px;
        padding: 14px;
    }

    .deep-mini-label {
        color: #64748b;
        font-size: 0.82rem;
        font-weight: 800;
        margin-bottom: 6px;
    }

    .deep-mini-value {
        color: #0f172a;
        font-size: 1.05rem;
        font-weight: 950;
    }

    .danger-chip {
        display: inline-block;
        background: #fee2e2;
        color: #991b1b;
        padding: 8px 11px;
        border-radius: 999px;
        font-weight: 900;
        font-size: 0.86rem;
        margin-right: 7px;
        margin-bottom: 7px;
    }

    .safe-chip {
        display: inline-block;
        background: #dcfce7;
        color: #166534;
        padding: 8px 11px;
        border-radius: 999px;
        font-weight: 900;
        font-size: 0.86rem;
        margin-right: 7px;
        margin-bottom: 7px;
    }

    .neutral-chip2 {
        display: inline-block;
        background: #eef2ff;
        color: #3730a3;
        padding: 8px 11px;
        border-radius: 999px;
        font-weight: 900;
        font-size: 0.86rem;
        margin-right: 7px;
        margin-bottom: 7px;
    }


    /* =============================
       V0.5 Pretty Login Override
    ============================= */
    .login-screen {
        min-height: 82vh;
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 18px;
        background:
            radial-gradient(circle at 20% 20%, rgba(37,99,235,0.10), transparent 28%),
            radial-gradient(circle at 80% 18%, rgba(124,58,237,0.10), transparent 26%),
            radial-gradient(circle at 50% 90%, rgba(239,68,68,0.07), transparent 30%);
    }

    .login-card {
        width: 100%;
        max-width: 460px;
        background: rgba(255,255,255,0.90);
        backdrop-filter: blur(18px);
        border: 1px solid rgba(226,232,240,0.95);
        border-radius: 34px;
        padding: 34px 30px 28px 30px;
        box-shadow: 0 28px 70px rgba(15,23,42,0.13);
        text-align: center;
        animation: splashPop 0.55s ease-out;
    }

    .login-logo {
        width: 78px;
        height: 78px;
        border-radius: 26px;
        margin: 0 auto 16px auto;
        display: flex;
        align-items: center;
        justify-content: center;
        background: linear-gradient(135deg, #ffe4e6, #dbeafe);
        font-size: 2.2rem;
        box-shadow: 0 16px 34px rgba(15,23,42,0.12);
    }

    .login-title {
        font-size: 2.05rem;
        font-weight: 950;
        color: #0f172a;
        letter-spacing: -1px;
        margin-bottom: 8px;
    }

    .login-subtitle {
        color: #64748b;
        font-weight: 750;
        line-height: 1.65;
        margin-bottom: 18px;
        font-size: 0.98rem;
    }

    .login-benefit {
        text-align: left;
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 22px;
        padding: 16px 17px;
        color: #334155;
        font-weight: 800;
        line-height: 1.85;
        margin-bottom: 20px;
        font-size: 0.92rem;
    }

    .social-preview {
        margin-top: 6px;
    }

    .social-btn {
        width: 100%;
        height: 52px;
        border-radius: 17px;
        border: 1px solid transparent;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 10px;
        font-weight: 950;
        font-size: 0.98rem;
        margin-bottom: 10px;
        box-shadow: 0 10px 22px rgba(15,23,42,0.055);
    }

    .social-kakao {
        background: #FEE500;
        color: #191919;
    }

    .social-naver {
        background: #03C75A;
        color: white;
    }

    .social-google {
        background: #ffffff;
        color: #111827;
        border: 1px solid #dbe3ef;
    }

    .social-email {
        background: #0f172a;
        color: white;
    }

    .social-icon {
        width: 25px;
        height: 25px;
        border-radius: 8px;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-weight: 950;
        font-size: 0.9rem;
    }

    .icon-kakao {
        background: rgba(0,0,0,0.10);
        color: #191919;
    }

    .icon-naver {
        background: rgba(255,255,255,0.22);
        color: white;
    }

    .icon-google {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        color: #4285F4;
    }

    .icon-email {
        background: rgba(255,255,255,0.13);
        color: white;
    }

    .login-divider {
        display: flex;
        align-items: center;
        gap: 12px;
        margin: 16px 0 14px 0;
        color: #94a3b8;
        font-size: 0.82rem;
        font-weight: 900;
    }

    .login-divider:before,
    .login-divider:after {
        content: "";
        flex: 1;
        height: 1px;
        background: #e2e8f0;
    }

    .guest-link {
        color: #64748b;
        font-weight: 900;
        font-size: 0.92rem;
        text-decoration: underline;
        text-underline-offset: 4px;
        margin-top: 6px;
        display: inline-block;
    }

    .login-small {
        color: #94a3b8;
        font-size: 0.80rem;
        line-height: 1.6;
        margin-top: 14px;
    }

    .login-action-box {
        max-width: 460px;
        margin: -8px auto 0 auto;
        padding: 0 18px;
    }

    .login-action-box .stButton > button {
        height: 46px;
        border-radius: 16px;
        font-weight: 950;
        margin-bottom: 2px;
        opacity: 0.96;
    }


    /* =============================
       V0.5.3 Real Clickable Pretty Login
       HTML 링크 방식: 예쁜 버튼 자체가 클릭됨
    ============================= */
    .login-screen {
        min-height: 82vh !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        padding: 18px !important;
        background:
            radial-gradient(circle at 20% 20%, rgba(37,99,235,0.10), transparent 28%),
            radial-gradient(circle at 80% 18%, rgba(124,58,237,0.10), transparent 26%),
            radial-gradient(circle at 50% 90%, rgba(239,68,68,0.07), transparent 30%) !important;
    }

    .login-card {
        width: 100% !important;
        max-width: 460px !important;
        background: rgba(255,255,255,0.92) !important;
        backdrop-filter: blur(18px) !important;
        border: 1px solid rgba(226,232,240,0.95) !important;
        border-radius: 34px !important;
        padding: 34px 30px 28px 30px !important;
        box-shadow: 0 28px 70px rgba(15,23,42,0.13) !important;
        text-align: center !important;
        animation: splashPop 0.55s ease-out !important;
    }

    .social-btn {
        width: 100%;
        height: 52px;
        border-radius: 17px;
        border: 1px solid transparent;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 10px;
        font-weight: 950;
        font-size: 0.98rem;
        margin-bottom: 10px;
        box-shadow: 0 10px 22px rgba(15,23,42,0.055);
        text-decoration: none !important;
        transition: transform .12s ease, box-shadow .12s ease;
        box-sizing: border-box;
    }

    .social-btn:hover {
        transform: translateY(-1px);
        box-shadow: 0 14px 28px rgba(15,23,42,0.10);
        text-decoration: none !important;
    }

    .social-kakao {
        background: #FEE500 !important;
        color: #191919 !important;
    }

    .social-naver {
        background: #03C75A !important;
        color: white !important;
    }

    .social-google {
        background: #ffffff !important;
        color: #111827 !important;
        border: 1px solid #dbe3ef !important;
    }

    .social-email {
        background: #0f172a !important;
        color: white !important;
    }

    .guest-link {
        color: #64748b !important;
        font-weight: 900 !important;
        font-size: 0.92rem !important;
        text-decoration: underline !important;
        text-underline-offset: 4px !important;
        margin-top: 8px !important;
        display: inline-block !important;
    }


    /* =============================
       V0.5.6 Safe Streamlit Real Buttons
    ============================= */
    .login-screen {
        min-height: auto !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        padding: 42px 18px 10px 18px !important;
        background:
            radial-gradient(circle at 20% 20%, rgba(37,99,235,0.10), transparent 28%),
            radial-gradient(circle at 80% 18%, rgba(124,58,237,0.10), transparent 26%),
            radial-gradient(circle at 50% 90%, rgba(239,68,68,0.07), transparent 30%) !important;
    }

    .login-card-clean {
        width: 100%;
        max-width: 460px;
        background: rgba(255,255,255,0.92);
        backdrop-filter: blur(18px);
        border: 1px solid rgba(226,232,240,0.95);
        border-radius: 34px;
        padding: 34px 30px 26px 30px;
        box-shadow: 0 28px 70px rgba(15,23,42,0.13);
        text-align: center;
        animation: splashPop 0.55s ease-out;
        margin: 0 auto;
    }

    .login-action-box {
        max-width: 460px;
        margin: 12px auto 0 auto !important;
        padding: 0 18px 40px 18px !important;
    }

    .login-action-box .stButton > button {
        height: 52px !important;
        border-radius: 17px !important;
        font-weight: 950 !important;
        margin-bottom: 7px !important;
        box-shadow: 0 10px 22px rgba(15,23,42,0.055) !important;
        border: 1px solid #dbe3ef !important;
        background: #ffffff !important;
        color: #111827 !important;
    }

    .login-action-box .stButton > button:hover {
        border: 1px solid #2563eb !important;
        background: #f8fbff !important;
        color: #111827 !important;
        transform: translateY(-1px);
    }


    /* =============================
       V0.5.9 Main HTML Clickable Login
       Streamlit markdown 내부 minified HTML이라 코드블록으로 안 뜸
    ============================= */
    .login-screen {
        min-height: 82vh !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        padding: 18px !important;
        background:
            radial-gradient(circle at 20% 20%, rgba(37,99,235,0.10), transparent 28%),
            radial-gradient(circle at 80% 18%, rgba(124,58,237,0.10), transparent 26%),
            radial-gradient(circle at 50% 90%, rgba(239,68,68,0.07), transparent 30%) !important;
    }

    .login-card {
        width: 100% !important;
        max-width: 460px !important;
        background: rgba(255,255,255,0.94) !important;
        backdrop-filter: blur(18px) !important;
        border: 1px solid rgba(226,232,240,0.95) !important;
        border-radius: 34px !important;
        padding: 34px 30px 28px 30px !important;
        box-shadow: 0 28px 70px rgba(15,23,42,0.13) !important;
        text-align: center !important;
        animation: splashPop 0.55s ease-out !important;
        margin: 0 auto !important;
    }

    .social-btn {
        width: 100% !important;
        height: 52px !important;
        border-radius: 17px !important;
        border: 1px solid transparent !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        gap: 10px !important;
        font-weight: 950 !important;
        font-size: 0.98rem !important;
        margin-bottom: 10px !important;
        box-shadow: 0 10px 22px rgba(15,23,42,0.055) !important;
        text-decoration: none !important;
        transition: transform .12s ease, box-shadow .12s ease, filter .12s ease !important;
        box-sizing: border-box !important;
    }

    .social-btn:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 14px 28px rgba(15,23,42,0.10) !important;
        text-decoration: none !important;
        filter: brightness(0.99) !important;
    }

    .social-kakao {
        background: #FEE500 !important;
        color: #191919 !important;
    }

    .social-naver {
        background: #03C75A !important;
        color: white !important;
    }

    .social-google {
        background: #ffffff !important;
        color: #111827 !important;
        border: 1px solid #dbe3ef !important;
    }

    .social-email {
        background: #0f172a !important;
        color: white !important;
    }

    .guest-link {
        color: #64748b !important;
        font-weight: 900 !important;
        font-size: 0.92rem !important;
        text-decoration: underline !important;
        text-underline-offset: 4px !important;
        margin-top: 8px !important;
        display: inline-block !important;
    }


    /* =============================
       V0.6 Watchlist
    ============================= */
    .watch-card {
        background: linear-gradient(135deg, #ffffff, #f8fbff);
        border: 1px solid #e5e7eb;
        border-radius: 22px;
        padding: 18px;
        box-shadow: 0 10px 26px rgba(0,0,0,0.045);
        margin-bottom: 18px;
    }

    .watch-title {
        font-size: 1.15rem;
        font-weight: 950;
        color: #111827;
        margin-bottom: 8px;
    }

    .watch-sub {
        color: #64748b;
        font-size: 0.9rem;
        font-weight: 700;
        margin-bottom: 12px;
        line-height: 1.55;
    }

    .watch-item {
        background: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 16px;
        padding: 13px 14px;
        margin-bottom: 8px;
        box-shadow: 0 6px 16px rgba(0,0,0,0.035);
    }

    .watch-name {
        font-weight: 950;
        color: #111827;
        font-size: 0.98rem;
        margin-bottom: 3px;
    }

    .watch-meta {
        color: #94a3b8;
        font-size: 0.78rem;
        font-weight: 700;
    }

    .watch-empty {
        background: #f8fafc;
        border: 1px dashed #cbd5e1;
        border-radius: 16px;
        padding: 14px;
        color: #64748b;
        font-weight: 750;
        line-height: 1.6;
    }

    .watch-action {
        background: #eef2ff;
        border: 1px solid #c7d2fe;
        color: #3730a3;
        padding: 12px 14px;
        border-radius: 16px;
        font-weight: 900;
        line-height: 1.55;
        margin-bottom: 14px;
    }


    /* =============================
       V0.6.2 Score Board Redesign
    ============================= */
    .score-board-v2 {
        background: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 24px;
        padding: 22px;
        box-shadow: 0 12px 30px rgba(15,23,42,0.06);
        margin-bottom: 20px;
    }

    .score-guide {
        background: linear-gradient(135deg, #f8fafc, #eef2ff);
        border: 1px solid #dbe3ef;
        border-radius: 18px;
        padding: 15px 16px;
        margin-bottom: 18px;
        color: #334155;
        font-weight: 750;
        line-height: 1.65;
    }

    .score-guide b {
        color: #0f172a;
        font-weight: 950;
    }

    .risk-summary-card {
        background: linear-gradient(135deg, #111827, #1e293b);
        color: white;
        border-radius: 22px;
        padding: 20px;
        margin-bottom: 18px;
        box-shadow: 0 14px 32px rgba(15,23,42,0.16);
    }

    .risk-summary-label {
        color: #cbd5e1;
        font-size: 0.88rem;
        font-weight: 800;
        margin-bottom: 8px;
    }

    .risk-summary-title {
        font-size: 1.22rem;
        font-weight: 950;
        line-height: 1.5;
        letter-spacing: -0.3px;
    }

    .score-row-v2 {
        display: grid;
        grid-template-columns: 150px 1fr 92px;
        gap: 14px;
        align-items: center;
        padding: 15px 0;
        border-bottom: 1px solid #eef2f7;
    }

    .score-row-v2:last-child {
        border-bottom: none;
    }

    .score-name-v2 {
        font-weight: 950;
        color: #111827;
        font-size: 0.96rem;
        line-height: 1.35;
    }

    .score-desc-v2 {
        color: #64748b;
        font-size: 0.80rem;
        font-weight: 700;
        margin-top: 4px;
        line-height: 1.45;
    }

    .score-track-v2 {
        width: 100%;
        height: 16px;
        background: #edf2f7;
        border-radius: 999px;
        overflow: hidden;
        position: relative;
    }

    .score-fill-v2 {
        height: 16px;
        border-radius: 999px;
    }

    .score-low-v2 {
        background: linear-gradient(90deg, #2563eb, #7c3aed);
    }

    .score-mid-v2 {
        background: linear-gradient(90deg, #f59e0b, #f97316);
    }

    .score-high-v2 {
        background: linear-gradient(90deg, #ef4444, #dc2626);
        box-shadow: 0 0 16px rgba(239,68,68,0.35);
    }

    .score-badge-v2 {
        text-align: center;
        border-radius: 999px;
        padding: 8px 9px;
        font-weight: 950;
        font-size: 0.86rem;
        white-space: nowrap;
    }

    .score-badge-low-v2 {
        background: #eef2ff;
        color: #3730a3;
    }

    .score-badge-mid-v2 {
        background: #fef3c7;
        color: #92400e;
    }

    .score-badge-high-v2 {
        background: #fee2e2;
        color: #991b1b;
    }

    .score-level-text {
        display: block;
        font-size: 0.72rem;
        font-weight: 900;
        margin-top: 2px;
    }

    .score-legend {
        display: flex;
        gap: 9px;
        flex-wrap: wrap;
        margin-top: 14px;
    }

    .legend-chip {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        border-radius: 999px;
        padding: 7px 10px;
        font-weight: 850;
        font-size: 0.78rem;
        color: #475569;
        background: #f8fafc;
        border: 1px solid #e2e8f0;
    }

    .legend-dot {
        width: 9px;
        height: 9px;
        border-radius: 999px;
        display: inline-block;
    }

    .dot-low {
        background: #4f46e5;
    }

    .dot-mid {
        background: #f97316;
    }

    .dot-high {
        background: #ef4444;
    }

    @media (max-width: 760px) {
        .score-row-v2 {
            grid-template-columns: 1fr;
            gap: 8px;
            padding: 16px 0;
        }

        .score-badge-v2 {
            width: fit-content;
        }
    }


    /* =============================
       V0.6.3 Score Board Layout Clean
       설명 문구를 그래프 아래로 분리
    ============================= */
    .score-row-v3 {
        padding: 16px 0;
        border-bottom: 1px solid #eef2f7;
    }

    .score-row-v3:last-child {
        border-bottom: none;
    }

    .score-top-v3 {
        display: grid;
        grid-template-columns: 145px 1fr 92px;
        gap: 14px;
        align-items: center;
    }

    .score-name-v3 {
        font-weight: 950;
        color: #111827;
        font-size: 0.98rem;
        line-height: 1.35;
        white-space: nowrap;
    }

    .score-track-v3 {
        width: 100%;
        height: 16px;
        background: #edf2f7;
        border-radius: 999px;
        overflow: hidden;
        position: relative;
    }

    .score-fill-v3 {
        height: 16px;
        border-radius: 999px;
    }

    .score-desc-v3 {
        color: #64748b;
        font-size: 0.82rem;
        font-weight: 700;
        line-height: 1.45;
        margin-top: 6px;
        margin-left: 145px;
        padding-left: 14px;
    }

    @media (max-width: 760px) {
        .score-top-v3 {
            grid-template-columns: 1fr 82px;
            gap: 10px;
        }

        .score-name-v3 {
            grid-column: 1 / 3;
        }

        .score-desc-v3 {
            margin-left: 0;
            padding-left: 0;
        }
    }


    /* =============================
       V0.7 Market Movers
    ============================= */
    .movers-card {
        background: linear-gradient(135deg, #ffffff, #f8fbff);
        border: 1px solid #e5e7eb;
        border-radius: 22px;
        padding: 18px;
        box-shadow: 0 10px 26px rgba(0,0,0,0.045);
        margin-bottom: 18px;
    }

    .movers-title {
        font-size: 1.15rem;
        font-weight: 950;
        color: #111827;
        margin-bottom: 8px;
    }

    .movers-sub {
        color: #64748b;
        font-size: 0.9rem;
        font-weight: 700;
        margin-bottom: 12px;
        line-height: 1.55;
    }

    .mover-item {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 18px;
        padding: 14px;
        margin-bottom: 10px;
        box-shadow: 0 7px 18px rgba(0,0,0,0.035);
    }

    .mover-rank {
        display: inline-block;
        background: #111827;
        color: white;
        border-radius: 999px;
        padding: 5px 9px;
        font-size: 0.78rem;
        font-weight: 950;
        margin-right: 8px;
    }

    .mover-name {
        font-weight: 950;
        color: #111827;
        font-size: 1rem;
    }

    .mover-rate {
        display: inline-block;
        background: #fee2e2;
        color: #991b1b;
        border-radius: 999px;
        padding: 6px 10px;
        font-weight: 950;
        font-size: 0.86rem;
        margin-top: 8px;
    }

    .mover-meta {
        color: #94a3b8;
        font-size: 0.78rem;
        font-weight: 700;
        margin-top: 6px;
    }

    .mover-reason {
        color: #475569;
        font-size: 0.88rem;
        line-height: 1.5;
        margin-top: 8px;
        font-weight: 700;
    }

    .mover-warning {
        background: #fff7ed;
        border: 1px solid #fed7aa;
        color: #9a3412;
        border-radius: 16px;
        padding: 13px 14px;
        line-height: 1.6;
        font-weight: 800;
        margin-top: 12px;
    }


    /* =============================
       V0.8 API Cache Monitor
    ============================= */
    .data-status-card {
        background: linear-gradient(135deg, #ffffff, #f8fbff);
        border: 1px solid #e5e7eb;
        border-radius: 22px;
        padding: 18px;
        box-shadow: 0 10px 26px rgba(0,0,0,0.045);
        margin-bottom: 16px;
    }

    .data-status-title {
        font-size: 1.15rem;
        font-weight: 950;
        color: #111827;
        margin-bottom: 8px;
    }

    .data-status-sub {
        color: #64748b;
        font-size: 0.9rem;
        font-weight: 700;
        margin-bottom: 12px;
        line-height: 1.55;
    }

    .usage-grid {
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 10px;
        margin-top: 12px;
    }

    .usage-box {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 16px;
        padding: 14px;
        box-shadow: 0 6px 16px rgba(0,0,0,0.035);
    }

    .usage-label {
        color: #64748b;
        font-size: 0.8rem;
        font-weight: 850;
        margin-bottom: 7px;
    }

    .usage-value {
        color: #111827;
        font-size: 1.15rem;
        font-weight: 950;
    }

    .usage-bar {
        width: 100%;
        height: 9px;
        border-radius: 999px;
        background: #eef2f7;
        overflow: hidden;
        margin-top: 9px;
    }

    .usage-fill {
        height: 9px;
        border-radius: 999px;
        background: linear-gradient(90deg, #2563eb, #7c3aed);
    }

    .cache-chip {
        display: inline-block;
        padding: 7px 10px;
        border-radius: 999px;
        font-weight: 900;
        font-size: 0.78rem;
        margin-right: 7px;
        margin-bottom: 7px;
    }

    .cache-hit {
        background: #dcfce7;
        color: #166534;
    }

    .cache-live {
        background: #fee2e2;
        color: #991b1b;
    }

    .cache-info {
        background: #eef2ff;
        color: #3730a3;
    }

    @media (max-width: 760px) {
        .usage-grid {
            grid-template-columns: repeat(2, minmax(0, 1fr));
        }
    }


    /* =============================
       V0.9 Disclosure Risk TOP
    ============================= */
    .disclosure-card {
        background: linear-gradient(135deg, #ffffff, #fff7ed);
        border: 1px solid #fed7aa;
        border-radius: 22px;
        padding: 18px;
        box-shadow: 0 10px 26px rgba(0,0,0,0.045);
        margin-bottom: 18px;
    }

    .disclosure-title {
        font-size: 1.15rem;
        font-weight: 950;
        color: #111827;
        margin-bottom: 8px;
    }

    .disclosure-sub {
        color: #64748b;
        font-size: 0.9rem;
        font-weight: 700;
        margin-bottom: 12px;
        line-height: 1.55;
    }

    .risk-filing-item {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 18px;
        padding: 14px;
        margin-bottom: 10px;
        box-shadow: 0 7px 18px rgba(0,0,0,0.035);
    }

    .risk-filing-head {
        display: flex;
        gap: 8px;
        align-items: center;
        flex-wrap: wrap;
        margin-bottom: 8px;
    }

    .risk-rank {
        display: inline-block;
        background: #111827;
        color: white;
        border-radius: 999px;
        padding: 5px 9px;
        font-size: 0.78rem;
        font-weight: 950;
    }

    .risk-tag-danger {
        display: inline-block;
        background: #fee2e2;
        color: #991b1b;
        border-radius: 999px;
        padding: 6px 10px;
        font-weight: 950;
        font-size: 0.82rem;
    }

    .risk-tag-mid {
        display: inline-block;
        background: #fef3c7;
        color: #92400e;
        border-radius: 999px;
        padding: 6px 10px;
        font-weight: 950;
        font-size: 0.82rem;
    }

    .risk-company {
        font-weight: 950;
        color: #111827;
        font-size: 1rem;
    }

    .risk-report {
        color: #334155;
        font-weight: 850;
        line-height: 1.55;
        margin-top: 6px;
    }

    .risk-meta {
        color: #94a3b8;
        font-size: 0.78rem;
        font-weight: 700;
        margin-top: 6px;
    }

    .risk-keywords {
        color: #991b1b;
        font-size: 0.84rem;
        font-weight: 900;
        margin-top: 8px;
    }


    /* =============================
       V0.9.1 Layout Stabilize
    ============================= */
    div[data-testid="stExpander"] {
        background: #ffffff;
        border-radius: 14px;
    }

    .top-user-bar {
        min-height: 24px;
    }


    /* =============================
       V0.9.2 Mobile UX Polish
    ============================= */
    .mobile-quick-guide {
        background: linear-gradient(135deg, #f8fafc, #eef2ff);
        border: 1px solid #dbe3ef;
        border-radius: 18px;
        padding: 14px 16px;
        color: #334155;
        font-weight: 800;
        line-height: 1.65;
        margin: 12px 0 18px 0;
        font-size: 0.92rem;
    }

    .mobile-quick-guide b {
        color: #0f172a;
        font-weight: 950;
    }

    .stButton > button,
    .stFormSubmitButton > button {
        min-height: 48px;
    }

    div[data-testid="stExpander"] {
        border-radius: 16px !important;
        overflow: hidden;
        margin-bottom: 10px;
    }

    div[data-testid="stExpander"] details summary {
        min-height: 44px;
        font-weight: 850;
    }

    @media (max-width: 760px) {
        .block-container {
            padding-top: 1rem !important;
            padding-left: 1rem !important;
            padding-right: 1rem !important;
            max-width: 100% !important;
        }

        .app-title {
            font-size: 2rem !important;
            line-height: 1.2 !important;
            margin-bottom: 0.15rem !important;
        }

        .app-subtitle {
            font-size: 0.92rem !important;
            margin-bottom: 1rem !important;
        }

        .section-title {
            font-size: 1.15rem !important;
            margin-top: 14px !important;
            margin-bottom: 10px !important;
        }

        .kpi-card {
            padding: 16px 12px !important;
            border-radius: 18px !important;
            min-height: 104px !important;
            margin-bottom: 8px !important;
        }

        .kpi-label {
            font-size: 0.8rem !important;
            margin-bottom: 8px !important;
        }

        .kpi-value {
            font-size: 1.35rem !important;
            word-break: keep-all !important;
        }

        .source-small {
            font-size: 0.70rem !important;
        }

        .insight-card {
            padding: 20px !important;
            border-radius: 22px !important;
            margin-top: 12px !important;
        }

        .insight-title {
            font-size: 1.12rem !important;
            line-height: 1.55 !important;
        }

        .mini-chip {
            font-size: 0.78rem !important;
            padding: 7px 10px !important;
        }

        .score-board-v2 {
            padding: 16px !important;
            border-radius: 22px !important;
        }

        .score-guide {
            padding: 13px !important;
            font-size: 0.84rem !important;
        }

        .risk-summary-card {
            padding: 16px !important;
            border-radius: 18px !important;
        }

        .risk-summary-title {
            font-size: 1.02rem !important;
        }

        .score-row-v3 {
            padding: 15px 0 !important;
        }

        .score-top-v3 {
            grid-template-columns: 1fr 82px !important;
            gap: 10px !important;
        }

        .score-name-v3 {
            grid-column: 1 / 3 !important;
            font-size: 0.95rem !important;
            white-space: normal !important;
        }

        .score-track-v3 {
            height: 14px !important;
        }

        .score-fill-v3 {
            height: 14px !important;
        }

        .score-desc-v3 {
            margin-left: 0 !important;
            padding-left: 0 !important;
            font-size: 0.78rem !important;
        }

        .score-badge-v2 {
            padding: 7px 8px !important;
            font-size: 0.78rem !important;
        }

        .news-card,
        .dart-card,
        .reason-card,
        .locked-card,
        .premium-card,
        .watch-card,
        .movers-card,
        .disclosure-card {
            padding: 15px !important;
            border-radius: 18px !important;
        }

        .card-title {
            font-size: 0.95rem !important;
            line-height: 1.45 !important;
        }

        .card-desc {
            font-size: 0.88rem !important;
            line-height: 1.6 !important;
        }

        .mover-item,
        .risk-filing-item,
        .watch-item {
            padding: 12px !important;
            border-radius: 16px !important;
        }

        .mover-name,
        .risk-company,
        .watch-name {
            font-size: 0.92rem !important;
        }

        .mover-rate {
            font-size: 0.8rem !important;
            padding: 5px 9px !important;
        }

        .ad-card {
            padding: 14px !important;
            border-radius: 18px !important;
        }

    
    /* =============================
       V0.9.3 App Finish Polish
       Streamlit 기본 UI 숨김 + 앱 마감
    ============================= */

    /* Streamlit 기본 헤더/메뉴/푸터 숨김 */
    #MainMenu {
        visibility: hidden !important;
    }

    header {
        visibility: hidden !important;
        height: 0rem !important;
    }

    footer {
        visibility: hidden !important;
        height: 0rem !important;
    }

    [data-testid="stToolbar"] {
        display: none !important;
    }

    [data-testid="stDecoration"] {
        display: none !important;
    }

    [data-testid="stStatusWidget"] {
        display: none !important;
    }

    .stDeployButton {
        display: none !important;
    }

    div[data-testid="stAppViewContainer"] {
        background:
            radial-gradient(circle at 10% 8%, rgba(37,99,235,0.035), transparent 24%),
            radial-gradient(circle at 90% 10%, rgba(124,58,237,0.035), transparent 24%),
            #ffffff;
    }

    .block-container {
        padding-top: 1.2rem !important;
    }

    .app-shell-note {
        background: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 18px;
        padding: 14px 16px;
        color: #475569;
        font-weight: 750;
        line-height: 1.65;
        margin: 12px 0 18px 0;
        box-shadow: 0 6px 18px rgba(15,23,42,0.035);
        font-size: 0.9rem;
    }

    .search-wrap-card {
        background: rgba(255,255,255,0.78);
        border: 1px solid #e5e7eb;
        border-radius: 22px;
        padding: 16px;
        margin-bottom: 16px;
        box-shadow: 0 8px 24px rgba(15,23,42,0.04);
    }

    @media (max-width: 760px) {
        .block-container {
            padding-top: 0.8rem !important;
            padding-bottom: 1.2rem !important;
        }

        .app-shell-note {
            font-size: 0.82rem !important;
            padding: 12px 13px !important;
            border-radius: 16px !important;
            margin: 10px 0 14px 0 !important;
        }

        div[data-testid="stExpander"] details summary {
            font-size: 0.86rem !important;
        }

    




    .news-filter-note {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 16px;
        padding: 10px 12px;
        color: #64748b;
        font-size: 0.78rem;
        font-weight: 760;
        line-height: 1.55;
        margin: 6px 0 12px 0;
    }

    /* =============================
       V1.2.2 Easy Deep Report
       지나가는 개도 이해하는 카드형 심층 리포트
    ============================= */
    .easy-report-hero {
        background: linear-gradient(135deg, #111827, #1e3a8a);
        color: #ffffff;
        border-radius: 28px;
        padding: 24px 24px;
        margin: 14px 0 18px 0;
        box-shadow: 0 18px 44px rgba(15,23,42,0.18);
    }

    .easy-report-kicker {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: rgba(255,255,255,0.13);
        border: 1px solid rgba(255,255,255,0.16);
        border-radius: 999px;
        padding: 7px 11px;
        color: #dbeafe;
        font-size: 0.78rem;
        font-weight: 1000;
        margin-bottom: 12px;
    }

    .easy-report-title {
        font-size: 1.28rem;
        font-weight: 1000;
        line-height: 1.55;
        letter-spacing: -0.4px;
        margin-bottom: 10px;
    }

    .easy-report-sub {
        color: #cbd5e1;
        font-size: 0.90rem;
        font-weight: 780;
        line-height: 1.65;
    }

    .easy-card {
        background: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 24px;
        padding: 18px 18px;
        margin: 12px 0;
        box-shadow: 0 10px 28px rgba(15,23,42,0.05);
    }

    .easy-card-head {
        display: flex;
        align-items: center;
        gap: 10px;
        margin-bottom: 11px;
    }

    .easy-num {
        min-width: 32px;
        height: 32px;
        border-radius: 999px;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        background: #eff6ff;
        color: #1d4ed8;
        font-size: 0.88rem;
        font-weight: 1000;
    }

    .easy-title {
        color: #0f172a;
        font-size: 1.06rem;
        font-weight: 1000;
        letter-spacing: -0.2px;
    }

    .easy-sentence {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 18px;
        padding: 13px 14px;
        color: #111827;
        font-size: 0.94rem;
        font-weight: 850;
        line-height: 1.75;
        margin-bottom: 11px;
        white-space: pre-line;
    }

    .easy-explain {
        color: #475569;
        font-size: 0.86rem;
        font-weight: 720;
        line-height: 1.75;
        white-space: pre-line;
    }

    .easy-label {
        display: inline-block;
        border-radius: 999px;
        padding: 5px 9px;
        background: #ecfeff;
        color: #155e75;
        font-size: 0.72rem;
        font-weight: 1000;
        margin-bottom: 8px;
        border: 1px solid #a5f3fc;
    }

    .easy-evidence-box {
        margin-top: 12px;
        background: #fafafa;
        border: 1px dashed #d4d4d8;
        border-radius: 18px;
        padding: 12px 13px;
    }

    .easy-evidence-title {
        color: #52525b;
        font-size: 0.76rem;
        font-weight: 1000;
        margin-bottom: 6px;
    }

    .easy-evidence-line {
        color: #64748b;
        font-size: 0.78rem;
        font-weight: 760;
        line-height: 1.6;
        margin-bottom: 4px;
    }

    .easy-checklist {
        background: #f0fdf4;
        border: 1px solid #bbf7d0;
        border-radius: 22px;
        padding: 16px 17px;
        margin: 12px 0;
    }

    .easy-check-title {
        color: #166534;
        font-size: 1rem;
        font-weight: 1000;
        margin-bottom: 9px;
    }

    .easy-check-line {
        color: #14532d;
        font-size: 0.86rem;
        font-weight: 790;
        line-height: 1.8;
        margin-bottom: 5px;
    }

    .easy-limit {
        background: #fffbeb;
        border: 1px solid #fde68a;
        color: #92400e;
        border-radius: 20px;
        padding: 14px 15px;
        font-size: 0.82rem;
        font-weight: 780;
        line-height: 1.65;
        margin: 12px 0;
    }

    .easy-key-grid {
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 10px;
        margin: 12px 0 16px 0;
    }

    .easy-key-box {
        background: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 18px;
        padding: 12px 13px;
        box-shadow: 0 8px 20px rgba(15,23,42,0.035);
    }

    .easy-key-label {
        color: #64748b;
        font-size: 0.72rem;
        font-weight: 950;
        margin-bottom: 5px;
    }

    .easy-key-value {
        color: #0f172a;
        font-size: 0.92rem;
        font-weight: 1000;
    }

    @media (max-width: 760px) {
        .easy-report-hero {
            padding: 19px 16px !important;
            border-radius: 22px !important;
        }

        .easy-report-title {
            font-size: 1.06rem !important;
        }

        .easy-report-sub {
            font-size: 0.80rem !important;
        }

        .easy-card {
            padding: 15px 14px !important;
            border-radius: 20px !important;
        }

        .easy-title {
            font-size: 0.96rem !important;
        }

        .easy-sentence {
            font-size: 0.84rem !important;
            padding: 12px 12px !important;
        }

        .easy-explain {
            font-size: 0.79rem !important;
        }

        .easy-key-grid {
            grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
        }
    }

    /* =============================
       V1.2.1 Advanced Deep Report
       PRO 가치를 만드는 서사형 심층 리포트
    ============================= */
    .advanced-report-hero {
        background: linear-gradient(135deg, #0f172a, #1e293b);
        color: #ffffff;
        border-radius: 26px;
        padding: 22px 22px;
        margin: 12px 0 16px 0;
        box-shadow: 0 16px 38px rgba(15,23,42,0.16);
    }

    .advanced-report-kicker {
        display: inline-block;
        background: rgba(255,255,255,0.12);
        border: 1px solid rgba(255,255,255,0.12);
        color: #dbeafe;
        border-radius: 999px;
        padding: 6px 10px;
        font-size: 0.76rem;
        font-weight: 950;
        margin-bottom: 10px;
    }

    .advanced-report-title {
        font-size: 1.18rem;
        font-weight: 1000;
        line-height: 1.55;
        letter-spacing: -0.3px;
    }

    .advanced-section-card {
        background: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 24px;
        padding: 18px 18px;
        margin: 12px 0;
        box-shadow: 0 10px 28px rgba(15,23,42,0.045);
    }

    .advanced-section-title {
        font-size: 1.02rem;
        font-weight: 1000;
        color: #111827;
        margin-bottom: 8px;
    }

    .advanced-section-desc {
        color: #334155;
        font-size: 0.91rem;
        font-weight: 720;
        line-height: 1.8;
        white-space: pre-line;
    }

    .advanced-evidence {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 18px;
        padding: 13px 14px;
        margin-top: 12px;
    }

    .advanced-evidence-title {
        color: #475569;
        font-size: 0.78rem;
        font-weight: 1000;
        margin-bottom: 7px;
    }

    .advanced-evidence-line {
        color: #64748b;
        font-size: 0.78rem;
        font-weight: 760;
        line-height: 1.65;
        margin-bottom: 4px;
    }

    .advanced-judgement-grid {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 10px;
        margin-top: 12px;
    }

    .advanced-judgement-box {
        border: 1px solid #e2e8f0;
        background: #f8fafc;
        border-radius: 18px;
        padding: 13px 14px;
    }

    .advanced-judgement-label {
        color: #64748b;
        font-size: 0.73rem;
        font-weight: 950;
        margin-bottom: 5px;
    }

    .advanced-judgement-value {
        color: #0f172a;
        font-size: 0.92rem;
        font-weight: 1000;
        line-height: 1.45;
    }

    .advanced-warning {
        background: #fffbeb;
        border: 1px solid #fde68a;
        color: #92400e;
        border-radius: 18px;
        padding: 13px 14px;
        font-size: 0.82rem;
        font-weight: 780;
        line-height: 1.65;
        margin: 12px 0;
    }

    @media (max-width: 760px) {
        .advanced-report-hero {
            padding: 18px 16px !important;
            border-radius: 22px !important;
        }

        .advanced-report-title {
            font-size: 1.02rem !important;
        }

        .advanced-section-card {
            padding: 15px 14px !important;
            border-radius: 20px !important;
        }

        .advanced-section-desc {
            font-size: 0.82rem !important;
        }

        .advanced-judgement-grid {
            grid-template-columns: 1fr !important;
        }
    }

    /* =============================
       V1.2.0 Direction-aware score colors
       상승 요인은 위험 빨간색이 아니라 긍정 기여도 색상으로 표시
    ============================= */
    .score-positive-high-v2 {
        background: linear-gradient(90deg, #22c55e, #16a34a) !important;
    }

    .score-positive-mid-v2 {
        background: linear-gradient(90deg, #38bdf8, #2563eb) !important;
    }

    .score-positive-low-v2 {
        background: linear-gradient(90deg, #a5b4fc, #6366f1) !important;
    }

    .score-badge-positive-high-v2 {
        background: #dcfce7 !important;
        color: #166534 !important;
    }

    .score-badge-positive-mid-v2 {
        background: #dbeafe !important;
        color: #1d4ed8 !important;
    }

    .score-badge-positive-low-v2 {
        background: #eef2ff !important;
        color: #4338ca !important;
    }

    .score-board-positive .risk-summary-card {
        background: linear-gradient(135deg, #052e16, #14532d) !important;
    }

    .score-board-neutral .risk-summary-card {
        background: linear-gradient(135deg, #1e293b, #334155) !important;
    }

    /* =============================
       V0.9.4 Mobile Readability Polish
       - AI 결론 모바일 가독성 개선
       - 점수 배지 가로형으로 변경
    ============================= */

    .score-badge-v2 {
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        gap: 5px !important;
        min-width: 74px !important;
        white-space: nowrap !important;
        line-height: 1 !important;
    }

    .score-level-text {
        display: inline !important;
        font-size: 0.78rem !important;
        font-weight: 950 !important;
        margin-top: 0 !important;
    }

    .insight-card {
        position: relative;
        overflow: hidden;
    }

    .insight-card::before {
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        width: 5px;
        height: 100%;
        background: linear-gradient(180deg, #60a5fa, #a78bfa, #f87171);
    }

    .insight-title {
        word-break: keep-all;
    }

    @media (max-width: 760px) {
        .insight-card {
            padding: 18px 17px 17px 18px !important;
            border-radius: 21px !important;
            margin-top: 12px !important;
        }

        .insight-label {
            font-size: 0.78rem !important;
            margin-bottom: 8px !important;
            color: #bfdbfe !important;
        }

        .insight-title {
            font-size: 1.02rem !important;
            line-height: 1.58 !important;
            letter-spacing: -0.2px !important;
            margin-bottom: 13px !important;
        }

        .risk-badge-high,
        .risk-badge-mid,
        .risk-badge-low {
            display: inline-flex !important;
            align-items: center !important;
            justify-content: center !important;
            min-height: 30px !important;
            padding: 7px 10px !important;
            font-size: 0.76rem !important;
            margin-bottom: 6px !important;
        }

        .mini-chip {
            display: inline-flex !important;
            align-items: center !important;
            min-height: 30px !important;
            font-size: 0.74rem !important;
            padding: 7px 9px !important;
            line-height: 1.25 !important;
            max-width: 100% !important;
        }

        .score-top-v3 {
            grid-template-columns: 1fr 86px !important;
        }

        .score-badge-v2 {
            min-width: 74px !important;
            padding: 8px 9px !important;
            font-size: 0.78rem !important;
            gap: 4px !important;
        }

        .score-level-text {
            font-size: 0.72rem !important;
        }
    }


    /* =============================
       V0.9.5 Friendly Error Handling
    ============================= */
    .soft-warning-card {
        background: #fff7ed;
        border: 1px solid #fed7aa;
        border-radius: 18px;
        padding: 14px 16px;
        color: #9a3412;
        font-weight: 800;
        line-height: 1.65;
        margin: 12px 0 16px 0;
        box-shadow: 0 6px 18px rgba(15,23,42,0.035);
    }

    .soft-warning-title {
        font-weight: 950;
        color: #7c2d12;
        margin-bottom: 6px;
    }

    .soft-warning-item {
        margin-top: 4px;
    }

    .fatal-error-card {
        background: #fef2f2;
        border: 1px solid #fecaca;
        border-radius: 18px;
        padding: 16px;
        color: #991b1b;
        font-weight: 850;
        line-height: 1.65;
        margin: 14px 0;
        box-shadow: 0 6px 18px rgba(15,23,42,0.035);
    }

    .fatal-error-title {
        font-size: 1.02rem;
        font-weight: 950;
        color: #7f1d1d;
        margin-bottom: 6px;
    }


    /* =============================
       V0.9.6 Visible Loading State
    ============================= */
    .loading-hero {
        background: linear-gradient(135deg, #111827, #1e293b);
        color: white;
        border-radius: 22px;
        padding: 20px 22px;
        margin: 14px 0 18px 0;
        box-shadow: 0 16px 36px rgba(15,23,42,0.20);
        border: 1px solid rgba(255,255,255,0.08);
    }
    .loading-title {
        font-size: 1.05rem;
        font-weight: 950;
        margin-bottom: 8px;
        letter-spacing: -0.2px;
    }
    .loading-sub {
        color: #cbd5e1;
        font-size: 0.9rem;
        font-weight: 750;
        line-height: 1.65;
        margin-bottom: 14px;
    }
    .loading-steps {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin-top: 10px;
    }
    .loading-step {
        background: rgba(255,255,255,0.10);
        color: #e5e7eb;
        border: 1px solid rgba(255,255,255,0.10);
        border-radius: 999px;
        padding: 7px 10px;
        font-size: 0.78rem;
        font-weight: 900;
    }
    .loading-bar {
        width: 100%;
        height: 9px;
        border-radius: 999px;
        background: rgba(255,255,255,0.13);
        overflow: hidden;
        margin-top: 8px;
    }
    .loading-bar-fill {
        height: 9px;
        width: 45%;
        border-radius: 999px;
        background: linear-gradient(90deg, #60a5fa, #a78bfa, #f87171);
        animation: loadingMove 1.1s ease-in-out infinite;
    }
    @keyframes loadingMove {
        0% { transform: translateX(-110%); }
        50% { transform: translateX(60%); }
        100% { transform: translateX(240%); }
    }
    @media (max-width: 760px) {
        .loading-hero {
            padding: 17px 16px !important;
            border-radius: 20px !important;
            margin: 12px 0 15px 0 !important;
        }
        .loading-title {
            font-size: 0.98rem !important;
            line-height: 1.45 !important;
        }
        .loading-sub {
            font-size: 0.82rem !important;
        }
        .loading-step {
            font-size: 0.72rem !important;
            padding: 6px 8px !important;
        }
    }

    .footer-box {
            margin-top: 18px !important;
        }
    }


    /* =============================
       V0.9.4 Mobile Readability Polish
       - AI 결론 모바일 가독성 개선
       - 점수 배지 가로형으로 변경
    ============================= */

    .score-badge-v2 {
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        gap: 5px !important;
        min-width: 74px !important;
        white-space: nowrap !important;
        line-height: 1 !important;
    }

    .score-level-text {
        display: inline !important;
        font-size: 0.78rem !important;
        font-weight: 950 !important;
        margin-top: 0 !important;
    }

    .insight-card {
        position: relative;
        overflow: hidden;
    }

    .insight-card::before {
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        width: 5px;
        height: 100%;
        background: linear-gradient(180deg, #60a5fa, #a78bfa, #f87171);
    }

    .insight-title {
        word-break: keep-all;
    }

    @media (max-width: 760px) {
        .insight-card {
            padding: 18px 17px 17px 18px !important;
            border-radius: 21px !important;
            margin-top: 12px !important;
        }

        .insight-label {
            font-size: 0.78rem !important;
            margin-bottom: 8px !important;
            color: #bfdbfe !important;
        }

        .insight-title {
            font-size: 1.02rem !important;
            line-height: 1.58 !important;
            letter-spacing: -0.2px !important;
            margin-bottom: 13px !important;
        }

        .risk-badge-high,
        .risk-badge-mid,
        .risk-badge-low {
            display: inline-flex !important;
            align-items: center !important;
            justify-content: center !important;
            min-height: 30px !important;
            padding: 7px 10px !important;
            font-size: 0.76rem !important;
            margin-bottom: 6px !important;
        }

        .mini-chip {
            display: inline-flex !important;
            align-items: center !important;
            min-height: 30px !important;
            font-size: 0.74rem !important;
            padding: 7px 9px !important;
            line-height: 1.25 !important;
            max-width: 100% !important;
        }

        .score-top-v3 {
            grid-template-columns: 1fr 86px !important;
        }

        .score-badge-v2 {
            min-width: 74px !important;
            padding: 8px 9px !important;
            font-size: 0.78rem !important;
            gap: 4px !important;
        }

        .score-level-text {
            font-size: 0.72rem !important;
        }
    }


    /* =============================
       V0.9.5 Friendly Error Handling
    ============================= */
    .soft-warning-card {
        background: #fff7ed;
        border: 1px solid #fed7aa;
        border-radius: 18px;
        padding: 14px 16px;
        color: #9a3412;
        font-weight: 800;
        line-height: 1.65;
        margin: 12px 0 16px 0;
        box-shadow: 0 6px 18px rgba(15,23,42,0.035);
    }

    .soft-warning-title {
        font-weight: 950;
        color: #7c2d12;
        margin-bottom: 6px;
    }

    .soft-warning-item {
        margin-top: 4px;
    }

    .fatal-error-card {
        background: #fef2f2;
        border: 1px solid #fecaca;
        border-radius: 18px;
        padding: 16px;
        color: #991b1b;
        font-weight: 850;
        line-height: 1.65;
        margin: 14px 0;
        box-shadow: 0 6px 18px rgba(15,23,42,0.035);
    }

    .fatal-error-title {
        font-size: 1.02rem;
        font-weight: 950;
        color: #7f1d1d;
        margin-bottom: 6px;
    }


    /* =============================
       V0.9.6 Visible Loading State
    ============================= */
    .loading-hero {
        background: linear-gradient(135deg, #111827, #1e293b);
        color: white;
        border-radius: 22px;
        padding: 20px 22px;
        margin: 14px 0 18px 0;
        box-shadow: 0 16px 36px rgba(15,23,42,0.20);
        border: 1px solid rgba(255,255,255,0.08);
    }
    .loading-title {
        font-size: 1.05rem;
        font-weight: 950;
        margin-bottom: 8px;
        letter-spacing: -0.2px;
    }
    .loading-sub {
        color: #cbd5e1;
        font-size: 0.9rem;
        font-weight: 750;
        line-height: 1.65;
        margin-bottom: 14px;
    }
    .loading-steps {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin-top: 10px;
    }
    .loading-step {
        background: rgba(255,255,255,0.10);
        color: #e5e7eb;
        border: 1px solid rgba(255,255,255,0.10);
        border-radius: 999px;
        padding: 7px 10px;
        font-size: 0.78rem;
        font-weight: 900;
    }
    .loading-bar {
        width: 100%;
        height: 9px;
        border-radius: 999px;
        background: rgba(255,255,255,0.13);
        overflow: hidden;
        margin-top: 8px;
    }
    .loading-bar-fill {
        height: 9px;
        width: 45%;
        border-radius: 999px;
        background: linear-gradient(90deg, #60a5fa, #a78bfa, #f87171);
        animation: loadingMove 1.1s ease-in-out infinite;
    }
    @keyframes loadingMove {
        0% { transform: translateX(-110%); }
        50% { transform: translateX(60%); }
        100% { transform: translateX(240%); }
    }
    @media (max-width: 760px) {
        .loading-hero {
            padding: 17px 16px !important;
            border-radius: 20px !important;
            margin: 12px 0 15px 0 !important;
        }
        .loading-title {
            font-size: 0.98rem !important;
            line-height: 1.45 !important;
        }
        .loading-sub {
            font-size: 0.82rem !important;
        }
        .loading-step {
            font-size: 0.72rem !important;
            padding: 6px 8px !important;
        }
    }

    .footer-box {
            font-size: 0.78rem !important;
            line-height: 1.6 !important;
        }

        /* Streamlit column gap reduction on mobile */
        div[data-testid="column"] {
            padding-left: 0.15rem !important;
            padding-right: 0.15rem !important;
        }

        /* Search input/button mobile spacing */
        .stTextInput > div > div > input {
            height: 46px !important;
            font-size: 0.92rem !important;
        }

        .stButton > button,
        .stFormSubmitButton > button {
            height: 46px !important;
            font-size: 0.88rem !important;
        }
    }


    /* =============================
       V0.9.3 App Finish Polish
       Streamlit 기본 UI 숨김 + 앱 마감
    ============================= */

    /* Streamlit 기본 헤더/메뉴/푸터 숨김 */
    #MainMenu {
        visibility: hidden !important;
    }

    header {
        visibility: hidden !important;
        height: 0rem !important;
    }

    footer {
        visibility: hidden !important;
        height: 0rem !important;
    }

    [data-testid="stToolbar"] {
        display: none !important;
    }

    [data-testid="stDecoration"] {
        display: none !important;
    }

    [data-testid="stStatusWidget"] {
        display: none !important;
    }

    .stDeployButton {
        display: none !important;
    }

    div[data-testid="stAppViewContainer"] {
        background:
            radial-gradient(circle at 10% 8%, rgba(37,99,235,0.035), transparent 24%),
            radial-gradient(circle at 90% 10%, rgba(124,58,237,0.035), transparent 24%),
            #ffffff;
    }

    .block-container {
        padding-top: 1.2rem !important;
    }

    .app-shell-note {
        background: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 18px;
        padding: 14px 16px;
        color: #475569;
        font-weight: 750;
        line-height: 1.65;
        margin: 12px 0 18px 0;
        box-shadow: 0 6px 18px rgba(15,23,42,0.035);
        font-size: 0.9rem;
    }

    .search-wrap-card {
        background: rgba(255,255,255,0.78);
        border: 1px solid #e5e7eb;
        border-radius: 22px;
        padding: 16px;
        margin-bottom: 16px;
        box-shadow: 0 8px 24px rgba(15,23,42,0.04);
    }

    @media (max-width: 760px) {
        .block-container {
            padding-top: 0.8rem !important;
            padding-bottom: 1.2rem !important;
        }

        .app-shell-note {
            font-size: 0.82rem !important;
            padding: 12px 13px !important;
            border-radius: 16px !important;
            margin: 10px 0 14px 0 !important;
        }

        div[data-testid="stExpander"] details summary {
            font-size: 0.86rem !important;
        }

    
    /* =============================
       V0.9.4 Mobile Readability Polish
       - AI 결론 모바일 가독성 개선
       - 점수 배지 가로형으로 변경
    ============================= */

    .score-badge-v2 {
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        gap: 5px !important;
        min-width: 74px !important;
        white-space: nowrap !important;
        line-height: 1 !important;
    }

    .score-level-text {
        display: inline !important;
        font-size: 0.78rem !important;
        font-weight: 950 !important;
        margin-top: 0 !important;
    }

    .insight-card {
        position: relative;
        overflow: hidden;
    }

    .insight-card::before {
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        width: 5px;
        height: 100%;
        background: linear-gradient(180deg, #60a5fa, #a78bfa, #f87171);
    }

    .insight-title {
        word-break: keep-all;
    }

    @media (max-width: 760px) {
        .insight-card {
            padding: 18px 17px 17px 18px !important;
            border-radius: 21px !important;
            margin-top: 12px !important;
        }

        .insight-label {
            font-size: 0.78rem !important;
            margin-bottom: 8px !important;
            color: #bfdbfe !important;
        }

        .insight-title {
            font-size: 1.02rem !important;
            line-height: 1.58 !important;
            letter-spacing: -0.2px !important;
            margin-bottom: 13px !important;
        }

        .risk-badge-high,
        .risk-badge-mid,
        .risk-badge-low {
            display: inline-flex !important;
            align-items: center !important;
            justify-content: center !important;
            min-height: 30px !important;
            padding: 7px 10px !important;
            font-size: 0.76rem !important;
            margin-bottom: 6px !important;
        }

        .mini-chip {
            display: inline-flex !important;
            align-items: center !important;
            min-height: 30px !important;
            font-size: 0.74rem !important;
            padding: 7px 9px !important;
            line-height: 1.25 !important;
            max-width: 100% !important;
        }

        .score-top-v3 {
            grid-template-columns: 1fr 86px !important;
        }

        .score-badge-v2 {
            min-width: 74px !important;
            padding: 8px 9px !important;
            font-size: 0.78rem !important;
            gap: 4px !important;
        }

        .score-level-text {
            font-size: 0.72rem !important;
        }
    }


    /* =============================
       V0.9.5 Friendly Error Handling
    ============================= */
    .soft-warning-card {
        background: #fff7ed;
        border: 1px solid #fed7aa;
        border-radius: 18px;
        padding: 14px 16px;
        color: #9a3412;
        font-weight: 800;
        line-height: 1.65;
        margin: 12px 0 16px 0;
        box-shadow: 0 6px 18px rgba(15,23,42,0.035);
    }

    .soft-warning-title {
        font-weight: 950;
        color: #7c2d12;
        margin-bottom: 6px;
    }

    .soft-warning-item {
        margin-top: 4px;
    }

    .fatal-error-card {
        background: #fef2f2;
        border: 1px solid #fecaca;
        border-radius: 18px;
        padding: 16px;
        color: #991b1b;
        font-weight: 850;
        line-height: 1.65;
        margin: 14px 0;
        box-shadow: 0 6px 18px rgba(15,23,42,0.035);
    }

    .fatal-error-title {
        font-size: 1.02rem;
        font-weight: 950;
        color: #7f1d1d;
        margin-bottom: 6px;
    }


    /* =============================
       V0.9.6 Visible Loading State
    ============================= */
    .loading-hero {
        background: linear-gradient(135deg, #111827, #1e293b);
        color: white;
        border-radius: 22px;
        padding: 20px 22px;
        margin: 14px 0 18px 0;
        box-shadow: 0 16px 36px rgba(15,23,42,0.20);
        border: 1px solid rgba(255,255,255,0.08);
    }
    .loading-title {
        font-size: 1.05rem;
        font-weight: 950;
        margin-bottom: 8px;
        letter-spacing: -0.2px;
    }
    .loading-sub {
        color: #cbd5e1;
        font-size: 0.9rem;
        font-weight: 750;
        line-height: 1.65;
        margin-bottom: 14px;
    }
    .loading-steps {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin-top: 10px;
    }
    .loading-step {
        background: rgba(255,255,255,0.10);
        color: #e5e7eb;
        border: 1px solid rgba(255,255,255,0.10);
        border-radius: 999px;
        padding: 7px 10px;
        font-size: 0.78rem;
        font-weight: 900;
    }
    .loading-bar {
        width: 100%;
        height: 9px;
        border-radius: 999px;
        background: rgba(255,255,255,0.13);
        overflow: hidden;
        margin-top: 8px;
    }
    .loading-bar-fill {
        height: 9px;
        width: 45%;
        border-radius: 999px;
        background: linear-gradient(90deg, #60a5fa, #a78bfa, #f87171);
        animation: loadingMove 1.1s ease-in-out infinite;
    }
    @keyframes loadingMove {
        0% { transform: translateX(-110%); }
        50% { transform: translateX(60%); }
        100% { transform: translateX(240%); }
    }
    @media (max-width: 760px) {
        .loading-hero {
            padding: 17px 16px !important;
            border-radius: 20px !important;
            margin: 12px 0 15px 0 !important;
        }
        .loading-title {
            font-size: 0.98rem !important;
            line-height: 1.45 !important;
        }
        .loading-sub {
            font-size: 0.82rem !important;
        }
        .loading-step {
            font-size: 0.72rem !important;
            padding: 6px 8px !important;
        }
    }

    .footer-box {
            margin-top: 18px !important;
        }
    }


    /* =============================
       V0.9.4 Mobile Readability Polish
       - AI 결론 모바일 가독성 개선
       - 점수 배지 가로형으로 변경
    ============================= */

    .score-badge-v2 {
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        gap: 5px !important;
        min-width: 74px !important;
        white-space: nowrap !important;
        line-height: 1 !important;
    }

    .score-level-text {
        display: inline !important;
        font-size: 0.78rem !important;
        font-weight: 950 !important;
        margin-top: 0 !important;
    }

    .insight-card {
        position: relative;
        overflow: hidden;
    }

    .insight-card::before {
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        width: 5px;
        height: 100%;
        background: linear-gradient(180deg, #60a5fa, #a78bfa, #f87171);
    }

    .insight-title {
        word-break: keep-all;
    }

    @media (max-width: 760px) {
        .insight-card {
            padding: 18px 17px 17px 18px !important;
            border-radius: 21px !important;
            margin-top: 12px !important;
        }

        .insight-label {
            font-size: 0.78rem !important;
            margin-bottom: 8px !important;
            color: #bfdbfe !important;
        }

        .insight-title {
            font-size: 1.02rem !important;
            line-height: 1.58 !important;
            letter-spacing: -0.2px !important;
            margin-bottom: 13px !important;
        }

        .risk-badge-high,
        .risk-badge-mid,
        .risk-badge-low {
            display: inline-flex !important;
            align-items: center !important;
            justify-content: center !important;
            min-height: 30px !important;
            padding: 7px 10px !important;
            font-size: 0.76rem !important;
            margin-bottom: 6px !important;
        }

        .mini-chip {
            display: inline-flex !important;
            align-items: center !important;
            min-height: 30px !important;
            font-size: 0.74rem !important;
            padding: 7px 9px !important;
            line-height: 1.25 !important;
            max-width: 100% !important;
        }

        .score-top-v3 {
            grid-template-columns: 1fr 86px !important;
        }

        .score-badge-v2 {
            min-width: 74px !important;
            padding: 8px 9px !important;
            font-size: 0.78rem !important;
            gap: 4px !important;
        }

        .score-level-text {
            font-size: 0.72rem !important;
        }
    }


    /* =============================
       V0.9.5 Friendly Error Handling
    ============================= */
    .soft-warning-card {
        background: #fff7ed;
        border: 1px solid #fed7aa;
        border-radius: 18px;
        padding: 14px 16px;
        color: #9a3412;
        font-weight: 800;
        line-height: 1.65;
        margin: 12px 0 16px 0;
        box-shadow: 0 6px 18px rgba(15,23,42,0.035);
    }

    .soft-warning-title {
        font-weight: 950;
        color: #7c2d12;
        margin-bottom: 6px;
    }

    .soft-warning-item {
        margin-top: 4px;
    }

    .fatal-error-card {
        background: #fef2f2;
        border: 1px solid #fecaca;
        border-radius: 18px;
        padding: 16px;
        color: #991b1b;
        font-weight: 850;
        line-height: 1.65;
        margin: 14px 0;
        box-shadow: 0 6px 18px rgba(15,23,42,0.035);
    }

    .fatal-error-title {
        font-size: 1.02rem;
        font-weight: 950;
        color: #7f1d1d;
        margin-bottom: 6px;
    }


    /* =============================
       V0.9.6 Visible Loading State
    ============================= */
    .loading-hero {
        background: linear-gradient(135deg, #111827, #1e293b);
        color: white;
        border-radius: 22px;
        padding: 20px 22px;
        margin: 14px 0 18px 0;
        box-shadow: 0 16px 36px rgba(15,23,42,0.20);
        border: 1px solid rgba(255,255,255,0.08);
    }
    .loading-title {
        font-size: 1.05rem;
        font-weight: 950;
        margin-bottom: 8px;
        letter-spacing: -0.2px;
    }
    .loading-sub {
        color: #cbd5e1;
        font-size: 0.9rem;
        font-weight: 750;
        line-height: 1.65;
        margin-bottom: 14px;
    }
    .loading-steps {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin-top: 10px;
    }
    .loading-step {
        background: rgba(255,255,255,0.10);
        color: #e5e7eb;
        border: 1px solid rgba(255,255,255,0.10);
        border-radius: 999px;
        padding: 7px 10px;
        font-size: 0.78rem;
        font-weight: 900;
    }
    .loading-bar {
        width: 100%;
        height: 9px;
        border-radius: 999px;
        background: rgba(255,255,255,0.13);
        overflow: hidden;
        margin-top: 8px;
    }
    .loading-bar-fill {
        height: 9px;
        width: 45%;
        border-radius: 999px;
        background: linear-gradient(90deg, #60a5fa, #a78bfa, #f87171);
        animation: loadingMove 1.1s ease-in-out infinite;
    }
    @keyframes loadingMove {
        0% { transform: translateX(-110%); }
        50% { transform: translateX(60%); }
        100% { transform: translateX(240%); }
    }
    @media (max-width: 760px) {
        .loading-hero {
            padding: 17px 16px !important;
            border-radius: 20px !important;
            margin: 12px 0 15px 0 !important;
        }
        .loading-title {
            font-size: 0.98rem !important;
            line-height: 1.45 !important;
        }
        .loading-sub {
            font-size: 0.82rem !important;
        }
        .loading-step {
            font-size: 0.72rem !important;
            padding: 6px 8px !important;
        }
    }

    .footer-box {
        color: #6b7280;
        font-size: 0.9rem;
        background: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 16px;
        padding: 16px;
        line-height: 1.7;
        margin-top: 26px;
    }

    .stTextInput > div > div > input {
        border-radius: 14px;
        border: 1px solid #d1d5db;
        padding: 14px;
        font-size: 1rem;
    }

    .stButton > button,
    .stFormSubmitButton > button {
        background: linear-gradient(135deg, #2563eb, #1d4ed8) !important;
        color: white !important;
        border: none !important;
        border-radius: 14px !important;
        padding: 0.78rem 1.4rem !important;
        font-weight: 900 !important;
        font-size: 1rem !important;
        height: 50px !important;
        box-shadow: 0 10px 24px rgba(37, 99, 235, 0.18) !important;
    }

    .stButton > button:hover,
    .stFormSubmitButton > button:hover {
        background: linear-gradient(135deg, #1d4ed8, #1e40af) !important;
        color: white !important;
        border: none !important;
    }
</style>
""",
    unsafe_allow_html=True
)


# =============================
# 공통 유틸
# =============================
def safe_text(value):
    return html.escape(str(value)) if value is not None else ""


def clean_number(value):
    if value is None:
        return None

    text = str(value)
    text = text.replace(",", "")
    text = text.replace("원", "")
    text = text.replace("%", "")
    text = text.replace("+", "")
    text = text.strip()

    return text


def format_won(value):
    if value is None or value == "":
        return "확인불가"

    raw = clean_number(value)

    try:
        return f"{int(float(raw)):,}원"
    except Exception:
        value = str(value)
        if value.endswith("원"):
            return value
        return f"{value}원"


def normalize_rate(value, sign=None):
    if value is None or value == "":
        return "0.00%"

    text = str(value).strip()
    text = text.replace("%", "")

    if text.startswith("-") or text.startswith("+"):
        return f"{text}%"

    if sign == "down":
        return f"-{text}%"

    if sign == "up":
        return f"+{text}%"

    return f"{text}%"


def make_request(url, params=None, timeout=10):
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://m.stock.naver.com/",
        "Accept": "application/json,text/html,*/*",
    }

    response = requests.get(url, params=params, headers=headers, timeout=timeout)
    response.raise_for_status()
    return response


def deep_find_first(obj, keys):
    if isinstance(obj, dict):
        for key in keys:
            if key in obj and obj[key] not in [None, ""]:
                return obj[key]

        for value in obj.values():
            found = deep_find_first(value, keys)
            if found not in [None, ""]:
                return found

    elif isinstance(obj, list):
        for item in obj:
            found = deep_find_first(item, keys)
            if found not in [None, ""]:
                return found

    return None


def collect_stock_candidates(obj):
    candidates = []

    def walk(x):
        if isinstance(x, dict):
            text_blob = json.dumps(x, ensure_ascii=False)

            code = None
            name = None

            code_keys = [
                "itemCode", "stockCode", "code", "symbolCode",
                "reutersCode", "cd", "itemcode"
            ]
            name_keys = [
                "stockName", "itemName", "name", "korName",
                "companyName", "nm", "stock_name"
            ]

            for key in code_keys:
                value = x.get(key)
                if value:
                    match = re.search(r"\d{6}", str(value))
                    if match:
                        code = match.group(0)
                        break

            for key in name_keys:
                value = x.get(key)
                if value and isinstance(value, str):
                    name = value.strip()
                    break

            if not code:
                match = re.search(r"\b\d{6}\b", text_blob)
                if match:
                    code = match.group(0)

            if code and name:
                item = {"code": code, "name": name}
                if item not in candidates:
                    candidates.append(item)

            for value in x.values():
                walk(value)

        elif isinstance(x, list):
            for item in x:
                walk(item)

    walk(obj)
    return candidates


def clean_html_text(text):
    if not text:
        return ""

    soup = BeautifulSoup(text, "html.parser")
    return soup.get_text(" ", strip=True)


# =============================
# 종목 검색
# =============================
@st.cache_data(ttl=3600)
def search_stock_code_from_naver_mobile(query):
    endpoints = [
        (
            "https://m.stock.naver.com/api/search/stock",
            {"keyword": query, "pageSize": 20, "page": 1}
        ),
        (
            "https://m.stock.naver.com/api/search/all",
            {"keyword": query}
        ),
        (
            "https://m.stock.naver.com/api/search/autoComplete",
            {"keyword": query}
        ),
    ]

    last_error = None

    for url, params in endpoints:
        try:
            response = make_request(url, params=params)
            data = response.json()
            candidates = collect_stock_candidates(data)

            if candidates:
                normalized_query = query.replace(" ", "").lower()

                for item in candidates:
                    if item["name"].replace(" ", "").lower() == normalized_query:
                        return item["code"], item["name"]

                return candidates[0]["code"], candidates[0]["name"]

        except Exception as e:
            last_error = e
            continue

    raise ValueError(f"네이버 모바일 증권 검색 실패: {last_error}")


@st.cache_data(ttl=3600)
def search_stock_code_from_naver_web(query):
    encoded = quote(f"{query} 주가")
    url = f"https://search.naver.com/search.naver?query={encoded}"

    response = make_request(url)
    soup = BeautifulSoup(response.text, "html.parser")

    links = soup.select('a[href*="finance.naver.com/item/main.naver?code="]')

    for link in links:
        href = link.get("href", "")
        match = re.search(r"code=(\d{6})", href)

        if match:
            code = match.group(1)
            name = get_stock_name_from_code(code)
            return code, name

    raise ValueError("네이버 통합검색에서도 종목코드를 찾지 못했습니다.")


def search_stock_code(query):
    try:
        return search_stock_code_from_naver_mobile(query)
    except Exception:
        return search_stock_code_from_naver_web(query)


COMMON_STOCK_UNIVERSE = [
    {"name": "삼성전자", "code": "005930"},
    {"name": "삼성전자우", "code": "005935"},
    {"name": "삼성전기", "code": "009150"},
    {"name": "삼성SDI", "code": "006400"},
    {"name": "삼성바이오로직스", "code": "207940"},
    {"name": "삼성물산", "code": "028260"},
    {"name": "삼성생명", "code": "032830"},
    {"name": "삼성화재", "code": "000810"},
    {"name": "삼성중공업", "code": "010140"},
    {"name": "삼성에스디에스", "code": "018260"},

    {"name": "현대차", "code": "005380"},
    {"name": "현대차우", "code": "005385"},
    {"name": "현대모비스", "code": "012330"},
    {"name": "현대글로비스", "code": "086280"},
    {"name": "현대제철", "code": "004020"},
    {"name": "현대건설", "code": "000720"},
    {"name": "현대오토에버", "code": "307950"},
    {"name": "현대위아", "code": "011210"},

    {"name": "기아", "code": "000270"},

    {"name": "SK하이닉스", "code": "000660"},
    {"name": "SK이노베이션", "code": "096770"},
    {"name": "SK스퀘어", "code": "402340"},
    {"name": "SK텔레콤", "code": "017670"},
    {"name": "SKC", "code": "011790"},
    {"name": "SK바이오팜", "code": "326030"},
    {"name": "SK바이오사이언스", "code": "302440"},

    {"name": "LG에너지솔루션", "code": "373220"},
    {"name": "LG화학", "code": "051910"},
    {"name": "LG전자", "code": "066570"},
    {"name": "LG이노텍", "code": "011070"},
    {"name": "LG생활건강", "code": "051900"},
    {"name": "LG디스플레이", "code": "034220"},

    {"name": "NAVER", "code": "035420"},
    {"name": "카카오", "code": "035720"},
    {"name": "카카오뱅크", "code": "323410"},
    {"name": "카카오페이", "code": "377300"},
    {"name": "카카오게임즈", "code": "293490"},

    {"name": "두산에너빌리티", "code": "034020"},
    {"name": "두산로보틱스", "code": "454910"},
    {"name": "두산퓨얼셀", "code": "336260"},

    {"name": "한화오션", "code": "042660"},
    {"name": "한화에어로스페이스", "code": "012450"},
    {"name": "한화솔루션", "code": "009830"},

    {"name": "POSCO홀딩스", "code": "005490"},
    {"name": "포스코퓨처엠", "code": "003670"},
    {"name": "포스코인터내셔널", "code": "047050"},

    {"name": "에코프로", "code": "086520"},
    {"name": "에코프로비엠", "code": "247540"},
    {"name": "에코프로머티", "code": "450080"},

    {"name": "셀트리온", "code": "068270"},
    {"name": "HLB", "code": "028300"},
    {"name": "알테오젠", "code": "196170"},
    {"name": "리가켐바이오", "code": "141080"},
]


def get_common_stock_suggestions(query, limit=8):
    query = str(query or "").strip()
    normalized_query = query.replace(" ", "").lower()

    if not normalized_query:
        return []

    matched = []

    for item in COMMON_STOCK_UNIVERSE:
        name = item["name"]
        code = item["code"]
        normalized_name = name.replace(" ", "").lower()

        if normalized_query in normalized_name or code.startswith(query):
            candidate = {"name": name, "code": code}

            if candidate not in matched:
                matched.append(candidate)

        if len(matched) >= limit:
            break

    return matched


@st.cache_data(ttl=3600)
def get_stock_suggestions(query, limit=8):
    """
    '삼성'처럼 일부 키워드만 입력해도 관련 종목 후보를 반환한다.
    구글 자동완성처럼 종목명 + KRX 코드를 보여주기 위한 데이터.
    """
    query = str(query or "").strip()

    if len(query) < 1:
        return []

    if re.fullmatch(r"\d{6}", query):
        try:
            return [{"code": query, "name": get_stock_name_from_code(query)}]
        except Exception:
            return [{"code": query, "name": query}]

    # 1차: 자주 검색되는 대형주/그룹주는 내장 후보에서 즉시 반환
    # 네이버 자동완성 API가 비어도 "삼성" 입력 시 삼성전자/삼성전기 등이 바로 뜨게 한다.
    collected = get_common_stock_suggestions(query, limit=limit)

    if len(collected) >= limit:
        return collected[:limit]

    endpoints = [
        (
            "https://m.stock.naver.com/api/search/stock",
            {"keyword": query, "pageSize": 30, "page": 1}
        ),
        (
            "https://m.stock.naver.com/api/search/all",
            {"keyword": query}
        ),
        (
            "https://m.stock.naver.com/api/search/autoComplete",
            {"keyword": query}
        ),
    ]

    for url, params in endpoints:
        try:
            response = make_request(url, params=params)
            data = response.json()
            candidates = collect_stock_candidates(data)

            for item in candidates:
                code = str(item.get("code", "")).strip()
                name = str(item.get("name", "")).strip()

                if not code or not name:
                    continue

                if not re.fullmatch(r"\d{6}", code):
                    continue

                normalized_query = query.replace(" ", "").lower()
                normalized_name = name.replace(" ", "").lower()

                # 종목명에 검색어가 들어가거나, 코드가 검색어로 시작하는 후보 우선
                if normalized_query not in normalized_name and not code.startswith(query):
                    continue

                candidate = {"code": code, "name": name}

                if candidate not in collected:
                    collected.append(candidate)

                if len(collected) >= limit:
                    return collected

        except Exception:
            continue

    return collected[:limit]


def stock_searchbox_options(search_term):
    search_term = str(search_term or "").strip()

    if len(search_term) < 1:
        return []

    suggestions = get_stock_suggestions(search_term, limit=8)

    labels = []
    for item in suggestions:
        name = item.get("name", "")
        code = item.get("code", "")

        if name and code:
            labels.append(f"📈 {name}  ·  KRX {code}")

    # 직접 6자리 코드를 친 경우도 선택 가능하게 유지
    if re.fullmatch(r"\d{6}", search_term) and not labels:
        labels.append(f"📈 {search_term}  ·  KRX {search_term}")

    return labels


def parse_stock_search_label(label):
    label = str(label or "").strip()

    match = re.search(r"KRX\s*:?\s*(\d{6})", label)
    if match:
        return match.group(1)

    # 아이콘/구분자 제거 후 종목명만 추출
    cleaned = label.replace("📈", "").strip()
    cleaned = re.sub(r"\s*[·|]\s*KRX\s*:?\s*\d{6}\s*$", "", cleaned).strip()
    cleaned = re.sub(r"\s*\(KRX:\s*\d{6}\)\s*$", "", cleaned).strip()

    return cleaned


@st.cache_data(ttl=3600)
def get_stock_name_from_code(stock_code):
    try:
        url = f"https://m.stock.naver.com/api/stock/{stock_code}/basic"
        response = make_request(url)
        data = response.json()

        name = deep_find_first(
            data,
            ["stockName", "itemName", "name", "korName", "companyName", "stock_name"]
        )

        if name:
            return str(name).strip()

    except Exception:
        pass

    try:
        url = f"https://finance.naver.com/item/main.naver?code={stock_code}"
        response = make_request(url)
        soup = BeautifulSoup(response.content, "html.parser", from_encoding="euc-kr")

        name_node = soup.select_one("div.wrap_company h2 a")
        if name_node:
            name = name_node.get_text(strip=True)
            if name:
                return name

        name_node = soup.select_one("div.wrap_company h2")
        if name_node:
            name = name_node.get_text(strip=True)
            if name:
                return name

    except Exception:
        pass

    return stock_code


def resolve_stock_code(user_input):
    user_input = user_input.strip()

    if not user_input:
        raise ValueError("종목명 또는 종목코드를 입력하세요.")

    if re.fullmatch(r"\d{6}", user_input):
        stock_code = user_input
        stock_name = get_stock_name_from_code(stock_code)
        return stock_code, stock_name

    return search_stock_code(user_input)


# =============================
# 가격 조회
# =============================
def get_price_from_mobile_basic(stock_code, stock_name):
    url = f"https://m.stock.naver.com/api/stock/{stock_code}/basic"
    response = make_request(url)
    data = response.json()

    real_name = deep_find_first(
        data,
        ["stockName", "itemName", "name", "korName", "companyName", "stock_name"]
    )
    if real_name:
        stock_name = str(real_name).strip()

    current_price = deep_find_first(
        data,
        ["closePrice", "nowVal", "currentPrice", "nv", "price"]
    )

    change_amount = deep_find_first(
        data,
        ["compareToPreviousClosePrice", "compareToPreviousPrice", "changePrice", "cv"]
    )

    change_rate = deep_find_first(
        data,
        ["fluctuationsRatio", "changeRate", "cr", "rate"]
    )

    risefall = str(deep_find_first(data, ["risefall", "rf", "compareToPreviousPriceCode"]) or "")

    sign = None
    if risefall in ["5", "down", "DOWN", "FALLING", "하락"]:
        sign = "down"
    elif risefall in ["2", "up", "UP", "RISING", "상승"]:
        sign = "up"

    if current_price is None:
        raise ValueError("모바일 basic API에서 현재가를 찾지 못했습니다.")

    display_rate = normalize_rate(change_rate, sign=sign)

    if sign == "down":
        display_change = f"-{format_won(change_amount)}"
    elif sign == "up":
        display_change = f"+{format_won(change_amount)}"
    else:
        display_change = format_won(change_amount)

    display_change = display_change.replace("원원", "원")

    return {
        "종목명": stock_name,
        "종목코드": stock_code,
        "현재가": format_won(current_price),
        "등락률": display_rate,
        "전일대비": display_change,
        "방향": "하락" if sign == "down" else "상승" if sign == "up" else "보합",
        "데이터출처": "네이버 모바일 증권",
    }


def get_price_from_pc_finance(stock_code, stock_name):
    url = f"https://finance.naver.com/item/main.naver?code={stock_code}"
    response = make_request(url)

    soup = BeautifulSoup(response.content, "html.parser", from_encoding="euc-kr")

    real_name = get_stock_name_from_code(stock_code)
    if real_name:
        stock_name = real_name

    current_node = soup.select_one("p.no_today span.blind")

    if not current_node:
        raise ValueError("PC 네이버 금융에서 현재가를 가져오지 못했습니다.")

    current_price = current_node.get_text(strip=True)

    no_exday = soup.select_one("p.no_exday")

    direction = "보합"
    change_amount = "0"
    change_rate = "0.00"

    if no_exday:
        if no_exday.select_one("em.no_down"):
            direction = "하락"
        elif no_exday.select_one("em.no_up"):
            direction = "상승"
        else:
            direction = "보합"

        nums = [x.get_text(strip=True) for x in no_exday.select("span.blind")]

        if len(nums) >= 1:
            change_amount = nums[0]

        if len(nums) >= 2:
            change_rate = nums[1]

    if direction == "하락":
        display_rate = normalize_rate(change_rate, sign="down")
        display_change = f"-{format_won(change_amount)}"
    elif direction == "상승":
        display_rate = normalize_rate(change_rate, sign="up")
        display_change = f"+{format_won(change_amount)}"
    else:
        display_rate = normalize_rate(change_rate)
        display_change = format_won(change_amount)

    display_change = display_change.replace("원원", "원")

    return {
        "종목명": stock_name,
        "종목코드": stock_code,
        "현재가": format_won(current_price),
        "등락률": display_rate,
        "전일대비": display_change,
        "방향": direction,
        "데이터출처": "네이버 금융",
    }



def get_kis_base_url():
    if KIS_ENV == "virtual":
        return "https://openapivts.koreainvestment.com:29443"

    return "https://openapi.koreainvestment.com:9443"


def is_kis_configured():
    return bool(KIS_APP_KEY and KIS_APP_SECRET)


@st.cache_data(ttl=60 * 60 * 23)
def get_kis_access_token_cached(app_key, app_secret, env):
    """
    한국투자증권 access token 발급.
    access token은 보통 24시간 유효하므로 23시간 캐시한다.
    """
    if not app_key or not app_secret:
        raise ValueError("KIS_APP_KEY 또는 KIS_APP_SECRET이 없습니다.")

    base_url = "https://openapivts.koreainvestment.com:29443" if env == "virtual" else "https://openapi.koreainvestment.com:9443"

    url = f"{base_url}/oauth2/tokenP"
    headers = {
        "content-type": "application/json; charset=UTF-8"
    }
    payload = {
        "grant_type": "client_credentials",
        "appkey": app_key,
        "appsecret": app_secret,
    }

    response = requests.post(url, headers=headers, json=payload, timeout=10)
    response.raise_for_status()

    data = response.json()
    token = data.get("access_token")

    if not token:
        raise ValueError("한국투자증권 access_token이 응답에 없습니다.")

    return token


def get_kis_access_token():
    return get_kis_access_token_cached(KIS_APP_KEY, KIS_APP_SECRET, KIS_ENV)


def parse_kis_number(value, default=0):
    try:
        if value is None:
            return default
        text = str(value).replace(",", "").strip()
        if text == "":
            return default
        return float(text)
    except Exception:
        return default


def format_kis_won(value):
    try:
        number = int(float(str(value).replace(",", "").strip()))
        return f"{number:,}원"
    except Exception:
        return "확인불가"


def format_kis_count(value):
    try:
        number = int(float(str(value).replace(",", "").strip()))
        return f"{number:,}"
    except Exception:
        return "확인불가"


def format_kis_trading_value(value):
    try:
        number = int(float(str(value).replace(",", "").strip()))
        if number >= 1_0000_0000_0000:
            return f"{number / 1_0000_0000_0000:.1f}조원"
        if number >= 1_0000_0000:
            return f"{number / 1_0000_0000:.0f}억원"
        return f"{number:,}원"
    except Exception:
        return "확인불가"


@st.cache_data(ttl=60)
def get_kis_price_data_cached(stock_code, stock_name, app_key, app_secret, env):
    if not app_key or not app_secret:
        raise ValueError("한국투자증권 API 키가 설정되지 않았습니다.")

    base_url = "https://openapivts.koreainvestment.com:29443" if env == "virtual" else "https://openapi.koreainvestment.com:9443"
    token = get_kis_access_token_cached(app_key, app_secret, env)

    url = f"{base_url}/uapi/domestic-stock/v1/quotations/inquire-price"
    headers = {
        "content-type": "application/json; charset=UTF-8",
        "authorization": f"Bearer {token}",
        "appkey": app_key,
        "appsecret": app_secret,
        "tr_id": "FHKST01010100",
        "custtype": "P",
    }
    params = {
        "FID_COND_MRKT_DIV_CODE": "J",
        "FID_INPUT_ISCD": stock_code,
    }

    response = requests.get(url, headers=headers, params=params, timeout=10)
    response.raise_for_status()

    data = response.json()

    if data.get("rt_cd") not in [None, "0"]:
        raise ValueError(f"한국투자증권 현재가 조회 실패: {data.get('msg1', data)}")

    output = data.get("output", {})

    current_price = output.get("stck_prpr")
    change_amount = output.get("prdy_vrss")
    change_rate = output.get("prdy_ctrt")
    sign_code = str(output.get("prdy_vrss_sign", ""))

    rate_value = parse_kis_number(change_rate)
    change_value = parse_kis_number(change_amount)

    if sign_code in ["5"] or rate_value < 0 or change_value < 0:
        direction = "하락"
        display_rate = f"-{abs(rate_value):.2f}%"
        display_change = f"-{format_kis_won(abs(change_value))}"
    elif sign_code in ["2"] or rate_value > 0 or change_value > 0:
        direction = "상승"
        display_rate = f"+{abs(rate_value):.2f}%"
        display_change = f"+{format_kis_won(abs(change_value))}"
    else:
        direction = "보합"
        display_rate = "0.00%"
        display_change = "0원"

    return {
        "종목명": stock_name,
        "종목코드": stock_code,
        "현재가": format_kis_won(current_price),
        "등락률": display_rate,
        "전일대비": display_change,
        "방향": direction,
        "거래량": format_kis_count(output.get("acml_vol")),
        "거래대금": format_kis_trading_value(output.get("acml_tr_pbmn")),
        "시가": format_kis_won(output.get("stck_oprc")),
        "고가": format_kis_won(output.get("stck_hgpr")),
        "저가": format_kis_won(output.get("stck_lwpr")),
        "전일종가": format_kis_won(output.get("stck_sdpr")),
        "데이터출처": "한국투자증권 API",
        "_raw": {
            "current_price": parse_kis_number(current_price),
            "change_rate": rate_value,
            "volume": parse_kis_number(output.get("acml_vol")),
            "trading_value": parse_kis_number(output.get("acml_tr_pbmn")),
            "open": parse_kis_number(output.get("stck_oprc")),
            "high": parse_kis_number(output.get("stck_hgpr")),
            "low": parse_kis_number(output.get("stck_lwpr")),
            "prev_close": parse_kis_number(output.get("stck_sdpr")),
        }
    }


def get_kis_price_data(stock_code, stock_name):
    return get_kis_price_data_cached(
        stock_code,
        stock_name,
        KIS_APP_KEY,
        KIS_APP_SECRET,
        KIS_ENV
    )


@st.cache_data(ttl=600)
def get_kis_daily_chart_data_cached(stock_code, app_key, app_secret, env, days=90):
    """
    한국투자증권 국내주식 기간별 시세.
    차트용 종가/거래량 데이터를 가져온다.
    실패 시 빈 리스트를 반환한다.
    """
    if not app_key or not app_secret:
        return []

    base_url = "https://openapivts.koreainvestment.com:29443" if env == "virtual" else "https://openapi.koreainvestment.com:9443"
    token = get_kis_access_token_cached(app_key, app_secret, env)

    end_date = datetime.now().strftime("%Y%m%d")
    start_date = (datetime.now() - pd.Timedelta(days=int(days * 1.8))).strftime("%Y%m%d")

    url = f"{base_url}/uapi/domestic-stock/v1/quotations/inquire-daily-itemchartprice"
    headers = {
        "content-type": "application/json; charset=UTF-8",
        "authorization": f"Bearer {token}",
        "appkey": app_key,
        "appsecret": app_secret,
        "tr_id": "FHKST03010100",
        "custtype": "P",
    }
    params = {
        "FID_COND_MRKT_DIV_CODE": "J",
        "FID_INPUT_ISCD": stock_code,
        "FID_INPUT_DATE_1": start_date,
        "FID_INPUT_DATE_2": end_date,
        "FID_PERIOD_DIV_CODE": "D",
        "FID_ORG_ADJ_PRC": "0",
    }

    response = requests.get(url, headers=headers, params=params, timeout=10)
    response.raise_for_status()

    data = response.json()

    if data.get("rt_cd") not in [None, "0"]:
        return []

    output2 = data.get("output2", [])
    rows = []

    for item in output2:
        date_text = str(item.get("stck_bsop_date", "")).strip()
        if len(date_text) != 8:
            continue

        try:
            date_value = datetime.strptime(date_text, "%Y%m%d")
        except Exception:
            continue

        close_price = parse_kis_number(item.get("stck_clpr"))
        open_price = parse_kis_number(item.get("stck_oprc"))
        high_price = parse_kis_number(item.get("stck_hgpr"))
        low_price = parse_kis_number(item.get("stck_lwpr"))
        volume = parse_kis_number(item.get("acml_vol"))

        if close_price <= 0:
            continue

        rows.append({
            "date": date_value,
            "종가": close_price,
            "시가": open_price,
            "고가": high_price,
            "저가": low_price,
            "거래량": volume,
        })

    rows = sorted(rows, key=lambda x: x["date"])

    if days:
        rows = rows[-int(days):]

    return rows


def get_kis_daily_chart_data(stock_code, days=90):
    return get_kis_daily_chart_data_cached(
        stock_code,
        KIS_APP_KEY,
        KIS_APP_SECRET,
        KIS_ENV,
        days
    )


def get_real_price_data(user_input):
    stock_code, stock_name = resolve_stock_code(user_input)

    if is_kis_configured():
        try:
            return get_kis_price_data(stock_code, stock_name)
        except Exception as e:
            try:
                st.session_state.data_warnings.append("한국투자증권 시세 조회가 지연되어 네이버 시세로 대체했습니다.")
                log_app_error("한국투자증권 현재가 조회 실패", e)
            except Exception:
                pass

    try:
        return get_price_from_mobile_basic(stock_code, stock_name)
    except Exception:
        return get_price_from_pc_finance(stock_code, stock_name)


# =============================
# 환율 조회
# =============================
@st.cache_data(ttl=600)
def get_usd_krw_exchange_rate():
    """
    네이버 금융 시장지표에서 원/달러 환율을 가져온다.
    실패하면 확인불가로 반환한다.
    """
    url = "https://finance.naver.com/marketindex/"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://finance.naver.com/",
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, "html.parser", from_encoding="euc-kr")

        usd_block = soup.select_one("div.market1 div.data")
        if not usd_block:
            usd_block = soup.select_one(".market1 .data")

        value_node = usd_block.select_one("span.value") if usd_block else None
        change_node = usd_block.select_one("span.change") if usd_block else None

        value = value_node.get_text(strip=True) if value_node else None
        change = change_node.get_text(strip=True) if change_node else ""

        if not value:
            raise ValueError("환율 값을 찾지 못했습니다.")

        direction = "보합"
        if usd_block and usd_block.select_one(".up"):
            direction = "상승"
        elif usd_block and usd_block.select_one(".down"):
            direction = "하락"

        if change:
            if direction == "상승" and not change.startswith("+"):
                change = f"+{change}"
            elif direction == "하락" and not change.startswith("-"):
                change = f"-{change}"

        return {
            "환율명": "USD/KRW",
            "현재환율": f"{value}원",
            "전일대비": change if change else "확인불가",
            "방향": direction,
            "데이터출처": "네이버 금융 시장지표",
        }

    except Exception:
        return {
            "환율명": "USD/KRW",
            "현재환율": "확인불가",
            "전일대비": "확인불가",
            "방향": "확인불가",
            "데이터출처": "네이버 금융 시장지표",
        }



# =============================
# 호출량/파일 캐시 관리
# =============================
CACHE_DIR = Path("cache_data")
API_USAGE_FILE = Path("api_usage.json")

NEWS_CACHE_TTL = 60 * 30          # 30분
DART_CACHE_TTL = 60 * 5           # 5분
MARKET_CACHE_TTL = 60 * 3         # 3분
AI_CACHE_TTL = 60 * 30            # 30분


def ensure_cache_dir():
    CACHE_DIR.mkdir(exist_ok=True)


def today_key():
    return datetime.now().strftime("%Y-%m-%d")


def load_api_usage():
    if not API_USAGE_FILE.exists():
        return {
            "date": today_key(),
            "naver_news": 0,
            "dart_list": 0,
            "market_pages": 0,
            "openai": 0,
            "cache_hit": 0,
        }

    try:
        data = json.loads(API_USAGE_FILE.read_text(encoding="utf-8"))
    except Exception:
        data = {}

    if data.get("date") != today_key():
        data = {
            "date": today_key(),
            "naver_news": 0,
            "dart_list": 0,
            "market_pages": 0,
            "openai": 0,
            "cache_hit": 0,
        }

    for key in ["naver_news", "dart_list", "market_pages", "openai", "cache_hit"]:
        data.setdefault(key, 0)

    return data


def save_api_usage(data):
    API_USAGE_FILE.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )


def increment_api_usage(key, amount=1):
    data = load_api_usage()
    data[key] = int(data.get(key, 0)) + amount
    save_api_usage(data)


def safe_cache_key(value):
    raw = str(value).encode("utf-8")
    return hashlib.md5(raw).hexdigest()


def cache_path(namespace, key):
    ensure_cache_dir()
    return CACHE_DIR / f"{namespace}_{safe_cache_key(key)}.json"


def get_file_cache(namespace, key, ttl_seconds):
    path = cache_path(namespace, key)

    if not path.exists():
        return None, "MISS", None

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        saved_at = data.get("_saved_at", 0)
        age = int(time.time() - saved_at)

        if age <= ttl_seconds:
            increment_api_usage("cache_hit")
            return data.get("payload"), "HIT", age

        return None, "EXPIRED", age

    except Exception:
        return None, "BROKEN", None


def set_file_cache(namespace, key, payload):
    path = cache_path(namespace, key)

    data = {
        "_saved_at": time.time(),
        "_saved_at_text": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "payload": payload,
    }

    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )


def format_age(seconds):
    if seconds is None:
        return "확인불가"

    seconds = int(seconds)

    if seconds < 60:
        return f"{seconds}초 전"

    minutes = seconds // 60

    if minutes < 60:
        return f"{minutes}분 전"

    hours = minutes // 60
    return f"{hours}시간 전"


def set_cache_status(label, status, age=None):
    if "cache_status" not in st.session_state:
        st.session_state.cache_status = []

    st.session_state.cache_status.append({
        "label": label,
        "status": status,
        "age": age,
    })


# =============================
# 실제 네이버 뉴스 API
# =============================
def get_mock_news(stock_name):
    return [
        {
            "title": f"{stock_name}, 외국인 매도세에 약세",
            "description": "최근 외국인 수급 악화와 시장 변동성 확대 영향으로 주가가 하락했다.",
            "link": "#",
            "pubDate": "mock",
        },
        {
            "title": f"{stock_name}, 업종 전반 조정 영향",
            "description": "관련 업종 전반의 투자심리 악화가 주가에 영향을 준 것으로 풀이된다.",
            "link": "#",
            "pubDate": "mock",
        },
        {
            "title": "코스피, 기관·외국인 매도에 하락 마감",
            "description": "국내 증시는 대외 불확실성과 차익실현 매물로 약세를 보였다.",
            "link": "#",
            "pubDate": "mock",
        },
    ]


def get_naver_news_live(stock_name, display=5):
    if not NAVER_CLIENT_ID or not NAVER_CLIENT_SECRET:
        return get_mock_news(stock_name)

    url = "https://openapi.naver.com/v1/search/news.json"

    headers = {
        "X-Naver-Client-Id": NAVER_CLIENT_ID,
        "X-Naver-Client-Secret": NAVER_CLIENT_SECRET,
    }

    params = {
        "query": f"{stock_name} 주가",
        "display": display,
        "sort": "date",
    }

    try:
        increment_api_usage("naver_news")
        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()

        items = response.json().get("items", [])

        news_list = []

        for item in items:
            title = clean_html_text(item.get("title", ""))
            description = clean_html_text(item.get("description", ""))
            link = item.get("originallink") or item.get("link", "")
            pub_date = item.get("pubDate", "")

            news_list.append({
                "title": title,
                "description": description,
                "link": link,
                "pubDate": pub_date,
            })

        if not news_list:
            return get_mock_news(stock_name)

        return news_list

    except Exception as e:
        st.warning(f"네이버 뉴스 API 조회 실패: {e}")
        return get_mock_news(stock_name)




def get_naver_news(stock_name, display=5):
    cache_key_value = f"{stock_name}_{display}"
    cached, status, age = get_file_cache("news", cache_key_value, NEWS_CACHE_TTL)

    if cached is not None:
        set_cache_status("뉴스", "캐시", age)
        return cached

    result = get_naver_news_live(stock_name, display)
    set_file_cache("news", cache_key_value, result)
    set_cache_status("뉴스", "실시간 호출", 0)
    return result


def dedupe_news_items(news_items, limit=18):
    deduped = []
    seen = set()

    for item in news_items:
        title = str(item.get("title", "")).strip()
        link = str(item.get("link", "")).strip()
        key = (title, link)

        if not title or key in seen:
            continue

        seen.add(key)
        deduped.append(item)

        if len(deduped) >= limit:
            break

    return deduped


def build_deep_news_queries(stock_name):
    """
    심층 리포트용 확장 뉴스 검색어.
    종목명만 검색하면 서사가 얕아지므로 실적/수주/전망/업종 키워드를 함께 본다.
    """
    base_queries = [
        f"{stock_name} 주가",
        f"{stock_name} 실적 전망",
        f"{stock_name} 수주",
        f"{stock_name} 목표가",
        f"{stock_name} 업황",
        f"{stock_name} 투자심리",
    ]

    thematic_queries = []

    name = str(stock_name)

    if any(keyword in name for keyword in ["삼성전자", "SK하이닉스", "한미반도체", "주성엔지니어링", "리노공업"]):
        thematic_queries += [
            "반도체 HBM 엔비디아",
            "메모리 반도체 가격 전망",
            "AI 반도체 수요",
            "파운드리 경쟁 TSMC 삼성전자",
        ]

    if any(keyword in name for keyword in ["씨에스윈드", "두산에너빌리티", "한화솔루션", "OCI"]):
        thematic_queries += [
            "풍력 정책 트럼프",
            "신재생에너지 원전 전력수요",
            "해상풍력 수주 전망",
        ]

    if any(keyword in name for keyword in ["두산에너빌리티", "비에이치아이", "한전기술", "우리기술"]):
        thematic_queries += [
            "원전 수주 SMR 전력수요",
            "AI 데이터센터 전력 원전",
        ]

    if any(keyword in name for keyword in ["현대차", "기아", "현대모비스"]):
        thematic_queries += [
            "자동차 수출 환율 실적",
            "전기차 하이브리드 판매 전망",
        ]

    if any(keyword in name for keyword in ["에코프로", "에코프로비엠", "LG에너지솔루션", "삼성SDI"]):
        thematic_queries += [
            "2차전지 전기차 수요 둔화",
            "리튬 가격 배터리 실적 전망",
        ]

    return (base_queries + thematic_queries)[:10]


def get_expanded_news_for_deep_report(stock_name):
    cache_key_value = f"deep_news_v2_{stock_name}"
    cached, status, age = get_file_cache("news", cache_key_value, NEWS_CACHE_TTL)

    if cached is not None:
        set_cache_status("심층 뉴스", "캐시", age)
        return cached

    all_news = []

    # 첫 검색은 기존 get_naver_news로 캐시와 mock fallback을 같이 활용
    try:
        all_news.extend(get_naver_news(stock_name, display=8))
    except Exception:
        pass

    # 확장 검색
    for query in build_deep_news_queries(stock_name):
        try:
            all_news.extend(get_naver_news_live(query, display=4))
        except Exception:
            continue

    result = dedupe_news_items(all_news, limit=22)

    if not result:
        result = get_mock_news(stock_name)

    set_file_cache("news", cache_key_value, result)
    set_cache_status("심층 뉴스", "실시간 호출", 0)
    return result


def score_news_relevance(news_item, price_data, ai_result=None):
    """
    심층 분석에는 많은 뉴스를 쓰되, 사용자 화면에는 주가 움직임과 가장 관계 깊은 뉴스만 보여준다.
    """
    stock_name = str(price_data.get("종목명", ""))
    move_type = get_price_move_type(price_data)
    text_value = f"{news_item.get('title', '')} {news_item.get('description', '')}".lower()

    score = 0

    # 종목명이 직접 들어간 뉴스 우선
    if stock_name and stock_name.lower() in text_value:
        score += 35

    # 주가/실적/수주/목표가/업황 같은 직접 관련 단어
    direct_keywords = [
        "주가", "급등", "급락", "상승", "하락", "강세", "약세",
        "실적", "영업이익", "매출", "수주", "계약", "목표가",
        "전망", "컨센서스", "증권가", "투자의견", "외국인", "기관",
        "거래량", "거래대금", "공시", "반도체", "hbm", "ai"
    ]

    for keyword in direct_keywords:
        if keyword.lower() in text_value:
            score += 8

    if move_type == "상승":
        positive_keywords = [
            "급등", "상승", "강세", "호재", "수혜", "기대", "반등",
            "상향", "최고", "신고가", "호실적", "개선", "증가", "수주"
        ]
        for keyword in positive_keywords:
            if keyword.lower() in text_value:
                score += 12

    elif move_type == "하락":
        negative_keywords = [
            "급락", "하락", "약세", "우려", "부진", "적자", "손실",
            "리스크", "불확실", "감소", "둔화", "소송", "악재"
        ]
        for keyword in negative_keywords:
            if keyword.lower() in text_value:
                score += 12

    # AI가 감지한 키워드가 제목/요약에 있으면 가산
    if ai_result:
        for keyword in ai_result.get("negative_keywords", [])[:8]:
            if str(keyword).lower() in text_value:
                score += 10

    # 너무 일반적인 시장 기사보다 종목 직접 기사를 우선
    generic_keywords = ["코스피", "코스닥", "증시", "뉴욕증시", "환율"]
    if stock_name and stock_name.lower() not in text_value:
        if any(k in text_value for k in generic_keywords):
            score -= 5

    return score


def select_display_news(news_data, price_data, ai_result=None, limit=5):
    """
    수집 뉴스는 AI 분석용으로 많이 유지하고,
    화면 노출은 관련도 높은 4~5개만 보여준다.
    """
    if not news_data:
        return []

    ranked = sorted(
        news_data,
        key=lambda item: score_news_relevance(item, price_data, ai_result),
        reverse=True
    )

    selected = []
    seen_titles = set()

    for item in ranked:
        title = str(item.get("title", "")).strip()

        if not title or title in seen_titles:
            continue

        seen_titles.add(title)
        selected.append(item)

        if len(selected) >= limit:
            break

    return selected

# =============================
# DART 공시
# =============================
def get_mock_dart(stock_name):
    return [
        {
            "title": "최근 주요 공시 없음",
            "description": "DART_API_KEY가 없거나 공시 조회에 실패했습니다.",
            "link": "#",
            "receipt_date": "",
        }
    ]


@st.cache_data(ttl=86400)
def get_dart_corp_code_map():
    """
    OpenDART corpCode.xml을 다운로드해 stock_code -> corp_code 매핑을 만든다.
    최초 1회 캐시 후 하루 동안 재사용.
    """
    if not DART_API_KEY:
        return {}

    url = "https://opendart.fss.or.kr/api/corpCode.xml"
    params = {"crtfc_key": DART_API_KEY}

    try:
        response = requests.get(url, params=params, timeout=20)
        response.raise_for_status()

        zf = zipfile.ZipFile(io.BytesIO(response.content))
        xml_name = zf.namelist()[0]
        xml_bytes = zf.read(xml_name)

        root = ET.fromstring(xml_bytes)

        mapping = {}

        for item in root.findall("list"):
            corp_code = item.findtext("corp_code", default="").strip()
            corp_name = item.findtext("corp_name", default="").strip()
            stock_code = item.findtext("stock_code", default="").strip()

            if corp_code and stock_code:
                mapping[stock_code] = {
                    "corp_code": corp_code,
                    "corp_name": corp_name,
                    "stock_code": stock_code,
                }

        return mapping

    except Exception:
        return {}


def get_corp_code_by_stock_code(stock_code):
    mapping = get_dart_corp_code_map()
    data = mapping.get(stock_code)

    if not data:
        return None

    return data.get("corp_code")


def classify_dart_filing(report_name):
    """
    공시 제목 기준으로 악재/주의/중립/호재 가능성을 간단 분류.
    """
    bad_keywords = [
        "유상증자", "전환사채", "신주인수권부사채", "감자", "관리종목",
        "상장폐지", "불성실공시", "횡령", "배임", "감사의견", "의견거절",
        "한정", "최대주주변경", "소송", "거래정지", "파산", "회생절차"
    ]

    good_keywords = [
        "단일판매", "공급계약", "자사주", "무상증자", "배당", "수주",
        "기술이전", "특허", "합병", "공개매수"
    ]

    for keyword in bad_keywords:
        if keyword in report_name:
            return "주의"

    for keyword in good_keywords:
        if keyword in report_name:
            return "긍정 가능"

    return "중립"


def get_dart_filings_live(stock_code, stock_name, count=5):
    """
    종목코드 -> corp_code 변환 후 OpenDART 공시검색 API 호출.
    """
    if not DART_API_KEY:
        return get_mock_dart(stock_name)

    corp_code = get_corp_code_by_stock_code(stock_code)

    if not corp_code:
        return [
            {
                "title": "DART 기업코드 매칭 실패",
                "description": f"{stock_name}({stock_code})의 DART corp_code를 찾지 못했습니다.",
                "link": "#",
                "receipt_date": "",
            }
        ]

    url = "https://opendart.fss.or.kr/api/list.json"
    params = {
        "crtfc_key": DART_API_KEY,
        "corp_code": corp_code,
        "page_no": 1,
        "page_count": count,
        "sort": "date",
        "sort_mth": "desc",
    }

    try:
        increment_api_usage("dart_list")
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()

        if data.get("status") not in ["000", "013"]:
            return [
                {
                    "title": "DART 공시 조회 실패",
                    "description": f"{data.get('message', '알 수 없는 오류')}",
                    "link": "#",
                    "receipt_date": "",
                }
            ]

        filings = data.get("list", [])

        if not filings:
            return [
                {
                    "title": "최근 주요 공시 없음",
                    "description": f"{stock_name}의 최근 공시가 조회되지 않았습니다.",
                    "link": "#",
                    "receipt_date": "",
                }
            ]

        result = []

        for item in filings[:count]:
            report_name = item.get("report_nm", "")
            receipt_no = item.get("rcept_no", "")
            receipt_date = item.get("rcept_dt", "")
            corp_name = item.get("corp_name", stock_name)
            category = classify_dart_filing(report_name)

            dart_url = f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={receipt_no}"

            result.append({
                "title": f"[{category}] {report_name}",
                "description": f"{corp_name} · 접수일 {receipt_date}",
                "link": dart_url,
                "receipt_no": receipt_no,
                "receipt_date": receipt_date,
                "category": category,
            })

        return result

    except Exception as e:
        return [
            {
                "title": "DART 공시 조회 오류",
                "description": str(e),
                "link": "#",
                "receipt_date": "",
            }
        ]




def get_dart_filings(stock_code, stock_name, count=5):
    cache_key_value = f"{stock_code}_{count}"
    cached, status, age = get_file_cache("dart", cache_key_value, DART_CACHE_TTL)

    if cached is not None:
        set_cache_status("DART", "캐시", age)
        return cached

    result = get_dart_filings_live(stock_code, stock_name, count)
    set_file_cache("dart", cache_key_value, result)
    set_cache_status("DART", "실시간 호출", 0)
    return result

# =============================
# AI 분석
# =============================
def analyze_with_ai_live(stock_name, price_data, news_data, dart_data, exchange_data):
    move_type = get_price_move_type(price_data)
    move_word = get_move_word(price_data)

    if not OPENAI_API_KEY:
        return {
            "summary": f"{stock_name}는 현재 {price_data.get('등락률', '확인불가')} {move_word} 중이며, 뉴스 흐름, 환율 환경, 공시 여부를 함께 확인해야 하는 상황입니다.",
            "risk_level": "중간",
            "market_or_company": "현재 데이터 기준으로는 개별 기업 악재와 시장/섹터 영향을 함께 확인해야 합니다.",
            "disclosure_risk": f"최근 공시: {dart_data[0].get('title') if dart_data else '확인 필요'}",
            "negative_keywords": ["주가 변동", "뉴스 확인", "환율", "공시 확인"],
            "reasons": [
                {
                    "title": "주가 변동성 확대",
                    "description": f"{price_data.get('종목명')}의 현재 등락률은 {price_data.get('등락률')}입니다. 단기 변동성이 커진 상태라면 뉴스와 공시를 함께 확인해야 합니다.",
                },
                {
                    "title": "환율 환경 확인 필요",
                    "description": f"현재 원/달러 환율은 {exchange_data.get('현재환율')}입니다. 환율 상승은 외국인 수급 부담으로 이어질 수 있습니다.",
                },
                {
                    "title": "공시 리스크 확인",
                    "description": "DART 공시에서 유상증자, 전환사채, 최대주주 변경, 실적 관련 공시가 있는지 확인해야 합니다.",
                },
            ],
            "checkpoints": [
                "최근 뉴스가 단순 시황인지 개별 악재인지 구분",
                "원/달러 환율 상승 여부 확인",
                "최근 DART 공시 제목 확인",
                "같은 업종 대장주의 흐름 확인",
            ],
        }

    client = OpenAI(api_key=OPENAI_API_KEY)

    prompt = f"""
너는 한국 주식 개인투자자를 위한 주가 변동 원인 분석 AI다.

현재 등락 방향:
{move_type}

중요 제한:
- 매수/매도 추천을 직접 하지 마라.
- 수익을 보장하지 마라.
- 목표가를 제시하지 마라.
- 투자 판단 보조 정보로만 설명하라.
- 초보 투자자가 이해할 수 있게 쉽게 설명하라.

분석 대상 종목:
{stock_name}

가격 데이터:
{price_data}

환율 데이터:
{exchange_data}

최근 뉴스:
{news_data}

최근 DART 공시:
{dart_data}

분석 방향:
- 현재 등락 방향이 "상승"이면 절대 "하락 원인"이라고 단정하지 말고, 상승 배경/상승 트리거/시장 반응을 중심으로 설명하라.
- 현재 등락 방향이 "하락"이면 하락 트리거/악재/리스크를 중심으로 설명하라.
- 현재 등락 방향이 "보합"이면 변동성이 제한적인 이유와 확인할 요인을 설명하라.
- 단순 뉴스 요약이 아니라 "최근 배경 → 직접 트리거 → 산업/정책 변화 → 실적·수주 또는 거래량 반응 → 추가 확인점" 순서로 생각하라.
- 제공된 가격 데이터에 거래량/거래대금/시가/고가/저가가 있으면 시장 반응 강도를 함께 해석하라.
- 수주 감소, 실적 하향, 정책 변화처럼 근거가 필요한 내용은 제공된 뉴스/공시에 근거가 있을 때만 확정적으로 말하라.
- 근거가 부족하면 "확인 필요"라고 표현하라.
- 상승 중인 종목에 대해 과거 악재 뉴스만 보고 현재를 하락처럼 설명하지 마라.
- 심층 리포트는 짧은 일반론이 아니라, 사용자가 돈을 내고 볼 만한 수준으로 구체적으로 작성하라.
- 단, 없는 사실을 만들지 마라. 뉴스/공시/가격 데이터에서 근거가 부족한 부분은 "확인 필요"라고 명확히 써라.
- 씨에스윈드 예시처럼 "최근 배경 → 직접 트리거 → 산업 흐름 → 실적/수주 우려 → 주가·거래량 반응 → 단기/구조 판단"의 서사를 만들어라.
- 2025/2026 매출·영업이익 전망처럼 컨센서스가 필요한 내용은 제공 데이터에 없으면 확정하지 말고 별도 확인 필요라고 써라.
- 문장은 반드시 초보자용으로 써라. 어려운 말은 풀어서 설명하라.
- 각 deep_report 항목은 너무 길게 쓰지 말고, 핵심 한 문장 + 쉬운 설명 1~2문장 수준으로 작성하라.
- 사용자가 한눈에 이해할 수 있게 "쉽게 말하면" 식으로 설명하라.

반드시 아래 JSON 형식으로만 답해라.
마크다운 설명은 넣지 마라.
JSON 앞뒤에 ```json 같은 코드블록도 넣지 마라.

{{
  "summary": "현재 등락 방향에 맞춰 상승/하락/변동 원인을 한 문장으로 요약",
  "risk_level": "낮음 또는 중간 또는 높음",
  "market_or_company": "시장/섹터 영향인지 개별 종목 이슈인지 판단",
  "disclosure_risk": "공시가 현재 등락에 주는 영향 설명",
  "negative_keywords": ["감지 키워드1", "감지 키워드2", "감지 키워드3"],
  "reasons": [
    {{
      "title": "현재 등락 원인 제목",
      "description": "초보자도 이해하기 쉬운 설명"
    }},
    {{
      "title": "현재 등락 원인 제목",
      "description": "초보자도 이해하기 쉬운 설명"
    }},
    {{
      "title": "하락 원인 제목",
      "description": "초보자도 이해하기 쉬운 설명"
    }}
  ],
  "checkpoints": [
    "개인투자자가 확인해야 할 체크포인트",
    "개인투자자가 확인해야 할 체크포인트",
    "개인투자자가 확인해야 할 체크포인트"
  ],
  "deep_report": {
    "one_line": "오늘 움직임을 투자 초보자도 이해할 수 있게 한 문장으로 결론",
    "recent_background": "최근 왜 관심을 받았는지 또는 직전 흐름이 어땠는지. 상승이면 상승 배경, 하락이면 직전 상승/하락 배경을 설명",
    "direct_trigger": "오늘 상승 또는 하락을 만든 직접 트리거. 제공된 뉴스/공시에 근거가 부족하면 확인 필요라고 표시",
    "industry_policy": "산업, 정책, 글로벌 매크로, 경쟁 구도 변화. 예: AI 전력수요, 원전 부각, 풍력 정책 불확실성, HBM 수요 등",
    "earnings_orders": "실적, 수주, 컨센서스, 목표가, 증권사 전망 관련 내용. 근거가 부족하면 확인 필요라고 표시",
    "price_volume_reaction": "현재가, 등락률, 거래량, 거래대금, 고가/저가로 본 시장 반응 강도",
    "structural_judgement": "단기 뉴스성 움직임인지, 구조적 추세 변화인지 균형 있게 판단",
    "evidence_lines": [
      "근거 뉴스/공시/가격 데이터 1줄 요약",
      "근거 뉴스/공시/가격 데이터 1줄 요약",
      "근거 뉴스/공시/가격 데이터 1줄 요약"
    ],
    "limitations": "현재 데이터로 확정하기 어려운 부분. 예: 정확한 2025/2026 컨센서스 수치는 별도 데이터 확인 필요"
  }
}}
"""

    increment_api_usage("openai")

    response = client.responses.create(
        model="gpt-4.1-mini",
        input=prompt,
    )

    raw_text = response.output_text.strip()

    try:
        return json.loads(raw_text)
    except Exception:
        cleaned = raw_text.replace("```json", "").replace("```", "").strip()

        try:
            return json.loads(cleaned)
        except Exception:
            return {
                "summary": raw_text,
                "risk_level": "중간",
                "market_or_company": "AI 응답을 구조화하지 못했습니다.",
                "disclosure_risk": "확인 필요",
                "negative_keywords": [],
                "reasons": [],
                "checkpoints": [],
            }





def make_ai_cache_key(stock_name, price_data, news_data, dart_data, exchange_data):
    """
    같은 종목이라도 뉴스/공시/환율/가격 데이터가 바뀌면 다른 AI 분석으로 취급한다.
    """
    key_payload = {
        "analysis_version": "fixed_html_easy_report_v6",
        "stock_name": stock_name,
        "price_data": price_data,
        "news_titles": [item.get("title", "") for item in news_data[:5]],
        "dart_titles": [item.get("title", "") for item in dart_data[:5]],
        "exchange_data": exchange_data,
    }

    return json.dumps(key_payload, ensure_ascii=False, sort_keys=True)


def analyze_with_ai(stock_name, price_data, news_data, dart_data, exchange_data):
    cache_key_value = make_ai_cache_key(
        stock_name,
        price_data,
        news_data,
        dart_data,
        exchange_data
    )

    cached, status, age = get_file_cache("ai", cache_key_value, AI_CACHE_TTL)

    if cached is not None:
        set_cache_status("AI 분석", "캐시", age)
        return cached

    result = analyze_with_ai_live(
        stock_name,
        price_data,
        news_data,
        dart_data,
        exchange_data
    )

    set_file_cache("ai", cache_key_value, result)
    set_cache_status("AI 분석", "실시간 호출", 0)
    return result


# =============================
# 앱형 분석 UI 보조 함수
# =============================
def extract_percent_number(value):
    if value is None:
        return 0.0

    text = str(value).replace("%", "").replace(",", "").strip()

    try:
        return float(text)
    except Exception:
        return 0.0


def get_price_move_type(price_data):
    """
    현재 등락 방향을 상승/하락/보합으로 통일한다.
    점수판과 AI 문구가 실제 등락률과 반대로 나오지 않도록 하는 핵심 함수.
    """
    direction = str(price_data.get("방향", "")).strip()
    rate = extract_percent_number(price_data.get("등락률", "0"))

    if direction == "상승" or rate > 0:
        return "상승"

    if direction == "하락" or rate < 0:
        return "하락"

    return "보합"


def get_move_word(price_data):
    move_type = get_price_move_type(price_data)

    if move_type == "상승":
        return "상승"

    if move_type == "하락":
        return "하락"

    return "변동"


def extract_volume_number(value):
    try:
        text = str(value or "0").replace(",", "").replace("주", "").strip()
        return float(text)
    except Exception:
        return 0.0


def extract_trading_value_number(value):
    """
    9.4조원, 9400억원, 123,456원 같은 표시값을 대략 숫자로 변환한다.
    점수 산정용 보조 함수라 정밀 회계용으로 쓰지 않는다.
    """
    try:
        text = str(value or "0").replace(",", "").replace(" ", "").strip()

        if "조" in text:
            number = float(text.split("조")[0])
            return number * 1_0000_0000_0000

        if "억" in text:
            number = float(text.split("억")[0])
            return number * 1_0000_0000

        return float(text.replace("원", ""))
    except Exception:
        return 0.0


def extract_won_number(value):
    if value is None:
        return 0.0

    text = str(value)
    text = text.replace("원", "").replace(",", "").replace("+", "").strip()

    try:
        return float(text)
    except Exception:
        return 0.0


def has_keywords(text, keywords):
    if not text:
        return False

    text = str(text)

    return any(keyword in text for keyword in keywords)


def compute_cause_scores(price_data, news_data, dart_data, exchange_data, ai_result):
    """
    등락 원인 점수판.
    기존에는 상승 종목에도 '하락 원인' 점수가 표시되는 문제가 있었다.
    이제 실제 등락 방향에 따라 상승/하락/변동 원인으로 분기한다.
    """
    move_type = get_price_move_type(price_data)
    change_rate_signed = extract_percent_number(price_data.get("등락률", "0"))
    change_rate = abs(change_rate_signed)
    exchange_change = abs(extract_won_number(exchange_data.get("전일대비", "0")))
    volume_value = extract_volume_number(price_data.get("거래량", "0"))
    trading_value = extract_trading_value_number(price_data.get("거래대금", "0"))

    news_text = " ".join([
        f"{item.get('title', '')} {item.get('description', '')}"
        for item in news_data
    ])

    dart_text = " ".join([
        f"{item.get('title', '')} {item.get('description', '')}"
        for item in dart_data
    ])

    bad_news_keywords = [
        "급락", "하락", "약세", "폭락", "우려", "부진", "손실", "적자",
        "쇼크", "리스크", "매도", "불확실", "악재", "둔화", "감소", "소송"
    ]

    good_news_keywords = [
        "급등", "상승", "강세", "호재", "기대", "수혜", "반등", "랠리",
        "실적", "호실적", "수주", "증가", "개선", "AI", "반도체", "HBM",
        "엔비디아", "목표가", "상향", "매수", "수출", "투자"
    ]

    bad_dart_keywords = [
        "주의", "유상증자", "전환사채", "감자", "상장폐지", "거래정지",
        "최대주주변경", "횡령", "배임", "소송", "감사의견", "의견거절"
    ]

    good_dart_keywords = [
        "단일판매", "공급계약", "수주", "영업실적", "매출액", "영업이익",
        "자기주식취득", "배당", "무상증자", "합병", "투자"
    ]

    volume_bonus = 0
    if volume_value >= 20_000_000 or trading_value >= 1_0000_0000_0000:
        volume_bonus = 25
    elif volume_value >= 5_000_000 or trading_value >= 3000_0000_0000:
        volume_bonus = 15
    elif volume_value > 0:
        volume_bonus = 8

    if move_type == "상승":
        score_market = min(95, int(30 + change_rate * 5 + (15 if has_keywords(news_text, ["반도체", "AI", "HBM", "코스피", "대형주", "섹터", "업종"]) else 0)))
        score_news = min(95, int(25 + change_rate * 4 + (25 if has_keywords(news_text, good_news_keywords) else 0)))
        score_volume = min(95, int(25 + change_rate * 3 + volume_bonus))
        score_disclosure = min(95, int(12 + (45 if has_keywords(dart_text, good_dart_keywords) else 0)))
        score_exchange = min(95, int(15 + exchange_change * 3 + (10 if exchange_data.get("방향") == "하락" else 0)))

        return [
            {
                "name": "시장/섹터 호재",
                "score": score_market,
                "desc": "지수 강세, 업종 회복, 대형주 동반 상승 가능성",
                "mode": "상승",
            },
            {
                "name": "뉴스 호재",
                "score": score_news,
                "desc": "최근 뉴스의 긍정 키워드와 기대감 반영",
                "mode": "상승",
            },
            {
                "name": "거래량 동반 상승",
                "score": score_volume,
                "desc": "거래량·거래대금이 함께 커졌는지 확인",
                "mode": "상승",
            },
            {
                "name": "공시/실적 모멘텀",
                "score": score_disclosure,
                "desc": "수주, 실적, 배당, 자사주 등 긍정 공시 가능성",
                "mode": "상승",
            },
            {
                "name": "환율/수급 환경",
                "score": score_exchange,
                "desc": "환율 안정 또는 외국인 수급에 우호적인 환경 여부",
                "mode": "상승",
            },
        ]

    if move_type == "하락":
        score_market = min(95, int(35 + change_rate * 7))
        score_news = min(95, int(25 + change_rate * 4 + (25 if has_keywords(news_text, bad_news_keywords) else 0)))
        score_exchange = min(95, int(20 + exchange_change * 5 + (25 if exchange_data.get("방향") == "상승" else 0)))
        score_disclosure = min(95, int(10 + (55 if has_keywords(dart_text, bad_dart_keywords) else 0)))
        score_company = min(95, int(20 + (30 if score_disclosure >= 50 else 0) + (15 if has_keywords(news_text, ["실적", "적자", "손실", "부진", "소송"]) else 0)))

        return [
            {
                "name": "시장/섹터 영향",
                "score": score_market,
                "desc": "지수 약세, 업종 조정, 대형주 동반 하락 가능성",
                "mode": "하락",
            },
            {
                "name": "뉴스 악재",
                "score": score_news,
                "desc": "최근 뉴스 제목/본문의 부정 키워드 반영",
                "mode": "하락",
            },
            {
                "name": "환율 부담",
                "score": score_exchange,
                "desc": "원/달러 환율 상승은 외국인 수급 부담 요인",
                "mode": "하락",
            },
            {
                "name": "공시 리스크",
                "score": score_disclosure,
                "desc": "DART 공시 제목의 위험 키워드 반영",
                "mode": "하락",
            },
            {
                "name": "개별 악재",
                "score": score_company,
                "desc": "기업 고유 이슈 가능성 추정",
                "mode": "하락",
            },
        ]

    # 보합 또는 미미한 등락
    score_news = min(70, int(20 + (20 if has_keywords(news_text, good_news_keywords + bad_news_keywords) else 0)))
    score_disclosure = min(70, int(10 + (30 if has_keywords(dart_text, good_dart_keywords + bad_dart_keywords) else 0)))
    score_volume = min(70, int(15 + volume_bonus))

    return [
        {
            "name": "뉴스 영향",
            "score": score_news,
            "desc": "뉴스가 가격 변동성에 영향을 줄 가능성",
            "mode": "변동",
        },
        {
            "name": "거래량 변화",
            "score": score_volume,
            "desc": "거래량·거래대금 변화로 본 관심도",
            "mode": "변동",
        },
        {
            "name": "공시 영향",
            "score": score_disclosure,
            "desc": "공시가 가격 변동에 영향을 줄 가능성",
            "mode": "변동",
        },
        {
            "name": "시장 환경",
            "score": 25,
            "desc": "시장 전체 분위기에 따른 변동 가능성",
            "mode": "변동",
        },
        {
            "name": "환율 영향",
            "score": min(70, int(15 + exchange_change * 3)),
            "desc": "환율 변화가 수급 심리에 주는 영향",
            "mode": "변동",
        },
    ]


def render_score_row(item):
    score = max(0, min(100, int(item.get("score", 0))))
    name = safe_text(item.get("name", ""))
    desc = safe_text(item.get("desc", ""))
    mode = item.get("mode", "하락")

    if mode == "상승":
        if score >= 80:
            fill_class = "score-positive-high-v2"
            badge_class = "score-badge-positive-high-v2"
            level = "기여 높음"
        elif score >= 60:
            fill_class = "score-positive-mid-v2"
            badge_class = "score-badge-positive-mid-v2"
            level = "기여 주의"
        else:
            fill_class = "score-positive-low-v2"
            badge_class = "score-badge-positive-low-v2"
            level = "기여 낮음"
    else:
        if score >= 80:
            fill_class = "score-high-v2"
            badge_class = "score-badge-high-v2"
            level = "높음"
        elif score >= 60:
            fill_class = "score-mid-v2"
            badge_class = "score-badge-mid-v2"
            level = "주의"
        else:
            fill_class = "score-low-v2"
            badge_class = "score-badge-low-v2"
            level = "낮음"

    st.markdown(
        f"""
        <div class="score-row-v2">
            <div class="score-name-v2">{name}</div>
            <div class="score-bar-bg-v2">
                <div class="score-bar-fill-v2 {fill_class}" style="width:{score}%;"></div>
            </div>
            <div class="score-badge-v2 {badge_class}">
                <span>{score}점</span>
                <span class="score-level-text">· {safe_text(level)}</span>
            </div>
        </div>
        <div class="score-desc-v2">{desc}</div>
        """,
        unsafe_allow_html=True
    )



def render_score_board(score_items):
    sorted_items = sorted(score_items, key=lambda x: x.get("score", 0), reverse=True)
    top_item = sorted_items[0] if sorted_items else {"name": "확인 필요", "score": 0, "mode": "변동"}
    top_name = safe_text(top_item.get("name", "확인 필요"))
    top_score = int(top_item.get("score", 0))
    mode = top_item.get("mode", "변동")

    if mode == "상승":
        if top_score >= 80:
            summary = f"오늘 상승에서 가장 강하게 잡힌 요인은 {top_name}입니다. {top_score}점으로 상승 기여도가 높게 나타났습니다."
        elif top_score >= 60:
            summary = f"오늘 상승에서 눈에 띄는 요인은 {top_name}입니다. {top_score}점으로 확인할 만한 요인입니다."
        else:
            summary = "특정 상승 요인이 압도적으로 높지는 않습니다. 여러 긍정 요인이 섞인 움직임으로 보는 편이 안전합니다."

        guide = (
            '<b>점수는 “그 요인이 오늘 상승에 영향을 줬을 가능성”입니다.</b><br>'
            '80점 이상은 상승 기여도가 높게 잡힌 요인입니다. 위험 신호가 아니라 상승 배경을 해석하기 위한 점수입니다.'
        )
    elif mode == "하락":
        if top_score >= 80:
            summary = f"오늘 하락에서 가장 강하게 잡힌 요인은 {top_name}입니다. {top_score}점으로 높은 단계라 우선 확인해야 합니다."
        elif top_score >= 60:
            summary = f"오늘 하락에서 가장 눈에 띄는 요인은 {top_name}입니다. {top_score}점으로 주의 단계입니다."
        else:
            summary = "특정 원인이 압도적으로 높지는 않습니다. 여러 요인이 섞인 하락으로 보는 편이 안전합니다."

        guide = (
            '<b>점수는 “그 요인이 오늘 하락에 영향을 줬을 가능성”입니다.</b><br>'
            '80점 이상은 빨간색으로 표시되며, 먼저 확인해야 할 핵심 위험 요인입니다.'
        )
    else:
        if top_score >= 60:
            summary = f"오늘 변동에서 가장 눈에 띄는 요인은 {top_name}입니다. {top_score}점으로 확인할 만합니다."
        else:
            summary = "등락폭이 크지 않아 특정 원인이 압도적으로 높지는 않습니다. 뉴스·공시·거래량을 함께 확인하세요."

        guide = (
            '<b>점수는 “그 요인이 오늘 변동에 영향을 줬을 가능성”입니다.</b><br>'
            '가격 방향이 뚜렷하지 않을 때는 뉴스·거래량·공시를 함께 보는 것이 좋습니다.'
        )

    board_extra_class = "score-board-positive" if mode == "상승" else "score-board-neutral" if mode == "변동" else ""

    intro_html = (
        f'<div class="score-board-v2 {board_extra_class}">'
        '<div class="score-guide">'
        f'{guide}'
        '</div>'
        '<div class="risk-summary-card">'
        '<div class="risk-summary-label">한눈에 보는 결론</div>'
        f'<div class="risk-summary-title">{safe_text(summary)}</div>'
        '</div>'
    )

    st.markdown(intro_html, unsafe_allow_html=True)

    for item in score_items:
        render_score_row(item)

    legend_html = (
        '<div class="score-legend">'
        '<span class="legend-chip"><span class="legend-dot dot-low"></span>0~59 낮음</span>'
        '<span class="legend-chip"><span class="legend-dot dot-mid"></span>60~79 주의</span>'
        '<span class="legend-chip"><span class="legend-dot dot-high"></span>80~100 높음</span>'
        '</div>'
        '</div>'
    )

    st.markdown(legend_html, unsafe_allow_html=True)



def extract_detected_keywords(news_data, dart_data, exchange_data):
    news_text = " ".join([
        f"{item.get('title', '')} {item.get('description', '')}"
        for item in news_data
    ])

    dart_text = " ".join([
        f"{item.get('title', '')} {item.get('description', '')}"
        for item in dart_data
    ])

    keyword_rules = [
        ("외국인 매도", "news"),
        ("기관 매도", "news"),
        ("급락", "news"),
        ("하락", "news"),
        ("약세", "news"),
        ("반도체", "news"),
        ("코스피", "news"),
        ("실적", "news"),
        ("적자", "news"),
        ("손실", "news"),
        ("우려", "news"),
        ("유상증자", "dart"),
        ("전환사채", "dart"),
        ("신주인수권부사채", "dart"),
        ("감자", "dart"),
        ("최대주주변경", "dart"),
        ("거래정지", "dart"),
        ("상장폐지", "dart"),
        ("횡령", "dart"),
        ("배임", "dart"),
        ("소송", "dart"),
    ]

    detected = []

    for keyword, source in keyword_rules:
        if source == "news" and keyword in news_text:
            detected.append(keyword)
        elif source == "dart" and keyword in dart_text:
            detected.append(keyword)

    if exchange_data.get("방향") == "상승":
        detected.append("환율 상승")

    return list(dict.fromkeys(detected))


def interpret_dart_risk(dart_data):
    dart_text = " ".join([
        f"{item.get('title', '')} {item.get('description', '')}"
        for item in dart_data
    ])

    high_risk = ["유상증자", "전환사채", "신주인수권부사채", "감자", "거래정지", "상장폐지", "횡령", "배임", "의견거절", "감사의견"]
    mid_risk = ["최대주주변경", "소송", "주요사항보고서", "타법인", "담보제공"]

    if has_keywords(dart_text, high_risk):
        return "높음", "최근 공시에 자금조달, 거래정지, 감사의견, 횡령/배임 등 주가에 직접 부담이 될 수 있는 키워드가 감지됩니다."

    if has_keywords(dart_text, mid_risk):
        return "중간", "최근 공시에 지배구조, 소송, 주요사항 관련 키워드가 있어 세부 내용을 확인할 필요가 있습니다."

    return "낮음", "최근 조회된 공시는 현재 화면 기준으로 직접적인 악재성 공시로 보기 어렵습니다."


def build_deep_summary(price_data, news_data, dart_data, exchange_data, score_items):
    market_score = next((x["score"] for x in score_items if x["name"] == "시장/섹터 영향"), 0)
    disclosure_score = next((x["score"] for x in score_items if x["name"] == "공시 리스크"), 0)
    exchange_score = next((x["score"] for x in score_items if x["name"] == "환율 부담"), 0)
    company_score = next((x["score"] for x in score_items if x["name"] == "개별 악재"), 0)

    if disclosure_score >= 60:
        core = "공시 리스크를 우선 확인해야 하는 하락입니다."
    elif market_score >= 65 and exchange_score >= 60:
        core = "시장/섹터 약세와 환율 부담이 동시에 작용한 하락으로 보입니다."
    elif company_score >= 55:
        core = "개별 기업 이슈 가능성이 있어 뉴스와 공시를 더 깊게 확인해야 합니다."
    elif market_score >= 60:
        core = "개별 악재보다는 시장 또는 업종 동반 하락 영향이 더 커 보입니다."
    else:
        core = "현재 데이터만으로는 단일 원인보다 여러 요인이 섞인 하락으로 보는 편이 안전합니다."

    return core




def build_chart_interpretation(chart_rows, price_data):
    if not chart_rows or len(chart_rows) < 2:
        return "차트 데이터가 부족해 추세 해석은 제한됩니다."

    first_close = float(chart_rows[0].get("종가", 0))
    last_close = float(chart_rows[-1].get("종가", 0))
    high_close = max(float(row.get("종가", 0)) for row in chart_rows)
    low_close = min(float(row.get("종가", 0)) for row in chart_rows)

    if first_close <= 0:
        period_rate = 0
    else:
        period_rate = (last_close - first_close) / first_close * 100

    volumes = [float(row.get("거래량", 0)) for row in chart_rows if float(row.get("거래량", 0)) > 0]
    avg_volume = sum(volumes) / len(volumes) if volumes else 0
    last_volume = float(chart_rows[-1].get("거래량", 0))

    trend_text = "상승 추세" if period_rate > 3 else "하락 추세" if period_rate < -3 else "횡보 구간"

    volume_text = "거래량 데이터는 제한적입니다."
    if avg_volume > 0:
        volume_ratio = last_volume / avg_volume
        if volume_ratio >= 1.8:
            volume_text = "최근 거래량이 평소보다 크게 늘어 투자심리 변화가 강하게 반영된 구간입니다."
        elif volume_ratio >= 1.2:
            volume_text = "최근 거래량이 평균보다 다소 늘어 가격 변동에 관심이 붙은 상태입니다."
        else:
            volume_text = "최근 거래량은 평균 수준으로, 가격 변동 강도는 추가 확인이 필요합니다."

    return (
        f"선택 기간 기준 주가는 {period_rate:+.2f}% 변동했고, 전체 흐름은 {trend_text}으로 볼 수 있습니다. "
        f"종가 기준 최고 {high_close:,.0f}원, 최저 {low_close:,.0f}원 범위에서 움직였습니다. "
        f"{volume_text}"
    )


def render_free_price_chart(price_data):
    stock_code = price_data.get("종목코드", "")
    stock_name = price_data.get("종목명", "해당 종목")

    if not stock_code:
        return

    st.markdown('<div class="section-title">📈 무료 주가 차트</div>', unsafe_allow_html=True)

    st.markdown(
        '<div class="news-filter-note">현재 차트는 한국투자증권 일봉 데이터를 기준으로 보여드립니다. 1일 차트는 분봉/실시간 데이터 연동 전까지 제외했습니다.</div>',
        unsafe_allow_html=True
    )

    period_label = st.radio(
        "차트 기간",
        ["5일", "1개월", "6개월"],
        index=1,
        horizontal=True,
        key=f"chart_period_{stock_code}",
        label_visibility="collapsed",
    )

    # 현재 KIS REST 일봉 데이터 기준.
    # 1일은 당일 분봉이 아니라 최근 영업일 종가/거래량 1개 표시로 처리한다.
    period_days = {
        "5일": 5,
        "1개월": 30,
        "6개월": 180,
    }.get(period_label, 30)

    chart_rows = []

    if is_kis_configured():
        try:
            chart_rows = get_kis_daily_chart_data(stock_code, days=period_days)
        except Exception as e:
            try:
                log_app_error("한국투자증권 차트 조회 실패", e)
            except Exception:
                pass
            chart_rows = []

    if not chart_rows:
        st.info("차트 데이터를 불러오지 못했습니다. 한국투자증권 API 키 또는 기간별 시세 권한을 확인해주세요.")
        return

    df = pd.DataFrame(chart_rows)
    df = df.sort_values("date").copy()
    df["date"] = pd.to_datetime(df["date"])
    df["날짜"] = df["date"].dt.strftime("%m/%d")
    df["종가"] = pd.to_numeric(df["종가"], errors="coerce")
    df["거래량"] = pd.to_numeric(df["거래량"], errors="coerce")
    df = df.dropna(subset=["종가"])

    if df.empty:
        st.info("차트 표시 가능한 가격 데이터가 부족합니다.")
        return

    chart_summary = build_chart_interpretation(chart_rows, price_data)

    first_close = float(df["종가"].iloc[0])
    last_close = float(df["종가"].iloc[-1])
    period_rate = ((last_close - first_close) / first_close * 100) if first_close else 0
    line_color = "#ef4444" if period_rate >= 0 else "#2563eb"

    last_volume = float(df["거래량"].iloc[-1]) if "거래량" in df and pd.notna(df["거래량"].iloc[-1]) else 0

    st.markdown(
        f"""<div class="chart-info-card">
<div class="chart-info-title">{safe_text(stock_name)} · {safe_text(period_label)} 주가 흐름</div>
<div class="chart-info-desc">{safe_text(chart_summary)}</div>
<div class="chart-mini-grid">
<div class="chart-mini-box">
<div class="chart-mini-label">기간 등락률</div>
<div class="chart-mini-value">{period_rate:+.2f}%</div>
</div>
<div class="chart-mini-box">
<div class="chart-mini-label">최근 종가</div>
<div class="chart-mini-value">{last_close:,.0f}원</div>
</div>
<div class="chart-mini-box">
<div class="chart-mini-label">최근 거래량</div>
<div class="chart-mini-value">{last_volume:,.0f}주</div>
</div>
<div class="chart-mini-box">
<div class="chart-mini-label">데이터</div>
<div class="chart-mini-value">KIS API</div>
</div>
</div>
</div>""",
        unsafe_allow_html=True
    )

    period_help = "상단은 주가 흐름, 하단은 거래량입니다. 가격이 오르거나 빠질 때 거래량이 함께 커졌는지를 보면 움직임의 강도를 더 쉽게 볼 수 있습니다. 1일 차트는 분봉/실시간 데이터 연동 전까지 제외했습니다."

    st.markdown(
        f"""<div class="beginner-chart-guide">
<div class="beginner-chart-title">{safe_text(stock_name)} 가격·거래량 차트</div>
<div class="beginner-chart-desc">{safe_text(period_help)}</div>
<div class="beginner-chart-legend">
<span class="legend-pill price-up">빨간선: 선택 기간 상승</span>
<span class="legend-pill price-down">파란선: 선택 기간 하락</span>
<span class="legend-pill volume">회색 막대: 거래량</span>
<span class="legend-pill">왼쪽 숫자: 원 단위 가격</span>
</div>
</div>
<div class="chart-label-row">
<div class="chart-label-box">
<div class="chart-label-title">상단 그래프 · 주가</div>
<div class="chart-label-desc">종가 기준 가격 흐름입니다. 축 숫자는 30만, 40만처럼 초보자도 읽기 쉽게 표시했습니다.</div>
</div>
<div class="chart-label-box">
<div class="chart-label-title">하단 그래프 · 거래량</div>
<div class="chart-label-desc">해당 날짜에 거래된 주식 수입니다. 막대가 클수록 그날 시장 관심과 매매가 많았다는 뜻입니다.</div>
</div>
</div>""",
        unsafe_allow_html=True
    )

    # 보기 좋은 축 범위를 만들기 위해 최저/최고에 여유를 둔다.
    min_price = float(df["종가"].min())
    max_price = float(df["종가"].max())
    price_gap = max(max_price - min_price, max_price * 0.03)
    y_min = max(0, min_price - price_gap * 0.25)
    y_max = max_price + price_gap * 0.25

    # 데이터가 1개뿐이면 선이 안 보이므로 점 차트에 가까운 표시로 보완
    if len(df) == 1:
        df_for_chart = pd.concat([df, df.copy()], ignore_index=True)
        df_for_chart.loc[1, "date"] = df_for_chart.loc[0, "date"] + pd.Timedelta(hours=8)
        df_for_chart.loc[1, "날짜"] = df_for_chart.loc[0, "날짜"]
    else:
        df_for_chart = df

    # 기간별 x축 라벨 밀도 조정
    x_tick_count = {
        "5일": 5,
        "1개월": 6,
        "6개월": 7,
    }.get(period_label, 6)

    price_axis = alt.Axis(
        title="주가(원)",
        titleColor="#334155",
        titleFontSize=12,
        titleFontWeight="bold",
        labelExpr="datum.value >= 10000 ? format(datum.value/10000, ',.0f') + '만' : format(datum.value, ',')",
        labelColor="#64748b",
        labelFontSize=11,
        grid=True,
        gridColor="#eef2f7",
        domain=False,
        tickColor="#e2e8f0",
    )

    volume_axis = alt.Axis(
        title="거래량(주)",
        titleColor="#334155",
        titleFontSize=12,
        titleFontWeight="bold",
        labelExpr="datum.value >= 100000000 ? format(datum.value/100000000, ',.1f') + '억' : datum.value >= 10000 ? format(datum.value/10000, ',.0f') + '만' : format(datum.value, ',')",
        labelColor="#64748b",
        labelFontSize=11,
        grid=True,
        gridColor="#f1f5f9",
        domain=False,
        tickColor="#e2e8f0",
    )

    x_axis = alt.Axis(
        format="%m/%d",
        labelAngle=0,
        labelOverlap="parity",
        tickCount=x_tick_count,
        labelColor="#64748b",
        labelFontSize=11,
        tickColor="#e2e8f0",
        domainColor="#e2e8f0",
        grid=False,
    )

    base = alt.Chart(df_for_chart).encode(
        x=alt.X("date:T", title=None, axis=x_axis)
    )

    # area를 제거한다. 기존 area가 y축 아래로 과하게 내려가 보여 차트가 싸 보이는 문제를 해결.
    line = base.mark_line(
        interpolate="monotone",
        strokeWidth=3,
        color=line_color,
    ).encode(
        y=alt.Y(
            "종가:Q",
            title="주가(원)",
            scale=alt.Scale(domain=[y_min, y_max], nice=False),
            axis=price_axis,
        ),
        tooltip=[
            alt.Tooltip("날짜:N", title="날짜"),
            alt.Tooltip("종가:Q", title="종가", format=","),
            alt.Tooltip("거래량:Q", title="거래량", format=","),
        ],
    )

    point = base.mark_point(
        filled=True,
        size=46,
        color=line_color,
        opacity=0.9,
    ).encode(
        y=alt.Y("종가:Q", scale=alt.Scale(domain=[y_min, y_max], nice=False)),
        tooltip=[
            alt.Tooltip("날짜:N", title="날짜"),
            alt.Tooltip("종가:Q", title="종가", format=","),
            alt.Tooltip("거래량:Q", title="거래량", format=","),
        ],
    )

    rule = base.mark_rule(
        color="#e2e8f0",
        strokeDash=[4, 4],
        opacity=0.7
    ).encode(
        y=alt.datum(first_close)
    )

    price_chart = (rule + line + point).properties(
        height=290
    )

    volume_chart = alt.Chart(df_for_chart).mark_bar(
        opacity=0.70,
        color="#94a3b8",
        cornerRadiusTopLeft=3,
        cornerRadiusTopRight=3,
    ).encode(
        x=alt.X("date:T", title=None, axis=x_axis),
        y=alt.Y(
            "거래량:Q",
            title="거래량(주)",
            axis=volume_axis,
        ),
        tooltip=[
            alt.Tooltip("날짜:N", title="날짜"),
            alt.Tooltip("거래량:Q", title="거래량", format=","),
        ],
    ).properties(
        height=120
    )

    final_chart = alt.vconcat(price_chart, volume_chart).resolve_scale(
        x="shared",
        y="independent"
    ).configure_view(
        strokeWidth=0
    ).configure_axis(
        labelFontSize=11,
        titleFontSize=12,
    ).configure_concat(
        spacing=12
    ).configure(
        autosize={"type": "fit", "contains": "padding"}
    )

    st.altair_chart(final_chart, use_container_width=True)

    st.markdown(
        '<div class="chart-source-note">차트 데이터 출처: 한국투자증권 Open API · 투자 판단 보조용 정보입니다.</div>',
        unsafe_allow_html=True
    )


def simplify_sentence(text_value, max_chars=240):
    value = str(text_value or "").strip()
    if len(value) <= max_chars:
        return value
    return value[:max_chars].rstrip() + "..."


def get_deep_report_from_ai(ai_result, price_data, news_data, dart_data, exchange_data, score_items):
    report = ai_result.get("deep_report")

    if isinstance(report, dict) and report.get("one_line"):
        return report

    move_word = get_move_word(price_data)
    top_score = sorted(score_items, key=lambda x: x.get("score", 0), reverse=True)[0] if score_items else {}

    evidence_lines = []
    for item in news_data[:3]:
        if item.get("title"):
            evidence_lines.append(f"뉴스: {item.get('title')}")
    for item in dart_data[:2]:
        if item.get("title"):
            evidence_lines.append(f"공시: {item.get('title')}")
    evidence_lines.append(
        f"가격: 현재가 {price_data.get('현재가', '확인불가')}, 등락률 {price_data.get('등락률', '확인불가')}, 거래대금 {price_data.get('거래대금', '확인불가')}"
    )

    return {
        "one_line": f"{price_data.get('종목명', '해당 종목')}은 현재 {move_word} 중이며, 가장 크게 잡힌 요인은 {top_score.get('name', '확인 필요')}입니다.",
        "recent_background": "최근 뉴스와 공시를 기준으로 직전 배경을 확인해야 합니다. 종목명 단독 뉴스만으로 산업 흐름을 확정하기는 어렵습니다.",
        "direct_trigger": f"현재 데이터에서 가장 강하게 잡힌 직접 요인은 {top_score.get('name', '확인 필요')}입니다. 정확한 트리거는 최신 뉴스 원문 확인이 필요합니다.",
        "industry_policy": "산업·정책 변화는 종목별로 다릅니다. 반도체, 원전, 2차전지, 풍력 등 해당 업종의 글로벌 수요와 정책 변화를 함께 확인해야 합니다.",
        "earnings_orders": "실적·수주·컨센서스 변화는 뉴스와 DART 공시에서 반복적으로 확인될 때 신뢰도가 높아집니다. 현재 데이터만으로 확정하기 어려운 부분은 확인 필요입니다.",
        "price_volume_reaction": f"현재가는 {price_data.get('현재가', '확인불가')}, 등락률은 {price_data.get('등락률', '확인불가')}, 거래량은 {price_data.get('거래량', '확인불가')}, 거래대금은 {price_data.get('거래대금', '확인불가')}입니다.",
        "structural_judgement": "단기 뉴스성 움직임인지 구조적 변화인지는 같은 이슈가 며칠 이상 반복되는지, 거래량이 동반되는지, 공시와 실적 전망이 함께 변하는지 확인해야 합니다.",
        "evidence_lines": evidence_lines[:6],
        "limitations": "정확한 컨센서스 수치, 증권사 리포트 원문, 외국인·기관 실시간 수급은 별도 데이터 연동이 필요합니다.",
    }


def html_card_section(number, title, label, sentence, explain="", evidence=None):
    evidence_html = ""
    if evidence:
        lines = "".join(
            f'<div style="color:#64748b;font-size:12px;font-weight:700;line-height:1.55;margin-bottom:4px;">• {safe_text(simplify_sentence(line, 115))}</div>'
            for line in evidence[:3]
        )
        evidence_html = (
            '<div style="margin-top:12px;background:#f8fafc;border:1px dashed #cbd5e1;border-radius:16px;padding:12px 13px;">'
            '<div style="color:#475569;font-size:12px;font-weight:900;margin-bottom:6px;">앱이 참고한 근거</div>'
            f'{lines}'
            '</div>'
        )

    return (
        '<div style="background:#ffffff;border:1px solid #e5e7eb;border-radius:22px;padding:18px 18px;margin:12px 0;box-shadow:0 10px 28px rgba(15,23,42,0.055);">'
        '<div style="display:flex;align-items:center;gap:10px;margin-bottom:12px;">'
        f'<div style="min-width:34px;height:34px;border-radius:999px;display:flex;align-items:center;justify-content:center;background:#eff6ff;color:#1d4ed8;font-size:14px;font-weight:1000;">{safe_text(number)}</div>'
        f'<div style="color:#0f172a;font-size:18px;font-weight:1000;letter-spacing:-0.3px;">{safe_text(title)}</div>'
        '</div>'
        f'<div style="display:inline-block;border-radius:999px;padding:6px 10px;background:#ecfeff;color:#155e75;font-size:12px;font-weight:1000;margin-bottom:10px;border:1px solid #a5f3fc;">{safe_text(label)}</div>'
        f'<div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:16px;padding:13px 14px;color:#111827;font-size:15px;font-weight:850;line-height:1.75;margin-bottom:10px;">{safe_text(simplify_sentence(sentence, 260))}</div>'
        f'<div style="color:#475569;font-size:13px;font-weight:720;line-height:1.75;">{safe_text(simplify_sentence(explain, 260))}</div>'
        f'{evidence_html}'
        '</div>'
    )


def metric_box(label, value):
    return (
        '<div style="background:#ffffff;border:1px solid #e5e7eb;border-radius:16px;padding:12px 13px;box-shadow:0 8px 20px rgba(15,23,42,0.035);">'
        f'<div style="color:#64748b;font-size:12px;font-weight:900;margin-bottom:5px;">{safe_text(label)}</div>'
        f'<div style="color:#0f172a;font-size:15px;font-weight:1000;">{safe_text(value)}</div>'
        '</div>'
    )


def render_deep_report(price_data, news_data, dart_data, exchange_data, ai_result, score_items):
    move_word = get_move_word(price_data)
    report = get_deep_report_from_ai(ai_result, price_data, news_data, dart_data, exchange_data, score_items)
    detected_keywords = extract_detected_keywords(news_data, dart_data, exchange_data)
    dart_risk_level, dart_risk_text = interpret_dart_risk(dart_data)

    st.markdown('<div class="section-title">🔓 심층 분석 리포트</div>', unsafe_allow_html=True)

    hero_html = (
        '<div style="background:linear-gradient(135deg,#111827,#1e3a8a);color:#ffffff;border-radius:26px;padding:24px 24px;margin:14px 0 18px 0;box-shadow:0 18px 44px rgba(15,23,42,0.18);">'
        f'<div style="display:inline-flex;background:rgba(255,255,255,0.13);border:1px solid rgba(255,255,255,0.16);border-radius:999px;padding:7px 11px;color:#dbeafe;font-size:12px;font-weight:1000;margin-bottom:12px;">PRO 리포트 · {safe_text(move_word)} 원인 쉽게 풀기</div>'
        f'<div style="font-size:21px;font-weight:1000;line-height:1.55;letter-spacing:-0.4px;margin-bottom:10px;">{safe_text(simplify_sentence(report.get("one_line", ""), 220))}</div>'
        '<div style="color:#cbd5e1;font-size:14px;font-weight:760;line-height:1.65;">뉴스·공시·가격·거래량을 묶어서 “왜 움직였는지”를 초보자 눈높이로 풀어쓴 리포트입니다.</div>'
        '</div>'
    )
    st.markdown(hero_html, unsafe_allow_html=True)

    metrics_html = (
        '<div style="display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px;margin:12px 0 16px 0;">'
        + metric_box("등락률", price_data.get("등락률", "확인불가"))
        + metric_box("거래량", price_data.get("거래량", "확인불가"))
        + metric_box("거래대금", price_data.get("거래대금", "확인불가"))
        + metric_box("환율", exchange_data.get("현재환율", "확인불가"))
        + '</div>'
    )
    st.markdown(metrics_html, unsafe_allow_html=True)

    evidence_lines = report.get("evidence_lines", [])

    sections = [
        ("1", "최근 왜 관심을 받았나", "배경", report.get("recent_background", "확인 필요"), "쉽게 말하면, 이 종목이 갑자기 움직인 게 아니라 최근 뉴스·업종 분위기·시장 관심이 먼저 깔려 있었는지 보는 단계입니다.", evidence_lines[:2]),
        ("2", f"오늘 {move_word}을 만든 직접 이유", "직접 트리거", report.get("direct_trigger", "확인 필요"), "쉽게 말하면, 오늘 주가를 실제로 밀어 올렸거나 끌어내린 방아쇠가 무엇인지 보는 단계입니다.", evidence_lines[2:4]),
        ("3", "업종과 정책 흐름", "큰 판 보기", report.get("industry_policy", "확인 필요"), "쉽게 말하면, 이 회사만의 문제가 아니라 반도체·원전·2차전지·풍력 같은 업종 전체 분위기가 좋은지 나쁜지 보는 단계입니다.", None),
        ("4", "실적·수주·전망", "돈을 벌 힘", report.get("earnings_orders", "확인 필요"), "쉽게 말하면, 회사가 앞으로 돈을 더 벌 가능성이 커졌는지, 아니면 기대가 낮아졌는지 확인하는 단계입니다.", None),
        ("5", "주가와 거래량 반응", "시장이 진짜 반응했나", report.get("price_volume_reaction", "확인 필요"), "쉽게 말하면, 말만 나온 뉴스인지 실제 매수·매도가 몰린 움직임인지 거래량과 거래대금으로 확인하는 단계입니다.", None),
        ("6", "하루짜리 이슈인가, 큰 흐름인가", "단기 vs 구조", report.get("structural_judgement", "확인 필요"), "쉽게 말하면, 오늘 하루만 반짝한 뉴스인지 아니면 앞으로도 주가에 영향을 줄 큰 변화인지 구분하는 단계입니다.", None),
    ]

    for sec in sections:
        st.markdown(html_card_section(*sec), unsafe_allow_html=True)

    if detected_keywords:
        chips = "".join([f'<span class="keyword-chip">{safe_text(keyword)}</span>' for keyword in detected_keywords[:12]])
    else:
        chips = '<span class="safe-chip">강한 키워드 미감지</span>'

    keyword_html = (
        '<div style="background:#ffffff;border:1px solid #e5e7eb;border-radius:22px;padding:18px 18px;margin:12px 0;box-shadow:0 10px 28px rgba(15,23,42,0.055);">'
        '<div style="display:flex;align-items:center;gap:10px;margin-bottom:12px;">'
        '<div style="min-width:34px;height:34px;border-radius:999px;display:flex;align-items:center;justify-content:center;background:#eff6ff;color:#1d4ed8;font-size:14px;font-weight:1000;">7</div>'
        '<div style="color:#0f172a;font-size:18px;font-weight:1000;">뉴스·공시에서 잡힌 키워드</div>'
        '</div>'
        '<div style="color:#475569;font-size:13px;font-weight:720;line-height:1.7;margin-bottom:12px;">아래 단어들은 뉴스와 공시에서 반복적으로 잡힌 표현입니다. 상승 종목에서는 호재 키워드인지, 하락 종목에서는 리스크 키워드인지 구분해서 봐야 합니다.</div>'
        f'<div>{chips}</div>'
        '</div>'
    )
    st.markdown(keyword_html, unsafe_allow_html=True)

    if dart_risk_level == "높음":
        dart_chip = '<span class="danger-chip">공시 위험 높음</span>'
    elif dart_risk_level == "중간":
        dart_chip = '<span class="neutral-chip2">공시 확인 필요</span>'
    else:
        dart_chip = '<span class="safe-chip">직접 악재 낮음</span>'

    dart_html = (
        '<div style="background:#ffffff;border:1px solid #e5e7eb;border-radius:22px;padding:18px 18px;margin:12px 0;box-shadow:0 10px 28px rgba(15,23,42,0.055);">'
        '<div style="display:flex;align-items:center;gap:10px;margin-bottom:12px;">'
        '<div style="min-width:34px;height:34px;border-radius:999px;display:flex;align-items:center;justify-content:center;background:#eff6ff;color:#1d4ed8;font-size:14px;font-weight:1000;">8</div>'
        '<div style="color:#0f172a;font-size:18px;font-weight:1000;">DART 공시 확인</div>'
        '</div>'
        f'<div style="margin-bottom:10px;">{dart_chip}</div>'
        f'<div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:16px;padding:13px 14px;color:#111827;font-size:15px;font-weight:850;line-height:1.75;margin-bottom:10px;">{safe_text(dart_risk_text)}</div>'
        '<div style="color:#475569;font-size:13px;font-weight:720;line-height:1.75;">쉽게 말하면, 회사가 공식적으로 낸 공시에 유상증자·CB·감자·최대주주 변경 같은 큰 변수가 있는지 확인하는 단계입니다.</div>'
        '</div>'
    )
    st.markdown(dart_html, unsafe_allow_html=True)

    limit_html = (
        '<div style="background:#fffbeb;border:1px solid #fde68a;color:#92400e;border-radius:18px;padding:14px 15px;font-size:13px;font-weight:780;line-height:1.65;margin:12px 0;">'
        '<b>지금 데이터의 한계</b><br>'
        f'{safe_text(simplify_sentence(report.get("limitations", "정확한 컨센서스 수치, 증권사 리포트 원문, 외국인·기관 실시간 수급은 별도 데이터 연동이 필요합니다."), 280))}'
        '</div>'
    )
    st.markdown(limit_html, unsafe_allow_html=True)

    checklist_html = (
        '<div style="background:#f0fdf4;border:1px solid #bbf7d0;border-radius:22px;padding:17px 17px;margin:12px 0;">'
        '<div style="color:#166534;font-size:17px;font-weight:1000;margin-bottom:10px;">마지막 체크리스트</div>'
        f'<div style="color:#14532d;font-size:14px;font-weight:790;line-height:1.85;">'
        f'✅ 이 {safe_text(move_word)}이 하루짜리 뉴스 반응인지 며칠간 이어지는 흐름인지 보기<br>'
        '✅ 거래량과 거래대금이 평소보다 커졌는지 보기<br>'
        '✅ 같은 업종 대장주와 경쟁사도 같은 방향으로 움직였는지 보기<br>'
        '✅ DART에 실적, 수주, 자금조달, 최대주주 관련 공시가 있는지 보기<br>'
        '✅ 증권사 전망이나 컨센서스가 실제로 바뀌었는지 추가 확인하기'
        '</div></div>'
    )
    st.markdown(checklist_html, unsafe_allow_html=True)



# =============================
# 관심종목 로컬 저장
# =============================
WATCHLIST_FILE = "watchlist.json"


def load_watchlist():
    try:
        path = Path(WATCHLIST_FILE)
        if not path.exists():
            return []

        data = json.loads(path.read_text(encoding="utf-8"))

        if isinstance(data, list):
            return data

        return []

    except Exception:
        return []


def save_watchlist(items):
    try:
        Path(WATCHLIST_FILE).write_text(
            json.dumps(items, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        return True
    except Exception:
        return False


def add_to_watchlist(stock_name, stock_code):
    items = load_watchlist()

    for item in items:
        if item.get("stock_code") == stock_code:
            return False, "이미 관심종목에 있습니다."

    items.insert(0, {
        "stock_name": stock_name,
        "stock_code": stock_code,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
    })

    # MVP에서는 최대 30개까지만 저장
    items = items[:30]

    if save_watchlist(items):
        return True, "관심종목에 추가했습니다."

    return False, "관심종목 저장에 실패했습니다."


def remove_from_watchlist(stock_code):
    items = load_watchlist()
    new_items = [item for item in items if item.get("stock_code") != stock_code]

    if save_watchlist(new_items):
        return True

    return False



# =============================
# 최근 조회 종목 로컬 저장
# =============================
RECENT_FILE = "recent_queries.json"


def load_recent_queries():
    try:
        path = Path(RECENT_FILE)
        if not path.exists():
            return []

        data = json.loads(path.read_text(encoding="utf-8"))

        if isinstance(data, list):
            return data

        return []

    except Exception:
        return []


def save_recent_queries(items):
    try:
        Path(RECENT_FILE).write_text(
            json.dumps(items, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        return True
    except Exception:
        return False


def add_recent_query(price_data):
    items = load_recent_queries()
    stock_code = price_data.get("종목코드")
    stock_name = price_data.get("종목명")

    # 같은 종목은 맨 위로 갱신
    items = [item for item in items if item.get("stock_code") != stock_code]

    items.insert(0, {
        "stock_name": stock_name,
        "stock_code": stock_code,
        "current_price": price_data.get("현재가", "확인불가"),
        "change_rate": price_data.get("등락률", "확인불가"),
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
    })

    # MVP에서는 최근 10개만 보관
    items = items[:10]

    save_recent_queries(items)






# =============================
# PRO 수요검증 로그 저장
# =============================
PRO_CLICK_FILE = "pro_clicks.json"
PRO_LEADS_FILE = "pro_leads.json"


def load_json_list_file(filename):
    try:
        path = Path(filename)
        if not path.exists():
            return []

        data = json.loads(path.read_text(encoding="utf-8"))

        if isinstance(data, list):
            return data

        return []

    except Exception:
        return []


def save_json_list_file(filename, items):
    try:
        Path(filename).write_text(
            json.dumps(items, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        return True
    except Exception:
        return False


def record_pro_click(stock_name="", source="result_card"):
    items = load_json_list_file(PRO_CLICK_FILE)

    items.insert(0, {
        "stock_name": stock_name,
        "source": source,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    })

    items = items[:1000]
    save_json_list_file(PRO_CLICK_FILE, items)


def save_pro_lead(email, stock_name="", source="pro_detail"):
    email = str(email).strip()

    if not email or "@" not in email or "." not in email:
        return False, "이메일 형식을 다시 확인해주세요."

    items = load_json_list_file(PRO_LEADS_FILE)

    # 같은 이메일은 최신 관심 종목으로 갱신
    items = [item for item in items if item.get("email") != email]

    items.insert(0, {
        "email": email,
        "stock_name": stock_name,
        "source": source,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    })

    items = items[:1000]

    if save_json_list_file(PRO_LEADS_FILE, items):
        return True, "신청 완료되었습니다. PRO 베타가 열리면 가장 먼저 알려드리겠습니다."

    return False, "신청 저장에 실패했습니다. 잠시 후 다시 시도해주세요."


def render_pro_value_card(stock_name=""):
    stock_label = safe_text(stock_name) if stock_name else "내 종목"

    # 기본 화면에서는 거부감 없도록 작게 보여주고,
    # 버튼을 눌렀을 때만 상세 기능/비교표/이메일 신청을 보여준다.
    st.markdown(
        f"""<div class="pro-compact-card">
<div class="pro-compact-top">
<span class="pro-compact-badge">왜빠짐 PRO · 출시 준비 중</span>
<span class="pro-compact-price">월 4,900원</span>
</div>
<div class="pro-compact-title">{stock_label}을 매일 AI가 감시해주는 기능을 준비 중입니다</div>
<div class="pro-compact-desc">
관심종목의 급락, 악성 뉴스, 위험 공시를 매일 확인하고 주린이 눈높이로 쉽게 정리합니다.
</div>
<div class="pro-compact-points">
<span class="pro-compact-point">AI 일일 감시</span>
<span class="pro-compact-point">위험 공시 해석</span>
<span class="pro-compact-point">악성 뉴스 감지</span>
<span class="pro-compact-point">급락 알림 예정</span>
</div>
</div>
<div class="pro-click-guide">아래 PRO 버튼을 누르면 제공 예정 기능을 자세히 볼 수 있습니다.</div>""",
        unsafe_allow_html=True
    )

def render_pro_detail_and_lead_form(stock_name=""):
    stock_label = safe_text(stock_name) if stock_name else "내 종목"

    st.markdown(
        f"""<div class="pro-hero-card">
<div class="pro-kicker">왜빠짐 PRO · 기능 상세</div>
<div class="pro-title">월 4,900원으로 {stock_label} AI 감시 시작하기</div>
<div class="pro-subtitle">
무료 분석은 “오늘 왜 빠졌는지”를 보여줍니다.<br>
PRO는 등록한 종목의 하락, 악성 뉴스, 위험 공시를 매일 감시해
놓치기 쉬운 위험 신호를 먼저 알려주는 기능입니다.
</div>
<div class="pro-price">월 4,900원 · 내 종목 AI 감시</div>
<div class="pro-grid">
<div class="pro-feature">
<div class="pro-feature-title">✅ 관심종목 AI 일일 감시</div>
<div class="pro-feature-desc">등록한 종목의 하락, 뉴스, 공시를 매일 확인합니다.</div>
</div>
<div class="pro-feature">
<div class="pro-feature-title">✅ 위험 공시 쉬운 해석</div>
<div class="pro-feature-desc">유상증자, CB, 감자, 거래정지를 주린이 눈높이로 풉니다.</div>
</div>
<div class="pro-feature">
<div class="pro-feature-title">✅ 최근 3일 하락 변화</div>
<div class="pro-feature-desc">오늘만이 아니라 악재가 이어지는지 흐름을 봅니다.</div>
</div>
<div class="pro-feature">
<div class="pro-feature-title">✅ 악성 뉴스 감지</div>
<div class="pro-feature-desc">소송, 규제, 실적악화, 최대주주 이슈를 따로 분류합니다.</div>
</div>
<div class="pro-feature">
<div class="pro-feature-title">✅ 주린이 위험 체크리스트</div>
<div class="pro-feature-desc">단순 조정인지 기업 자체 문제인지 쉽게 구분합니다.</div>
</div>
<div class="pro-feature">
<div class="pro-feature-title">✅ 급락/위험 공시 알림</div>
<div class="pro-feature-desc">크게 빠지거나 위험 공시가 뜨면 먼저 알려줍니다.</div>
</div>
</div>
</div>""",
        unsafe_allow_html=True
    )

    st.markdown(
        """<div class="compare-card">
<div class="compare-title">무료와 PRO 차이</div>
<div class="compare-grid">
<div class="compare-box-free">
<div class="compare-head">무료 분석</div>
<div class="compare-line">
✅ 오늘 하락 원인 요약<br>
✅ 하락 원인 점수판<br>
✅ 최근 뉴스/공시 확인<br>
✅ 광고 보고 심층 리포트 열기
</div>
</div>
<div class="compare-box-pro">
<div class="compare-head">왜빠짐 PRO</div>
<div class="compare-line">
✅ 관심종목 AI 일일 감시<br>
✅ 위험 공시 쉬운 해석<br>
✅ 최근 3일 하락 원인 변화<br>
✅ 악성 뉴스 감지<br>
✅ 급락/위험 공시 알림<br>
✅ 심층 리포트 무제한
</div>
</div>
</div>
</div>""",
        unsafe_allow_html=True
    )

    st.markdown(
        f"""<div class="pro-detail-card">
<div class="pro-detail-title">PRO를 누르면 실제로 열리는 기능</div>
<div class="pro-detail-desc">
{stock_label}을 매번 직접 검색하지 않아도,
AI가 매일 뉴스·공시·시장 변동을 확인하고 위험 신호를 정리해주는 기능을 준비 중입니다.
</div>
<div class="pro-proof">
<b>핵심 가치</b><br>
정보가 많은 것이 아니라, 주린이가 놓치기 쉬운 위험 신호를
“쉬운 말”로 먼저 알려주는 것입니다.
</div>
<div class="pro-proof">
<b>예시 알림</b><br>
“{stock_label}에 전환사채/유상증자/최대주주 변경성 공시가 감지되었습니다.
기존 주주에게 불리할 수 있어 세부 확인이 필요합니다.”
</div>
</div>""",
        unsafe_allow_html=True
    )

    with st.form("pro_lead_form", clear_on_submit=True):
        email = st.text_input(
            "PRO 베타 출시 알림 받을 이메일",
            placeholder="예: your@email.com",
            label_visibility="visible"
        )

        submitted = st.form_submit_button("PRO 출시 알림 신청하기", use_container_width=True)

        if submitted:
            ok, msg = save_pro_lead(email, stock_name=stock_name, source="pro_beta_waitlist")

            if ok:
                st.markdown(
                    f"""<div class="pro-success-card">
{safe_text(msg)}<br>
지금은 결제 전 수요검증 단계이며, 실제 결제는 아직 진행되지 않습니다.
</div>""",
                    unsafe_allow_html=True
                )
            else:
                st.warning(msg)



# =============================
# 오류 처리 / 로그 저장
# =============================
ERROR_LOG_FILE = Path("error_log.txt")


def log_app_error(stage, error):
    try:
        message = (
            f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] "
            f"{stage}: {repr(error)}\n"
            f"{traceback.format_exc()}\n"
            f"{'-' * 80}\n"
        )

        with ERROR_LOG_FILE.open("a", encoding="utf-8") as f:
            f.write(message)
    except Exception:
        pass


def make_fallback_ai_result(stock_name, price_data, news_data, dart_data, exchange_data):
    return {
        "summary": f"{stock_name}는 현재 가격 변동, 뉴스 흐름, 환율, 공시 여부를 함께 확인해야 합니다.",
        "risk_level": "중간",
        "market_or_company": "AI 상세 분석이 지연되어 기본 데이터 기준으로만 판단합니다.",
        "disclosure_risk": f"최근 공시: {dart_data[0].get('title') if dart_data else '최근 공시 확인 필요'}",
        "negative_keywords": ["주가 변동", "뉴스 확인", "공시 확인", "환율"],
        "reasons": [
            {
                "title": "기본 데이터 기준 분석",
                "description": f"현재 등락률은 {price_data.get('등락률', '확인불가')}입니다. 뉴스와 공시를 함께 확인해야 합니다.",
            },
            {
                "title": "뉴스/공시 확인 필요",
                "description": "AI 분석이 일시적으로 지연되어 최신 뉴스와 공시 카드를 우선 확인하는 것이 좋습니다.",
            },
            {
                "title": "환율 환경 확인",
                "description": f"현재 원/달러 환율은 {exchange_data.get('현재환율', '확인불가')}입니다.",
            },
        ],
        "checkpoints": [
            "뉴스 제목이 시장 전체 이슈인지 개별 기업 악재인지 확인",
            "DART 공시에 유상증자, CB, 감자, 최대주주 변경이 있는지 확인",
            "같은 업종 대표 종목도 같이 하락했는지 확인",
        ],
    }


def friendly_fatal_error(message):
    st.markdown(
        f"""
        <div class="fatal-error-card">
            <div class="fatal-error-title">분석을 완료하지 못했습니다</div>
            <div>{safe_text(message)}</div>
            <div style="margin-top:8px;">종목명 또는 종목코드를 다시 확인한 뒤 재시도해주세요.</div>
        </div>
        """,
        unsafe_allow_html=True
    )


def run_analysis_for_input(user_input):
    st.session_state.cache_status = []
    st.session_state.data_warnings = []

    with st.spinner("실제 주가, 환율, 최신 뉴스, DART 공시를 조회하고 등락 원인을 분석 중입니다..."):
        # 1. 주가/종목 식별은 필수
        try:
            price_data = get_real_price_data(user_input)
        except Exception as e:
            log_app_error("주가 조회 실패", e)
            raise Exception("종목 정보를 찾지 못했습니다. 종목명 또는 종목코드를 다시 확인해주세요.")

        # 2. 환율은 실패해도 앱이 죽으면 안 됨
        try:
            exchange_data = get_usd_krw_exchange_rate()
        except Exception as e:
            log_app_error("환율 조회 실패", e)
            exchange_data = {
                "환율명": "USD/KRW",
                "현재환율": "확인불가",
                "전일대비": "확인불가",
                "방향": "중립",
                "데이터출처": "환율 조회 지연",
            }
            st.session_state.data_warnings.append("환율 조회가 지연되어 일부 분석은 제한될 수 있습니다.")

        # 3. 뉴스는 실패 시 대체 메시지
        try:
            news_data = get_expanded_news_for_deep_report(price_data["종목명"])
        except Exception as e:
            log_app_error("뉴스 조회 실패", e)
            news_data = [
                {
                    "title": "최근 뉴스 조회 지연",
                    "description": "현재 뉴스 데이터를 불러오지 못했습니다. 잠시 후 다시 시도해주세요.",
                    "link": "#",
                    "pubDate": datetime.now().strftime("%Y-%m-%d %H:%M"),
                }
            ]
            st.session_state.data_warnings.append("뉴스 조회가 지연되어 기본 분석으로 대체했습니다.")

        # 4. DART는 실패 시 대체 메시지
        try:
            dart_data = get_dart_filings(price_data["종목코드"], price_data["종목명"])
        except Exception as e:
            log_app_error("DART 조회 실패", e)
            dart_data = [
                {
                    "title": "최근 공시 조회 지연",
                    "description": "현재 DART 공시 조회가 지연되고 있습니다.",
                    "link": "#",
                    "pubDate": datetime.now().strftime("%Y-%m-%d %H:%M"),
                }
            ]
            st.session_state.data_warnings.append("공시 조회가 지연되어 공시 리스크 판단이 제한될 수 있습니다.")

        # 5. AI는 실패 시 기본 규칙 분석으로 대체
        try:
            ai_result = analyze_with_ai(
                price_data["종목명"],
                price_data,
                news_data,
                dart_data,
                exchange_data
            )
        except Exception as e:
            log_app_error("AI 분석 실패", e)
            ai_result = make_fallback_ai_result(
                price_data["종목명"],
                price_data,
                news_data,
                dart_data,
                exchange_data
            )
            st.session_state.data_warnings.append("AI 상세 분석이 지연되어 기본 분석으로 대체했습니다.")

    st.session_state.last_analysis = {
        "price_data": price_data,
        "exchange_data": exchange_data,
        "news_data": news_data,
        "dart_data": dart_data,
        "ai_result": ai_result,
        "data_warnings": st.session_state.get("data_warnings", []),
    }
    st.session_state.show_deep_report = False
    st.session_state.show_pro_detail = False
    st.session_state.last_query = price_data["종목명"]
    add_recent_query(price_data)



# =============================
# 코스피/코스닥 전체 급락 TOP
# =============================
def parse_market_rate(rate_text):
    if rate_text is None:
        return 0.0

    text = str(rate_text)
    text = text.replace("%", "").replace(",", "").replace("+", "").strip()

    try:
        return float(text)
    except Exception:
        return 0.0


def infer_market_reason(stock_name, stock_code, market_name):
    name = str(stock_name)

    if any(keyword in name for keyword in ["삼성전자", "SK하이닉스", "DB하이텍", "한미반도체", "리노공업"]):
        return "반도체 업종 하락 후보"
    if any(keyword in name for keyword in ["에코프로", "엘앤에프", "포스코", "금양", "LG에너지"]):
        return "2차전지/소재 업종 하락 후보"
    if any(keyword in name for keyword in ["NAVER", "카카오", "더존", "안랩"]):
        return "인터넷/플랫폼 업종 하락 후보"
    if any(keyword in name for keyword in ["현대차", "기아", "HL만도", "현대모비스"]):
        return "자동차 업종 하락 후보"
    if any(keyword in name for keyword in ["셀트리온", "삼성바이오", "HLB", "알테오젠", "리가켐"]):
        return "바이오 업종 하락 후보"
    if any(keyword in name for keyword in ["한화오션", "HD현대", "삼성중공업", "현대로템"]):
        return "조선/방산 업종 하락 후보"

    return f"{market_name} 전체 종목 중 급락 후보"


@st.cache_data(ttl=300)
def fetch_naver_market_page(sosok, page):
    """
    네이버 금융 시가총액 페이지에서 코스피/코스닥 전체 종목을 페이지 단위로 가져온다.
    sosok=0 코스피, sosok=1 코스닥
    """
    market_name = "코스피" if sosok == 0 else "코스닥"

    url = "https://finance.naver.com/sise/sise_market_sum.naver"
    params = {
        "sosok": sosok,
        "page": page,
    }

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://finance.naver.com/",
    }

    try:
        increment_api_usage("market_pages")
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, "html.parser", from_encoding="euc-kr")
        rows = soup.select("table.type_2 tr")

        result = []

        for row in rows:
            link = row.select_one("a.tltle")

            if not link:
                continue

            href = link.get("href", "")
            match = re.search(r"code=(\d{6})", href)

            if not match:
                continue

            stock_code = match.group(1)
            stock_name = link.get_text(strip=True)

            tds = [td.get_text(" ", strip=True) for td in row.select("td")]

            if len(tds) < 5:
                continue

            current_price = tds[2] if len(tds) > 2 else "확인불가"
            rate_text = ""

            for value in tds:
                if "%" in value:
                    rate_text = value.replace(" ", "")
                    break

            if not rate_text:
                continue

            rate_value = parse_market_rate(rate_text)

            result.append({
                "stock_name": stock_name,
                "stock_code": stock_code,
                "current_price": f"{current_price}원" if current_price and "원" not in current_price else current_price,
                "change_rate": rate_text,
                "rate_value": rate_value,
                "market": market_name,
                "reason": infer_market_reason(stock_name, stock_code, market_name),
            })

        return result

    except Exception:
        return []


@st.cache_data(ttl=300)
def get_all_market_movers(limit=10, max_pages_per_market=45):
    """
    코스피/코스닥 전체 페이지를 훑어서 등락률이 가장 낮은 종목을 뽑는다.
    MVP에서는 네이버 금융 시가총액 페이지 기준.
    """
    all_items = []

    for sosok in [0, 1]:
        empty_count = 0

        for page in range(1, max_pages_per_market + 1):
            page_items = fetch_naver_market_page(sosok, page)

            if not page_items:
                empty_count += 1

                if empty_count >= 2:
                    break

                continue

            empty_count = 0
            all_items.extend(page_items)

    # 하락 종목만 우선
    negative_items = [item for item in all_items if item.get("rate_value", 0) < 0]

    if negative_items:
        sorted_items = sorted(negative_items, key=lambda x: x.get("rate_value", 0))
    else:
        sorted_items = sorted(all_items, key=lambda x: x.get("rate_value", 0))

    # ETF/ETN/우선주성 이름 일부 제외
    exclude_keywords = ["KODEX", "TIGER", "ACE", "SOL", "RISE", "PLUS", "KOSEF", "HANARO", "ARIRANG", "ETN", "스팩", "우B", "우"]

    filtered = []

    for item in sorted_items:
        name = item.get("stock_name", "")

        if any(keyword in name for keyword in exclude_keywords):
            continue

        filtered.append(item)

        if len(filtered) >= limit:
            break

    return filtered


def clear_market_mover_cache():
    fetch_naver_market_page.clear()
    get_all_market_movers.clear()



# =============================
# 공시 위험 TOP
# =============================
DISCLOSURE_DANGER_KEYWORDS = [
    "유상증자", "전환사채", "신주인수권부사채", "감자", "거래정지",
    "상장폐지", "횡령", "배임", "의견거절", "감사의견", "회생절차",
    "파산", "불성실공시", "관리종목"
]

DISCLOSURE_MID_KEYWORDS = [
    "최대주주변경", "소송", "주요사항보고서", "타법인", "담보제공",
    "단기차입금", "자기주식처분", "매출액또는손익구조"
]


def score_disclosure_risk(report_name):
    matched_danger = [keyword for keyword in DISCLOSURE_DANGER_KEYWORDS if keyword in report_name]
    matched_mid = [keyword for keyword in DISCLOSURE_MID_KEYWORDS if keyword in report_name]

    if matched_danger:
        return 90, "위험", matched_danger

    if matched_mid:
        return 65, "주의", matched_mid

    return 0, "중립", []


@st.cache_data(ttl=300)
def get_recent_disclosure_risks(limit=10, page_count=100):
    """
    OpenDART 최신 공시 목록에서 위험 키워드를 포함한 공시를 뽑는다.
    corp_code를 지정하지 않고 전체 공시 목록을 가져오는 방식.
    """
    if not DART_API_KEY:
        return []

    url = "https://opendart.fss.or.kr/api/list.json"
    params = {
        "crtfc_key": DART_API_KEY,
        "page_no": 1,
        "page_count": page_count,
        "sort": "date",
        "sort_mth": "desc",
    }

    try:
        increment_api_usage("dart_list")
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data.get("status") not in ["000", "013"]:
            return []

        items = data.get("list", [])
        results = []

        for item in items:
            report_name = item.get("report_nm", "")
            risk_score, risk_level, keywords = score_disclosure_risk(report_name)

            if risk_score <= 0:
                continue

            receipt_no = item.get("rcept_no", "")
            stock_code = item.get("stock_code", "")
            corp_name = item.get("corp_name", "")
            receipt_date = item.get("rcept_dt", "")

            results.append({
                "corp_name": corp_name,
                "stock_code": stock_code,
                "report_name": report_name,
                "receipt_no": receipt_no,
                "receipt_date": receipt_date,
                "risk_score": risk_score,
                "risk_level": risk_level,
                "keywords": keywords,
                "link": f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={receipt_no}",
            })

        results = sorted(results, key=lambda x: x.get("risk_score", 0), reverse=True)

        return results[:limit]

    except Exception:
        return []


def clear_disclosure_risk_cache():
    get_recent_disclosure_risks.clear()


# =============================
# 앱 시작 / 로그인 화면
# =============================
if "splash_done" not in st.session_state:
    st.session_state.splash_done = False

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "login_provider" not in st.session_state:
    st.session_state.login_provider = "비회원"

if not st.session_state.splash_done:
    st.markdown(
        """
        <div class="splash-screen">
            <div class="splash-card">
                <div class="splash-icon">📉</div>
                <div class="splash-title">왜빠짐</div>
                <div class="splash-subtitle">
                    내 종목이 왜 빠졌는지<br>
                    뉴스·공시·환율을 AI가 한 번에 분석합니다
                </div>
                <div class="splash-loader">
                    <div class="splash-loader-fill"></div>
                </div>
                <div class="splash-note">AI 하락 원인 분석 준비 중</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    time.sleep(1.6)
    st.session_state.splash_done = True
    st.rerun()

# URL query parameter 기반 MVP 로그인 처리
# MVP 로그인 상태 처리
login_query = st.query_params.get("login")

if login_query and not st.session_state.logged_in:
    provider_map = {
        "kakao": "카카오",
        "naver": "네이버",
        "google": "Google",
        "email": "이메일",
        "guest": "비회원 체험",
    }
    st.session_state.logged_in = True
    st.session_state.login_provider = provider_map.get(login_query, "비회원 체험")
    st.query_params.clear()
    st.rerun()

if not st.session_state.logged_in:
    login_html = '<div class="login-screen"><div class="login-card"><div class="login-logo">📉</div><div class="login-title">왜빠짐 시작하기</div><div class="login-subtitle">내 종목이 왜 빠졌는지<br>AI가 뉴스·공시·환율을 한 번에 분석합니다.</div><div class="login-benefit">✅ 관심종목 저장<br>✅ 최근 조회 종목 기록<br>✅ 급락·공시 알림 준비<br>✅ 프리미엄/광고 제거 연동 준비</div><a class="social-btn social-kakao" href="?login=kakao" target="_self"><span class="social-icon icon-kakao">💬</span><span>카카오로 시작하기</span></a><a class="social-btn social-naver" href="?login=naver" target="_self"><span class="social-icon icon-naver">N</span><span>네이버로 시작하기</span></a><a class="social-btn social-google" href="?login=google" target="_self"><span class="social-icon icon-google">G</span><span>Google로 시작하기</span></a><div class="login-divider">또는</div><a class="social-btn social-email" href="?login=email" target="_self"><span class="social-icon icon-email">✉</span><span>이메일로 회원가입</span></a><a class="guest-link" href="?login=guest" target="_self">로그인 없이 둘러보기</a><div class="login-small">MVP에서는 버튼 클릭 시 로그인된 것처럼 본 페이지로 진입합니다.<br>실제 앱에서는 OAuth와 서버 회원 DB를 연결합니다.</div></div></div>'
    st.markdown(login_html, unsafe_allow_html=True)
    st.stop()

st.markdown(
    f"""
    <div class="top-user-bar">
        <span>{st.session_state.login_provider} 로그인</span>
    </div>
    """,
    unsafe_allow_html=True
)



# =============================
# 세션 상태 초기화
# =============================
if "last_analysis" not in st.session_state:
    st.session_state.last_analysis = None

if "show_deep_report" not in st.session_state:
    st.session_state.show_deep_report = False

if "last_query" not in st.session_state:
    st.session_state.last_query = ""

if "watchlist_message" not in st.session_state:
    st.session_state.watchlist_message = ""

if "data_warnings" not in st.session_state:
    st.session_state.data_warnings = []

if "show_pro_detail" not in st.session_state:
    st.session_state.show_pro_detail = False

# =============================
# Header
# =============================
st.markdown('<div class="app-title">📉 왜빠짐</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="app-subtitle">국장 개인투자자를 위한 AI 하락 원인 분석 앱</div>',
    unsafe_allow_html=True
)


# =============================
# 검색 영역
# =============================
# V1.1.3
# 구글 자동완성처럼 "삼성"만 입력해도 관련 종목 후보를 드롭다운으로 보여준다.
search_col, button_col = st.columns([4, 1])

selected_search_label = None
direct_stock_input = ""

with search_col:
    if st_searchbox is not None:
        selected_search_label = st_searchbox(
            stock_searchbox_options,
            key="stock_autocomplete_searchbox",
            placeholder="예: 삼성, 현대, SK, 005930",
        )

        st.markdown(
            """
            <div class="stock-search-preview">
                <div class="stock-search-preview-title">종목명을 일부만 입력해도 관련 종목을 찾습니다</div>
                <div class="stock-search-preview-desc">예: 삼성 → 삼성전자, 삼성전기, 삼성SDI · 현대 → 현대차, 현대모비스</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        direct_stock_input = st.text_input(
            "종목명 또는 종목코드를 입력하세요",
            placeholder="예: 삼성전자, 005930",
            label_visibility="collapsed",
        )

with button_col:
    analyze_clicked = st.button("분석하기", use_container_width=True)

if st_searchbox is None:
    st.markdown(
        """
        <div class="search-helper-card">
            자동완성 패키지가 설치되지 않아 기본 검색창으로 표시됩니다.
            <b>streamlit-searchbox</b>를 requirements.txt에 추가하면 삼성 입력 시 관련 종목 후보가 드롭다운으로 표시됩니다.
        </div>
        """,
        unsafe_allow_html=True
    )

stock_input = ""

if selected_search_label:
    stock_input = parse_stock_search_label(selected_search_label)

    st.markdown(
        f"""
        <div class="search-selected-card">
            선택한 종목 · {safe_text(selected_search_label)}
        </div>
        """,
        unsafe_allow_html=True
    )
else:
    stock_input = direct_stock_input

# 검색 직후 바로 보이는 로딩 영역
loading_placeholder = st.empty()

if analyze_clicked:
    if not stock_input:
        st.warning("검색창에서 종목을 선택하거나 종목코드를 입력하세요.")
    else:
        loading_placeholder.markdown(
            f"""
            <div class="loading-hero">
                <div class="loading-title">"{safe_text(stock_input)}" 분석을 시작했습니다</div>
                <div class="loading-sub">
                    KIS 시세, 차트, 환율, 뉴스, 공시, AI 분석을 순서대로 확인 중입니다.<br>
                    보통 5~15초 정도 걸릴 수 있습니다.
                </div>
                <div class="loading-bar"><div class="loading-bar-fill"></div></div>
                <div class="loading-steps">
                    <span class="loading-step">KIS 시세 확인</span>
                    <span class="loading-step">차트 데이터</span>
                    <span class="loading-step">뉴스 수집</span>
                    <span class="loading-step">AI 요약 생성</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        try:
            run_analysis_for_input(stock_input)
            # 결과가 실제로 렌더링되기 전에 로딩 카드가 먼저 사라지는 빈틈을 막기 위해
            # 여기서 st.rerun()을 호출하지 않는다.
            # 같은 실행 흐름에서 아래 결과 영역이 바로 이어서 렌더링된다.

        except Exception as e:
            loading_placeholder.empty()
            log_app_error("분석 전체 실패", e)
            friendly_fatal_error(str(e))



# =============================
# 앱 홈 대시보드
# =============================
st.markdown(
    """
    <div class="app-shell-note">
        <b>사용법</b> · 종목을 검색하거나 아래 메뉴에서 관심종목, 급락 TOP, 공시 위험 종목을 바로 확인하세요.
    </div>
    """,
    unsafe_allow_html=True
)

# =============================
# 관심종목 패널
# =============================
watchlist_items = load_watchlist()

with st.expander("⭐ 내 관심종목", expanded=False):
    st.markdown(
        """
        <div class="watch-card">
            <div class="watch-title">내 관심종목</div>
            <div class="watch-sub">
                자주 보는 종목을 저장해두면 앱을 열 때 바로 다시 분석할 수 있습니다.
                MVP에서는 이 컴퓨터의 watchlist.json 파일에 저장됩니다.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    if st.session_state.watchlist_message:
        st.info(st.session_state.watchlist_message)

    if watchlist_items:
        for idx, item in enumerate(watchlist_items):
            c1, c2, c3 = st.columns([3, 1.2, 1])

            with c1:
                st.markdown(
                    f"""
                    <div class="watch-item">
                        <div class="watch-name">{safe_text(item.get("stock_name", ""))}</div>
                        <div class="watch-meta">종목코드 {safe_text(item.get("stock_code", ""))} · 추가일 {safe_text(item.get("created_at", ""))}</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            with c2:
                if st.button("분석", key=f"watch_analyze_{idx}", use_container_width=True):
                    run_analysis_for_input(item.get("stock_code"))
                    st.rerun()

            with c3:
                if st.button("삭제", key=f"watch_delete_{idx}", use_container_width=True):
                    remove_from_watchlist(item.get("stock_code"))
                    st.session_state.watchlist_message = f"{item.get('stock_name')} 관심종목을 삭제했습니다."
                    st.rerun()
    else:
        st.markdown(
            """
            <div class="watch-empty">
                아직 관심종목이 없습니다.<br>
                종목을 분석한 뒤 결과 화면에서 <b>관심종목 추가</b>를 눌러보세요.
            </div>
            """,
            unsafe_allow_html=True
        )



# =============================
# 최근 조회 종목 패널
# =============================
recent_items = load_recent_queries()

with st.expander("🕘 최근 조회 종목", expanded=False):
    st.markdown(
        """
        <div class="watch-card">
            <div class="watch-title">최근 조회 종목</div>
            <div class="watch-sub">
                최근 분석한 종목을 빠르게 다시 열 수 있습니다.
                MVP에서는 이 컴퓨터의 recent_queries.json 파일에 저장됩니다.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    if recent_items:
        for idx, item in enumerate(recent_items):
            c1, c2 = st.columns([3.2, 1])

            with c1:
                change_rate = str(item.get("change_rate", ""))
                rate_class = "negative" if "-" in change_rate else "positive" if "+" in change_rate else "neutral"

                st.markdown(
                    f"""
                    <div class="watch-item">
                        <div class="watch-name">{safe_text(item.get("stock_name", ""))} <span class="{rate_class}">{safe_text(change_rate)}</span></div>
                        <div class="watch-meta">종목코드 {safe_text(item.get("stock_code", ""))} · 현재가 {safe_text(item.get("current_price", ""))} · 조회일 {safe_text(item.get("created_at", ""))}</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            with c2:
                if st.button("다시 분석", key=f"recent_analyze_{idx}", use_container_width=True):
                    run_analysis_for_input(item.get("stock_code"))
                    st.rerun()
    else:
        st.markdown(
            """
            <div class="watch-empty">
                아직 최근 조회 종목이 없습니다.<br>
                종목을 한 번 분석하면 여기에 자동으로 저장됩니다.
            </div>
            """,
            unsafe_allow_html=True
        )



# =============================
# 급락 TOP 패널
# =============================
with st.expander("🔥 코스피·코스닥 급락 TOP", expanded=False):
    st.markdown(
        """
        <div class="movers-card">
            <div class="movers-title">코스피·코스닥 급락 TOP</div>
            <div class="movers-sub">
                코스피/코스닥 전체 종목을 훑어서 현재 등락률이 낮은 종목을 보여줍니다.
                MVP에서는 네이버 금융 시가총액 페이지 기준으로 집계합니다.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    if st.button("급락 TOP 새로고침", use_container_width=True):
        clear_market_mover_cache()

    try:
        movers = get_all_market_movers(limit=10)

        if movers:
            for idx, item in enumerate(movers, start=1):
                c1, c2 = st.columns([3.2, 1])

                with c1:
                    rate = safe_text(item.get("change_rate", "확인불가"))

                    st.markdown(
                        f"""
                        <div class="mover-item">
                            <div>
                                <span class="mover-rank">TOP {idx}</span>
                                <span class="mover-name">{safe_text(item.get("stock_name", ""))}</span>
                            </div>
                            <div class="mover-rate">{rate}</div>
                            <div class="mover-meta">종목코드 {safe_text(item.get("stock_code", ""))} · 현재가 {safe_text(item.get("current_price", ""))}</div>
                            <div class="mover-reason">{safe_text(item.get("reason", ""))}</div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                with c2:
                    if st.button("분석", key=f"mover_analyze_{idx}", use_container_width=True):
                        run_analysis_for_input(item.get("stock_code"))
                        st.rerun()
        else:
            st.info("급락 TOP 데이터를 가져오지 못했습니다.")

        st.markdown(
            """
            <div class="mover-warning">
                현재는 코스피/코스닥 전체 시가총액 페이지 기준입니다. 정식 버전에서는 거래대금, 시가총액, 투자주의/정지 여부 필터를 추가합니다.
            </div>
            """,
            unsafe_allow_html=True
        )

    except Exception as e:
        st.warning(f"급락 TOP 조회 실패: {e}")



# =============================
# 관리자 전용 데이터/호출량 상태 패널
# =============================
# 일반 사용자는 이 패널을 보지 않는다.
# 관리자 확인이 필요할 때만 주소 뒤에 ?admin=1 을 붙이면 표시된다.
is_admin_mode = st.query_params.get("admin") == "1"

if is_admin_mode:
    with st.expander("🛠 관리자 · 데이터/호출량 상태", expanded=False):
        usage = load_api_usage()

        st.markdown(
            """
            <div class="data-status-card">
                <div class="data-status-title">관리자용 데이터 호출량 관리</div>
                <div class="data-status-sub">
                    이 영역은 일반 사용자에게 노출되지 않습니다.
                    API 호출량, 캐시 재사용 횟수, 데이터 갱신 상태를 내부 운영자가 확인하는 용도입니다.
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        naver_limit = 25000
        dart_limit = 40000

        naver_pct = min(100, usage.get("naver_news", 0) / naver_limit * 100)
        dart_pct = min(100, usage.get("dart_list", 0) / dart_limit * 100)

        st.markdown(
            f"""
            <div class="usage-grid">
                <div class="usage-box">
                    <div class="usage-label">네이버 뉴스 API</div>
                    <div class="usage-value">{usage.get("naver_news", 0):,} / {naver_limit:,}</div>
                    <div class="usage-bar"><div class="usage-fill" style="width:{naver_pct}%;"></div></div>
                </div>
                <div class="usage-box">
                    <div class="usage-label">DART 공시 API</div>
                    <div class="usage-value">{usage.get("dart_list", 0):,} / {dart_limit:,}</div>
                    <div class="usage-bar"><div class="usage-fill" style="width:{dart_pct}%;"></div></div>
                </div>
                <div class="usage-box">
                    <div class="usage-label">급락 TOP 페이지 호출</div>
                    <div class="usage-value">{usage.get("market_pages", 0):,}회</div>
                    <div class="usage-bar"><div class="usage-fill" style="width:20%;"></div></div>
                </div>
                <div class="usage-box">
                    <div class="usage-label">OpenAI 호출</div>
                    <div class="usage-value">{usage.get("openai", 0):,}회</div>
                    <div class="usage-bar"><div class="usage-fill" style="width:25%;"></div></div>
                </div>
                <div class="usage-box">
                    <div class="usage-label">캐시 재사용</div>
                    <div class="usage-value">{usage.get("cache_hit", 0):,}회</div>
                    <div class="usage-bar"><div class="usage-fill" style="width:45%;"></div></div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        cache_status = st.session_state.get("cache_status", [])

        if cache_status:
            chip_html = ""

            for item in cache_status:
                cls = "cache-hit" if item.get("status") == "캐시" else "cache-live"
                age_text = format_age(item.get("age"))
                chip_html += f'<span class="cache-chip {cls}">{safe_text(item.get("label"))}: {safe_text(item.get("status"))} · {safe_text(age_text)}</span>'

            st.markdown(chip_html, unsafe_allow_html=True)
        else:
            st.markdown(
                '<span class="cache-chip cache-info">아직 분석 전입니다. 종목을 분석하면 캐시 사용 여부가 표시됩니다.</span>',
                unsafe_allow_html=True
            )

        st.markdown(
            """
            <div class="mover-warning">
                권장 TTL: 주가 30초~1분, 급락 TOP 1~3분, DART 5분, 뉴스 30분, AI 분석 30분.
                현재 MVP는 뉴스/DART/AI 분석 파일 캐시와 호출량 카운터를 적용했습니다.
            </div>
            """,
            unsafe_allow_html=True
        )



# =============================
# 공시 위험 TOP 패널
# =============================
with st.expander("🚨 공시 위험 TOP", expanded=False):
    st.markdown(
        """
        <div class="disclosure-card">
            <div class="disclosure-title">공시 위험 TOP</div>
            <div class="disclosure-sub">
                최근 DART 전체 공시 중 유상증자, 전환사채, 감자, 최대주주 변경 등
                개인투자자가 우선 확인해야 할 공시 키워드를 감지합니다.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    if st.button("공시 위험 새로고침", use_container_width=True):
        clear_disclosure_risk_cache()

    if not DART_API_KEY:
        st.warning("DART_API_KEY가 없어 공시 위험 TOP을 조회할 수 없습니다.")
    else:
        try:
            risk_items = get_recent_disclosure_risks(limit=10, page_count=100)

            if risk_items:
                for idx, item in enumerate(risk_items, start=1):
                    c1, c2 = st.columns([3.2, 1])

                    with c1:
                        risk_class = "risk-tag-danger" if item.get("risk_level") == "위험" else "risk-tag-mid"
                        keywords = ", ".join(item.get("keywords", [])) if item.get("keywords") else "키워드 확인"

                        st.markdown(
                            f"""
                            <div class="risk-filing-item">
                                <div class="risk-filing-head">
                                    <span class="risk-rank">TOP {idx}</span>
                                    <span class="{risk_class}">{safe_text(item.get("risk_level", ""))}</span>
                                    <span class="risk-company">{safe_text(item.get("corp_name", ""))}</span>
                                </div>
                                <div class="risk-report">
                                    <a href="{safe_text(item.get("link", "#"))}" target="_blank">{safe_text(item.get("report_name", ""))}</a>
                                </div>
                                <div class="risk-meta">종목코드 {safe_text(item.get("stock_code", ""))} · 접수일 {safe_text(item.get("receipt_date", ""))}</div>
                                <div class="risk-keywords">감지 키워드: {safe_text(keywords)}</div>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

                    with c2:
                        stock_code = item.get("stock_code", "")

                        if stock_code:
                            if st.button("분석", key=f"risk_filing_analyze_{idx}", use_container_width=True):
                                run_analysis_for_input(stock_code)
                                st.rerun()
                        else:
                            st.button("분석불가", key=f"risk_filing_disabled_{idx}", disabled=True, use_container_width=True)
            else:
                st.info("최근 공시에서 위험 키워드가 감지되지 않았습니다.")

            st.markdown(
                """
                <div class="mover-warning">
                    공시 위험 TOP은 키워드 기반 1차 필터입니다.
                    실제 영향은 공시 원문, 발행 규모, 기업 상황을 함께 확인해야 합니다.
                </div>
                """,
                unsafe_allow_html=True
            )

        except Exception as e:
            st.warning(f"공시 위험 TOP 조회 실패: {e}")



# =============================
# 결과 영역
# =============================
if "last_analysis" not in st.session_state:
    st.session_state.last_analysis = None

if "show_deep_report" not in st.session_state:
    st.session_state.show_deep_report = False

if "last_query" not in st.session_state:
    st.session_state.last_query = ""

if "watchlist_message" not in st.session_state:
    st.session_state.watchlist_message = ""

if "data_warnings" not in st.session_state:
    st.session_state.data_warnings = []

if st.session_state.last_analysis:
    # 분석 결과 영역이 실제로 그려지는 시점에 로딩 카드를 닫는다.
    # 이 위치에서 닫아야 "로딩 종료 → 빈 화면 → 결과 표시" 공백이 생기지 않는다.
    try:
        loading_placeholder.empty()
    except Exception:
        pass

    price_data = st.session_state.last_analysis["price_data"]
    exchange_data = st.session_state.last_analysis["exchange_data"]
    news_data = st.session_state.last_analysis["news_data"]
    dart_data = st.session_state.last_analysis["dart_data"]
    ai_result = st.session_state.last_analysis["ai_result"]
    move_word = get_move_word(price_data)

    try:
        action_col1, action_col2 = st.columns([1, 3])

        with action_col1:
            if st.button("⭐ 관심종목 추가", use_container_width=True):
                ok, msg = add_to_watchlist(price_data["종목명"], price_data["종목코드"])
                st.session_state.watchlist_message = msg
                if ok:
                    st.success(msg)
                else:
                    st.info(msg)

        with action_col2:
            st.markdown(
                f"""
                <div class="watch-action">
                    현재 분석 종목: {safe_text(price_data["종목명"])} · {safe_text(price_data["종목코드"])}
                </div>
                """,
                unsafe_allow_html=True
            )

        st.markdown('<div class="section-title">📊 핵심 지표</div>', unsafe_allow_html=True)

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.markdown(
                f"""
                <div class="kpi-card">
                    <div class="kpi-label">종목명</div>
                    <div class="kpi-value">{safe_text(price_data['종목명'])}</div>
                    <div class="source-small">종목코드 {safe_text(price_data['종목코드'])}</div>
                </div>
                """,
                unsafe_allow_html=True
            )

        with col2:
            st.markdown(
                f"""
                <div class="kpi-card">
                    <div class="kpi-label">현재가</div>
                    <div class="kpi-value">{safe_text(price_data['현재가'])}</div>
                    <div class="source-small">{safe_text(price_data['데이터출처'])}</div>
                </div>
                """,
                unsafe_allow_html=True
            )

        with col3:
            if "-" in price_data["등락률"]:
                change_class = "negative"
            elif "+" in price_data["등락률"]:
                change_class = "positive"
            else:
                change_class = "neutral"

            st.markdown(
                f"""
                <div class="kpi-card">
                    <div class="kpi-label">등락률</div>
                    <div class="kpi-value {change_class}">{safe_text(price_data['등락률'])}</div>
                    <div class="source-small">전일대비 {safe_text(price_data['전일대비'])}</div>
                </div>
                """,
                unsafe_allow_html=True
            )

        with col4:
            if exchange_data.get("방향") == "상승":
                exchange_class = "negative"
            elif exchange_data.get("방향") == "하락":
                exchange_class = "positive"
            else:
                exchange_class = "neutral"

            st.markdown(
                f"""
                <div class="kpi-card">
                    <div class="kpi-label">원/달러 환율</div>
                    <div class="kpi-value {exchange_class}" style="font-size:1.35rem;">{safe_text(exchange_data['현재환율'])}</div>
                    <div class="source-small">전일대비 {safe_text(exchange_data['전일대비'])}</div>
                </div>
                """,
                unsafe_allow_html=True
            )

        if price_data.get("거래량") or price_data.get("거래대금"):
            vol_col1, vol_col2, vol_col3, vol_col4 = st.columns(4)

            with vol_col1:
                st.markdown(
                    f"""
                    <div class="kpi-card">
                        <div class="kpi-label">거래량</div>
                        <div class="kpi-value" style="font-size:1.25rem;">{safe_text(price_data.get("거래량", "확인불가"))}</div>
                        <div class="source-small">한국투자증권 시세</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            with vol_col2:
                st.markdown(
                    f"""
                    <div class="kpi-card">
                        <div class="kpi-label">거래대금</div>
                        <div class="kpi-value" style="font-size:1.25rem;">{safe_text(price_data.get("거래대금", "확인불가"))}</div>
                        <div class="source-small">거래 강도 확인</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            with vol_col3:
                st.markdown(
                    f"""
                    <div class="kpi-card">
                        <div class="kpi-label">장중 고가</div>
                        <div class="kpi-value" style="font-size:1.25rem;">{safe_text(price_data.get("고가", "확인불가"))}</div>
                        <div class="source-small">오늘 고점</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            with vol_col4:
                st.markdown(
                    f"""
                    <div class="kpi-card">
                        <div class="kpi-label">장중 저가</div>
                        <div class="kpi-value" style="font-size:1.25rem;">{safe_text(price_data.get("저가", "확인불가"))}</div>
                        <div class="source-small">오늘 저점</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            st.write("")

        st.caption("데이터는 항목별로 짧게 갱신됩니다. 주가·급락 TOP은 짧게, 뉴스·공시·AI 분석은 캐시를 활용합니다.")

        data_warnings = st.session_state.last_analysis.get("data_warnings", [])

        if data_warnings:
            warning_html = '<div class="soft-warning-card"><div class="soft-warning-title">일부 데이터 조회가 지연되었습니다</div>'

            for warning in data_warnings:
                warning_html += f'<div class="soft-warning-item">• {safe_text(warning)}</div>'

            warning_html += '</div>'

            st.markdown(warning_html, unsafe_allow_html=True)

        # -----------------------------
        # 무료 차트
        # -----------------------------
        render_free_price_chart(price_data)

        # -----------------------------
        # 상단 AI 결론 카드
        # -----------------------------
        risk_level = ai_result.get("risk_level", "중간")

        if risk_level == "높음":
            risk_class = "risk-badge-high"
        elif risk_level == "낮음":
            risk_class = "risk-badge-low"
        else:
            risk_class = "risk-badge-mid"

        st.markdown(
            f"""
            <div class="insight-card">
                <div class="insight-label">AI 요약</div>
                <div class="insight-title">{safe_text(ai_result.get("summary", ""))}</div>
                <span class="{risk_class}">위험도: {safe_text(risk_level)}</span>
                <span class="mini-chip">{safe_text(move_word)} 성격: {safe_text(ai_result.get("market_or_company", "확인 필요"))}</span>
                <span class="mini-chip">공시: {safe_text(ai_result.get("disclosure_risk", "확인 필요"))}</span>
            </div>
            """,
            unsafe_allow_html=True
        )

        # -----------------------------
        # 등락 원인 점수판
        # -----------------------------
        move_word = get_move_word(price_data)
        st.markdown(f'<div class="section-title">🧭 {safe_text(move_word)} 원인 점수판</div>', unsafe_allow_html=True)

        score_items = compute_cause_scores(
            price_data,
            news_data,
            dart_data,
            exchange_data,
            ai_result
        )

        render_score_board(score_items)

        # -----------------------------
        # 광고 / PRO 수요검증 구조
        # -----------------------------
        st.markdown(
            """
            <div class="ad-card">
                <div class="ad-title">스폰서 영역</div>
                <div>무료 사용자는 광고를 보고 심층 분석을 열 수 있습니다. PRO는 광고 없이 내 종목을 매일 감시하는 방향으로 검증합니다.</div>
            </div>
            """,
            unsafe_allow_html=True
        )

        render_pro_value_card(price_data.get("종목명", ""))

        reward_col, pro_col = st.columns(2)

        deep_is_open = st.session_state.get("show_deep_report", False)
        pro_is_open = st.session_state.get("show_pro_detail", False)

        with reward_col:
            deep_button_label = "심층 분석 리포트 닫기" if deep_is_open else "광고 보고 심층 분석 열기"

            if st.button(deep_button_label, use_container_width=True):
                st.session_state.show_deep_report = not deep_is_open
                st.rerun()

        with pro_col:
            pro_button_label = "PRO 기능 설명 닫기" if pro_is_open else "월 4,900원으로 내 종목 AI 감시 시작하기"

            if st.button(pro_button_label, use_container_width=True):
                if not pro_is_open:
                    record_pro_click(price_data.get("종목명", ""), source="result_pro_button")

                st.session_state.show_pro_detail = not pro_is_open
                st.rerun()

        if st.session_state.get("show_pro_detail", False):
            render_pro_detail_and_lead_form(price_data.get("종목명", ""))

        if st.session_state.get("show_deep_report", False):
            render_deep_report(price_data, news_data, dart_data, exchange_data, ai_result, score_items)

        st.write("")


        # -----------------------------
        # 뉴스 / 공시
        # -----------------------------
        left, right = st.columns([1.15, 0.85])

        with left:
            st.markdown('<div class="section-title">📰 주가 관련 핵심 뉴스</div>', unsafe_allow_html=True)

            display_news = select_display_news(news_data, price_data, ai_result, limit=5)

            st.markdown(
                f"""
                <div class="news-filter-note">
                    AI 분석에는 수집한 뉴스 {len(news_data)}개를 활용하고, 화면에는 주가 흐름과 가장 관련 높은 뉴스 {len(display_news)}개만 보여드립니다.
                </div>
                """,
                unsafe_allow_html=True
            )

            for news in display_news:
                title = safe_text(news.get("title", ""))
                description = safe_text(news.get("description", ""))
                link = safe_text(news.get("link", "#"))
                pub_date = safe_text(news.get("pubDate", ""))

                st.markdown(
                    f"""
                    <div class="news-card">
                        <div class="card-title">
                            <a href="{link}" target="_blank">{title}</a>
                        </div>
                        <div class="card-desc">{description}</div>
                        <div class="card-date">{pub_date}</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

        with right:
            st.markdown('<div class="section-title">📄 최근 공시</div>', unsafe_allow_html=True)

            for item in dart_data:
                title = safe_text(item.get("title", ""))
                description = safe_text(item.get("description", ""))
                link = safe_text(item.get("link", "#"))

                st.markdown(
                    f"""
                    <div class="dart-card">
                        <div class="card-title">
                            <a href="{link}" target="_blank">{title}</a>
                        </div>
                        <div class="card-desc">{description}</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

        st.write("")

        # -----------------------------
        # 상세 AI 분석
        # -----------------------------
        st.markdown('<div class="section-title">🤖 AI 상세 분석</div>', unsafe_allow_html=True)

        col_a, col_b = st.columns(2)

        with col_a:
            st.markdown("#### 📌 하락 성격")
            st.markdown(
                f"""
                <div class="reason-card">
                    <div class="reason-title">시장/섹터 vs 개별 악재</div>
                    <div class="reason-desc">{safe_text(ai_result.get("market_or_company", ""))}</div>
                </div>
                """,
                unsafe_allow_html=True
            )

        with col_b:
            st.markdown("#### 📄 공시 리스크")
            st.markdown(
                f"""
                <div class="reason-card">
                    <div class="reason-title">공시 악재 여부</div>
                    <div class="reason-desc">{safe_text(ai_result.get("disclosure_risk", ""))}</div>
                </div>
                """,
                unsafe_allow_html=True
            )

        st.markdown(f"#### 🔍 주요 {safe_text(move_word)} 원인")

        reasons = ai_result.get("reasons", [])

        if reasons:
            for reason in reasons:
                st.markdown(
                    f"""
                    <div class="reason-card">
                        <div class="reason-title">{safe_text(reason.get("title", ""))}</div>
                        <div class="reason-desc">{safe_text(reason.get("description", ""))}</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
        else:
            st.info("AI가 등락 원인을 구조화하지 못했습니다. 다시 분석을 시도해보세요.")

        keywords = ai_result.get("negative_keywords", [])

        if keywords:
            st.markdown("#### ⚠️ 감지된 주요 키워드")

            keyword_html = ""

            for keyword in keywords:
                keyword_html += f'<span class="keyword-chip">{safe_text(keyword)}</span>'

            st.markdown(keyword_html, unsafe_allow_html=True)

        st.markdown("#### ✅ 개인투자자 체크포인트")

        checkpoints = ai_result.get("checkpoints", [])

        if checkpoints:
            for checkpoint in checkpoints:
                st.markdown(
                    f"""
                    <div class="check-card">
                        ✅ {safe_text(checkpoint)}
                    </div>
                    """,
                    unsafe_allow_html=True
                )
        else:
            st.info("체크포인트가 생성되지 않았습니다.")

    except Exception as e:
        st.error(str(e))



if is_admin_mode:
    with st.expander("💰 관리자 · PRO 수요검증 데이터", expanded=False):
        pro_clicks = load_json_list_file(PRO_CLICK_FILE)
        pro_leads = load_json_list_file(PRO_LEADS_FILE)

        click_count = len(pro_clicks)
        lead_count = len(pro_leads)
        conversion = (lead_count / click_count * 100) if click_count else 0

        st.markdown(
            f"""
            <div class="data-status-card">
                <div class="data-status-title">PRO 버튼 반응</div>
                <div class="data-status-sub">
                    PRO 버튼 클릭 {click_count:,}회 · 출시 알림 신청 {lead_count:,}명 · 신청 전환율 {conversion:.1f}%
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        if pro_leads:
            st.markdown("#### 최근 PRO 출시 알림 신청자")

            for item in pro_leads[:10]:
                st.markdown(
                    f"""
                    <div class="check-card">
                        ✅ {safe_text(item.get("email", ""))} · 관심 종목 {safe_text(item.get("stock_name", ""))} · {safe_text(item.get("created_at", ""))}
                    </div>
                    """,
                    unsafe_allow_html=True
                )
        else:
            st.info("아직 PRO 출시 알림 신청자가 없습니다.")

        if pro_clicks:
            st.markdown("#### 최근 PRO 버튼 클릭")

            for item in pro_clicks[:10]:
                st.markdown(
                    f"""
                    <div class="check-card">
                        👆 {safe_text(item.get("stock_name", ""))} · {safe_text(item.get("source", ""))} · {safe_text(item.get("created_at", ""))}
                    </div>
                    """,
                    unsafe_allow_html=True
                )
        else:
            st.info("아직 PRO 버튼 클릭 기록이 없습니다.")



# =============================
# Footer
# =============================
st.markdown(
    """
    <div class="footer-box">
        왜빠짐은 투자 판단을 돕기 위한 정보 분석 도구입니다.<br>
        특정 종목의 매수·매도·보유를 권유하지 않으며, 제공 정보의 정확성이나 수익을 보장하지 않습니다.<br>
        최종 투자 판단과 책임은 투자자 본인에게 있습니다.
    </div>
    """,
    unsafe_allow_html=True
)
