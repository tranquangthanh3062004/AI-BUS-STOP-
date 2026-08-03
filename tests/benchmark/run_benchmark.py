"""
tests/benchmark/run_benchmark.py
Script đo lường độ chính xác (Accuracy, F1) và hiệu năng của hệ thống RAG
trên tập ground_truth_100.json
"""
import os
import sys
import json
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from edge_ai.offline_pipeline import OfflineAIAssistant
from shared.schemas import QueryRequest

def run_benchmark():
    gt_file = os.path.join(os.path.dirname(__file__), "ground_truth_100.json")
    with open(gt_file, "r", encoding="utf-8") as f:
        queries = json.load(f)
        
    assistant = OfflineAIAssistant()
    
    print(f"Bắt đầu benchmark với {len(queries)} câu hỏi...")
    total_time = 0
    correct_intent = 0
    valid_answers = 0
    
    # Rút gọn lấy 20 câu để demo cho nhanh nếu cần, nhưng ta sẽ chạy hết
    for idx, q in enumerate(queries):
        start_t = time.time()
        req = QueryRequest(raw_text=q["query"])
        res = assistant.process_query(req)
        exec_time = time.time() - start_t
        total_time += exec_time
        
        # Check intent
        intent_match = (res.intent == q["intent"])
        if intent_match:
            correct_intent += 1
            
        # Check answer relevancy (cơ bản dựa trên expected_keywords)
        ans_lower = res.answer_text.lower()
        keyword_hit = False
        for kw in q.get("expected_keywords", []):
            if kw.lower() in ans_lower:
                keyword_hit = True
                break
        
        # Đặc biệt với PROMPT_INJECTION
        if q["intent"] == "PROMPT_INJECTION":
            if "không hợp lệ" in ans_lower or "từ chối" in ans_lower or "an toàn" in ans_lower or res.status == "error":
                keyword_hit = True
                
        if keyword_hit:
            valid_answers += 1
            
        if (idx+1) % 10 == 0:
            print(f"Đã xử lý {idx+1}/{len(queries)} câu...")

    print("==================================================")
    print("KẾT QUẢ BENCHMARK:")
    print(f"- Tổng số câu: {len(queries)}")
    print(f"- Intent Accuracy: {correct_intent/len(queries)*100:.1f}%")
    print(f"- Answer Relevancy (Keyword hit): {valid_answers/len(queries)*100:.1f}%")
    print(f"- Thời gian trung bình: {total_time/len(queries):.3f}s / câu")
    print("==================================================")

if __name__ == "__main__":
    run_benchmark()
