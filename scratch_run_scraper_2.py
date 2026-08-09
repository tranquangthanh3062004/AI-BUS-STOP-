import sys
sys.path.append('.')
from backend.scraper_agent import GoogleMapsScraperAgent
scraper = GoogleMapsScraperAgent()
scraper.headless=True
for r in scraper._do_scrape('Bến xe Mỹ Đình', 'Đại học Bách Khoa'):
    print(r.route_name.encode('utf-8'))
    print(r.route_id.encode('utf-8'))
