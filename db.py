import mysql.connector
from mysql.connector import pooling, Error
from config import MYSQL_CONFIG, LOGGING_CONFIG
import logging
import logging.config
import re
from datetime import datetime
from typing import Dict, List


logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger("etimad.db")

def parse_arabic_datetime(value: str) -> datetime:
    """
    Extract Gregorian date and time (if exists) from Arabic Etimad string,
    convert to datetime object. Ignores Hijri date. Returns None for invalid or 'لا يوجد'.
    """
    if not value or not isinstance(value, str) or value.strip() == "لا يوجد":
        return None

    match = re.search(r'(\d{2}/\d{2}/\d{4})(?:\s+(\d{1,2}:\d{2}\s*(?:AM|PM)?))?', value)
    if not match:
        return None

    date_part = match.group(1)
    time_part = match.group(2) or "00:00"

    try:
        if "AM" in time_part or "PM" in time_part:
            dt = datetime.strptime(f"{date_part} {time_part}", "%d/%m/%Y %I:%M %p")
        else:
            dt = datetime.strptime(f"{date_part} {time_part}", "%d/%m/%Y %H:%M")
        return dt
    except ValueError:
        return None
    
def parse_decimal(value: str) -> float:
    """
    Convert a string to a DECIMAL-compatible float. Handles 'مجانا' as 0.0.
    Returns None for invalid values.
    """
    if not value or not isinstance(value, str) or value.strip() == "مجانا":
        return 0.0
    try:
        cleaned_value = re.sub(r'[^\d.]', '', value)
        return float(cleaned_value)
    except (ValueError, TypeError):
        return None

class DatabaseManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_pool()
        return cls._instance

    def _init_pool(self):
        try:
            self.connection_pool = pooling.MySQLConnectionPool(
                pool_name=MYSQL_CONFIG["pool_name"],
                pool_size=MYSQL_CONFIG["pool_size"],
                **{k: v for k, v in MYSQL_CONFIG.items()
                   if k not in ["pool_size", "pool_name"]}
            )
            logger.info("Database connection pool initialized")
        except Error as e:
            logger.error(f"Error initializing connection pool: {e}")
            raise

    def get_connection(self):
        try:
            return self.connection_pool.get_connection()
        except Error as e:
            logger.error(f"Error getting connection: {e}")
            raise

    def initialize_table(self):
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            # Create etimad_classifications table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS etimad_classifications (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    unit ENUM ('Data & Innovation', 'SAP', 'MANA Services', 'other') DEFAULT 'other' NOT NULL,
                    name_en VARCHAR(255) NOT NULL,
                    name_ar VARCHAR(255),
                    description TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)

            # Create etimad_classification_keywords table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS etimad_classification_keywords (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    classification_id INT NOT NULL,
                    keyword_en VARCHAR(255) NOT NULL,
                    keyword_ar VARCHAR(255),
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (classification_id) REFERENCES etimad_classifications(id)
                        ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)

            # Create tenders table with keyword_id column
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tenders (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    link VARCHAR(255) NOT NULL,
                    tender_name VARCHAR(255) NOT NULL,
                    tender_number VARCHAR(50) NOT NULL UNIQUE,
                    reference_number VARCHAR(50),
                    purpose TEXT,
                    document_value DECIMAL(10, 2),
                    status VARCHAR(50) NOT NULL,
                    status_company ENUM ('Under Evaluation', 'Under Development', 'Submitted', 'Technical DiscQ', 'Financial DiscQ', 'Won') NOT NULL DEFAULT 'Under Evaluation',
                    contract_duration VARCHAR(50),
                    insurance_required ENUM('نعم', 'لا') DEFAULT 'لا',
                    tender_type VARCHAR(50) NOT NULL DEFAULT 'منافسة عامة',
                    government_entity VARCHAR(255) NOT NULL,
                    last_query_date DATETIME,
                    last_submission_date DATETIME,
                    opening_date DATETIME,
                    evaluation_date DATETIME,
                    suspension_period INT,
                    expected_award_date DATETIME,
                    start_date DATETIME,
                    question_start_date DATETIME,
                    max_query_response_time INT,
                    opening_location TEXT,
                    attachment VARCHAR(255) DEFAULT NULL,
                    keyword_id INT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (keyword_id) REFERENCES etimad_classification_keywords(id) ON DELETE SET NULL
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)

            # Create scraping_logs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS scraping_logs (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    key_word_id INT,
                    classification_id INT,
                    tender_count INT NOT NULL,
                    status VARCHAR(50) NOT NULL,
                    error_message TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (key_word_id) REFERENCES etimad_classification_keywords(id) ON DELETE SET NULL,
                    FOREIGN KEY (classification_id) REFERENCES etimad_classifications(id) ON DELETE SET NULL
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)

            # Drop the old tender_keywords table if it exists
            cursor.execute("DROP TABLE IF EXISTS tender_keywords")

            conn.commit()
            logger.info("Database tables initialized with new schema")
        except Error as e:
            logger.error(f"Error initializing tables: {e}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()

    def execute_query(self, query, params=None):
        """Execute a single SQL query (INSERT/UPDATE/DELETE)"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(query, params or ())
            conn.commit()
            return cursor.rowcount
        except Error as e:
            logger.error(f"Error executing query: {e}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()

    def execute_many(self, query, params_list):
        """Execute multiple SQL statements with different parameters"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.executemany(query, params_list)
            conn.commit()
            return cursor.rowcount
        except Error as e:
            logger.error(f"Error executing many queries: {e}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()

    def fetch_all(self, query, params=None, dictionary=False):
        """Fetch all rows from a SELECT query"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor(dictionary=dictionary)
            cursor.execute(query, params or ())
            return cursor.fetchall()
        except Error as e:
            logger.error(f"Error fetching data: {e}")
            raise
        finally:
            if conn:
                conn.close()

    def upsert_tender(self, tender):
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            key_mapping = {
                "رقم_المنافسة": "tender_number",
                "اسم_المنافسة": "tender_name",
                "الرقم_المرجعي": "reference_number",
                "الغرض_من_المنافسة": "purpose",
                "قيمة_وثائق_المنافسة": "document_value",
                "حالة_المنافسة": "status",
                "مدة_العقد": "contract_duration",
                "هل_التأمين_من_متطلبات_المنافسة": "insurance_required",
                "نوع_المنافسة": "tender_type",
                "الجهة_الحكوميه": "government_entity",
                "آخر_موعد_لإستلام_الإستفسارات": "last_query_date",
                "آخر_موعد_لتقديم_العروض": "last_submission_date",
                "تاريخ_فتح_العروض": "opening_date",
                "تاريخ_فحص_العروض": "evaluation_date",
                "فترة_التوقف": "suspension_period",
                "التاريخ_المتوقع_للترسية": "expected_award_date",
                "تاريخ_بدء_الأعمال_/_الخدمات": "start_date",
                "بداية_إرسال_الأسئلة_و_الاستفسارات": "question_start_date",
                "اقصى_مدة_للاجابة_على_الاستفسارات": "max_query_response_time",
                "مكان_فتح_العرض": "opening_location",
                "Link": "link"
            }

            mapped_tender = {}
            for arabic_key, english_key in key_mapping.items():
                if arabic_key in tender:
                    value = tender[arabic_key]
                    mapped_tender[english_key] = value
                    
            mapped_tender.setdefault("attachment", None)
            mapped_tender.setdefault("status_company", "Under Evaluation")
            mapped_tender.setdefault("created_at", datetime.now())
            
            if "document_value" in mapped_tender:
                if mapped_tender["document_value"] == "مجانا":
                    mapped_tender["document_value"] = 0.0
                elif isinstance(mapped_tender["document_value"], str):
                    try:
                        mapped_tender["document_value"] = float(mapped_tender["document_value"])
                    except ValueError:
                        mapped_tender["document_value"] = 0.0
            
            date_fields = ["last_query_date", "last_submission_date", "opening_date", 
                        "evaluation_date", "expected_award_date", "start_date", "question_start_date"]
            for field in date_fields:
                if field in mapped_tender:
                    if mapped_tender[field] == "لا يوجد":
                        mapped_tender[field] = None
                    else:
                        mapped_tender[field] = parse_arabic_datetime(mapped_tender[field])

            # Get keyword_id from SubCategory if available
            if "keyword_ids" in tender:
                mapped_tender["keyword_id"] = tender["keyword_ids"][0]


            keys = mapped_tender.keys() 
            values = [mapped_tender[k] for k in keys]

            cursor.execute("DELETE FROM tenders WHERE tender_number = %s", (mapped_tender["tender_number"],))

            placeholders = ", ".join(["%s"] * len(keys))
            columns = ", ".join(f"`{k}`" for k in keys)
            update_clause = ", ".join([f"`{k}`=VALUES(`{k}`)" for k in keys if k != "tender_number"])

            sql = f"""
                INSERT INTO tenders ({columns})
                VALUES ({placeholders})
                ON DUPLICATE KEY UPDATE {update_clause}
            """
            
            cursor.execute(sql, values)
            conn.commit()
            logger.debug(f"Upserted tender: {mapped_tender.get('tender_number', 'Unknown')}")
        except Error as e:
            logger.error(f"Error upserting tender: {e}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()


    def log_scraping(self, key_word_id=None, classification_id=None, count=0, status="unknown", error=None, note=None):
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            sql = """
                INSERT INTO scraping_logs 
                (key_word_id, classification_id, tender_count, status, error_message)
                VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(sql, (key_word_id, classification_id, count, status, error or note))
            conn.commit()
        except Error as e:
            logger.error(f"Error logging scraping: {e}")
            if conn:
                conn.rollback()
        finally:
            if conn:
                conn.close()

# Singleton instance
db_manager = DatabaseManager()
db_manager.initialize_table()