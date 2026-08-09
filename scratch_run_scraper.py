from backend.scraper_agent import GoogleMapsScraperAgent
import urllib.parse
from playwright.sync_api import sync_playwright

origin = "Bến xe Mỹ Đình"
destination = "Đại học Bách Khoa"
url = f"https://www.google.com/maps/dir/?api=1&origin={urllib.parse.quote(origin+', Hà Nội, Việt Nam')}&destination={urllib.parse.quote(destination+', Hà Nội, Việt Nam')}&travelmode=transit&hl=vi"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto(url, timeout=15000)
    page.wait_for_selector('div[data-trip-index]', timeout=5000)
    trip = page.query_selector_all('div[data-trip-index]')[0]
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
    print("TEXTS EXTRACTED:")
    for t in texts:
        print(t.encode("utf-8"))
    browser.close()
