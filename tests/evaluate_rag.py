import os
import sys
import json
import asyncio
from dotenv import load_dotenv

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
load_dotenv()

from edge_ai.offline_pipeline import OfflineAIAssistant
from shared.schemas import QueryRequest

# DeepEval imports
try:
    from deepeval.metrics import FaithfulnessMetric, AnswerRelevancyMetric
    from deepeval.test_case import LLMTestCase
    from deepeval import evaluate
except ImportError:
    print("Please install deepeval to run these metrics: pip install deepeval")
    sys.exit(1)

def run_evaluation():
    print("Setting up Offline RAG Evaluation...")
    assistant = OfflineAIAssistant()
    
    test_queries = [
        "Từ Mỹ Đình đến Bách Khoa đi xe buýt nào?",
        "Tuyến buýt 26 chạy ở đâu?",
        "Giá vé xe buýt ở Hà Nội là bao nhiêu?",
        "Có xe buýt nào đi qua Lăng Bác không?"
    ]
    
    test_cases = []
    
    for query in test_queries:
        print(f"Generating answer for: '{query}'")
        req = QueryRequest(raw_text=query, session_id="eval_session")
        response = assistant.process_query(req)
        
        # Format context from response
        context_str_list = response.sources_used
        if not context_str_list:
            context_str_list = ["No specific sources found in context."]
            
        test_case = LLMTestCase(
            input=query,
            actual_output=response.answer_text,
            retrieval_context=context_str_list
        )
        test_cases.append(test_case)
        
    print("\nRunning DeepEval Metrics...")
    
    # Initialize metrics
    # We use basic thresholds. Note: DeepEval requires an OpenAI key by default to run evaluator LLM
    faithfulness = FaithfulnessMetric(threshold=0.7)
    answer_relevancy = AnswerRelevancyMetric(threshold=0.7)
    
    try:
        evaluate(test_cases, [faithfulness, answer_relevancy])
    except Exception as e:
        print(f"DeepEval encountered an error (likely missing API key for evaluator LLM): {e}")

if __name__ == "__main__":
    run_evaluation()
