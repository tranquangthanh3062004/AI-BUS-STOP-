import time
import urllib.parse
from playwright.sync_api import sync_playwright
from typing import Dict, Any, List
from shared.logger import logger
from shared.schemas import RouteRecommendation
import uuid

class GoogleMapsScraperAgent:
    def __init__(self):
        self.headless = True
        
    def scrape_route(self, origin: str, destination: str) -> List[RouteRecommendation]:
        logger.info(f"[ScraperAgent] Đang cào dữ liệu Google Maps: {origin} -> {destination}")
        
        # Format the URL for transit directions in Hanoi
        origin_encoded = urllib.parse.quote(f"{origin}, Hà Nội, Việt Nam")
        dest_encoded = urllib.parse.quote(f"{destination}, Hà Nội, Việt Nam")
        
        # !3e3 stands for transit mode in Google Maps URL parameters
        url = f"https://www.google.com/maps/dir/{origin_encoded}/{dest_encoded}/data=!4m2!4m1!3e3?hl=vi"
        
        recommendations = []
        
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=self.headless)
                page = browser.new_page()
                
                logger.info(f"[ScraperAgent] Đang tải trang: {url}")
                page.goto(url, timeout=15000)
                
                # Wait for the transit route results to load.
                try:
                    page.wait_for_selector('div[data-trip-index]', timeout=10000)
                except Exception as e:
                    logger.warning("[ScraperAgent] Không tìm thấy phần tử chỉ đường (có thể do lỗi hoặc không có tuyến): " + str(e))
                    browser.close()
                    return []

                # Lấy tất cả các kết quả tuyến đường
                trips = page.query_selector_all('div[data-trip-index]')
                
                # Lấy duy nhất 3 kết quả đầu tiên (Phương án tối ưu nhất của Google Maps)
                for idx, trip in enumerate(trips[:3]):
                    try:
                        # Extract duration (Thời gian) - still try to use the common class, but fallback to first text
                        duration_el = trip.query_selector('div.Fk3sm.fontHeadlineSmall')
                        duration = duration_el.inner_text().strip() if duration_el else "N/A"
                        
                        # Sử dụng thuật toán DOM Text Node Filtering để chống đứt gãy khi Google đổi Class
                        texts = trip.evaluate("""el => {
                            let results = [];
                            let walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT, null, false);
                            let node;
                            while(node = walker.nextNode()) {
                                if(node.nodeValue.trim()) {
                                    results.push(node.nodeValue.trim());
                                }
                            }
                            return results;
                        }""")
                            
                        buses = []
                        import re
                        for txt in texts:
                            # Lọc các từ có chứa chữ số, ngắn, không phải phút/giờ
                            if any(char.isdigit() for char in txt) and len(txt) <= 6 and not any(skip in txt.lower() for skip in ["phút", "giờ", "min", " m", "km"]):
                                # Kiểm tra định dạng tuyến xe Hà Nội (VD: 01, 26, E03, 14CT, BRT01)
                                if re.match(r'^(?:BRT\s*0?1|E0[1-9]|E10|[0-9]{1,3}[A-Z]{0,2})$', txt.replace(" ", ""), re.IGNORECASE):
                                    buses.append(txt)
                                
                        if not buses:
                            continue
                            
                        # Lọc trùng lặp do cấu trúc DOM (ví dụ DOM lồng nhau)
                        # Dùng list dict fromkeys để giữ nguyên thứ tự
                        buses = list(dict.fromkeys(buses))
                            
                        route_name = " - ".join([f"Tuyến {b}" for b in buses])
                        
                        rec = RouteRecommendation(
                            route_id=" -> ".join(buses) if buses else str(uuid.uuid4())[:4],
                            route_name=f"Google Maps: {route_name}",
                            board_stop=origin,
                            alight_stop=destination,
                            transfers_count=len(buses) - 1,
                            transfer_stop="Không rõ" if len(buses) == 1 else "Chuyển tuyến theo GG Maps",
                            fare_vnd=7000 * len(buses), # Ước tính
                            operating_hours="Thời gian thực tế",
                            description=f"Phương án TỐI ƯU NHẤT do Google Maps đề xuất. Tổng thời gian dự kiến: {duration}.",
                            itinerary=f"Đi từ {origin} đến {destination}"
                        )
                        recommendations.append(rec)
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
