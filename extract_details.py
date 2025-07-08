import json
import asyncio
from playwright.async_api import async_playwright
from config import SCRAPER_CONFIG, LOGGING_CONFIG
from db import db_manager
import logging
import logging.config
from typing import List, Dict, Optional

logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger("etimad.details")

SECTION_1_FIELDS = [
    "اسم المنافسة", "رقم المنافسة", "الرقم المرجعي", 
    "الغرض من المنافسة", "قيمة وثائق المنافسة",
    "حالة المنافسة", "مدة العقد", 
    "هل التأمين من متطلبات المنافسة", 
    "نوع المنافسة", "الجهة الحكوميه"
]

SECTION_2_FIELDS = [
    "آخر موعد لإستلام الإستفسارات",
    "آخر موعد لتقديم العروض",
    "تاريخ فتح العروض",
    "تاريخ فحص العروض",
    "فترة التوقف",
    "التاريخ المتوقع للترسية",
    "تاريخ بدء الأعمال / الخدمات",
    "بداية إرسال الأسئلة و الاستفسارات",
    "اقصى مدة للاجابة على الاستفسارات",
    "مكان فتح العرض"
]

def extract_fields(raw_text: str, keys: List[str]) -> Dict[str, str]:
    result = {}
    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
    
    for i in range(len(lines)):
        if lines[i] in keys and i + 1 < len(lines):
            result[lines[i]] = lines[i + 1]
    
    return result

async def extract_single_tender(page, link: str) -> Optional[Dict[str, str]]:
    tender = {"Link": link}
    
    for attempt in range(SCRAPER_CONFIG["max_retries"]):
        try:
            await page.goto(
                link, 
                # wait_until="networkidle",
                timeout=SCRAPER_CONFIG["timeout"]
            )
            
            # Section 1
            await page.click("a[href='#d-1']")
            raw1 = await page.inner_text("#d-1")
            tender.update(extract_fields(raw1, SECTION_1_FIELDS))
            
            # Section 2
            await page.click("a[href='#d-2']")
            raw2 = await page.inner_text("#d-2")
            tender.update(extract_fields(raw2, SECTION_2_FIELDS))
            
            # Add raw JSON
            tender["Raw"] = json.dumps(tender, ensure_ascii=False)
            
            logger.debug(f"Extracted tender: {tender.get('رقم المنافسة', 'Unknown')}")
            return tender
            
        except Exception as e:
            logger.warning(f"Attempt {attempt + 1} failed for {link}: {str(e)}")
            if attempt == SCRAPER_CONFIG["max_retries"] - 1:
                logger.error(f"Failed to extract {link} after {SCRAPER_CONFIG['max_retries']} attempts")
                return None
            await asyncio.sleep(2 ** attempt)

async def extract_all_details(links: List[str]) -> List[Dict[str, str]]:
    semaphore = asyncio.Semaphore(SCRAPER_CONFIG["concurrent_requests"])
    detailed = []
    
    async def process_link(link):
        async with semaphore:
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=False,
                    timeout=SCRAPER_CONFIG["timeout"]
                )
                context = await browser.new_context()
                page = await context.new_page()
                
                try:
                    result = await extract_single_tender(page, link)
                    if result:
                        detailed.append(result)
                finally:
                    await context.close()
                    await browser.close()
    
    # Process in batches
    for i in range(0, len(links), SCRAPER_CONFIG["batch_size"]):
        batch = links[i:i + SCRAPER_CONFIG["batch_size"]]
        logger.info(f"Processing batch {i//SCRAPER_CONFIG['batch_size'] + 1} of {len(links)//SCRAPER_CONFIG['batch_size'] + 1}")
        
        await asyncio.gather(*[process_link(link) for link in batch])
    
    return detailed
