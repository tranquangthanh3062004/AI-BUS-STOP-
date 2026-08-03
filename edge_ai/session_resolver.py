"""
edge_ai/session_resolver.py
Centralized session + entity resolution — eliminates duplicate code
between offline_pipeline.py and online_pipeline.py.
"""
from typing import Tuple, Optional
from shared.schemas import IntentResult
from edge_ai.session_manager import SessionManager
from edge_ai.intent_classifier import IntentClassifier


NOISE_WORDS = frozenset(["xe buýt", "xe bus", "đi", "xe", "tuyến", "đến", "tôi muốn đi"])


def resolve_entities_from_session(
    session_id: str,
    raw_text: str,
    intent_res: IntentResult,
    session_manager: SessionManager,
    intent_classifier: IntentClassifier,
) -> Tuple[IntentResult, Optional[str]]:
    """
    Fills missing origin/destination from session context.
    Returns (updated_intent_res, clarification_text_or_None).
    If clarification_text is not None → caller must return CLARIFICATION response immediately.
    """
    session_data = session_manager.get_session(session_id)

    # Restore entities from previous turn
    if session_data.get("intent") == "ROUTE_QUERY":
        if intent_res.intent_label in ("UNKNOWN", "ROUTE_QUERY") \
                and not intent_res.entities.route_id:
            intent_res.intent_label = "ROUTE_QUERY"
            if not intent_res.entities.origin and session_data.get("origin"):
                intent_res.entities.origin = session_data["origin"]
            if not intent_res.entities.destination and session_data.get("destination"):
                intent_res.entities.destination = session_data["destination"]

            # Try to fill still-missing slot from current input
            input_val = (
                intent_res.entities.location_keyword
                or intent_classifier._clean_entity_text(raw_text.strip())
                or raw_text.strip()
            )
            if input_val and input_val.lower() not in NOISE_WORDS:
                if intent_res.entities.origin and not intent_res.entities.destination:
                    intent_res.entities.destination = input_val
                elif intent_res.entities.destination and not intent_res.entities.origin:
                    intent_res.entities.origin = input_val
                elif not intent_res.entities.origin and not intent_res.entities.destination:
                    intent_res.entities.destination = input_val

    # Map location_keyword → destination if needed
    if intent_res.intent_label == "ROUTE_QUERY":
        if intent_res.entities.location_keyword and not intent_res.entities.destination:
            intent_res.entities.destination = intent_res.entities.location_keyword

        missing_origin = not intent_res.entities.origin and not intent_res.entities.route_id
        missing_dest = not intent_res.entities.destination and not intent_res.entities.route_id

        if missing_origin or missing_dest:
            session_manager.update_session(
                session_id,
                intent="ROUTE_QUERY",
                origin=intent_res.entities.origin,
                destination=intent_res.entities.destination,
            )
            if missing_origin and missing_dest:
                return intent_res, "Bạn muốn đi từ đâu đến đâu?"
            elif missing_origin:
                return intent_res, (
                    f"Bạn muốn đi đến {intent_res.entities.destination}, "
                    "vậy bạn xuất phát từ đâu?"
                )
            else:
                return intent_res, (
                    f"Bạn xuất phát từ {intent_res.entities.origin}, "
                    "vậy bạn muốn đi đến đâu?"
                )
    else:
        session_manager.clear_session(session_id)

    return intent_res, None
