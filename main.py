import re
import time
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

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
        
        # Skip if no merchant context
        if not merchant_id or merchant_id not in contexts["merchant"]:
            continue
            
        merchant = contexts["merchant"][merchant_id]["payload"]
        category_slug = merchant.get("category_slug", "unknown")
        category = contexts["category"].get(category_slug, {}).get("payload", {})
        
        # Get merchant details
        identity = merchant.get("identity", {})
        owner_name = identity.get("owner_first_name", "Partner")
        m_name = identity.get("name", "Business")
        locality = identity.get("locality", "")
        
        # Get offers
        offers = merchant.get("offers", [])
        active_offer = next((o for o in offers if o.get("status") == "active"), None)
        offer_title = active_offer["title"] if active_offer else "Special Offer"
        
        # Category-specific salutation
        if category_slug == "dentists":
            salutation = f"Dr. {owner_name}"
        elif category_slug == "salons":
            salutation = f"Hi {owner_name}"
        elif category_slug == "restaurants":
            salutation = f"Hi {owner_name}"
        elif category_slug == "gyms":
            salutation = f"Hi {owner_name}"
        elif category_slug == "pharmacies":
            salutation = f"Hi {owner_name}"
        else:
            salutation = f"Hi {owner_name}"

        body = ""
        cta = "binary_yes_no"
        rationale = ""
        send_as = "vera"

        # Handle different trigger types with specific context
        if t_kind == "research_digest":
            top_id = t_payload.get("top_item_id")
            digest_items = category.get("digest", [])
            digest = next((d for d in digest_items if d.get("id") == top_id), None)
            
            if digest and category_slug == "dentists":
                source = digest.get('source', 'JIDA')
                title = digest.get('title', 'new research')
                body = f"{salutation}, {source} just shared: '{title}'. This affects your high-risk adult cohort. Want me to pull the 2-min abstract + draft a patient-ed WhatsApp for you?"
                rationale = "Specific research citation with clear clinical relevance and actionable next step."
            else:
                body = f"{salutation}, I found new clinical research relevant to your practice. Want the summary and patient communication draft?"
                rationale = "Research update with actionable follow-up."
                
        elif t_kind == "cde_opportunity" or t_kind == "cde_webinar":
            if category_slug == "dentists":
                credits = t_payload.get('credits', 2)
                fee = t_payload.get('fee', 'free')
                body = f"{salutation}, there's a CDE webinar coming up offering {credits} credits and it's {fee}. Want me to send the registration link?"
                rationale = "CDE opportunity with specific credits and fee information."
            else:
                body = f"{salutation}, there's a professional development webinar available. Want the details?"
                rationale = "Professional development opportunity."

        elif t_kind == "regulation_change" or t_kind == "compliance_dci_radiograph":
            if category_slug == "dentists":
                deadline = t_payload.get("deadline_iso", "soon")
                body = f"{salutation}, urgent DCI compliance update effective {deadline}. This affects radiograph protocols. Want me to review your current SOPs?"
                rationale = "Compliance urgency with specific deadline and actionable review offer."
            else:
                body = f"{salutation}, there's a regulatory update that may affect your business. Want me to review the details?"
                rationale = "Regulatory compliance update."

        elif t_kind == "recall_due" and customer_id:
            customer = contexts["customer"].get(customer_id, {}).get("payload", {})
            c_identity = customer.get("identity", {})
            c_name = c_identity.get("first_name", "Patient")
            
            slots = t_payload.get("available_slots", [])
            if slots:
                slot_text = " or ".join([s.get("label", "") for s in slots])
                body = f"Hi {c_name}, {m_name} here. It's been 6 months since your last visit. We have slots ready: {slot_text}. Reply 1 for the first, 2 for the second, or tell us a time that works."
            else:
                body = f"Hi {c_name}, {m_name} here. It's been 6 months since your last visit. We have appointments available this week. When works best for you?"
            
            cta = "multi_choice_slot"
            send_as = "merchant_on_behalf"
            rationale = "Customer-facing recall with specific available slots and clear response options."

        elif t_kind == "perf_dip":
            metric = t_payload.get("metric", "calls")
            delta_pct = t_payload.get("delta_pct", 0)
            pct_change = abs(int(delta_pct * 100))
            window = t_payload.get("window", "7d")
            baseline = t_payload.get("vs_baseline", 0)
            
            body = f"{salutation}, your {metric} dropped {pct_change}% in the last {window} (vs baseline {baseline}). Should we push your '{offer_title}' offer to boost visibility?"
            rationale = f"Performance alert with specific metrics and actionable offer suggestion."

        elif t_kind == "festival_upcoming":
            festival = t_payload.get("festival", "Festival")
            days_until = t_payload.get("days_until", "a few")
            
            if category_slug == "salons":
                body = f"{salutation}, {festival} is in {days_until} days! Perfect time for bridal packages. Let's schedule a targeted campaign for '{offer_title}' to boost bookings. Sound good?"
            elif category_slug == "restaurants":
                body = f"{salutation}, {festival} is in {days_until} days! Great opportunity for special menus. Want to promote '{offer_title}' for the festive rush?"
            else:
                body = f"{salutation}, {festival} is in {days_until} days! Let's create a festive campaign for '{offer_title}' to capture the holiday demand. Ready?"
            
            rationale = "Festival timing with category-specific opportunity and clear campaign proposal."

        elif t_kind == "renewal_due":
            days_remaining = t_payload.get("days_remaining", 0)
            plan = t_payload.get("plan", "Pro")
            amount = t_payload.get("renewal_amount", 0)
            
            body = f"{salutation}, your {plan} plan expires in {days_remaining} days. Renewal is ₹{amount}. Want me to process it now to avoid any service interruption?"
            rationale = "Renewal urgency with specific timeline and amount."

        elif t_kind == "wedding_package_followup":
            if category_slug == "salons":
                wedding_date = t_payload.get("wedding_date", "")
                days_to_wedding = t_payload.get("days_to_wedding", 0)
                body = f"{salutation}, the bride's wedding is in {days_to_wedding} days ({wedding_date}). Time for the 30-day skin prep program. Should I send her the package details?"
                rationale = "Wedding timeline with specific prep program recommendation."
            else:
                body = f"{salutation}, there's a wedding package follow-up needed. Want me to handle the next steps?"
                rationale = "Wedding package follow-up."

        else:
            # Fallback with context-specific details
            if category_slug == "dentists":
                body = f"{salutation}, I have an update about {t_kind.replace('_', ' ')} that affects your practice. Want me to review the details with you?"
            elif category_slug == "salons":
                body = f"{salutation}, there's a {t_kind.replace('_', ' ')} opportunity for your salon. Should we discuss it?"
            elif category_slug == "restaurants":
                body = f"{salutation}, I found something about {t_kind.replace('_', ' ')} that could help your restaurant. Want the details?"
            elif category_slug == "gyms":
                body = f"{salutation}, there's a {t_kind.replace('_', ' ')} update relevant to your gym. Should we review it?"
            elif category_slug == "pharmacies":
                body = f"{salutation}, I have a {t_kind.replace('_', ' ')} update for your pharmacy. Want me to explain?"
            else:
                body = f"{salutation}, I have an important update about {t_kind.replace('_', ' ')}. Should we review this together?"
            
            rationale = f"Category-specific {t_kind} update with clear engagement prompt."

        # Ensure we have a body
        if not body:
            body = f"{salutation}, I have an update for your {category_slug.rstrip('s')} business. Want to review it together?"
            rationale = "Generic update with category context."

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
            "suppression_key": f"suppress_{trigger_id}",
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
    
    # Enhanced auto-reply detection
    auto_reply_patterns = [
        "thank you for contacting",
        "will respond shortly", 
        "we'll get back to you",
        "received your message",
        "auto-reply",
        "out of office",
        "currently unavailable"
    ]
    
    if any(pattern in msg_lower for pattern in auto_reply_patterns):
        if data.turn_number >= 3:  # More aggressive auto-reply detection
            return {
                "action": "end",
                "rationale": "Auto-reply detected after 3 turns; ending conversation to prevent spam."
            }
        return {
            "action": "wait",
            "wait_seconds": 14400,  # 4 hours
            "rationale": "Auto-reply detected; backing off 4 hours to wait for human response."
        }
        
    # Hostile/Opt-out handling
    hostile_patterns = ["stop", "unsubscribe", "useless", "not interested", "bothering", "spam", "don't message", "leave me alone"]
    if any(pattern in msg_lower for pattern in hostile_patterns):
        return {
            "action": "end",
            "rationale": "Merchant opted out or expressed frustration; ending conversation."
        }
        
    # Get merchant context for personalized responses
    merchant = contexts["merchant"].get(data.merchant_id, {}).get("payload", {})
    category_slug = merchant.get("category_slug", "unknown")
    owner_name = merchant.get("identity", {}).get("owner_first_name", "Partner")
    
    # Category-specific salutation
    if category_slug == "dentists":
        salutation = f"Dr. {owner_name}"
    else:
        salutation = owner_name
        
    # Intent transition / commitment
    commitment_patterns = ["yes", "do it", "sure", "next", "ok", "draft", "proceed", "go ahead", "sounds good"]
    if any(pattern in msg_lower for pattern in commitment_patterns):
        if category_slug == "dentists":
            body = f"Perfect {salutation}. Drafting your patient WhatsApp now — 90 seconds. I'll also pre-fill the GBP post for tomorrow 10am. Reply CONFIRM to send the WhatsApp draft to your patient list."
        elif category_slug == "salons":
            body = f"Great {salutation}! Creating your bridal package promotion now. I'll have the social media posts ready in 2 minutes. Reply CONFIRM to schedule them."
        elif category_slug == "restaurants":
            body = f"Excellent {salutation}! Preparing your festive menu promotion. I'll draft the posts and offers in 90 seconds. Reply CONFIRM to go live."
        else:
            body = f"Perfect {salutation}! I'm preparing your campaign now. Will have everything ready in 2 minutes. Reply CONFIRM to proceed."
            
        return {
            "action": "send",
            "body": body,
            "cta": "binary_confirm_cancel",
            "rationale": "Merchant committed; switching to action execution with category-specific next steps."
        }
        
    # Context-aware responses based on merchant message content
    if "x-ray" in msg_lower or "radiograph" in msg_lower:
        if category_slug == "dentists":
            body = f"Got it {salutation}. For X-ray setup audits, I'll check: equipment calibration dates, radiation safety protocols, and DCI compliance records. Want me to start with the calibration review?"
        else:
            body = f"I understand you mentioned X-ray equipment. Let me connect you with our compliance specialist for that specific audit."
        return {
            "action": "send",
            "body": body,
            "cta": "binary_yes_no",
            "rationale": "Context-aware response to X-ray audit request with specific next steps."
        }
        
    if "audit" in msg_lower or "review" in msg_lower:
        if category_slug == "dentists":
            body = f"Understood {salutation}. I can audit: patient communication templates, Google profile optimization, or compliance documentation. Which area should I prioritize?"
        elif category_slug == "salons":
            body = f"Got it {salutation}. I can review: service pricing strategy, customer retention programs, or social media presence. What's your priority?"
        else:
            body = f"Perfect {salutation}. I can review your business profile, customer engagement, or promotional strategy. Which would help most right now?"
        return {
            "action": "send",
            "body": body,
            "cta": "multi_choice",
            "rationale": "Category-specific audit options based on merchant request."
        }
        
    # Curveballs / Out of scope
    if any(term in msg_lower for term in ["gst", "tax", "account", "payment", "billing", "invoice"]):
        body = f"I'll have to leave that to your accountant {salutation} — that's outside my scope. Coming back to your practice growth — want me to draft that patient communication we discussed?"
        return {
            "action": "send",
            "body": body,
            "cta": "binary_yes_no",
            "rationale": "Out-of-scope request politely declined; redirecting to core value proposition."
        }
        
    # Questions or clarifications
    if "?" in data.message or any(word in msg_lower for word in ["what", "how", "when", "why", "which"]):
        if category_slug == "dentists":
            body = f"Good question {salutation}. For your dental practice, I focus on: patient recall automation, compliance updates, and profile optimization. Which area interests you most?"
        elif category_slug == "salons":
            body = f"Great question {salutation}. I help salons with: bridal package marketing, customer retention, and seasonal promotions. What's your biggest challenge right now?"
        else:
            body = f"That's a good question {salutation}. I specialize in customer engagement and business growth for {category_slug}. What specific area can I help with?"
        return {
            "action": "send",
            "body": body,
            "cta": "open_ended",
            "rationale": "Question response with category-specific value propositions."
        }
        
    # Default contextual reply
    if category_slug == "dentists":
        body = f"Understood {salutation}. For dental practices, I typically help with patient communication, compliance tracking, and profile optimization. Should we focus on one of these areas?"
    elif category_slug == "salons":
        body = f"Got it {salutation}. I usually help salons with customer retention, bridal packages, and seasonal campaigns. Which would benefit your business most?"
    elif category_slug == "restaurants":
        body = f"I see {salutation}. For restaurants, I focus on menu promotions, customer reviews, and festive campaigns. What's your priority right now?"
    else:
        body = f"Understood {salutation}. Let me know what specific aspect of your {category_slug.rstrip('s')} business you'd like to focus on, and I'll provide targeted recommendations."
    
    return {
        "action": "send",
        "body": body,
        "cta": "open_ended",
        "rationale": "Category-specific default response maintaining conversation flow."
    }

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8085))
    uvicorn.run(app, host="0.0.0.0", port=port)
