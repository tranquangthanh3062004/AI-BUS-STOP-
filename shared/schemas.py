"""
shared/schemas.py
Pydantic data models for the Offline AI Assistant pipeline.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    raw_text: str = Field(..., description="Câu hỏi của hành khách (Text hoặc STT Output)")
    user_location: Optional[str] = Field(default=None, description="Vị trí trạm xe buýt hiện tại nếu có")
    session_id: Optional[str] = Field(default="default_session", description="Mã phiên tương tác")


class EntityExtract(BaseModel):
    origin: Optional[str] = Field(default=None, description="Điểm đi (Bến xe Mỹ Đình, Nhổn...)")
    destination: Optional[str] = Field(default=None, description="Điểm đến (ĐH Bách Khoa, Hồ Gươm...)")
    route_id: Optional[str] = Field(default=None, description="Mã số tuyến xe buýt (01, 26, 32...)")
    location_keyword: Optional[str] = Field(default=None, description="Tên địa danh/bệnh viện/trường học")


class IntentResult(BaseModel):
    intent_label: str = Field(..., description="ROUTE_QUERY | FARE_QUERY | SCHEDULE_QUERY | RULE_QUERY | METRO_QUERY | UNKNOWN")
    confidence: float = Field(default=1.0, description="Độ tin cậy của intent classification")
    entities: EntityExtract = Field(default_factory=EntityExtract)


class RouteRecommendation(BaseModel):
    route_id: str = Field(..., description="Mã số tuyến (Ví dụ: 26 hoặc 32 -> 31)")
    route_name: str = Field(..., description="Tên tuyến xe buýt")
    board_stop: str = Field(..., description="Trạm lên xe")
    alight_stop: str = Field(..., description="Trạm xuống xe")
    transfers_count: int = Field(default=0, description="Số lần chuyển tuyến")
    transfer_stop: Optional[str] = Field(default=None, description="Trạm trung chuyển nếu có")
    fare_vnd: int = Field(default=7000, description="Giá vé lượt (VNĐ)")
    operating_hours: str = Field(default="5:00 - 21:00", description="Giờ hoạt động")
    distance_m: Optional[int] = Field(default=None, description="Tổng quãng đường di chuyển (mét)")
    duration_s: Optional[int] = Field(default=None, description="Tổng thời gian di chuyển (giây)")
    description: str = Field(..., description="Mô tả tóm tắt lộ trình")
    itinerary: Optional[str] = Field(default=None, description="Chi tiết các trạm đi qua")
    google_maps_url: Optional[str] = Field(default=None, description="Link Google Maps Deep Link")


class RetrievedContext(BaseModel):
    intent: IntentResult
    structured_routes: List[RouteRecommendation] = Field(default_factory=list)
    unstructured_chunks: List[str] = Field(default_factory=list)
    valid_route_ids: List[str] = Field(default_factory=list)
    valid_stop_names: List[str] = Field(default_factory=list)


class OfflineResponse(BaseModel):
    status: str = Field(..., description="SUCCESS | NO_DATA | FALLBACK | CLARIFICATION")
    raw_query: str
    normalized_query: str
    intent: str
    answer_text: str = Field(..., description="Câu trả lời hoàn chỉnh Tiếng Việt cho hành khách")
    recommendations: List[RouteRecommendation] = Field(default_factory=list)
    execution_time_ms: float = Field(..., description="Tổng thời gian xử lý (ms)")
    sources_used: List[str] = Field(default_factory=list)
    is_offline_mode: bool = Field(default=True, description="Đánh dấu câu trả lời từ Offline Pipeline")
