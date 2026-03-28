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
                
                # Wait for flight rows (EaseMyTrip uses different classes for Domestic and Intl)
                try:
                    await page.wait_for_selector(".flt-container, .flt-bx-cont, .nw_listing_bx", timeout=20000)
                    # Give an extra second for data to populate
                    await asyncio.sleep(2)
                except:
                    print(f"⚠️  No flight rows found for {origin}-{destination} on {formatted_date}")
                    await browser.close()
                    return []

                # Extract flight data (handle both formats)
                rows = await page.query_selector_all(".flt-container, .flt-bx-cont, .nw_listing_bx")
                
                for row in rows[:15]: # Limit to top 15 results
                    try:
                        # Extract airline
                        # Selectors: .txt-al-n (Old Dom), .flt-lg-nm (Intl), .air_nmm_txt h6 (New Dom)
                        airline_el = (await row.query_selector(".air_nmm_txt h6") or 
                                      await row.query_selector(".txt-al-n") or 
                                      await row.query_selector(".flt-lg-nm") or 
                                      await row.query_selector(".flt-logo"))
                        airline = await airline_el.inner_text() if airline_el else "Unknown"
                        airline = airline.strip()
                        
                        # Extract times
                        dep_time = "--:--"
                        arr_time = "--:--"
                        
                        # New Domestic Pattern
                        new_dep_el = await row.query_selector(".tm_lc.texrgt h4")
                        new_arr_el = await row.query_selector(".tm_lc:not(.texrgt) h4")
                        
                        if new_dep_el and new_arr_el:
                            dep_time = await new_dep_el.inner_text()
                            arr_time = await new_arr_el.inner_text()
                        else:
                            # Fallback to older patterns
                            time_els = await row.query_selector_all(".txt-r2n")
                            if time_els and len(time_els) >= 2: # Domestic
                                dep_time = await time_els[0].inner_text()
                                arr_time = await time_els[1].inner_text()
                            else: # International
                                dep_el = await row.query_selector(".dept-tme")
                                arr_el = await row.query_selector(".arr-nme") or await row.query_selector(".arr-nme span")
                                if dep_el: dep_time = await dep_el.inner_text()
                                if arr_el: arr_time = await arr_el.inner_text()
                        
                        # Extract price
                        # Selectors: .aln_prc (Old Dom), .final-price (Intl), .flt_prc (New Dom)
                        price_el = (await row.query_selector(".flt_prc") or 
                                    await row.query_selector(".aln_prc") or 
                                    await row.query_selector(".final-price"))
                        price_text = await price_el.inner_text() if price_el else "0"
                        price = int(re.sub(r'[^\d]', '', price_text))
                        
                        # Extract duration
                        dur_el = (await row.query_selector(".dur_nmm") or 
                                  await row.query_selector("._fntsm") or 
                                  await row.query_selector(".durs") or 
                                  await row.query_selector(".tme"))
                        duration_text = await dur_el.inner_text() if dur_el else "0h 0m"
                        iso_duration = self._convert_to_iso_duration(duration_text)
                        
                        # Extract stops
                        stops_el = (await row.query_selector(".stp_nmm") or 
                                    await row.query_selector(".txt-r4n") or 
                                    await row.query_selector(".stp"))
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
                            'departure_time': dep_time.strip(),
                            'arrival_time': arr_time.strip(),
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

    async def scrape_makemytrip(self, origin, destination, departure_date):
        """Scrape MakeMyTrip for flight data."""
        results = []
        max_retries = 2
        
        # Detect if it's international (MMT needs intl=true for non-India routes)
        domestic_iac = ["BOM", "DEL", "BLR", "MAA", "CCU", "HYD", "GOI", "PNQ", "JAI", "AMD", "COK"]
        is_intl = "true" if origin not in domestic_iac or destination not in domestic_iac else "false"
        formatted_date = departure_date.strftime('%d/%m/%Y')
        url = f"https://www.makemytrip.com/flight/search?itinerary={origin}-{destination}-{formatted_date}&tripType=O&paxType=A-1_C-0_I-0&intl={is_intl}&cabinClass=E&lang=eng"

        for attempt in range(max_retries):
            try:
                async with async_playwright() as p:
                    # Disable HTTP/2 to prevent net::ERR_HTTP2_PROTOCOL_ERROR which is common with Akamai/bot detection
                    browser = await p.chromium.launch(
                        headless=self.headless,
                        args=['--disable-http2']
                    )
                    context = await browser.new_context(
                        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
                        viewport={'width': 1280, 'height': 800}
                    )
                    
                    page = await context.new_page()
                    await Stealth().apply_stealth_async(page)
                    
                    print(f"🔍 Scraping MakeMyTrip (Attempt {attempt+1}): {url}")
                    
                    try:
                        # Use a longer timeout and wait_until="load" for better stability
                        await page.goto(url, wait_until="load", timeout=60000)
                    except Exception as e:
                        if "ERR_HTTP2_PROTOCOL_ERROR" in str(e) or "ERR_CONNECTION_CLOSED" in str(e):
                            print(f"⚠️  Protocol error on MMT, retrying... ({e})")
                            await browser.close()
                            continue
                        raise e

                    # Wait a bit for the modal to potentially appear
                    await asyncio.sleep(3)
                    
                    # Robust Modal Handling
                    try:
                        # Multiple possible close selectors for MMT modals
                        close_selectors = [".commonModal__close", ".overlayCrossIconV2", ".newCrossIconV2", ".close", ".ic_close", "[class*='close']"]
                        for selector in close_selectors:
                            if await page.query_selector(selector):
                                await page.click(selector)
                                print(f"✅ Dismissed modal using {selector}")
                                await asyncio.sleep(1)
                                break
                    except:
                        pass

                    # Direct interaction to wake up the page if needed
                    await page.mouse.move(100, 100)
                    await page.mouse.wheel(0, 500)
                    await asyncio.sleep(1)

                    # Wait for flight cards
                    try:
                        await page.wait_for_selector(".listingCard", timeout=25000)
                    except:
                        # Fallback: check if the page actually loaded results or an empty state
                        if await page.query_selector(".noFlights"):
                            print(f"ℹ️  MMT reported no flights for {origin}-{destination}")
                            await browser.close()
                            return []
                        
                        print(f"⚠️  Timeout waiting for .listingCard on MMT")
                        # Take a screenshot for debugging if not headless or if user can see logs
                        # await page.screenshot(path="mmt_error.png")
                        await browser.close()
                        continue

                    # Extract data
                    cards = await page.query_selector_all(".listingCard")
                    
                    for card in cards[:15]:
                        try:
                            airline_el = await card.query_selector(".airlineName")
                            airline = await airline_el.inner_text() if airline_el else "Unknown"
                            
                            price_el = await card.query_selector(".clusterViewPrice span")
                            price_text = await price_el.inner_text() if price_el else "0"
                            price = int(re.sub(r'[^\d]', '', price_text))
                            
                            time_els = await card.query_selector_all(".flightTimeInfo span")
                            dep_time = await time_els[0].inner_text() if len(time_els) > 0 else "--:--"
                            arr_time = await time_els[1].inner_text() if len(time_els) > 1 else "--:--"
                            
                            dur_el = await card.query_selector(".stop-info p")
                            duration_text = await dur_el.inner_text() if dur_el else "0h 0m"
                            iso_duration = self._convert_to_iso_duration(duration_text)
                            
                            stops_el = await card.query_selector(".flightsLayoverInfo")
                            stops_text = await stops_el.inner_text() if stops_el else "0"
                            stops = 0 if "non" in stops_text.lower() else int(re.search(r'\d+', stops_text).group()) if re.search(r'\d+', stops_text) else 0

                            results.append({
                                'source': 'MakeMyTrip (Scraped)',
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
                            print(f"⚠️  MMT parsing error: {e}")
                            continue

                    await browser.close()
                    print(f"✅ MakeMyTrip: {len(results)} flights scraped")
                    return results

            except Exception as e:
                print(f"❌ MMT scraping error (Attempt {attempt+1}): {e}")
                if attempt == max_retries - 1:
                    return []
                await asyncio.sleep(2)

        return []

    async def scrape_cleartrip(self, origin, destination, departure_date):
        """Scrape Cleartrip for flight data."""
        results = []
        try:
            # Detect if it's international
            domestic_iac = ["BOM", "DEL", "BLR", "MAA", "CCU", "HYD", "GOI", "PNQ", "JAI", "AMD", "COK"]
            is_intl = origin not in domestic_iac or destination not in domestic_iac
            intl_param = "y" if is_intl else "n"
            path = "international/results" if is_intl else "results"
            
            # Helper to get city/country info (fallback to codes)
            city_map = {
                "BOM": ("Mumbai", "IN"), "DEL": ("Delhi", "IN"), "BLR": ("Bengaluru", "IN"),
                "MAA": ("Chennai", "IN"), "CCU": ("Kolkata", "IN"), "HYD": ("Hyderabad", "IN"),
                "GOI": ("Goa", "IN"), "DXB": ("Dubai", "AE"), "AUH": ("Abu Dhabi", "AE"),
                "LHR": ("London", "GB"), "LGW": ("London", "GB"), "SIN": ("Singapore", "SG"),
                "BKK": ("Bangkok", "TH"), "JFK": ("New York", "US"), "ATL": ("Atlanta", "US"),
                "SFO": ("San Francisco", "US"), "ORD": ("Chicago", "US"), "MUC": ("Munich", "DE"),
                "FRA": ("Frankfurt", "DE"), "CDG": ("Paris", "FR"), "AMS": ("Amsterdam", "NL")
            }
            
            orig_city, orig_cc = city_map.get(origin, (origin, "IN"))
            dest_city, dest_cc = city_map.get(destination, (destination, "IN"))
            
            # Format: DD%2FMM%2FYYYY (encoded)
            formatted_date = departure_date.strftime('%d/%m/%Y').replace('/', '%2F')
            
            import urllib.parse
            orig_str = urllib.parse.quote(f"{origin} - {orig_city}, {orig_cc}")
            dest_str = urllib.parse.quote(f"{destination} - {dest_city}, {dest_cc}")
            
            # MMT/Cleartrip Search URL (Perfected per user feedback)
            url = (f"https://www.cleartrip.com/flights/{path}?"
                   f"adults=1&childs=0&infants=0&class=Economy&depart_date={formatted_date}"
                   f"&from={origin}&to={destination}&origin={orig_str}&destination={dest_str}"
                   f"&intl={intl_param}&isCfw=false&rnd_one=O&isFF=true")
            
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=self.headless,
                    args=['--disable-http2']
                )
                context = await browser.new_context(
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
                )
                
                page = await context.new_page()
                await Stealth().apply_stealth_async(page)
                
                print(f"🔍 Scraping Cleartrip: {url}")
                await page.goto(url, wait_until="domcontentloaded", timeout=60000)
                
                # Wait for results
                try:
                    # Wait for either the cards or the result counter
                    await page.wait_for_selector(".sc-aXZVg, .sc-bYTeLD, [class*='krEXgg']", timeout=35000)
                    await asyncio.sleep(6) # Cleartrip UI is heavy and results pop in slowly
                except:
                    print(f"⚠️  No flight results found on Cleartrip for {origin}-{destination}")
                    await browser.close()
                    return []

                # Extract data - Using broader selectors for containers
                cards = await page.query_selector_all("div.sc-bYTeLD, div[class*='krEXgg'], div.sc-aXZVg.bg-white.br-12")
                
                if not cards:
                    # Final fallback: look for any div that has a price and an airline logo
                    cards = await page.query_selector_all("div.bg-white.br-12.ba-solid")

                for card in cards[:15]:
                    try:
                        card_text = await card.inner_text()
                        
                        # Airline
                        airline_el = (await card.query_selector("img[src*='airlogo']") or 
                                      await card.query_selector("p.t-truncate, p.sc-gEvEer, p[class*='mt-1']"))
                        
                        if airline_el and await airline_el.evaluate("el => el.tagName") == 'IMG':
                            airline = await airline_el.get_attribute('alt') or "Unknown"
                        else:
                            airline = await airline_el.inner_text() if airline_el else "Unknown"
                        
                        # Times using Regex as primary (since classes change)
                        times = re.findall(r'\d{2}:\d{2}', card_text)
                        if len(times) >= 2:
                            dep_time, arr_time = times[0], times[1]
                        else:
                            # Fallback if CSS or layout weirdness
                            time_els = await card.query_selector_all("p.kSzAkB, p.sc-gEvEer.fs-16, div.fs-16")
                            texts = [await el.inner_text() for el in time_els if ":" in await el.inner_text()]
                            if len(texts) >= 2:
                                dep_time, arr_time = texts[0], texts[1]
                            elif len(texts) == 1 and "-" in texts[0]:
                                parts = texts[0].split("-")
                                dep_time = parts[0].strip()
                                arr_time = parts[1].strip() if len(parts) > 1 else "--:--"
                            else:
                                dep_time, arr_time = "--:--", "--:--"
                        
                        # Price using Regex as primary
                        # Finds all ₹ prices like ₹27,470 and gets the first or lowest reasonable one
                        price_matches = re.findall(r'₹\s*([\d,]+)', card_text)
                        price = 0
                        if price_matches:
                            # Cleartrip shows crossed-out price, then final price, then bank offer.
                            # So the second one is usually the final ticket price if there's > 1.
                            prices = [int(p.replace(',', '')) for p in price_matches]
                            # Usually actual price is the lowest non-bank-offer one
                            # Let's take the lowest price above 1000 to be safe
                            valid_prices = [p for p in prices if p > 1000]
                            if valid_prices:
                                price = min(valid_prices) # Grab lowest possible price listed
                        
                        if price == 0: 
                            print(f"⚠️ Cleartrip skipping card, price parse error in: {price_matches}")
                            continue
                        
                        # Duration/Stops
                        dur_match = re.search(r'(\d+h\s*\d+m|\d+h|\d+m)', card_text)
                        duration_text = dur_match.group(1) if dur_match else "0h 0m"
                        iso_duration = self._convert_to_iso_duration(duration_text)

                        stops = 0
                        stop_match = re.search(r'(\d+)\s+stop', card_text, re.IGNORECASE)
                        if stop_match:
                            stops = int(stop_match.group(1))
                        elif "non-stop" in card_text.lower() or "non stop" in card_text.lower():
                            stops = 0

                        results.append({
                            'source': 'Cleartrip (Scraped)',
                            'type': 'Flight',
                            'origin': origin,
                            'destination': destination,
                            'departure_date': departure_date.strftime('%Y-%m-%d'),
                            'airline': airline.strip(),
                            'price': float(price),
                            'currency': 'INR',
                            'departure_time': dep_time[:5],
                            'arrival_time': arr_time[:5],
                            'duration': iso_duration,
                            'stops': stops,
                            'cabin_class': 'ECONOMY',
                            'booking_url': url
                        })
                    except Exception as e:
                        print(f"⚠️  Cleartrip row parse error: {e}")
                        continue

                await browser.close()
                print(f"✅ Cleartrip: {len(results)} flights scraped")
                return results

        except Exception as e:
            print(f"❌ Cleartrip scraping error: {e}")
            return []

    def _convert_to_iso_duration(self, text):
        """Convert '2h 30m' to 'PT2H30M'."""
        h = re.search(r'(\d+)h', text) or re.search(r'(\d+) h', text)
        m = re.search(r'(\d+)m', text) or re.search(r'(\d+) m', text)
        hours = h.group(1) if h else "0"
        mins = m.group(1) if m else "0"
        return f"PT{hours}H{mins}M"

if __name__ == "__main__":
    # Test script
    import asyncio
    from datetime import datetime
    scraper = ScraperEngine(headless=False)
    # asyncio.run(scraper.scrape_easemytrip("BOM", "DEL", datetime.strptime("30/03/2026", "%d/%m/%Y")))
    asyncio.run(scraper.scrape_cleartrip("BOM", "DEL", datetime.strptime("30/03/2026", "%d/%m/%Y")))
