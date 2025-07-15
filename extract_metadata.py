from playwright.async_api import async_playwright
from config import SCRAPER_CONFIG, LOGGING_CONFIG
from db import db_manager
import logging
import logging.config
import asyncio
from typing import List, Dict
import sys
from utils import generate_main_to_sub_mapping

# Fix Windows console encoding for Arabic logs
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger("etimad.metadata")

MAIN_TO_SUB = generate_main_to_sub_mapping()

def get_classification_id(sub_category: str) -> int:
    """Retrieve classification_id for a sub_category from etimad_classifications."""
    try:
        query = """
            SELECT id AS key_word_id, classification_id FROM etimad_classification_keywords 
            WHERE keyword_en = %s OR keyword_ar = %s
            LIMIT 1
        """
        result = db_manager.fetch_all(query, (sub_category, sub_category), dictionary=True)
        return (result[0]['key_word_id'], result[0]['classification_id']) if result else None
    except Exception as e:
        logger.error(f"Error fetching classification_id for {sub_category}: {e}")
        return None

async def extract_metadata(sub_category: str) -> List[Dict[str, str]]:
    logger.info(f"Starting metadata extraction for: {sub_category}")
    results = []

    # Get classification_id for the sub_category
    key_word_id, classification_id = get_classification_id(sub_category)
    for attempt in range(SCRAPER_CONFIG["max_retries"]):
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=False, timeout=SCRAPER_CONFIG["timeout"])
                context = await browser.new_context()
                page = await context.new_page()

                # Retry goto
                for nav_attempt in range(3):
                    try:
                        logger.debug(f"Attempt {nav_attempt + 1}: Navigating to Etimad...")
                        await page.goto("https://tenders.etimad.sa/Tender/AllTendersForVisitor",
                                        # wait_until="networkidle",
                                        timeout=60000)
                        break
                    except Exception as e:
                        logger.warning(f"Navigation attempt {nav_attempt + 1} failed: {e}")
                        if nav_attempt == 2:
                            raise

                # Fill search form
                await page.click("#searchBtnColaps")
                await page.wait_for_selector("#txtMultipleSearch", state="visible")
                await page.fill("#txtMultipleSearch", sub_category)
                await page.click('label:has-text("حالة المنافسة") + div .dropdown-toggle')
                await page.click('div.dropdown-menu.show a:has-text("المنافسات النشطة (تقديم العروض)")')
                await page.click("#searchBtn")
                await page.wait_for_selector("#cardsresult", timeout=SCRAPER_CONFIG["timeout"])
                await page.wait_for_timeout(2000)

                logger.debug("Extracting tender cards...")

                cards = await page.locator("#cardsresult .tender-card").element_handles()

                if not cards:
                    logger.warning(f"No relevant result found for: {sub_category}")
                    db_manager.log_scraping(
                        key_word_id=key_word_id,
                        classification_id=classification_id,
                        count=0,
                        status="success",
                        error="No relevant tenders found"
                    )
                    return [{"Message": "No relevant result found for the search"}]

                seen_links = set()
                for card in cards:
                    try:
                        title_element = await card.query_selector("h3 a, h2 a, a.tender-title")
                        if not title_element:
                            continue

                        title = await title_element.inner_text()
                        href = await title_element.get_attribute("href")
                        if not title or not href:
                            continue

                        full_link = f"https://tenders.etimad.sa{href}" if not href.startswith("http") else href

                        if full_link and full_link not in seen_links:
                            seen_links.add(full_link)
                            results.append({
                                "Title": title.strip(),
                                "Link": full_link.strip(),
                                "SubCategory": sub_category,  # For downstream use
                                "KeyWordID": key_word_id,
                            })
                    except Exception as e:
                        logger.warning(f"Error processing card: {e}")
                        continue

                await browser.close()

                logger.info(f"Found {len(results)} tenders for {sub_category}")
                db_manager.log_scraping(
                    key_word_id=key_word_id,
                    classification_id=classification_id,
                    count=len(results),
                    status="success"
                )
                return results

        except Exception as e:
            logger.error(f"Attempt {attempt + 1} failed: {e}")
            if attempt == SCRAPER_CONFIG["max_retries"] - 1:
                db_manager.log_scraping(
                    key_word_id=key_word_id,
                    classification_id=classification_id,
                    count=0,
                    status="failed",
                    error=str(e)
                )
            await asyncio.sleep(2 ** attempt)

    return []

async def extract_all_metadata() -> List[Dict[str, str]]:
    all_results = []
    tasks = []

    for sub_list in MAIN_TO_SUB.values():
        for sub_cat in sub_list:
            tasks.append(extract_metadata(sub_cat))

    results = await asyncio.gather(*tasks)

    for res in results:
        all_results.extend(res)

    # Deduplicate by link
    unique_results = {item['Link']: item for item in all_results if 'Link' in item}.values()
    logger.info(f"Total unique tenders found: {len(unique_results)}")
    return list(unique_results)