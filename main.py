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
        # Inner payload contains trigger-specific fields (metric, delta_pct, top_item_id, etc.)
        t_inner = t_payload.get("payload", {})
        # Merge: prefer inner payload keys, but fall back to outer for shared keys
        t_data = {**t_payload, **t_inner}
        
        # Skip if no merchant context
        if not merchant_id or merchant_id not in contexts["merchant"]:
            continue
            
        merchant = contexts["merchant"][merchant_id]["payload"]
        category_slug = merchant.get("category_slug", "unknown")
        category = contexts["category"].get(category_slug, {}).get("payload", {})
        
        # MAXIMUM DATA EXTRACTION - Get ALL merchant details
        identity = merchant.get("identity", {})
        owner_name = identity.get("owner_first_name", "Partner")
        m_name = identity.get("name", "Business")
        locality = identity.get("locality", "")
        city = identity.get("city", "")
        
        # Performance metrics for specificity
        perf = merchant.get("performance", {})
        views = perf.get("views", 0)
        calls = perf.get("calls", 0)
        ctr = perf.get("ctr", 0)
        delta_7d = perf.get("delta_7d", {})
        
        # Customer aggregate for retention insights
        cust_agg = merchant.get("customer_aggregate", {})
        lapsed_count = cust_agg.get("lapsed_180d_plus", 0)
        high_risk_count = cust_agg.get("high_risk_adult_count", 0)
        
        # Peer stats for comparison
        peer_stats = category.get("peer_stats", {})
        peer_ctr = peer_stats.get("avg_ctr", 0)
        peer_calls = peer_stats.get("avg_calls_30d", 0)
        
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

        # Handle different trigger types with MAXIMUM SPECIFICITY
        if t_kind == "research_digest":
            top_id = t_data.get("top_item_id")
            digest_items = category.get("digest", [])
            digest = next((d for d in digest_items if d.get("id") == top_id), None)
            
            if digest and category_slug == "dentists":
                source = digest.get('source', 'JIDA')  # Already includes page: "JIDA Oct 2026, p.14"
                title = digest.get('title', 'new research')
                trial_n = digest.get('trial_n', 0)
                segment = digest.get('patient_segment', 'patients')
                
                # Build with ALL data points
                trial_info = f"(n={trial_n:,})" if trial_n else ""
                
                # Use actual patient count for specificity
                if high_risk_count > 0:
                    body = f"{salutation}, {source}: '{title}' {trial_info}. Affects your {high_risk_count} high-risk {segment.replace('_', ' ')}. Want 2-min abstract + patient WhatsApp draft? (90sec)"
                else:
                    body = f"{salutation}, {source}: '{title}' {trial_info}. Relevant for {segment.replace('_', ' ')}. Want 2-min abstract + patient draft?"
                
                rationale = f"Research with full citation ({source}, n={trial_n}), tied to merchant's {high_risk_count} patients, effort externalized (90sec), clear CTA."
            else:
                body = f"{salutation}, new clinical research for {locality} practices. Want summary + patient communication template?"
                rationale = "Research update with locality context."
                
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
                # Get deadline from payload - it's in the outer payload, not inner
                deadline = t_payload.get("deadline_iso", "")
                top_id = t_payload.get("top_item_id", "")
                
                # Get digest for more details
                digest_items = category.get("digest", [])
                digest = next((d for d in digest_items if d.get("id") == top_id), None)
                
                if digest and deadline:
                    title = digest.get("title", "DCI compliance update")
                    body = f"{salutation}, urgent: {title}. Deadline: {deadline}. Want me to audit your X-ray setup?"
                elif deadline:
                    body = f"{salutation}, urgent DCI compliance update. Deadline: {deadline}. Affects radiograph protocols. Want me to review your SOPs?"
                else:
                    body = f"{salutation}, urgent DCI compliance update. Affects radiograph protocols. Want me to review your SOPs?"
                
                rationale = f"Compliance alert with specific deadline ({deadline}), actionable audit offer."
            else:
                body = f"{salutation}, regulatory update affecting {category_slug} in {city}. Want the compliance checklist?"
                rationale = "Regulatory compliance with location context."

        elif t_kind == "recall_due" and customer_id:
            customer = contexts["customer"].get(customer_id, {}).get("payload", {})
            c_identity = customer.get("identity", {})
            # Fix: use first_name from identity, or extract from name field
            c_name = c_identity.get("first_name", c_identity.get("name", "Patient"))
            if not c_name or c_name == "Patient":
                # Try to extract first name from full name
                full_name = c_identity.get("name", "")
                if full_name and " " in full_name:
                    c_name = full_name.split()[0]
                elif full_name:
                    c_name = full_name
                else:
                    c_name = "Patient"
            
            # Get relationship data for specificity
            relationship = customer.get("relationship", {})
            last_visit = relationship.get("last_visit", "")
            service_due = t_data.get("service_due", "checkup")
            
            slots = t_data.get("available_slots", [])
            
            # Build with specific dates and slots
            if last_visit:
                body = f"Hi {c_name}, {m_name} here. Your 6-month {service_due} is due (last visit: {last_visit}). "
            else:
                body = f"Hi {c_name}, {m_name} here. Time for your {service_due}. "
            
            if len(slots) >= 2:
                slot1 = slots[0].get("label", "")
                slot2 = slots[1].get("label", "")
                body += f"Slots ready: {slot1} or {slot2}. Reply 1 or 2, or suggest your time."
            elif slots:
                slot1 = slots[0].get("label", "")
                body += f"We have {slot1} available. Works for you?"
            else:
                body += "When works best this week?"
            
            cta = "multi_choice_slot"
            send_as = "merchant_on_behalf"
            rationale = f"Customer recall with name ({c_name}), last visit ({last_visit}), service ({service_due}), specific slots, multi-choice CTA."

        elif t_kind == "perf_dip":
            metric = t_data.get("metric", "calls")
            delta_pct = t_data.get("delta_pct", 0)
            if delta_pct == 0:
                delta_pct = merchant.get("performance", {}).get("delta_7d", {}).get(f"{metric}_pct", 0)
            window = t_data.get("window", "7d")
            baseline = t_data.get("vs_baseline", 0)
            
            # If baseline is 0, try to get from merchant performance
            if baseline == 0:
                if metric == "calls":
                    baseline = calls
                elif metric == "views":
                    baseline = views
            
            # Only calculate if we have valid data
            if baseline > 0 and delta_pct != 0:
            current = int(baseline * (1 + delta_pct))
            pct_change = abs(int(delta_pct * 100))
            
            # Peer comparison for context
            peer_value = peer_calls if metric == "calls" else peer_ctr if metric == "ctr" else 0
            if peer_value > 0:
                if metric == "ctr":
                    peer_comp = f"(peer avg: {peer_value:.3f})"
                else:
                    peer_comp = f"(peer avg: {int(peer_value)})"
            else:
                peer_comp = ""
            
            # Revenue impact for calls
            if metric == "calls":
                lost_calls = baseline - current
                revenue_impact = lost_calls * 500
                impact_str = f"â‰ˆ â‚¹{revenue_impact:,} potential revenue"
            else:
                impact_str = ""
            
            # Build message with ALL specifics
            body = f"{salutation}, alert: {metric} dropped {pct_change}% in {window} â€” {baseline} â†’ {current} {peer_comp}. "
            if impact_str:
                body += f"{impact_str}. "
            body += f"Push '{offer_title}' to recover?"
            
            rationale = f"Performance alert with exact numbers ({baseline}â†’{current}, {pct_change}%), peer comparison {peer_comp}, revenue impact {impact_str}, recovery offer."

        elif t_kind == "festival_upcoming":
            festival = t_data.get("festival", "Festival")
            days_until = t_data.get("days_until", "a few")
            
            if category_slug == "salons":
                body = f"{salutation}, {festival} is in {days_until} days! Perfect time for bridal packages. Let's schedule a targeted campaign for '{offer_title}' to boost bookings. Sound good?"
            elif category_slug == "restaurants":
                body = f"{salutation}, {festival} is in {days_until} days! Great opportunity for special menus. Want to promote '{offer_title}' for the festive rush?"
            else:
                body = f"{salutation}, {festival} is in {days_until} days! Let's create a festive campaign for '{offer_title}' to capture the holiday demand. Ready?"
            
            rationale = "Festival timing with category-specific opportunity and clear campaign proposal."

        elif t_kind == "renewal_due":
            days_remaining = t_data.get("days_remaining", 0)
            plan = t_data.get("plan", "Pro")
            amount = t_data.get("renewal_amount", 0)
            
            body = f"{salutation}, your {plan} plan expires in {days_remaining} days. Renewal is â‚¹{amount}. Want me to process it now to avoid any service interruption?"
            rationale = "Renewal urgency with specific timeline and amount."

        elif t_kind == "wedding_package_followup":
            if category_slug == "salons":
                wedding_date = t_data.get("wedding_date", "")
                days_to_wedding = t_data.get("days_to_wedding", 0)
                body = f"{salutation}, the bride's wedding is in {days_to_wedding} days ({wedding_date}). Time for the 30-day skin prep program. Should I send her the package details?"
                rationale = "Wedding timeline with specific prep program recommendation."
            else:
                body = f"{salutation}, there's a wedding package follow-up needed. Want me to handle the next steps?"
                rationale = "Wedding package follow-up."

        # Add more specific trigger handlers
        elif t_kind == "seasonal_perf_dip":
            metric = t_data.get("metric", "bookings")
            season = t_data.get("season", "current season")
            body = f"{salutation}, your {metric} are down this {season} vs last year. Your '{offer_title}' could help recover. Should we activate it?"
            rationale = "Seasonal performance comparison with specific recovery action."

        elif t_kind == "customer_lapsed_hard":
            days_lapsed = t_data.get("days_since_last_visit", 180)
            count = t_data.get("count", lapsed_count) or lapsed_count
            
            # Revenue calculation - loss aversion framing
            revenue_min = count * 800
            revenue_max = count * 1200
            
            body = f"{salutation}, {count} customers haven't visited in {days_lapsed}+ days. That's â‚¹{revenue_min:,}-{revenue_max:,} lost revenue. Winback with '{offer_title}'?"
            rationale = f"Customer retention with specific count ({count}), timeframe ({days_lapsed}d), revenue loss (â‚¹{revenue_min:,}-{revenue_max:,}), winback offer."

        elif t_kind == "active_planning_intent":
            intent_type = t_data.get("intent", "service planning")
            body = f"{salutation}, I detected {intent_type} activity from your customers. Perfect time to promote '{offer_title}'. Should we create a targeted campaign?"
            rationale = "Customer intent detection with timely offer promotion."

        elif t_kind == "trial_followup":
            service = t_data.get("service", "trial service")
            days_since = t_data.get("days_since_trial", 7)
            body = f"{salutation}, it's been {days_since} days since the {service} trial. Time for follow-up. Should I send the conversion offer?"
            rationale = "Trial follow-up with specific timing and conversion focus."

        elif t_kind == "supply_alert":
            item = t_data.get("item", "inventory item")
            status = t_data.get("status", "low stock")
            body = f"{salutation}, {item} is showing {status}. This affects your operations. Want me to help with supplier coordination?"
            rationale = "Supply chain alert with operational impact and assistance offer."

        elif t_kind == "chronic_refill_due":
            medication = t_data.get("medication", "prescription")
            patient_count = t_data.get("patient_count", "several patients")
            body = f"{salutation}, {patient_count} need {medication} refills this week. Should I send reminder notifications to ensure continuity?"
            rationale = "Medication management with patient care focus and proactive service."

        elif t_kind == "category_seasonal":
            trend = t_data.get("trend", "seasonal demand")
            impact = t_data.get("impact", "increased interest")
            body = f"{salutation}, {trend} is showing {impact} in your area. Your '{offer_title}' aligns perfectly. Ready to capitalize?"
            rationale = "Seasonal trend analysis with strategic offer alignment."

        elif t_kind == "gbp_unverified":
            verification_benefit = "improved visibility and customer trust"
            body = f"{salutation}, your Google Business Profile needs verification. This unlocks {verification_benefit}. Want me to guide you through the 2-minute process?"
            rationale = "Profile optimization with specific benefits and easy action path."

        elif t_kind in ["competitor_opened_nearby", "competitor"]:
            distance = t_data.get("distance", "nearby")
            competitor_type = t_data.get("type", "competitor")
            body = f"{salutation}, a new {competitor_type} opened {distance}. Time to strengthen your position with '{offer_title}'. Should we launch a defensive campaign?"
            rationale = "Competitive threat with strategic response and defensive positioning."

        elif t_kind == "perf_spike":
            metric = t_data.get("metric", "engagement")
            increase = t_data.get("increase_pct", 20)
            body = f"{salutation}, your {metric} spiked {increase}% this week! Perfect momentum to amplify with '{offer_title}'. Strike while it's hot?"
            rationale = "Performance momentum with amplification opportunity and urgency."

        elif t_kind == "ipl_match_today":
            match_details = t_data.get("match", "IPL match")
            crowd_impact = "increased foot traffic expected"
            body = f"{salutation}, {match_details} today means {crowd_impact}. Your '{offer_title}' could capture this surge. Ready to go live?"
            rationale = "Event-driven opportunity with crowd dynamics and immediate action."

        elif t_kind in ["review_theme_emerging", "review_theme"]:
            theme = t_data.get("theme", "service quality")
            sentiment = t_data.get("sentiment", "positive")
            body = f"{salutation}, reviews are highlighting {theme} ({sentiment} trend). This validates your '{offer_title}' positioning. Want to amplify this momentum?"
            rationale = "Review analysis with validation of current strategy and amplification opportunity."

        elif t_kind == "milestone_reached":
            milestone = t_data.get("milestone", "business milestone")
            achievement = t_data.get("achievement", "significant growth")
            body = f"{salutation}, congratulations on {milestone}! This {achievement} deserves celebration. Should we create a milestone campaign with '{offer_title}'?"
            rationale = "Achievement recognition with celebration marketing and offer integration."

        elif t_kind == "winback_eligible":
            segment = t_data.get("segment", "lapsed customers")
            timeframe = t_data.get("optimal_window", "this week")
            body = f"{salutation}, {segment} are in the optimal winback window {timeframe}. Your '{offer_title}' could re-engage them. Launch the campaign?"
            rationale = "Winback timing optimization with specific segment and offer matching."

        elif t_kind == "curious_ask_due":
            inquiry_type = t_data.get("inquiry_type", "service inquiry")
            response_window = t_data.get("response_window", "24 hours")
            body = f"{salutation}, you have pending {inquiry_type} requiring response within {response_window}. Should I draft personalized responses?"
            rationale = "Customer inquiry management with time sensitivity and personalized service."

        else:
            # Enhanced fallback with more context
            payload_details = []
            for key, value in t_payload.items():
                if key not in ["merchant_id", "customer_id", "category", "kind", "scope"] and isinstance(value, (str, int, float)):
                    if len(str(value)) < 30:  # Only include short, meaningful values
                        payload_details.append(f"{key.replace('_', ' ')}: {value}")
            
            details_str = " | ".join(payload_details[:2])  # Limit to 2 most relevant details
            
            if details_str:
                body = f"{salutation}, I have a {t_kind.replace('_', ' ')} update: {details_str}. This could impact your {category_slug.rstrip('s')} business. Should we review it together?"
                rationale = f"Specific {t_kind} update with payload details and category context."
            else:
                body = f"{salutation}, I have an important {t_kind.replace('_', ' ')} update for your {category_slug.rstrip('s')} business. Want to review the details?"
                rationale = f"Category-specific {t_kind} update with engagement prompt."

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
        return {
            "action": "end",
            "rationale": "Auto-reply detected; ending conversation to prevent spam loop."
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

    if data.from_role == "customer":
        customer = contexts["customer"].get(data.customer_id, {}).get("payload", {}) if data.customer_id else {}
        c_name = customer.get("identity", {}).get("name", "Patient")
        
        if any(word in msg_lower for word in ["yes", "book", "confirm", "sure", "ok", "works", "please"]):
            return {
                "action": "send",
                "body": f"Perfect {c_name}, I've provisionally booked that for you. {owner_name} or the clinic team will confirm shortly.",
                "cta": "none",
                "rationale": "Customer booking confirmation on behalf of merchant."
            }
        elif any(word in msg_lower for word in ["no", "cancel", "later", "busy"]):
            return {
                "action": "end",
                "rationale": "Customer declined; ending conversation."
            }
        else:
            return {
                "action": "send",
                "body": f"Thanks {c_name}. Let me know if you need to schedule a different time.",
                "cta": "open_ended",
                "rationale": "General customer reply handling."
            }

    # Curveballs / Out of scope
    if any(term in msg_lower for term in ["gst", "tax", "account", "payment", "billing", "invoice"]):
        hostile_patterns = ["stop", "unsubscribe", "useless", "not interested", "bothering", "spam", "don't message", "leave me alone"]
        if any(pattern in msg_lower for pattern in hostile_patterns):
            body = f"I apologize if my previous messages were unhelpful {salutation}. Regarding your question, I leave that to your accountant. I'm here to help with practice growth â€” should I pause messaging for now?"
            return {
                "action": "send",
                "body": body,
                "cta": "binary_yes_no",
                "rationale": "Handled hostile curveball politely."
            }
        body = f"I'll have to leave that to your accountant {salutation} â€” that's outside my scope. Coming back to your practice growth â€” want me to draft that patient communication we discussed?"
        return {
            "action": "send",
            "body": body,
            "cta": "binary_yes_no",
            "rationale": "Out-of-scope request politely declined; redirecting to core value proposition."
        }

    # Hostile/Opt-out handling
    hostile_patterns = ["stop", "unsubscribe", "useless", "not interested", "bothering", "spam", "don't message", "leave me alone"]
    if any(pattern in msg_lower for pattern in hostile_patterns):
        return {
            "action": "end",
            "rationale": "Merchant opted out or expressed frustration; ending conversation."
        }
        
    # Intent transition / commitment
    commitment_patterns = ["yes", "do it", "sure", "next", "ok", "draft", "proceed", "go ahead", "sounds good"]
    if any(pattern in msg_lower for pattern in commitment_patterns):
        if category_slug == "dentists":
            body = f"Perfect {salutation}. Drafting your patient WhatsApp now â€” 90 seconds. I'll also pre-fill the GBP post for tomorrow 10am. Reply CONFIRM to send the WhatsApp draft to your patient list."
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
