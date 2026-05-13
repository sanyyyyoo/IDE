# src/core/scraping/scrape_and_classify.py
import asyncio
from playwright.async_api import async_playwright
import json
import re
import pandas as pd
from typing import List, Dict
from collections import OrderedDict
from pathlib import Path
import logging
from src.core.ml.hybrid_classifier import GoogleMapsDataProcessor
from src.core.ml.utils import normalize_phone, normalize_address, normalize_name, normalize_category

# -----------------------------------------------------------
# Setup Logging
# -----------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger(__name__)

# -----------------------------------------------------------
# Scraping Categories
# -----------------------------------------------------------
categories = [
    "General store", "Grocery store", "Chemist shop", "Medical store", "Electronics Store", "Furniture shop", 
    "Sofa Shop", "Curtains Shop", "Clothing Shop", "Garments Shop", "Hardware Shop", "Tiles Shop", "Plywood Shop", "Decorative items Shop",
    "Footwear Shop", "Paint Shop", "Gas stove Shop", "Ro Filter Shop", "Utensils Shop", "Stationery Shop", "Sweets Shop",
    "Cakes and Bakery Shop", "Vet Shop", "Pet Shop", "Veterinary Medicine shops", "Labs", "Diagnostic Centres"
]

# -----------------------------------------------------------
# Filtering & Extraction Utilities
# -----------------------------------------------------------
def is_valid_text(text: str) -> bool:
    if not text or len(text.strip()) < 3:
        return False
    bad_keywords = ['open', 'review', 'rating', 'closes', '24 hours', 'today', 'tomorrow', 'hrs']
    return not any(kw in text.lower() for kw in bad_keywords)

def extract_phone(text: str) -> str:
    match = re.search(r"\+?\d[\d\s\-]{7,}", text)
    return match.group(0).strip() if match else ""

# -----------------------------------------------------------
# Scraper Core
# -----------------------------------------------------------
async def scrape_google_maps(search_query: str, search_category: str, limit: int = None) -> List[Dict]:
    """Scrape Google Maps asynchronously for a single category."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        query = search_query.replace(" ", "+")
        url = f"https://www.google.com/maps/search/{query}/"
        logger.info(f"🌐 Opening {url}")
        await page.goto(url, timeout=60000)
        await page.wait_for_timeout(5000)

        collected = set()
        retries = 0

        while True:
            results = await page.evaluate("""
                () => {
                    const cards = Array.from(document.querySelectorAll('.Nv2PK'));
                    return cards.map(card => {
                        const name = card.querySelector('.qBF1Pd')?.textContent.trim() || '';
                        const addressSpans = card.querySelectorAll('.W4Efsd span');
                        let address = '';
                        for (const span of addressSpans) {
                            const addr = span.textContent.trim();
                            // Exclude if address looks like a phone number
                            if (
                                addr &&
                                addr.length > 5 &&
                                addr.split(' ').length > 2 &&
                                !/^[\\d\\s\\-\\+]+$/.test(addr)
                            ) {
                                address = addr;
                                break;
                            }
                        }
                        const phone = card.querySelector('.UsdlK')?.textContent.trim() || '';
                        return { name, address, phone };
                    });
                }
            """)

            before = len(collected)
            for item in results:
                # Always set category to searched category
                item['category'] = search_category
                
                # Validate address - must be valid text and longer than 5 chars
                item['address'] = item['address'] if is_valid_text(item['address']) and len(item['address']) > 5 else ''
                
                # Add to collected set (using JSON for deduplication)
                collected.add(json.dumps(item, sort_keys=True))

            scrollable = await page.query_selector('div[role="feed"]')
            if scrollable:
                await scrollable.evaluate('(el) => el.scrollBy(0, 1000)')
                await page.wait_for_timeout(2000)
            else:
                break

            if len(collected) == before:
                retries += 1
                if retries > 3:
                    break
            else:
                retries = 0

        await browser.close()
        logger.info(f"✅ Collected {len(collected)} listings for {search_category}")
        return [json.loads(item) for item in collected]

# -----------------------------------------------------------
# Scrape + Classify
# -----------------------------------------------------------
async def scrape_multiple_categories(city: str, processor: GoogleMapsDataProcessor, categories_list: List[str] = None, limit: int = None) -> pd.DataFrame:
    all_data = []
    
    # Use provided categories or fall back to global categories
    cats_to_scrape = categories_list if categories_list else categories

    for cat in cats_to_scrape:
        logger.info(f"🔍 Scraping: {cat} in {city}")
        results = await scrape_google_maps(f"{cat} in {city}", cat, limit=None)
        all_data.extend(results)

    if not all_data:
        logger.warning("⚠️ No data scraped. Please check selectors or network.")
        return pd.DataFrame()

    logger.info("🧠 Running hybrid classifier on scraped data...")
    # Process with ML model to classify name, address, phone (category is already set)
    processed = processor.process_scraped_data(all_data)

    cleaned_data = []
    for item in processed:
        classified = item["classified_data"]
        # Extract classified fields
        name = classified.get("name", "").strip()
        address = classified.get("address", "").strip()
        phone = classified.get("phone", "")
        category = classified.get("category", "")  # This is the search category
        
        # Validate name - should not be an address fragment
        if name:
            # Check if name looks like an address (common patterns)
            name_lower = name.lower()
            invalid_name_patterns = [
                r'^shop\s*no',  # "Shop No", "Shop no"
                r'^[G/]?\d+[,\s]',  # Starts with number like "G/3, " or "21, "
                r'^no\.?\s*\d+',  # "No. 22" or "No 22"
                r'station\s*[rR]$',  # "Station R"
                r'^[a-z]+\s*[rR]$',  # Single letter at end
            ]
            if any(re.search(pattern, name_lower) for pattern in invalid_name_patterns):
                # If name is invalid and address is valid, swap them
                if address and len(address) > 5:
                    name, address = address, name
                    logger.info(f"🔄 Fixed invalid name: swapped '{name}' with '{address}'")
                else:
                    # Skip this entry if name is invalid and no valid address
                    continue
        
        # Only skip if name is completely empty or too short
        if not name or len(name) < 3:
            continue
        
        cleaned_data.append({
            "name": normalize_name(name),
            "address": normalize_address(address),
            "phone": normalize_phone(phone),
            "category": category  # Use search category directly
        })

    df = pd.DataFrame(cleaned_data)
    
    # Filter out entries without phone numbers
    df = df[df['phone'].notna() & (df['phone'].str.strip() != '')]
    
    # Remove duplicates based on name and phone
    df = df.drop_duplicates(subset=['name', 'phone']).reset_index(drop=True)
    
    logger.info(f"✅ Classification complete. {len(df)} valid records.")
    return df

# -----------------------------------------------------------
# Entry Point
# -----------------------------------------------------------
def run_scraper(city: str, model_path: str, output_file: str, selected_categories: List[str] = None, limit: int = None):
    """Main entry: Scrape, classify, normalize, and save.
    
    Args:
        city: City name to scrape
        model_path: Path to the DistilBERT model
        output_file: Output file path (CSV or XLSX)
        selected_categories: List of categories to scrape (uses global categories if None)
        limit: (Deprecated) No longer used - scrapes all available results
    """
    from src.core.ml.hybrid_classifier import GoogleMapsDataProcessor
    import os

    logger.info(f"🏙️ Starting scraping for city: {city}")
    if selected_categories:
        logger.info(f"📋 Categories to scrape: {', '.join(selected_categories)}")
    processor = GoogleMapsDataProcessor(model_path)

    df = asyncio.run(scrape_multiple_categories(city, processor, categories_list=selected_categories, limit=None))

    if df.empty:
        logger.warning("❌ No valid data to save.")
        return

    os.makedirs(os.path.dirname(output_file) or ".", exist_ok=True)
    
    # Save based on file extension
    if output_file.lower().endswith('.xlsx'):
        df.to_excel(output_file, index=False)
    else:
        df.to_csv(output_file, index=False)
    
    logger.info(f"💾 Saved {len(df)} entries to {output_file}")

# -----------------------------------------------------------
# Debug run
# -----------------------------------------------------------
# -----------------------------------------------------------
# Debug run
# -----------------------------------------------------------
if __name__ == "__main__":
    import os

    # ✅ Read model path from environment or fallback
    model_path = os.getenv(
        "MODEL_PATH",
        "C:/Users/PMCC/Desktop/IDE/models/distilbert_finetuned"
    )

    print(f"[MODEL] 🔍 Using DistilBERT model from:\n    {model_path}")

    run_scraper(
        city="New Delhi",
        model_path=model_path,
        output_file="output/test_grocery_log.csv",
        selected_categories=None,  # Uses global categories
        limit=12
    )

