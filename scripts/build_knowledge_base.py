"""
scripts/build_knowledge_base.py
Comprehensive Knowledge Base Builder.
Ingests ALL files from data/hanoi/ (including BRT01, Metro 2A & 3, legal docs, BusMap guide, Vinbus),
data/hcm/, data/archive/gtcc_kienthuc.txt, data/archive/raw_data/data xe buýt.xlsx,
and data/finetune_gtcc.jsonl into local SQLite CSDL and FAQ Store.
"""

import os
import re
import sqlite3
import json
import pandas as pd
import sys

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
HANOI_DIR = os.path.join(DATA_DIR, "hanoi")
HCM_DIR = os.path.join(DATA_DIR, "hcm")
ARCHIVE_DIR = os.path.join(DATA_DIR, "archive")
RAW_DIR = os.path.join(ARCHIVE_DIR, "raw_data")
KB_DIR = os.path.join(os.path.dirname(__file__), "..", "knowledge_base")
DB_PATH = os.path.join(KB_DIR, "local_transit.db")
FAQ_PATH = os.path.join(KB_DIR, "faq_store.json")

os.makedirs(KB_DIR, exist_ok=True)

def init_db(conn):
    cursor = conn.cursor()
    cursor.executescript("""
    DROP TABLE IF EXISTS route_stops;
    DROP TABLE IF EXISTS routes;
    DROP TABLE IF EXISTS stops;
    DROP TABLE IF EXISTS faqs;
    DROP TABLE IF EXISTS transfers;
    DROP TABLE IF EXISTS routes_fts;
    DROP TABLE IF EXISTS stops_fts;

    CREATE TABLE transfers (
        route_1 TEXT,
        route_2 TEXT,
        transfer_stop TEXT,
        PRIMARY KEY (route_1, route_2, transfer_stop)
    );

    CREATE VIRTUAL TABLE routes_fts USING fts5(
        route_id, 
        route_name, 
        start_stop, 
        end_stop, 
        outbound_itinerary, 
        inbound_itinerary
    );

    CREATE VIRTUAL TABLE stops_fts USING fts5(
        stop_name
    );

    CREATE VIRTUAL TABLE faqs_fts USING fts5(
        category,
        title,
        content
    );

    CREATE TABLE routes (
        route_id TEXT PRIMARY KEY,
        route_name TEXT NOT NULL,
        start_stop TEXT,
        end_stop TEXT,
        operating_hours TEXT,
        start_time INTEGER,
        end_time INTEGER,
        frequency TEXT,
        fare_vnd INTEGER,
        outbound_itinerary TEXT,
        inbound_itinerary TEXT,
        vehicle_type TEXT DEFAULT 'Bus',
        special_notes TEXT,
        city TEXT DEFAULT 'Hà Nội'
    );

    CREATE TABLE stops (
        stop_id INTEGER PRIMARY KEY AUTOINCREMENT,
        stop_name TEXT NOT NULL UNIQUE,
        district TEXT,
        city TEXT DEFAULT 'Hà Nội'
    );

    CREATE TABLE route_stops (
        route_id TEXT,
        stop_name TEXT,
        stop_sequence INTEGER,
        direction INTEGER DEFAULT 0,
        distance_m INTEGER DEFAULT 0,
        duration_s INTEGER DEFAULT 0,
        PRIMARY KEY (route_id, stop_name, stop_sequence, direction),
        FOREIGN KEY (route_id) REFERENCES routes(route_id)
    );

    CREATE TABLE faqs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category TEXT,
        title TEXT,
        content TEXT
    );
    """)
    conn.commit()

def extract_fare(fare_str):
    digits = re.findall(r"\d+", fare_str.replace(".", "").replace(",", ""))
    return int(digits[0]) if digits else 7000

def clean_id(route_id):
    r_id = str(route_id).upper().replace("TUYẾN", "").replace(" ", "").strip()
    # Zero pad single digit routes (e.g., "1" -> "01", "3A" -> "03A")
    m = re.match(r"^(\d)([A-Z]*)$", r_id)
    if m:
        r_id = "0" + r_id
    
    # Validation: Route ID must contain digits OR start with E/BRT to prevent garbage like "QUAN"
    has_digit = any(char.isdigit() for char in r_id)
    if not has_digit and not r_id.startswith("E") and not r_id.startswith("BRT"):
        return ""
    
    return r_id

def normalize_stop_name(name):
    if not name: return ""
    n = name.strip()
    n = re.sub(r'\bĐH\b', 'Đại học', n, flags=re.IGNORECASE)
    n = re.sub(r'\bBV\b', 'Bệnh viện', n, flags=re.IGNORECASE)
    n = re.sub(r'\bTW\b', 'Trung ương', n, flags=re.IGNORECASE)
    n = re.sub(r'\bCS2\b', 'Cơ sở 2', n, flags=re.IGNORECASE)
    n = re.sub(r'\bcơ sở II\b', 'Cơ sở 2', n, flags=re.IGNORECASE)
    n = re.sub(r'\bKĐT\b', 'Khu đô thị', n, flags=re.IGNORECASE)
    n = re.sub(r'\bTHPT\b', 'Trường THPT', n, flags=re.IGNORECASE)
    n = re.sub(r'\s+', ' ', n).strip()
    return n

def parse_operating_hours(time_str):
    if not time_str: return 0, 0
    m = re.findall(r"(\d{1,2}):(\d{2})", time_str)
    if len(m) >= 2:
        start = int(m[0][0]) * 100 + int(m[0][1])
        end = int(m[1][0]) * 100 + int(m[1][1])
        return start, end
    return 0, 0

def detect_vehicle_type(r_id, text_block=""):
    r_id_up = r_id.upper()
    if "BRT" in r_id_up or r_id_up == "BRT01":
        return "BRT"
    if r_id_up in ("2A", "3"):
        return "Metro"
    if r_id_up.startswith("E") or r_id_up in ("153", "155", "157", "159"):
        return "Vinbus"
    return "Bus"

def split_stops(itin):
    if not itin: return []
    itin = itin.replace('\xa0', ' ')
    stops = []
    current_stop = []
    paren_level = 0
    i = 0
    while i < len(itin):
        if itin[i] == '(':
            paren_level += 1
            current_stop.append(itin[i])
        elif itin[i] == ')':
            paren_level = max(0, paren_level - 1)
            current_stop.append(itin[i])
        else:
            if paren_level == 0:
                if itin[i:i+2] == '<>':
                    stops.append("".join(current_stop).strip())
                    current_stop = []
                    i += 2
                    continue
                elif itin[i] == '→':
                    stops.append("".join(current_stop).strip())
                    current_stop = []
                    i += 1
                    continue
                elif itin[i:i+3] == ' - ':
                    stops.append("".join(current_stop).strip())
                    current_stop = []
                    i += 3
                    continue
                elif itin[i:i+3] == ' – ':
                    stops.append("".join(current_stop).strip())
                    current_stop = []
                    i += 3
                    continue
            current_stop.append(itin[i])
        i += 1
    if current_stop:
        stops.append("".join(current_stop).strip())
    return [normalize_stop_name(s) for s in stops if len(s) > 2]

def reverse_itinerary(itinerary_str):
    stops = split_stops(itinerary_str)
    if not stops: return ""
    stops.reverse()
    return " - ".join(stops)

def parse_and_seed_data(conn):
    cursor = conn.cursor()
    routes_map = {}
    faqs_data = []

    def get_or_create_route(r_id):
        r_id = clean_id(r_id)
        if not r_id: return None
        if r_id not in routes_map:
            routes_map[r_id] = {
                "route_id": r_id, "route_name": "", "start_stop": "", "end_stop": "",
                "operating_hours": "5:00 - 21:00", "frequency": "10 - 15 phút/chuyến",
                "fare_vnd": 7000, "outbound_itinerary": "", "inbound_itinerary": "",
                "vehicle_type": "Bus", "special_notes": "", "city": "Hà Nội"
            }
        return routes_map[r_id]

    # --- 1. Parse Excel data (if any) ---
    excel_files = [f for f in os.listdir(RAW_DIR) if f.endswith('.xlsx')] if os.path.exists(RAW_DIR) else []
    archive_dir = os.path.join(RAW_DIR, "archive", "raw_data")
    if os.path.exists(archive_dir):
        excel_files.extend([os.path.join("archive", "raw_data", f) for f in os.listdir(archive_dir) if f.endswith('.xlsx')])
    
    if excel_files:
        excel_path = os.path.join(RAW_DIR, excel_files[0])
        try:
            df = pd.read_excel(excel_path)
            for _, row in df.iterrows():
                r_code = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else ""
                r_name = str(row.iloc[1]).strip() if pd.notna(row.iloc[1]) else ""
                time_str = str(row.iloc[2]).strip() if pd.notna(row.iloc[2]) else "5h00 - 21h00"
                fare_str = str(row.iloc[3]).strip() if pd.notna(row.iloc[3]) else "7.000 VNĐ"
                if not r_code or r_code.lower() == "mã số": continue

                r = get_or_create_route(r_code)
                if not r: continue
                r["vehicle_type"] = detect_vehicle_type(r["route_id"])
                if not r["route_name"]:
                    r["route_name"] = r_name
                    parts = r_name.split("-") if "-" in r_name else [r_name, ""]
                    r["start_stop"] = parts[0].strip()
                    r["end_stop"] = parts[-1].strip() if len(parts) > 1 else ""
                r["operating_hours"] = time_str
                r["fare_vnd"] = extract_fare(fare_str)
        except Exception as e:
            print(f"Warning parsing Excel: {e}")

    # --- 2. Parse danh_sach_tuyen_buyt.txt ---
    fpath = os.path.join(HANOI_DIR, "danh_sach_tuyen_buyt.txt")
    if os.path.exists(fpath):
        with open(fpath, "r", encoding="utf-8") as f:
            for line in f:
                m = re.search(r"Mã số:\s*([A-Za-z0-9]+)\s*\|\s*Tuyến xe buýt:\s*([^|]+)", line, re.IGNORECASE)
                if m:
                    r_id, r_name = m.group(1), m.group(2).strip()
                    r = get_or_create_route(r_id)
                    if not r: continue
                    r["vehicle_type"] = detect_vehicle_type(r["route_id"])
                    if not r["route_name"]: r["route_name"] = r_name
                    parts = r_name.split("-")
                    r["start_stop"] = parts[0].strip()
                    r["end_stop"] = parts[-1].strip() if len(parts) > 1 else ""
                    
                    m_time = re.search(r"Thời gian hoạt động:\s*([^|]+)", line)
                    if m_time: r["operating_hours"] = m_time.group(1).strip()
                    
                    m_fare = re.search(r"Giá vé tham khảo:\s*([^|]+)", line)
                    if m_fare: r["fare_vnd"] = extract_fare(m_fare.group(1))

    # --- 3. Parse lich_trinh_buyt.txt & bus_brt_hanoi.txt & vinbus_dien_hanoi.txt & tuyen_lien_tinh.txt & bo_sung_lo_trinh.txt ---
    files_to_parse = [
        "lich_trinh_buyt.txt", 
        "bus_brt_hanoi.txt", 
        "vinbus_dien_hanoi.txt",
        "tuyen_lien_tinh.txt",
        "bo_sung_lo_trinh.txt",
        "tuyen_bo_sung_2026.txt"
    ]

    for fname in files_to_parse:
        fpath = os.path.join(HANOI_DIR, fname)
        if not os.path.exists(fpath): continue
        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read()

        # Handle hardcoded BRT01 from bus_brt_hanoi.txt separately since it lacks standard Tuyến block
        if fname == "bus_brt_hanoi.txt":
            if "BRT HA NỘI (KIM MÃ - YÊN NGHĨA)" in content.upper() or "BRT HÀ NỘI" in content.upper():
                r = get_or_create_route("BRT01")
                if r:
                    r["route_name"] = "Kim Mã - Yên Nghĩa"
                    r["start_stop"] = "Kim Mã"
                    r["end_stop"] = "Yên Nghĩa"
                    r["vehicle_type"] = "BRT"
                    m_itin = re.search(r"Lộ trình:\s*([^\n]+)", content)
                    if m_itin: r["outbound_itinerary"] = m_itin.group(1).strip()
                    r["operating_hours"] = "05:00 - 22:00"
                    r["fare_vnd"] = 9000

        blocks = re.split(r"\n(?=\s*(?:-\s*Mã số:|Tuyến))", content, flags=re.IGNORECASE)
        for block in blocks:
            block = block.strip()
            if not block: continue
            
            m_id = re.search(r"(?:Mã số|Tuyến(?:[^:\n\d]*))\s*:?\s*([A-Za-z0-9]+)", block, re.IGNORECASE)
            r_id = m_id.group(1) if m_id else None
            
            if r_id:
                # Exclude false positive BRT if it parsed string "BRT" from "TUYẾN BRT 01" instead of "01"
                if r_id.upper() == "BRT": continue
                
                r = get_or_create_route(r_id)
                if not r: continue
                r["vehicle_type"] = detect_vehicle_type(r["route_id"], block)
                
                first_line = block.split("\n")[0]
                if '|' in first_line:
                    first_line = first_line.split('|')[-1]
                if ':' in first_line:
                    clean_name = first_line.split(':', 1)[1].strip()
                else:
                    m_name = re.search(r"(?:Tuyến[^:\d\n]*|Mã số[^:\n]*)\s*[A-Za-z0-9]+\s*[:-]?\s*(.+?)$", first_line, re.IGNORECASE)
                    clean_name = m_name.group(1).strip() if m_name else first_line
                
                if clean_name and len(clean_name) > 3:
                    clean_name = clean_name.strip("-").strip()
                    r["route_name"] = clean_name
                    
                    parts = re.split(r'\s*(?:[-–⇄]|<>)\s*', clean_name)
                    if len(parts) >= 2:
                        r["start_stop"] = normalize_stop_name(parts[0].strip())
                        r["end_stop"] = normalize_stop_name(parts[-1].strip())
                    else:
                        r["start_stop"] = normalize_stop_name(clean_name)
                        r["end_stop"] = ""
                
                m_itin = re.search(r"(?:Lộ trình|Lộ trình chính|Lộ trình lượt đi)[^:\n]*:\s*([^\n]+)", block, re.IGNORECASE)
                itin = None
                if m_itin:
                    itin = m_itin.group(1).strip()
                else:
                    lines = block.split("\n")
                    if len(lines) > 1:
                        potential_itin = lines[1].strip()
                        if "-" in potential_itin or "<>" in potential_itin or "–" in potential_itin:
                            itin = potential_itin
                if itin and len(itin) > len(r["outbound_itinerary"]):
                    r["outbound_itinerary"] = itin
                
                m_time = re.search(r"Thời gian hoạt động:\s*([^\n]+)", block, re.IGNORECASE)
                if m_time: r["operating_hours"] = m_time.group(1).strip()
                
                m_freq = re.search(r"Tần suất:\s*([^\n]+)", block, re.IGNORECASE)
                if m_freq: r["frequency"] = m_freq.group(1).strip()
                
                m_fare = re.search(r"Giá vé[^\n:]*:\s*([^\n]+)", block, re.IGNORECASE)
                if m_fare: r["fare_vnd"] = extract_fare(m_fare.group(1))

    # --- 4. Parse hanoi_bus_routes_full.txt (for separated Inbound/Outbound) ---
    fpath = os.path.join(HANOI_DIR, "hanoi_bus_routes_full.txt")
    if os.path.exists(fpath):
        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read()
            blocks = re.split(r"\n(?=\s*Tuyến\s*[A-Za-z0-9]+:)", content, flags=re.IGNORECASE)
            for block in blocks:
                block = block.strip()
                if not block: continue
                m_id = re.search(r"Tuyến\s*([A-Za-z0-9]+):", block, re.IGNORECASE)
                if m_id:
                    r_id = m_id.group(1)
                    if r_id.upper() == "BRT": continue
                    r = get_or_create_route(r_id)
                    if not r: continue
                    r["vehicle_type"] = detect_vehicle_type(r["route_id"], block)
                    
                    outbound_m = re.search(r"Lộ trình lượt đi:\s*([^\n]+)", block, re.IGNORECASE)
                    if outbound_m: r["outbound_itinerary"] = outbound_m.group(1).strip()
                    
                    inbound_m = re.search(r"Lộ trình lượt về:\s*([^\n]+)", block, re.IGNORECASE)
                    if inbound_m: r["inbound_itinerary"] = inbound_m.group(1).strip()

    # --- 5. Parse metro_hanoi.txt ---
    fpath = os.path.join(HANOI_DIR, "metro_hanoi.txt")
    if os.path.exists(fpath):
        r_2a = get_or_create_route("2A")
        r_2a["vehicle_type"] = "Metro"
        r_2a["route_name"] = "Đường sắt đô thị Cát Linh - Hà Đông"
        r_2a["outbound_itinerary"] = "Cát Linh - La Thành - Thái Hà - Láng - Thượng Đình - Vành Đai 3 - Phùng Khoang - Văn Quán - Hà Đông - La Khê - Văn Khê - Yên Nghĩa"
        
        r_3 = get_or_create_route("3")
        r_3["vehicle_type"] = "Metro"
        r_3["route_name"] = "Đường sắt đô thị Nhổn - Ga Hà Nội"
        r_3["outbound_itinerary"] = "Nhổn - Minh Khai - Phú Diễn - Cầu Diễn - Lê Đức Thọ - Đại học Quốc gia - Chùa Hà - Cầu Giấy"

    # --- 6. Special Notes from lich_trinh_dac_biet.txt ---
    fpath = os.path.join(HANOI_DIR, "lich_trinh_dac_biet.txt")
    if os.path.exists(fpath):
        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read()
            m_hohoankiem = re.search(r"Các tuyến bị ảnh hưởng:([^\n\(\)]+)", content)
            if m_hohoankiem:
                affected_routes = [clean_id(x) for x in m_hohoankiem.group(1).split(",")]
                for a_id in affected_routes:
                    if a_id in routes_map:
                        routes_map[a_id]["special_notes"] = "Thay đổi lộ trình vào cuối tuần (Phố đi bộ Hồ Hoàn Kiếm). Xe buýt sẽ không đi vào khu vực quanh Hồ Hoàn Kiếm."

    # --- Auto-Reverse Inbound Itinerary ---
    for r_id, r_data in routes_map.items():
        if r_data["outbound_itinerary"] and not r_data["inbound_itinerary"]:
            r_data["inbound_itinerary"] = reverse_itinerary(r_data["outbound_itinerary"])

    # --- Build Stops and Insert ---
    all_stops = set()
    for r_id, r_data in routes_map.items():
        start_time, end_time = parse_operating_hours(r_data.get("operating_hours", ""))
        cursor.execute("""
            INSERT OR REPLACE INTO routes (route_id, route_name, start_stop, end_stop, operating_hours, start_time, end_time, frequency, fare_vnd, outbound_itinerary, inbound_itinerary, vehicle_type, special_notes, city)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            r_data["route_id"], r_data["route_name"], r_data["start_stop"], r_data["end_stop"],
            r_data["operating_hours"], start_time, end_time, r_data["frequency"], r_data["fare_vnd"],
            r_data["outbound_itinerary"], r_data["inbound_itinerary"],
            r_data["vehicle_type"], r_data["special_notes"], r_data["city"]
        ))
        
        for direction, itin_str in [(0, r_data["outbound_itinerary"]), (1, r_data["inbound_itinerary"])]:
            if not itin_str: continue
            stops = split_stops(itin_str)
            for idx, s in enumerate(stops):
                stop_clean = s.strip()
                all_stops.add(stop_clean)
                cursor.execute("""
                    INSERT OR IGNORE INTO route_stops (route_id, stop_name, stop_sequence, direction, distance_m, duration_s)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (r_data["route_id"], stop_clean, idx, direction, 800 if idx > 0 else 0, 120 if idx > 0 else 0))

    for s in all_stops:
        cursor.execute("INSERT OR IGNORE INTO stops (stop_name, city) VALUES (?, ?)", (s, "Hà Nội"))
        cursor.execute("INSERT INTO stops_fts (rowid, stop_name) SELECT last_insert_rowid(), ?", (s,))
        
    print("Building Full-Text Search index for routes...")
    cursor.execute("""
        INSERT INTO routes_fts (rowid, route_id, route_name, start_stop, end_stop, outbound_itinerary, inbound_itinerary)
        SELECT rowid, route_id, route_name, start_stop, end_stop, outbound_itinerary, inbound_itinerary FROM routes
    """)
    
    print("Pre-computing Transfer Matrix...")
    cursor.execute("""
        INSERT INTO transfers (route_1, route_2, transfer_stop)
        SELECT DISTINCT a.route_id, b.route_id, a.stop_name
        FROM route_stops a
        JOIN route_stops b ON a.stop_name = b.stop_name AND a.route_id != b.route_id
    """)
    
    conn.commit()
    print(f"Total Bus Routes indexed: {len(routes_map)}")
    print(f"Total Unique Stops indexed: {len(all_stops)}")


def process_faqs(conn):
    cursor = conn.cursor()
    faqs_data = []

    # 1. finetune_gtcc.jsonl (OpenAI chat format: {"messages": [...]})
    fpath = os.path.join(DATA_DIR, "finetune_gtcc.jsonl")
    if os.path.exists(fpath):
        with open(fpath, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip(): continue
                try:
                    obj = json.loads(line)
                    # Support OpenAI chat format: {"messages": [{"role": ..., "content": ...}]}
                    messages = obj.get("messages", [])
                    if messages:
                        q = ""
                        a = ""
                        for msg in messages:
                            if msg.get("role") == "user":
                                q = msg.get("content", "").strip()
                            elif msg.get("role") == "assistant":
                                a = msg.get("content", "").strip()
                        if q and a:
                            faqs_data.append({"category": "Q&A", "title": q, "content": a})
                            continue
                    # Fallback: legacy "text" format
                    text = obj.get("text", "")
                    if "### Câu hỏi:" in text:
                        parts = text.split("### Trả lời:")
                        q = parts[0].replace("### Câu hỏi:", "").strip()
                        a = parts[1].strip() if len(parts) > 1 else ""
                        if q and a:
                            faqs_data.append({"category": "Q&A", "title": q, "content": a})
                except:
                    pass

    # 2. huong_dan_busmap.txt
    fpath = os.path.join(HANOI_DIR, "huong_dan_busmap.txt")
    if os.path.exists(fpath):
        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read()
            faqs_data.append({"category": "App Guide", "title": "Hướng dẫn dùng BusMap", "content": content[:1000]})

    # 3. gtcc_kienthuc.txt
    fpath = os.path.join(ARCHIVE_DIR, "gtcc_kienthuc.txt")
    if os.path.exists(fpath):
        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read()
            blocks = content.split("===")
            for b in blocks:
                b = b.strip()
                if len(b) > 20:
                    faqs_data.append({"category": "General Rules", "title": b[:50], "content": b})

    # 4. Ingest all important knowledge .txt files from data/hanoi/
    knowledge_files = {
        "bang_gia_ve_2026.txt": ("Fare", "Bảng giá vé xe buýt và vé tháng Hà Nội"),
        "ben_xe_diem_trung_chuyen.txt": ("Station", "Thông tin bến xe và điểm trung chuyển Hà Nội"),
        "quy_dinh_phap_luat.txt": ("Rules", "Quy định pháp luật đi xe buýt và metro"),
        "ung_dung_thanh_toan.txt": ("App Guide", "Ứng dụng di động và thanh toán điện tử xe buýt"),
        "tourist_guide_en.txt": ("Tourist", "Tourist Guide - Hanoi Bus System Information"),
        "hanoi_tickets_and_passes.txt": ("Fare", "Hướng dẫn vé và thẻ đi xe buýt Hà Nội"),
        "metro_hanoi.txt": ("Metro", "Thông tin tuyến Metro Hà Nội"),
        "hanoi_metro_update_2026.txt": ("Metro", "Cập nhật Metro Hà Nội 2026"),
        "ket_noi_metro_bus.txt": ("Metro", "Kết nối Metro - Xe buýt Hà Nội"),
        "lich_trinh_dac_biet.txt": ("Schedule", "Lịch trình đặc biệt và thay đổi tuyến xe buýt"),
        "bus_brt_hanoi.txt": ("BRT", "Thông tin tuyến BRT Hà Nội"),
        "buyt_online_hanoi.txt": ("App Guide", "Hướng dẫn tra cứu xe buýt trực tuyến Hà Nội"),
    }
    for fname, (category, title) in knowledge_files.items():
        fpath = os.path.join(HANOI_DIR, fname)
        if os.path.exists(fpath):
            with open(fpath, "r", encoding="utf-8") as f:
                content = f.read().strip()
            if len(content) > 20:
                # Split large files into sections by "===" delimiter if present
                if "===" in content:
                    sections = content.split("===")
                    for sec in sections:
                        sec = sec.strip()
                        if len(sec) > 20:
                            sec_title = sec.split("\n")[0].strip()[:80] or title
                            faqs_data.append({"category": category, "title": sec_title, "content": sec})
                else:
                    faqs_data.append({"category": category, "title": title, "content": content})

    for item in faqs_data:
        cursor.execute("INSERT INTO faqs (category, title, content) VALUES (?, ?, ?)", 
                       (item["category"], item["title"], item["content"]))
        cursor.execute("INSERT INTO faqs_fts (category, title, content) VALUES (?, ?, ?)", 
                       (item["category"], item["title"], item["content"]))
    conn.commit()
    
    if os.path.exists(FAQ_PATH):
        try: os.remove(FAQ_PATH)
        except: pass
    print(f"Total FAQs items indexed: {len(faqs_data)}")

if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    conn = sqlite3.connect(DB_PATH)
    init_db(conn)
    parse_and_seed_data(conn)
    process_faqs(conn)
    conn.close()
    print(f"Successfully populated comprehensive SQLite DB at {os.path.abspath(DB_PATH)}")
