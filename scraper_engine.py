import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import re
from datetime import datetime

class ScraperEngine:
    def __init__(self, headless=True):
        self.headless = headless

    async def scrape_easemytrip(self, origin, destination, departure_date):
        """Scrape EaseMyTrip for flight data."""
        results = []
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=self.headless)
                context = await browser.new_context(
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
                )
                
                page = await context.new_page()
                await Stealth().apply_stealth_async(page)
                
                # Format: DD/MM/YYYY
                formatted_date = departure_date.strftime('%d/%m/%Y')
                
                import sys
                import urllib.parse
                
                # Fetch city names if possible (fallback to codes)
                try:
                    from travel_aggregator import AIRPORTS
                    orig_city = AIRPORTS.get(origin, origin)
                    dest_city = AIRPORTS.get(destination, destination)
                except ImportError:
                    orig_city = origin
                    dest_city = destination
                
                # Construct EaseMyTrip's modern search query, e.g. BOM-Mumbai-India|LGW-London-United Kingdom|28/03/2026
                srch_raw = f"{origin}-{orig_city}-Any|{destination}-{dest_city}-Any|{formatted_date}"
                srch_encoded = urllib.parse.quote(srch_raw)
                
                # The full URL structure
                url = f"https://www.easemytrip.com/flight-search/listing?srch={srch_encoded}&px=1-0-0&cbn=0&ar=undefined&isow=true&isdm=false&lang=en-us&IsDoubleSeat=false&CCODE=IN&curr=INR&apptype=B2C"
                
                print(f"🔍 Scraping EaseMyTrip: {url}")
                await page.goto(url, wait_until="domcontentloaded", timeout=45000)
                
                # Wait for flight rows to load (EaseMyTrip uses different classes for Domestic and Intl)
                try:
                    await page.wait_for_selector(".flt-container, .flt-bx-cont", timeout=20000)
                    # Give an extra second for data to populate
                    await asyncio.sleep(2)
                except:
                    print(f"⚠️  No flight rows found for {origin}-{destination} on {formatted_date}")
                    await browser.close()
                    return []

                # Extract flight data (handle both formats)
                rows = await page.query_selector_all(".flt-container, .flt-bx-cont")
                
                for row in rows[:15]: # Limit to top 15 results
                    try:
                        # Extract airline (.txt-al-n for Domestic, .flt-lg-nm for Intl)
                        airline_el = await row.query_selector(".txt-al-n") or await row.query_selector(".flt-lg-nm") or await row.query_selector(".flt-logo")
                        airline = await airline_el.inner_text() if airline_el else "Unknown"
                        airline = airline.strip()
                        
                        # Extract times
                        dep_time = "--:--"
                        arr_time = "--:--"
                        time_els = await row.query_selector_all(".txt-r2n")
                        if time_els and len(time_els) >= 2: # Domestic
                            dep_time = await time_els[0].inner_text()
                            arr_time = await time_els[1].inner_text()
                        else: # International
                            dep_el = await row.query_selector(".dept-tme")
                            arr_el = await row.query_selector(".arr-nme") or await row.query_selector(".arr-nme span")
                            if dep_el: dep_time = await dep_el.inner_text()
                            if arr_el: arr_time = await arr_el.inner_text()
                        
                        # Extract price (.aln_prc serves Domestic, .final-price serves Intl)
                        price_el = await row.query_selector(".aln_prc") or await row.query_selector(".final-price")
                        price_text = await price_el.inner_text() if price_el else "0"
                        price = int(re.sub(r'[^\d]', '', price_text))
                        
                        # Extract duration (._fntsm for Domestic, .durs or .tme for Intl)
                        dur_el = await row.query_selector("._fntsm") or await row.query_selector(".durs") or await row.query_selector(".tme")
                        duration_text = await dur_el.inner_text() if dur_el else "0h 0m"
                        iso_duration = self._convert_to_iso_duration(duration_text)
                        
                        # Extract stops (.txt-r4n for Domestic, .stp for Intl)
                        stops_el = await row.query_selector(".txt-r4n") or await row.query_selector(".stp")
                        stops_text = await stops_el.inner_text() if stops_el else "0"
                        stops = 0 if "non" in stops_text.lower() else int(re.search(r'\d+', stops_text).group()) if re.search(r'\d+', stops_text) else 0

                        results.append({
                            'source': 'EaseMyTrip (Scraped)',
                            'type': 'Flight',
                            'origin': origin,
                            'destination': destination,
                            'departure_date': departure_date.strftime('%Y-%m-%d'),
                            'airline': airline,
                            'price': float(price),
                            'currency': 'INR',
                            'departure_time': dep_time,
                            'arrival_time': arr_time,
                            'duration': iso_duration,
                            'stops': stops,
                            'cabin_class': 'ECONOMY',
                            'booking_url': url
                        })
                    except Exception as e:
                        print(f"⚠️  Error parsing row: {e}")
                        continue

                await browser.close()
                print(f"✅ EaseMyTrip: {len(results)} flights scraped")
                return results

        except Exception as e:
            print(f"❌ Scraping error: {e}")
            return []

    def _convert_to_iso_duration(self, text):
        """Convert '2h 30m' to 'PT2H30M'."""
        h = re.search(r'(\d+)h', text)
        m = re.search(r'(\d+)m', text)
        hours = h.group(1) if h else "0"
        mins = m.group(1) if m else "0"
        return f"PT{hours}H{mins}M"

if __name__ == "__main__":
    # Test script
    import asyncio
    from datetime import datetime
    scraper = ScraperEngine(headless=False)
    asyncio.run(scraper.scrape_easemytrip("BOM", "LGW", datetime.strptime("28/03/2026", "%d/%m/%Y")))
