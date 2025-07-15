import asyncio
from typing import List, Dict
from tqdm import tqdm
from db import db_manager
from extract_metadata import extract_all_metadata
from extract_details import extract_all_details
from config import LOGGING_CONFIG, SCRAPER_CONFIG
import logging
import logging.config

logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger("etimad.orchestrator")

class ScraperOrchestrator:
    def __init__(self):
        self.db = db_manager
        self.db.initialize_table()

    def normalize_tender_keys(self, tender: Dict[str, str]) -> Dict[str, str]:
        return {k.replace(" ", "_"): v for k, v in tender.items()}

    async def run_pipeline(self) -> None:
        try:
            logger.info("Starting metadata collection phase")
            metadata = await extract_all_metadata()

            if not metadata:
                logger.warning("No metadata found - aborting pipeline")
                return

            logger.info("Starting detail extraction phase")
            details = await extract_all_details(metadata)

            logger.info("Starting data persistence phase")
            success_count = 0
            for tender in tqdm(details, desc="Saving tenders"):
                if not tender:
                    logger.warning("Empty tender skipped")
                    continue
                try:
                    normalized = self.normalize_tender_keys(tender)
                    self.db.upsert_tender(normalized)
                    success_count += 1
                except Exception as e:
                    logger.error(f"Failed to save tender: {tender.get('رقم المنافسة', 'UNKNOWN')}. Error: {e}")

            logger.info(f"✅ Pipeline completed. Successfully saved {success_count}/{len(details)} tenders")

        except Exception as e:
            logger.error(f"Pipeline failed: {str(e)}")
            raise

if __name__ == "__main__":
    orchestrator = ScraperOrchestrator()
    asyncio.run(orchestrator.run_pipeline())
