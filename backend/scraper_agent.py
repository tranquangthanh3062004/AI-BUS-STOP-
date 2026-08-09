import time
import urllib.parse
try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
from typing import Dict, Any, List
from shared.logger import logger
from shared.schemas import RouteRecommendation
import uuid
import hashlib
import re
import threading

class GoogleMapsScraperAgent:
    _cache = {}  # {cache_key: (timestamp, results)}
    CACHE_TTL = 600  # 10 phút
    MAX_CACHE_SIZE = 100
    _lock = threading.Lock()

    def __init__(self):
        self.headless = True
        logger.info("GoogleMapsScraperAgent initialized")
        
    def scrape_route(self, origin: str, destination: str) -> List[RouteRecommendation]:
        """Scrape route from Google Maps with threading lock and memory leak prevention."""
        if not PLAYWRIGHT_AVAILABLE:
            return []
            
        cache_key = hashlib.md5(f"{origin}-{destination}".encode()).hexdigest()
        
        with self._lock:
            # 1. Clean old cache and enforce size limit
            now = time.time()
            keys_to_delete = [k for k, v in self._cache.items() if now - v[0] > self.CACHE_TTL]
            for k in keys_to_delete:
                del self._cache[k]
                
            if len(self._cache) > self.MAX_CACHE_SIZE:
                # Remove oldest item
                oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k][0])
                del self._cache[oldest_key]
                
            # 2. Return cached if valid
            if cache_key in self._cache:
                logger.info(f"[ScraperAgent] Trả về kết quả từ cache cho {origin} -> {destination}")
                return self._cache[cache_key][1]
        
        # Scrape with retry
        for attempt in range(2):
            with self._lock:
                results = self._do_scrape(origin, destination)
            
            if results:
                with self._lock:
                    self._cache[cache_key] = (time.time(), results)
                return results
                
            if attempt == 0:
                logger.info(f"[ScraperAgent] Lần {attempt+1} thất bại, thử lại sau 1s...")
                time.sleep(1)
        
        return []

    def _do_scrape(self, origin: str, destination: str) -> List[RouteRecommendation]:
        if not PLAYWRIGHT_AVAILABLE:
            logger.warning("[ScraperAgent] Playwright is not installed. Scraper is disabled.")
            return []

        logger.info(f"[ScraperAgent] Đang cào dữ liệu Google Maps: {origin} -> {destination}")
        
        # Format the URL for transit directions in Hanoi
        origin_encoded = urllib.parse.quote(f"{origin}, Hà Nội, Việt Nam")
        dest_encoded = urllib.parse.quote(f"{destination}, Hà Nội, Việt Nam")
        
        # Phase 1: URL chính thức, travelmode=transit
        url = f"https://www.google.com/maps/dir/?api=1&origin={origin_encoded}&destination={dest_encoded}&travelmode=transit&hl=vi"
        
        recommendations = []
        
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=self.headless)
                page = browser.new_page()
                
                logger.info(f"[ScraperAgent] Đang tải trang: {url}")
                page.goto(url, timeout=15000)
                
                # Phase 2: Multi-Strategy Selector
                TRIP_SELECTORS = [
                    'div[data-trip-index]',
                    'div[class*="trip"]',
                    'div[role="listitem"]',
                    'section[aria-label*="route"]'
                ]
                
                trips = []
                for selector in TRIP_SELECTORS:
                    try:
                        page.wait_for_selector(selector, timeout=5000)
                        trips = page.query_selector_all(selector)
                        if trips:
                            break
                    except Exception:
                        continue
                        
                if not trips:
                    logger.warning(f"[ScraperAgent] Không tìm thấy phần tử chỉ đường. URL: {url}")
                    browser.close()
                    return []

                # Lấy duy nhất 3 kết quả đầu tiên
                for idx, trip in enumerate(trips[:3]):
                    try:
                        # Extract duration fallback
                        duration_el = trip.query_selector('div.Fk3sm.fontHeadlineSmall')
                        if not duration_el:
                            duration_el = trip.query_selector('div:text-matches("\\d+\\s*(phút|giờ|min|h|p)", "i")')
                        
                        duration = duration_el.inner_text().strip() if duration_el else "N/A"
                        if "N/A" != duration and "\n" in duration:
                            duration = duration.split("\n")[0]
                        
                        texts = trip.evaluate("""el => {
                            let results = [];
                            let walker = document.createTreeWalker(el, NodeFilter.SHOW_ALL, null, false);
                            let node;
                            while(node = walker.nextNode()) {
                                if (node.nodeType === Node.TEXT_NODE) {
                                    if(node.nodeValue.trim()) {
                                        results.push(node.nodeValue.trim());
                                    }
                                } else if (node.nodeType === Node.ELEMENT_NODE && node.tagName.toLowerCase() === 'img') {
                                    if(node.alt && node.alt.trim()) {
                                        results.push(node.alt.trim());
                                    }
                                }
                            }
                            return results;
                        }""")
                            
                        # Phase 3: 2-Pass Regex + NLP Context Filtering
                        bus_context_indices = set()
                        for i, txt in enumerate(texts):
                            if any(kw in txt.lower() for kw in ["xe buýt", "bus", "tuyến"]):
                                bus_context_indices.add(i)
                                bus_context_indices.add(i + 1)
                                bus_context_indices.add(i + 2)
                        
                        buses = []
                        for i, txt in enumerate(texts):
                            txt = txt.strip()
                            if not txt:
                                continue
                                
                            if re.match(r'^\d+\s*(phút|giờ|min|hr|km|m|trạm|lần|bước|chuyến)$', txt, re.IGNORECASE):
                                continue
                                
                            is_in_context = i in bus_context_indices
                            is_special = re.match(r'^(BRT\s*0?1|E0[1-9]|E10)$', txt, re.IGNORECASE)
                            
                            if (is_in_context or is_special) and re.match(
                                r'^(?:BRT\s*0?1|E0[1-9]|E10|[0-9]{1,3}[A-Z]{0,2})$', 
                                txt.replace(" ", ""), re.IGNORECASE
                            ):
                                buses.append(txt)
                        
                        if not buses:
                            continue
                            
                        buses = list(dict.fromkeys(buses))
                            
                        route_name = " - ".join([f"Tuyến {b}" for b in buses])
                        
                        rec = RouteRecommendation(
                            route_id=" -> ".join(buses) if buses else str(uuid.uuid4())[:4],
                            route_name=f"{route_name}",
                            board_stop=origin,
                            alight_stop=destination,
                            transfers_count=len(buses) - 1,
                            transfer_stop="Không rõ" if len(buses) == 1 else "Theo lộ trình chuyển tuyến",
                            fare_vnd=7000 * len(buses), # Ước tính
                            operating_hours="Thời gian thực tế",
                            description=f"Phương án di chuyển tối ưu nhất. Tổng thời gian dự kiến: {duration}.",
                            itinerary=f"Đi từ {origin} đến {destination}"
                        )
                        recommendations.append(rec)
                        break  # Chỉ lấy 1 tuyến tối ưu nhất như yêu cầu
                    except Exception as trip_err:
                        logger.error(f"[ScraperAgent] Lỗi khi đọc trip {idx}: {trip_err}")
                
                browser.close()
                
        except Exception as e:
            logger.error(f"[ScraperAgent] Lỗi scrape: {e}")
            
        return recommendations

if __name__ == "__main__":
    # Test
    scraper = GoogleMapsScraperAgent()
    scraper.headless = False # Hiện trình duyệt để debug
    res = scraper.scrape_route("Bến xe Mỹ Đình", "Đại học Bách Khoa")
    for r in res:
        print(r)
