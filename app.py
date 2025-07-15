import gradio as gr
import threading
import asyncio
import logging
import time
import os
from db import db_manager
from orchestrator import ScraperOrchestrator
from config import MAIN_TO_SUB, LOGGING_CONFIG
from utils import setup_logger

# Setup logging
logging.config.dictConfig(LOGGING_CONFIG)
logger = setup_logger("etimad.gui")

# Global state
scraping_in_progress = False
last_log_position = 0

def run_scraper():
    """Run the scraper in a background thread"""
    global scraping_in_progress
    scraping_in_progress = True
    try:
        logger.info("Starting scraping process")
        orchestrator = ScraperOrchestrator()
        asyncio.run(orchestrator.run_pipeline())
    except Exception as e:
        logger.error(f"Scraping failed: {e}")
    finally:
        scraping_in_progress = False
        logger.info("Scraping process completed")

def start_scraper():
    """Start the scraping process in a background thread"""
    global scraping_in_progress
    if scraping_in_progress:
        return "Scraping is already running!"
    
    thread = threading.Thread(target=run_scraper)
    thread.daemon = True
    thread.start()
    return "Scraping started in the background. Check the logs below for progress."

def get_logs():
    """Get the latest logs from the log file"""
    global last_log_position
    log_file = "etimad_scraper.log"
    
    if not os.path.exists(log_file):
        return "Log file not found. Scraping hasn't started yet."
    
    try:
        with open(log_file, "r", encoding="utf-8") as f:
            # Handle log rotation
            current_size = os.path.getsize(log_file)
            if current_size < last_log_position:
                last_log_position = 0  # Log file was reset
                
            f.seek(last_log_position)
            new_content = f.read()
            last_log_position = f.tell()
            return new_content
    except Exception as e:
        return f"Error reading logs: {str(e)}"

def get_tenders():
    """Fetch tenders from the database"""
    conn = None
    try:
        conn = db_manager.get_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Only fetch essential columns for display
        cursor.execute("""
            SELECT 
                `Link`, 
                `اسم_المنافسة` AS TenderName,
                `رقم_المنافسة` AS TenderNumber,
                `الجهة_الحكوميه` AS GovernmentEntity,
                `حالة_المنافسة` AS Status,
                `آخر_موعد_لتقديم_العروض` AS SubmissionDeadline,
                `updated_at` AS LastUpdated
            FROM tenders 
            ORDER BY updated_at DESC
            LIMIT 100
        """)
        
        tenders = cursor.fetchall()
        return tenders if tenders else []
    except Exception as e:
        logger.error(f"Error fetching tenders: {e}")
        return []
    finally:
        if conn:
            conn.close()

def get_scraping_history():
    """Get scraping history from database"""
    conn = None
    try:
        conn = db_manager.get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT 
                id, 
                category, 
                subcategory, 
                tender_count, 
                status, 
                error_message,
                timestamp
            FROM scraping_logs 
            ORDER BY timestamp DESC
            LIMIT 50
        """)
        return cursor.fetchall()
    except Exception as e:
        logger.error(f"Error fetching scraping history: {e}")
        return []
    finally:
        if conn:
            conn.close()

def get_category_options():
    """Get category options for the dropdown"""
    return list(MAIN_TO_SUB.keys())

def get_subcategory_options(category):
    """Get subcategory options based on selected category"""
    return MAIN_TO_SUB.get(category, [])

# Create Gradio interface
with gr.Blocks(title="Etimad Tenders Scraper", theme=gr.themes.Soft()) as app:
    gr.Markdown("# 🏢 Etimad Tenders Scraper")
    
    with gr.Tab("Dashboard"):
        gr.Markdown("### Scraper Control Panel")
        start_btn = gr.Button("🚀 Run Scraper", variant="primary")
        status_text = gr.Textbox(label="Status", interactive=False)
        
        gr.Markdown("### Realtime Logs")
        log_display = gr.Textbox(
            label="Scraping Logs", 
            interactive=False, 
            lines=15,
            max_lines=50
        )
        
        # Refresh button for logs
        log_refresh_btn = gr.Button("🔄 Refresh Logs")
        
    with gr.Tab("View Tenders"):
        gr.Markdown("### Latest Tenders")
        tender_table = gr.Dataframe(
            headers=["Link", "Tender Name", "Tender Number", "Government Entity", 
                     "Status", "Submission Deadline", "Last Updated"],
            datatype=["str", "str", "str", "str", "str", "str", "str"],
            interactive=False,
            wrap=True
        )
        refresh_btn = gr.Button("🔄 Refresh Tenders")
    
    with gr.Tab("Scraping History"):
        gr.Markdown("### Recent Scraping Sessions")
        history_table = gr.Dataframe(
            headers=["ID", "Category", "Subcategory", "Tender Count", 
                     "Status", "Error Message", "Timestamp"],
            datatype=["number", "str", "str", "number", "str", "str", "str"],
            interactive=False
        )
        history_refresh = gr.Button("🔄 Refresh History")
    
    with gr.Tab("Category Settings"):
        gr.Markdown("### Manage Scraping Categories")
        category_dropdown = gr.Dropdown(
            label="Main Category", 
            choices=get_category_options(),
            interactive=True
        )
        subcategory_dropdown = gr.Dropdown(
            label="Subcategories", 
            choices=[],
            interactive=True,
            multiselect=True
        )
        
        # Update subcategories when category changes
        category_dropdown.change(
            get_subcategory_options,
            inputs=category_dropdown,
            outputs=subcategory_dropdown
        )
        
        # Initialize subcategories
        app.load(
            lambda: get_subcategory_options(get_category_options()[0]),
            None,
            subcategory_dropdown
        )
    
    # Set button actions
    start_btn.click(
        start_scraper, 
        None, 
        status_text
    )
    
    # Refresh actions
    log_refresh_btn.click(
        get_logs,
        None,
        log_display
    )
    
    refresh_btn.click(
        get_tenders,
        None,
        tender_table
    )
    
    history_refresh.click(
        get_scraping_history,
        None,
        history_table
    )
    
    # Load initial data
    app.load(get_logs, None, log_display)
    app.load(get_tenders, None, tender_table)
    app.load(get_scraping_history, None, history_table)

# Launch the app
if __name__ == "__main__":
    # Initialize database tables
    db_manager.initialize_table()
    
    # Start the Gradio app
    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True
    )