import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import time

async def test():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=['--disable-http2'])
        context = await browser.new_context(user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36')
        page = await context.new_page()
        await Stealth().apply_stealth_async(page)
        
        url = "https://www.cleartrip.com/flights/international/results?adults=1&childs=0&infants=0&class=Economy&depart_date=10%2F04%2F2026&from=BOM&to=LGW&origin=BOM%20-%20Mumbai%2C%20IN&destination=LGW%20-%20London%2C%20GB&intl=y&isCfw=false&rnd_one=O&isFF=true"
        print("Navigating...")
        await page.goto(url, wait_until="domcontentloaded", timeout=60000)
        await asyncio.sleep(10)
        
        # Check elements
        cards = await page.query_selector_all("div.sc-bYTeLD, div[class*='krEXgg'], div.sc-aXZVg.bg-white.br-12, div.bg-white.br-12.ba-solid")
        print(f"Found {len(cards)} cards")
        
        if len(cards) == 0:
            print("Trying broader query. Looking for any element with INR symbol and digits...")
            prices = await page.query_selector_all("p")
            for p_tag in prices[:50]:
                try:
                    text = await p_tag.inner_text()
                    cls = await p_tag.get_attribute("class")
                    if text and "₹" in text:
                        print(f"Class: {cls} | Text: {text.strip()}")
                except:
                    pass
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test())
