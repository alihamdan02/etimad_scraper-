import mysql.connector
from mysql.connector import pooling, Error
from config import MYSQL_CONFIG, LOGGING_CONFIG
import logging
import logging.config

logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger("etimad.db")

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

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tenders (
                    `Link` TEXT,
                    `اسم_المنافسة` TEXT,
                    `رقم_المنافسة` VARCHAR(255) PRIMARY KEY,
                    `الرقم_المرجعي` VARCHAR(255),
                    `الغرض_من_المنافسة` TEXT,
                    `قيمة_وثائق_المنافسة` VARCHAR(255),
                    `حالة_المنافسة` VARCHAR(255),
                    `مدة_العقد` VARCHAR(255),
                    `هل_التأمين_من_متطلبات_المنافسة` VARCHAR(255),
                    `نوع_المنافسة` VARCHAR(255),
                    `الجهة_الحكوميه` TEXT,
                    `آخر_موعد_لإستلام_الإستفسارات` VARCHAR(255),
                    `آخر_موعد_لتقديم_العروض` VARCHAR(255),
                    `تاريخ_فتح_العروض` VARCHAR(255),
                    `تاريخ_فحص_العروض` VARCHAR(255),
                    `فترة_التوقف` VARCHAR(255),
                    `التاريخ_المتوقع_للترسية` VARCHAR(255),
                    `تاريخ_بدء_الأعمال_الخدمات` VARCHAR(255),
                    `بداية_إرسال_الأسئلة_و_الاستفسارات` VARCHAR(255),
                    `اقصى_مدة_للاجابة_على_الاستفسارات` VARCHAR(255),
                    `مكان_فتح_العرض` TEXT,
                    `Raw` JSON,
                    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FULLTEXT (`اسم_المنافسة`, `الغرض_من_المنافسة`)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS scraping_logs (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    category VARCHAR(255),
                    subcategory VARCHAR(255),
                    tender_count INT,
                    status VARCHAR(50),
                    error_message TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            conn.commit()
            logger.info("Database tables initialized")
        except Error as e:
            logger.error(f"Error initializing tables: {e}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()

    def upsert_tender(self, tender):
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            # Delete existing tender by primary key
            cursor.execute("DELETE FROM tenders WHERE رقم_المنافسة = %s", (tender["رقم_المنافسة"],))

            keys = [k for k in tender.keys() if k not in ["created_at", "updated_at"]]
            values = [tender[k] for k in keys]

            placeholders = ", ".join(["%s"] * len(keys))
            columns = ", ".join(f"`{k}`" for k in keys)
            update_clause = ", ".join([f"`{k}`=VALUES(`{k}`)" for k in keys if k != "رقم_المنافسة"])

            sql = f"""
                INSERT INTO tenders ({columns})
                VALUES ({placeholders})
                ON DUPLICATE KEY UPDATE {update_clause}
            """

            cursor.execute(sql, values)
            conn.commit()
            logger.debug(f"Upserted tender: {tender.get('رقم_المنافسة', 'Unknown')}")
        except Error as e:
            logger.error(f"Error upserting tender: {e}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()

    def log_scraping(self, category, subcategory, count, status, error=None, note=None):
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            sql = """
                INSERT INTO scraping_logs 
                (category, subcategory, tender_count, status, error_message)
                VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(sql, (category, subcategory, count, status, error or note))
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
