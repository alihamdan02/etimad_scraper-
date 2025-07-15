import json
import asyncio
import logging
import logging.config
from typing import List, Dict
from playwright.async_api import async_playwright, Page, TimeoutError as PlaywrightTimeoutError
from config import SCRAPER_CONFIG, LOGGING_CONFIG

# Configure logging
logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger("etimad.details")

SECTION_1_FIELDS = [
    "اسم المنافسة", "رقم المنافسة", "الرقم المرجعي", "الغرض من المنافسة",
    "قيمة وثائق المنافسة", "حالة المنافسة", "مدة العقد",
    "هل التأمين من متطلبات المنافسة", "نوع المنافسة", "الجهة الحكوميه"
]

SECTION_2_FIELDS = [
    "آخر موعد لإستلام الإستفسارات", "آخر موعد لتقديم العروض", "تاريخ فتح العروض",
    "تاريخ فحص العروض", "فترة التوقف", "التاريخ المتوقع للترسية",
    "تاريخ بدء الأعمال / الخدمات", "بداية إرسال الأسئلة و الاستفسارات",
    "اقصى مدة للاجابة على الاستفسارات", "مكان فتح العرض"
]

def extract_fields(raw_text: str, keys: List[str]) -> Dict[str, str]:
    lines = raw_text.strip().splitlines()
    result = {}
    i = 0
    while i < len(lines):
        key = lines[i].strip()
        if key in keys and i + 1 < len(lines):
            value = lines[i + 1].strip()
            result[key] = value
            i += 2
        else:
            i += 1
    return result

async def extract_single_tender(page: Page, link: str) -> Dict[str, str]:
    tender = {"Link": link}
    
    for attempt in range(SCRAPER_CONFIG["max_retries"]):
        try:
            logger.debug(f"🌐 Attempt {attempt + 1} - Loading: {link}")
            await page.goto(link, timeout=SCRAPER_CONFIG["timeout"])
            break
        except PlaywrightTimeoutError:
            logger.warning(f"⚠️ Timeout loading {link}, retrying...")
            if attempt == SCRAPER_CONFIG["max_retries"] - 1:
                logger.error(f"❌ Failed after {SCRAPER_CONFIG['max_retries']} attempts: {link}")
                return {"Link": link, "Error": "Timeout after retries"}
        await asyncio.sleep(2 ** attempt)

    try:
        await page.click("a[href='#d-1']")
        await page.wait_for_selector("#d-1", state="visible")
        try:
            show_more = await page.query_selector("#d-1 >> text=عرض المزيد")
            if show_more:
                await show_more.click()
                await page.wait_for_timeout(500)
        except:
            pass

        raw1 = await page.inner_text("#d-1")
        tender.update(extract_fields(raw1, SECTION_1_FIELDS))

        await page.click("a[href='#d-2']")
        await page.wait_for_timeout(1000)
        await page.wait_for_selector("#d-2 >> text=آخر موعد", timeout=5000)
        raw2 = await page.inner_text("#d-2")
        tender.update(extract_fields(raw2, SECTION_2_FIELDS))

        tender["Raw"] = json.dumps(tender, ensure_ascii=False)
        logger.debug(f"✅ Extracted: {tender.get('رقم المنافسة', 'Unknown')}")

        return tender

    except Exception as e:
        logger.error(f"❌ Error extracting fields from {link}: {e}")
        tender["Error"] = str(e)
        return tender

async def extract_all_details(links_with_ids: List[Dict[str, str]]) -> List[Dict[str, str]]:
    semaphore = asyncio.Semaphore(SCRAPER_CONFIG["concurrent_requests"])
    detailed_results = []

    async def process_link(item: Dict[str, str]):
        link = item["Link"]
        keyword_id = item.get("KeyWordID")

        async with semaphore:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=False, timeout=SCRAPER_CONFIG["timeout"])
                context = await browser.new_context()
                page = await context.new_page()
                try:
                    result = await extract_single_tender(page, link)
                    if result:
                        if keyword_id:
                            result["keyword_ids"] = [keyword_id]
                        detailed_results.append(result)
                finally:
                    await context.close()
                    await browser.close()

    total_batches = (len(links_with_ids) + SCRAPER_CONFIG["batch_size"] - 1) // SCRAPER_CONFIG["batch_size"]
    for i in range(0, len(links_with_ids), SCRAPER_CONFIG["batch_size"]):
        batch = links_with_ids[i:i + SCRAPER_CONFIG["batch_size"]]
        logger.info(f"🚀 Processing batch {i // SCRAPER_CONFIG['batch_size'] + 1} of {total_batches}")
        await asyncio.gather(*[process_link(item) for item in batch])

    return detailed_results
