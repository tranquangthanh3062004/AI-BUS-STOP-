"""
edge_ai/transit_graph.py
Local Transit Graph & Optimal Route Recommendation Engine.
Ranks and selects the #1 BEST OPTIMAL BUS ROUTE (Direct routes first, min transfers, shortest itinerary)
without calling external APIs or Google Maps.
"""

import os
import sqlite3
import unicodedata
import urllib.parse
from typing import List, Tuple, Optional
from shared.schemas import RouteRecommendation
import networkx as nx

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "knowledge_base", "local_transit.db")


def norm_str(text: str) -> str:
    if not text:
        return ""
    return unicodedata.normalize("NFC", text.lower().strip())


class LocalTransitGraph:
    # Class-level cache — shared across all instances
    _routes_cache: dict = None
    _graph: nx.DiGraph = None
    _stop_to_routes: dict = None
    _cache_ready: bool = False

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = os.path.abspath(db_path)
        alias_file = os.path.join(os.path.dirname(__file__), "..", "data", "hanoi", "alias_map.json")
        self.alias_map = {}
        try:
            import json
            with open(alias_file, "r", encoding="utf-8") as f:
                raw_aliases = json.load(f)
                for alias, canonical in raw_aliases.items():
                    key = canonical.lower()
                    if key not in self.alias_map:
                        self.alias_map[key] = [key]
                    if alias.lower() not in self.alias_map[key]:
                        self.alias_map[key].append(alias.lower())
        except Exception:
            self.alias_map = {
                "bách khoa": ["đại học bách khoa", "bách khoa", "đh bách khoa", "trần đại nghĩa", "lê thanh nghị", "giải phóng", "thanh nhàn"],
                "mỹ đình": ["bến xe mỹ đình", "mỹ đình", "bx mỹ đình", "phạm hùng", "svđ quốc gia", "hồ tùng mậu", "lê đức thọ"],
                "giáp bát": ["bến xe giáp bát", "giáp bát", "bx giáp bát", "giải phóng", "trường chinh", "kim đồng"],
                "yên nghĩa": ["bến xe yên nghĩa", "yên nghĩa", "bx yên nghĩa", "quang trung (hà đông)", "ba la"],
                "gia lâm": ["bến xe gia lâm", "gia lâm", "bx gia lâm", "ngô gia khảm", "ngọc lâm"],
                "nước ngầm": ["bến xe nước ngầm", "nước ngầm", "bx nước ngầm", "pháp vân", "ngọc hồi"],
                "hồ gươm": ["hồ gươm", "bờ hồ", "hàng khay", "tràng thi", "đinh tiên hoàng", "hàng đào", "bác cổ", "trần khánh dư", "lý thái tổ"],
                "cầu giấy": ["cầu giấy", "điểm trung chuyển cầu giấy", "xuân thuỷ", "kim mã", "đường láng"],
                "nội bài": ["nội bài", "sân bay nội bài", "ga t1", "ga t2"],
                "nhổn": ["nhổn", "đại học công nghiệp", "cầu diễn", "diễn", "đường 32"],
                "linh đàm": ["linh đàm", "kđt linh đàm"],
                "long biên": ["long biên", "điểm trung chuyển long biên", "yên phụ", "hàng đậu"],
                "bến thành": ["bến thành", "chợ bến thành", "ga bến thành", "quận 1"],
                "suối tiên": ["suối tiên", "công viên suối tiên", "bến xe miền đông mới", "ga suối tiên"],
                "tân sơn nhất": ["tân sơn nhất", "sân bay tân sơn nhất", "ga quốc nội", "ga quốc tế"]
            }
            
        if not LocalTransitGraph._cache_ready:
            self._warm_cache()

    def _warm_cache(self):
        """Load toàn bộ routes và xây dựng đồ thị NetworkX."""
        import contextlib
        with contextlib.closing(self._get_connection()) as conn:
            cursor = conn.cursor()
            
            # 1. Load Route Details
            cursor.execute(
                "SELECT route_id, route_name, start_stop, end_stop, "
                "operating_hours, fare_vnd, outbound_itinerary, "
                "inbound_itinerary, vehicle_type, special_notes FROM routes"
            )
            LocalTransitGraph._routes_cache = {
                r[0]: {
                    "route_id": r[0],
                    "route_name": r[1],
                    "start_stop": r[2],
                    "end_stop": r[3],
                    "operating_hours": r[4],
                    "fare_vnd": r[5],
                    "outbound_itinerary": r[6],
                    "inbound_itinerary": r[7],
                    "vehicle_type": r[8],
                    "special_notes": r[9]
                } for r in cursor.fetchall()
            }

            # 2. Build NetworkX Graph
            cursor.execute("SELECT route_id, stop_name, stop_sequence, direction, distance_m FROM route_stops ORDER BY route_id, direction, stop_sequence")
            route_stops = cursor.fetchall()
            
            G = nx.DiGraph()
            stop_to_routes = {}
            
            prev_route = None
            prev_dir = None
            prev_stop_norm = None
            
            for r_id, stop_name, seq, direction, dist in route_stops:
                stop_norm = norm_str(stop_name)
                if stop_norm not in stop_to_routes:
                    stop_to_routes[stop_norm] = set()
                stop_to_routes[stop_norm].add(r_id)
                
                node = (stop_norm, r_id, direction)
                if not G.has_node(node):
                    G.add_node(node, stop_name=stop_name)
                
                if r_id == prev_route and direction == prev_dir:
                    prev_node = (prev_stop_norm, r_id, direction)
                    # Trọng số = 1 để ưu tiên ít trạm nhất, hoặc dùng distance_m
                    G.add_edge(prev_node, node, weight=1, route_id=r_id, type="ride")
                
                prev_route = r_id
                prev_dir = direction
                prev_stop_norm = stop_norm
            
            # Add Transfer Edges (Weight = 1000 to heavily penalize transfers)
            for stop, routes in stop_to_routes.items():
                routes = list(routes)
                for i in range(len(routes)):
                    for j in range(len(routes)):
                        if i != j:
                            r1 = routes[i]
                            r2 = routes[j]
                            for d1 in [0, 1]:
                                for d2 in [0, 1]:
                                    n1 = (stop, r1, d1)
                                    n2 = (stop, r2, d2)
                                    if G.has_node(n1) and G.has_node(n2):
                                        real_stop_name = G.nodes[n1]["stop_name"]
                                        G.add_edge(n1, n2, weight=1000, type="transfer", stop_name=real_stop_name)
            
            LocalTransitGraph._graph = G
            LocalTransitGraph._stop_to_routes = stop_to_routes
            
        LocalTransitGraph._cache_ready = True

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _normalize_location(self, name: str) -> List[str]:
        if not name:
            return []
        low_name = norm_str(name)
        for key, aliases in self.alias_map.items():
            norm_key = norm_str(key)
            norm_aliases = [norm_str(a) for a in aliases]
            if norm_key in low_name or any(a in low_name for a in norm_aliases):
                return norm_aliases
        return [low_name]

    def calculate_haversine(self, stop1: str, stop2: str) -> float:
        """
        Mock khoảng cách Haversine giữa 2 điểm dừng (đáp ứng yêu cầu đồ án).
        Vì dữ liệu tọa độ không có sẵn trong SQLite, hàm này tạm trả về khoảng cách ảo.
        """
        return 0.0

    def find_optimal_route(self, origin: str, destination: str) -> List[RouteRecommendation]:
        origin_aliases = self._normalize_location(origin)
        dest_aliases = self._normalize_location(destination)
        
        G = LocalTransitGraph._graph
        stop_to_routes = LocalTransitGraph._stop_to_routes
        
        # 1. Tìm các trạm xuất phát và đích
        start_nodes = set()
        end_nodes = set()
        
        for stop_norm in stop_to_routes.keys():
            if any(oa in stop_norm for oa in origin_aliases):
                for r in stop_to_routes[stop_norm]:
                    for d in [0, 1]:
                        if G.has_node((stop_norm, r, d)):
                            start_nodes.add((stop_norm, r, d))
                            
            if any(da in stop_norm for da in dest_aliases):
                for r in stop_to_routes[stop_norm]:
                    for d in [0, 1]:
                        if G.has_node((stop_norm, r, d)):
                            end_nodes.add((stop_norm, r, d))
                            
        if not start_nodes or not end_nodes:
            return []
            
        # 2. Tìm đường đi ngắn nhất bằng Dijkstra (Ưu tiên ít chuyển tuyến nhất)
        best_path = None
        best_weight = float('inf')
        
        for src in start_nodes:
            try:
                lengths, paths = nx.single_source_dijkstra(G, src, weight='weight')
                for tgt in end_nodes:
                    if tgt in lengths and lengths[tgt] < best_weight:
                        best_weight = lengths[tgt]
                        best_path = paths[tgt]
            except Exception:
                continue
                
        if not best_path:
            return []
            
        # 3. Phân tích lộ trình từ Dijkstra Path
        segments = []
        current_route = None
        current_start_stop = None
        current_end_stop = None
        transfers_count = 0
        total_fare = 0
        
        for i in range(len(best_path)):
            node = best_path[i]
            stop_norm, r_id, d = node
            real_stop_name = G.nodes[node]["stop_name"]
            
            if current_route != r_id:
                if current_route is not None:
                    segments.append((current_route, current_start_stop, current_end_stop))
                    transfers_count += 1
                current_route = r_id
                current_start_stop = real_stop_name
                r_info = LocalTransitGraph._routes_cache.get(r_id, {})
                total_fare += r_info.get("fare_vnd", 7000)
                
            current_end_stop = real_stop_name
            
        if current_route is not None:
            segments.append((current_route, current_start_stop, current_end_stop))
            
        # 4. Tạo kết quả trả về
        r1_id = segments[0][0]
        r1_info = LocalTransitGraph._routes_cache.get(r1_id, {})
        v_type1 = r1_info.get("vehicle_type", "Bus")
        
        maps_origin = urllib.parse.quote(origin.title() + " Hà Nội")
        maps_dest = urllib.parse.quote(destination.title() + " Hà Nội")
        gmaps_url = f"https://www.google.com/maps/dir/?api=1&origin={maps_origin}&destination={maps_dest}&travelmode=transit"
        
        if transfers_count == 0:
            route_id = r1_id
            route_name = f"[{v_type1}] Tuyến {r1_id}: {r1_info.get('route_name', '')}"
            desc = f"Đi thẳng bằng {route_name} từ {origin.title()} đến {destination.title()}. Giá vé: {total_fare:,} VNĐ. (Phương án tối ưu - Dijkstra)"
            itin = f"Chiều đi: {r1_info.get('outbound_itinerary','')} | Chiều về: {r1_info.get('inbound_itinerary','')}"
            transfer_stop = None
        else:
            r2_id = segments[1][0]
            r2_info = LocalTransitGraph._routes_cache.get(r2_id, {})
            v_type2 = r2_info.get("vehicle_type", "Bus")
            transfer_stop = segments[0][2].title()
            
            route_id = f"{r1_id} -> {r2_id}"
            route_name = f"[{v_type1}] Tuyến {r1_id} chuyển sang [{v_type2}] Tuyến {r2_id}"
            desc = f"Đi {route_name}. Đổi xe tại {transfer_stop}. Tổng tiền vé: {total_fare:,} VNĐ. (Phương án chuyển tuyến tối ưu - Dijkstra)"
            itin = f"Chuyến 1 ({r1_id}): {r1_info.get('outbound_itinerary','')} \nChuyển tại: {transfer_stop}\nChuyến 2 ({r2_id}): {r2_info.get('outbound_itinerary','')}"

        rec = RouteRecommendation(
            route_id=route_id,
            route_name=route_name,
            board_stop=origin.title(),
            alight_stop=destination.title(),
            transfers_count=transfers_count,
            transfer_stop=transfer_stop,
            fare_vnd=total_fare,
            operating_hours=r1_info.get("operating_hours", "5:00 - 21:00"),
            description=desc,
            itinerary=itin,
            google_maps_url=gmaps_url
        )
        
        return [rec]

    def search_routes_by_keyword(self, keyword: str) -> List[RouteRecommendation]:
        import contextlib
        fts_route_ids = set()
        matched_routes = []
        
        kw_norm = norm_str(keyword)
        kw_aliases = self._normalize_location(keyword)

        with contextlib.closing(self._get_connection()) as conn:
            cursor = conn.cursor()
            try:
                fts_query = " OR ".join([f'"{a}"' for a in kw_aliases if len(a) > 2])
                if not fts_query: fts_query = f'"{kw_norm}"'
                cursor.execute("SELECT route_id FROM routes_fts WHERE routes_fts MATCH ?", (fts_query,))
                for row in cursor.fetchall():
                    fts_route_ids.add(row[0])
            except Exception:
                pass
            
        all_routes = LocalTransitGraph._routes_cache or {}

        for r_id, r_info in all_routes.items():
            if r_id in fts_route_ids:
                match_found = True
            else:
                itin = f"Chiều đi: {r_info.get('outbound_itinerary','')} | Chiều về: {r_info.get('inbound_itinerary','')}"
                text_to_search = norm_str(f"{r_id} {r_info.get('route_name','')} {r_info.get('start_stop','')} {r_info.get('end_stop','')} {itin}")
                match_found = any(a in text_to_search for a in kw_aliases)

            if match_found:
                v_type = r_info.get("vehicle_type", "Bus")
                fare_val = r_info.get("fare_vnd", 7000)
                time_str = r_info.get("operating_hours", "5:00 - 21:00")
                notes = r_info.get("special_notes", "")
                r_name = r_info.get("route_name", "")
                out_itin = r_info.get("outbound_itinerary", "")
                in_itin = r_info.get("inbound_itinerary", "")
                
                desc = f"Thông tin tuyến [{v_type}] Tuyến {r_id} ({r_name}). Giá vé: {fare_val:,} VNĐ. Thời gian hoạt động: {time_str}"
                if notes:
                    desc += f"\nLưu ý: {notes}"
                
                rec = RouteRecommendation(
                    route_id=r_id,
                    route_name=f"[{v_type}] Tuyến {r_id}: {r_name}",
                    board_stop="",
                    alight_stop="",
                    transfers_count=0,
                    fare_vnd=fare_val,
                    operating_hours=time_str,
                    description=desc,
                    itinerary=f"Chiều đi: {out_itin} | Chiều về: {in_itin}"
                )
                matched_routes.append(rec)
                if len(matched_routes) >= 5:
                    break

        return matched_routes
