import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from backend.online_pipeline import OnlineAIAssistant
from shared.schemas import QueryRequest
a = OnlineAIAssistant()
req = QueryRequest(raw_text='Tìm đường từ Time City đến nhà hát lớn Hà Nội', session_id='test')
print(a.process_query(req).answer_text)
