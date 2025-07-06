import streamlit as st
import asyncio
from extract_metadata import MAIN_TO_SUB
from db import db_manager
from orchestrator import ScraperOrchestrator
from config import LOGGING_CONFIG
import logging
import logging.config

logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger("etimad.app")

st.set_page_config(page_title="Etimad Tender Scraper", layout="wide")

def init_session_state():
    if "scraper" not in st.session_state:
        st.session_state.scraper = ScraperOrchestrator()
    if "running" not in st.session_state:
        st.session_state.running = False

init_session_state()

st.title("🏛️ Etimad Tender Scraper")
st.markdown("""
    <style>
        .stProgress > div > div > div > div {
            background-color: #4CAF50;
        }
        .stButton button {
            width: 100%;
        }
    </style>
""", unsafe_allow_html=True)

col1, col2 = st.columns([1, 3])
with col1:
    main_category = st.selectbox(
        "Main Category", 
        list(MAIN_TO_SUB.keys()),
        help="Select the main category for tenders"
    )
    subcategories = MAIN_TO_SUB[main_category]
    selected_sub = st.selectbox(
        "Sub Category", 
        subcategories,
        help="Select the specific sub-category"
    )
    
    if st.button("🚀 Run Scraper", disabled=st.session_state.running):
        st.session_state.running = True
        st.session_state.progress = 0
        st.session_state.result = None
        
        async def run():
            try:
                # Initialize database
                db_manager.initialize_table()
                
                # Run metadata extraction
                with st.spinner("🔍 Searching for tenders..."):
                    metadata = await st.session_state.scraper.extract_metadata(selected_sub)
                    links = [item["Link"] for item in metadata if "Link" in item]
                    st.session_state.progress = 33
                
                # Run detail extraction
                with st.spinner("📥 Downloading tender details..."):
                    details = await extract_all_details(links)
                    st.session_state.progress = 66
                
                # Save results
                with st.spinner("💾 Saving to database..."):
                    for tender in details:
                        if tender and "رقم المنافسة" in tender:
                            db_manager.upsert_tender(tender)
                    st.session_state.progress = 100
                    st.session_state.result = details
                
            except Exception as e:
                st.error(f"Error: {str(e)}")
            finally:
                st.session_state.running = False
        
        asyncio.run(run())

with col2:
    if st.session_state.running:
        st.progress(st.session_state.progress)
        status_text = st.empty()
        
        if st.session_state.progress < 33:
            status_text.text("Searching for matching tenders...")
        elif st.session_state.progress < 66:
            status_text.text("Extracting tender details...")
        else:
            status_text.text("Saving results to database...")
    
    if st.session_state.result is not None:
        st.success(f"✅ Successfully fetched and stored {len(st.session_state.result)} tenders!")
        st.download_button(
            label="📥 Download as JSON",
            data=json.dumps(st.session_state.result, ensure_ascii=False),
            file_name=f"etimad_tenders_{selected_sub}.json",
            mime="application/json"
        )
        
        if st.checkbox("Show raw data"):
            st.json(st.session_state.result)