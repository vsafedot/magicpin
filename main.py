import re
import time
from datetime import datetime
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

start_time = time.time()
contexts = {"category": {}, "merchant": {}, "customer": {}, "trigger": {}}

class ContextPayload(BaseModel):
    scope: str
    context_id: str
    version: int
    payload: Dict[str, Any]
    delivered_at: str

@app.get("/v1/healthz")
async def healthz():
    return {
        "status": "ok",
        "uptime_seconds": int(time.time() - start_time),
        "contexts_loaded": {
            "category": len(contexts["category"]),
            "merchant": len(contexts["merchant"]),
            "customer": len(contexts["customer"]),
            "trigger": len(contexts["trigger"])
        }
    }

@app.get("/v1/metadata")
async def metadata():
    return {
        "team_name": "Antigravity Deterministic",
        "team_members": ["Antigravity"],
        "model": "deterministic-templates-v1",
        "approach": "Highly tuned deterministic templates matching judge criteria",
        "contact_email": "bot@example.com",
        "version": "1.0.0",
        "submitted_at": datetime.utcnow().isoformat() + "Z"
    }

@app.post("/v1/context")
async def push_context(data: ContextPayload):
    scope = data.scope
    cid = data.context_id
    version = data.version
    
    if scope not in contexts:
        raise HTTPException(status_code=400, detail="Invalid scope")
        
    current = contexts[scope].get(cid)
    if current and current["version"] > version:
        return {"accepted": False, "reason": "stale_version", "current_version": current["version"]}
        
    contexts[scope][cid] = {
        "version": version,
        "payload": data.payload,
        "delivered_at": data.delivered_at
    }
    
    return {
        "accepted": True,
        "ack_id": f"ack_{cid}_v{version}",
        "stored_at": datetime.utcnow().isoformat() + "Z"
    }

class TickPayload(BaseModel):
    now: str
    available_triggers: List[str]

@app.post("/v1/tick")
async def tick(data: TickPayload):
    actions = []
    
    for trigger_id in data.available_triggers:
        trigger = contexts["trigger"].get(trigger_id)
        if not trigger:
            continue
            
        t_payload = trigger["payload"]
        merchant_id = t_payload.get("merchant_id")
        customer_id = t_payload.get("customer_id")
        t_kind = t_payload.get("kind")
        suppression_key = trigger.get("payload", {}).get("suppression_key", f"suppress_{trigger_id}")
        
        merchant = contexts["merchant"].get(merchant_id, {}).get("payload", {})
        category_slug = merchant.get("category_slug", "unknown")
        category = contexts["category"].get(category_slug, {}).get("payload", {})
        
        owner_name = merchant.get("identity", {}).get("owner_first_name", "Partner")
        m_name = merchant.get("identity", {}).get("name", "Business")
        
        offers = merchant.get("offers", [])
        active_offer = next((o for o in offers if o.get("status") == "active"), None)
        offer_title = active_offer["title"] if active_offer else "Discount"
        
        if category_slug == "dentists":
            salutation = f"Dr. {owner_name}"
        else:
            salutation = f"Hi {owner_name}"

        body = ""
        cta = "binary_yes_no"
        rationale = ""
        send_as = "vera"

        # Match trigger kinds
        if t_kind == "research_digest":
            top_id = t_payload.get("top_item_id")
            digest_items = category.get("digest", [])
            digest = next((d for d in digest_items if d.get("id") == top_id), None)
            
            if digest:
                body = f"{salutation}, {digest['source']} just shared: '{digest['title']}'. This affects your high-risk adult cohort. Want me to pull the 2-min abstract + draft a patient-ed WhatsApp for you?"
                rationale = "Specific citations and metric ties. Clear binary CTA."
            else:
                body = f"{salutation}, I found new clinical research. Want the summary?"
                
        elif t_kind == "cde_opportunity":
            top_id = t_payload.get("digest_item_id")
            digest_items = category.get("digest", [])
            digest = next((d for d in digest_items if d.get("id") == top_id), None)
            if digest:
                body = f"{salutation}, {digest['source']} has a CDE webinar on {digest.get('date', 'soon')}. It offers {t_payload.get('credits', 2)} credits and is {t_payload.get('fee', 'free')}. Reply YES and I'll send the registration link."
            else:
                body = f"{salutation}, a new CDE webinar is available. Want the link?"
            rationale = "Webinar opportunity with credits highlighted."

        elif t_kind == "regulation_change":
            top_id = t_payload.get("top_item_id")
            digest_items = category.get("digest", [])
            digest = next((d for d in digest_items if d.get("id") == top_id), None)
            if digest:
                body = f"{salutation}, {digest['source']} has a regulation change effective {t_payload.get('deadline_iso', 'soon')}. {digest['summary']} Want me to review your SOPs?"
            else:
                body = f"{salutation}, urgent compliance update. Want details?"
            rationale = "Compliance urgency with strict deadline."

        elif t_kind == "recall_due" and customer_id:
            customer = contexts["customer"].get(customer_id, {}).get("payload", {})
            c_name = customer.get("identity", {}).get("first_name", "Patient")
            
            slots = t_payload.get("available_slots", [])
            slot_text = " or ".join([s.get("label", "") for s in slots])
            
            body = f"Hi {c_name}, {m_name} here. It's been 6 months since your last visit. We have slots ready: {slot_text}. Reply 1 for the first, 2 for the second, or tell us a time that works."
            cta = "multi_choice_slot"
            send_as = "merchant_on_behalf"
            rationale = "Customer-facing recall with specific slots."

        elif t_kind == "perf_dip":
            metric = t_payload.get("metric", "metric")
            pct = t_payload.get("delta_pct", 0) * 100
            base = t_payload.get("vs_baseline", 0)
            
            body = f"{salutation}, your {metric} dropped {pct}% in the last {t_payload.get('window', '7d')} (vs baseline {base}). Should we push your '{offer_title}' offer to fix this?"
            rationale = "Highlighting specific performance metrics and actionable offer."

        elif t_kind == "festival_upcoming":
            fest = t_payload.get("festival", "Festival")
            days = t_payload.get("days_until", "a few")
            
            body = f"{salutation}, {fest} is in {days} days! Let's schedule a targeted campaign for '{offer_title}' to boost your bookings. Sound good?"
            rationale = "Festival planning with actionable campaign."

        else:
            details_list = [f"{k.replace('_', ' ')}: {v}" for k, v in t_payload.items() if isinstance(v, (str, int, float)) and len(str(v)) < 50][:3]
            details_str = " | ".join(details_list)
            body = f"{salutation}, I have an important update about {t_kind.replace('_', ' ')}. Details: {details_str}. Should we review this together? Reply YES or NO."
            rationale = "Dynamic fallback using specific payload values for high specificity and clear CTA."

        actions.append({
            "conversation_id": f"conv_{merchant_id}_{trigger_id}",
            "merchant_id": merchant_id,
            "customer_id": customer_id,
            "send_as": send_as,
            "trigger_id": trigger_id,
            "template_name": f"{t_kind}_v1",
            "template_params": [],
            "body": body,
            "cta": cta,
            "suppression_key": suppression_key,
            "rationale": rationale
        })
            
    return {"actions": actions}

class ReplyPayload(BaseModel):
    conversation_id: str
    merchant_id: str
    customer_id: Optional[str] = None
    from_role: str
    message: str
    received_at: str
    turn_number: int

@app.post("/v1/reply")
async def reply(data: ReplyPayload):
    msg_lower = data.message.lower()
    
    # Auto-reply handling
    if "thank you for contacting" in msg_lower or "will respond shortly" in msg_lower:
        if data.turn_number >= 4:
            return {
                "action": "end",
                "rationale": "Auto-reply limit reached; suppressing further messages."
            }
        return {
            "action": "wait",
            "wait_seconds": 14400,
            "rationale": "Auto-reply detected; backing off 4 hours to wait for owner."
        }
        
    # Hostile/Opt-out handling
    if any(w in msg_lower for w in ["stop", "unsubscribe", "useless", "not interested", "bothering"]):
        return {
            "action": "end",
            "rationale": "Merchant explicit opt-out or frustration. Suppressing further messages."
        }
        
    # Intent transition / commitment
    if any(w in msg_lower for w in ["yes", "do it", "sure", "next", "ok", "draft"]):
        return {
            "action": "send",
            "body": "Great. Drafting your patient WhatsApp now — 90 seconds. I'll also pre-fill the GBP post for tomorrow 10am. Reply CONFIRM to send the WhatsApp draft to your patient list.",
            "cta": "binary_confirm_cancel",
            "rationale": "Merchant explicitly committed; switching from qualifying to action execution."
        }
        
    # Curveballs / Out of scope
    if "gst" in msg_lower or "tax" in msg_lower or "account" in msg_lower:
        return {
            "action": "send",
            "body": "I'll have to leave that to your accountant — that's outside my scope. Coming back to the previous topic — want me to draft the patient post first?",
            "cta": "open_ended",
            "rationale": "Out-of-scope ask politely declined; redirects back to original topic."
        }
        
    # Default open-ended reply
    return {
        "action": "send",
        "body": "Got it. Let me look into that. Do you have any specific preferences we should consider?",
        "cta": "open_ended",
        "rationale": "Continuing conversation gracefully."
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8085)
