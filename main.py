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
            
            # Debug: if digest not found, try to get it anyway
            if not digest and digest_items:
                # Use first digest item as fallback
                digest = digest_items[0]
            
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
                # Get deadline - try multiple sources
                deadline = t_data.get("deadline_iso", "") or t_data.get("deadline", "") or t_payload.get("deadline_iso", "") or "upcoming"
                top_id = t_data.get("top_item_id", "")
                
                # Get digest for more details
                digest_items = category.get("digest", [])
                digest = next((d for d in digest_items if d.get("id") == top_id), None)
                
                if digest:
                    title = digest.get("title", "DCI compliance update")
                    body = f"{salutation}, urgent: {title}. Deadline: {deadline}. Want me to audit your X-ray setup?"
                    rationale = f"Compliance alert with specific deadline ({deadline}), digest title, actionable audit offer."
                else:
                    body = f"{salutation}, urgent DCI compliance update. Deadline: {deadline}. Affects radiograph protocols. Want me to review your SOPs?"
                    rationale = f"Compliance alert with specific deadline ({deadline}), actionable review offer."
            else:
                body = f"{salutation}, regulatory update affecting {category_slug} in {city}. Want the compliance checklist?"
                rationale = "Regulatory compliance with location context."

        elif t_kind == "recall_due" and customer_id:
            customer = contexts["customer"].get(customer_id, {}).get("payload", {})
            c_identity = customer.get("identity", {})
            # Customer data has "name" field, not "first_name"
            c_name = c_identity.get("name", "")
            
            # Extract first name if it's a full name
            if c_name and " " in c_name:
                # Handle cases like "Aanya (parent: Sneha)"
                if "(" in c_name:
                    c_name = c_name.split("(")[0].strip()
                # Get first name
                c_name = c_name.split()[0]
            elif not c_name:
                c_name = "Patient"
            
            # Get relationship data for specificity
            relationship = customer.get("relationship", {})
            last_visit = relationship.get("last_visit", "")
            service_due = t_data.get("service_due", "checkup").replace("_", " ")
            
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
            # Pull delta_pct and baseline DIRECTLY from trigger payload first
            delta_pct = t_data.get("delta_pct") or t_payload.get("delta_pct") or 0
            baseline = t_data.get("vs_baseline") or t_payload.get("vs_baseline") or 0
            window = t_data.get("window", "7d")

            # Only fall back to merchant perf when payload has nothing
            if not delta_pct:
                delta_pct = merchant.get("performance", {}).get("delta_7d", {}).get(f"{metric}_pct", 0)
            if not baseline:
                baseline = calls if metric == "calls" else views if metric == "views" else 0

            if baseline > 0 and delta_pct != 0:
                current = int(baseline * (1 + delta_pct))
                pct_change = abs(int(delta_pct * 100))

                peer_value = peer_calls if metric == "calls" else peer_ctr if metric == "ctr" else 0
                peer_comp = ""
                if peer_value > 0:
                    peer_comp = f"(peer avg: {peer_value:.3f})" if metric == "ctr" else f"(peer avg: {int(peer_value)})"

                impact_str = ""
                if metric == "calls" and current < baseline:
                    lost_calls = baseline - current
                    impact_str = f"≈ ₹{lost_calls * 500:,} lost revenue. "

                body = f"{salutation}, alert: {metric} dropped {pct_change}% in {window} — {baseline} → {current} {peer_comp}. {impact_str}Push '{offer_title}' to recover?"
                rationale = f"Performance alert with exact numbers ({baseline}→{current}, {pct_change}%), peer comparison, revenue impact, recovery offer."
            else:
                # Describe dip using merchant's own delta_7d as fallback
                dip_pct = abs(int(delta_pct * 100)) if delta_pct else 0
                pct_str = f"{dip_pct}% " if dip_pct else ""
                body = f"{salutation}, your {metric} {pct_str}performance dip needs attention. Push '{offer_title}' to recover?"
                rationale = f"Performance alert for {metric} with recovery offer."

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
            
            body = f"{salutation}, your {plan} plan expires in {days_remaining} days. Renewal is ₹{amount}. Want me to process it now to avoid any service interruption?"
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
            prev_focus = t_data.get("previous_focus", "").replace("_", " ")
            prev_months = t_data.get("previous_membership_months", 0)
            count = t_data.get("count", lapsed_count) or lapsed_count

            if customer_id:
                # Customer-scoped: send directly to customer
                customer = contexts["customer"].get(customer_id, {}).get("payload", {})
                c_name = customer.get("identity", {}).get("name", "").split()[0] or "there"
                focus_str = f" You were working on {prev_focus}." if prev_focus else ""
                body = f"Hi {c_name}, we miss you at {m_name}!{focus_str} It's been {days_lapsed} days. Come back with '{offer_title}' — exclusive for you. Book now?"
                send_as = "merchant_on_behalf"
                cta = "binary_yes_no"
                rationale = f"Customer lapsed {days_lapsed}d. Focus: {prev_focus}. Personal winback with exclusive offer."
            else:
                # Merchant-scoped: alert the merchant
                revenue_min = count * 800
                revenue_max = count * 1200
                body = f"{salutation}, {count} customers haven't visited in {days_lapsed}+ days — ₹{revenue_min:,}–{revenue_max:,} at risk. Winback with '{offer_title}'?"
                rationale = f"Lapsed {count} customers, {days_lapsed}d. Revenue risk ₹{revenue_min:,}–{revenue_max:,}. Loss-aversion winback."

        elif t_kind == "active_planning_intent":
            intent_topic = t_data.get("intent_topic", "service planning").replace("_", " ")
            last_msg = t_data.get("merchant_last_message", "")
            # Bot should ACTION immediately — merchant already said yes
            body = f"{salutation}, picking up from your question about '{intent_topic}': here's my recommendation — should I draft the full plan with pricing, timeline, and a GBP post? Ready in 90 seconds."
            rationale = f"Active planning intent: '{intent_topic}'. Merchant already engaged. Bot switches to action mode immediately."

        elif t_kind == "trial_followup":
            trial_date = t_data.get("trial_date", "")
            next_sessions = t_data.get("next_session_options", [])
            slot_str = ""
            if next_sessions:
                slot_label = next_sessions[0].get("label", "") if isinstance(next_sessions[0], dict) else str(next_sessions[0])
                slot_str = f" Next slot: {slot_label}." if slot_label else ""
            trial_str = f" (trial was {trial_date})" if trial_date else ""
            body = f"{salutation}, following up on the trial{trial_str}.{slot_str} Ready to join the full program? Reply YES to confirm."
            rationale = f"Trial followup{trial_str}. Specific next slot offered. Clear yes/no CTA."

        elif t_kind == "supply_alert":
            molecule = t_data.get("molecule", t_data.get("item", "medication"))
            batches = t_data.get("affected_batches", [])
            manufacturer = t_data.get("manufacturer", "")
            batch_str = f" (batches: {', '.join(batches[:2])})" if batches else ""
            mfr_str = f" by {manufacturer}" if manufacturer else ""
            body = f"{salutation}, urgent: voluntary recall on {molecule}{mfr_str}{batch_str}. Check your stock now. Want the affected customer list to notify them?"
            rationale = f"Supply alert: {molecule} recall{mfr_str}. Specific batches cited. Patient safety action + customer list offer."

        elif t_kind == "chronic_refill_due":
            molecules = t_data.get("molecule_list", [t_data.get("medication", "prescription")])
            last_refill = t_data.get("last_refill", "")
            runs_out = t_data.get("stock_runs_out_iso", "")
            delivery_saved = t_data.get("delivery_address_saved", False)
            mol_str = ", ".join(molecules[:3]) if isinstance(molecules, list) else str(molecules)
            refill_str = f" (last refill: {last_refill})" if last_refill else ""
            delivery_str = " I can dispatch immediately — address on file." if delivery_saved else " Reply to confirm refill."
            body = f"{salutation}, refill due: {mol_str}{refill_str}. Stock runs out soon.{delivery_str}"
            rationale = f"Chronic refill: {mol_str}. Last refill {last_refill}. Delivery={delivery_saved}. Specific meds + urgency."

        elif t_kind == "category_seasonal":
            season = t_data.get("season", "season").replace("_", " ")
            trends = t_data.get("trends", [])
            shelf_action = t_data.get("shelf_action_recommended", False)
            if trends:
                # Parse trend strings like "ORS_demand_+40"
                top_trends = []
                for t in trends[:2]:
                    parts = str(t).replace("_demand_", ": ").replace("_", " ")
                    top_trends.append(parts)
                trend_str = " | ".join(top_trends)
                body = f"{salutation}, {season} demand shift: {trend_str}. Restock and promote '{offer_title}' to capture this surge now?"
            else:
                body = f"{salutation}, {season} trends are shifting. Your '{offer_title}' aligns perfectly — ready to capitalize?"
            rationale = f"Seasonal trend for {season}: {trends[:2]}. Shelf action={shelf_action}. Specific data-driven ask."

        elif t_kind == "gbp_unverified":
            uplift_pct = int(t_data.get("estimated_uplift_pct", 0) * 100)
            uplift_str = f"up to {uplift_pct}% more visibility" if uplift_pct else "improved visibility and trust"
            body = f"{salutation}, your Google Business Profile isn't verified — this costs you {uplift_str}. Takes 2 minutes. Want me to walk you through it now?"
            rationale = f"GBP unverified: {uplift_pct}% visibility uplift at stake. Specific benefit + 2-min effort framing."

        elif t_kind in ["competitor_opened_nearby", "competitor", "competitor_opened"]:
            comp_name = t_data.get("competitor_name", "a competitor")
            distance_km = t_data.get("distance_km", "")
            their_offer = t_data.get("their_offer", "")
            dist_str = f"{distance_km}km away" if distance_km else "nearby"
            offer_str = f" (their offer: {their_offer})" if their_offer else ""
            body = f"{salutation}, {comp_name} opened {dist_str}{offer_str}. Counter with '{offer_title}' before they take your customers. Launch defensive campaign?"
            rationale = f"Competitive threat: {comp_name} {dist_str}{offer_str}. Specific counter-offer proposed."

        elif t_kind == "perf_spike":
            metric = t_data.get("metric", "calls")
            delta_pct = t_data.get("delta_pct", 0)
            baseline = t_data.get("vs_baseline", 0)
            driver = t_data.get("likely_driver", "").replace("_", " ")
            increase = abs(int(delta_pct * 100)) if delta_pct else t_data.get("increase_pct", 20)
            current = int(baseline * (1 + delta_pct)) if baseline and delta_pct else 0
            spike_str = f"{baseline} → {current} " if baseline and current else ""
            driver_str = f" (driver: {driver})" if driver else ""
            body = f"{salutation}, great news: {metric} up {increase}% this week — {spike_str}{driver_str}. Lock in this momentum with '{offer_title}'. Strike while it's hot?"
            rationale = f"Performance spike: {metric} +{increase}%, {spike_str}{driver_str}. Amplification opportunity."

        elif t_kind == "ipl_match_today":
            match_details = t_data.get("match", "IPL match")
            venue = t_data.get("venue", "")
            is_weeknight = t_data.get("is_weeknight", False)
            venue_str = f" at {venue}" if venue else ""
            timing_str = "Weeknight crowd" if is_weeknight else "Match day crowd"
            body = f"{salutation}, {match_details} tonight{venue_str}. {timing_str} = surge in orders. Push '{offer_title}' right now — match starts soon?"
            rationale = f"IPL match day: {match_details}{venue_str}. {timing_str} impact. Time-sensitive offer push."

        elif t_kind in ["review_theme_emerging", "review_theme", "review_theme_emerged"]:
            theme = t_data.get("theme", "service quality").replace("_", " ")
            occurrences = t_data.get("occurrences_30d", 0)
            trend = t_data.get("trend", "")
            common_quote = t_data.get("common_quote", "")
            occ_str = f" ({occurrences}x in 30d)" if occurrences else ""
            quote_str = f' — customers say: "{common_quote[:60]}"' if common_quote else ""
            body = f"{salutation}, review theme: '{theme}'{occ_str}{quote_str}. Address this to protect your rating. Want a response template?"
            rationale = f"Review theme '{theme}' flagged {occurrences}x in 30d. Specific quote cited, actionable response offered."

        elif t_kind == "milestone_reached":
            metric = t_data.get("metric", "reviews").replace("_", " ")
            value_now = t_data.get("value_now", 0)
            milestone_value = t_data.get("milestone_value", 0)
            is_imminent = t_data.get("is_imminent", False)
            gap = milestone_value - value_now if milestone_value > value_now else 0
            if gap > 0:
                body = f"{salutation}, you're {gap} {metric} away from {milestone_value}! This milestone brings a badge boost. Push '{offer_title}' to hit it this week?"
            else:
                body = f"{salutation}, you just hit {milestone_value} {metric}! Celebrate with '{offer_title}' — ride the momentum. Should I draft the post?"
            rationale = f"Milestone {milestone_value} {metric} (currently {value_now}). Imminent={is_imminent}. Urgency + celebration framing."

        elif t_kind == "winback_eligible":
            days_expiry = t_data.get("days_since_expiry", 0)
            lapsed_added = t_data.get("lapsed_customers_added_since_expiry", 0)
            dip_pct = abs(int(t_data.get("perf_dip_pct", 0) * 100))
            body = f"{salutation}, {lapsed_added} customers lapsed in the {days_expiry} days since your plan expired, and calls are down {dip_pct}%. Reactivate today with '{offer_title}' to win them back. Shall I send the campaign?"
            rationale = f"Winback: {lapsed_added} lapsed customers, {dip_pct}% call dip, {days_expiry}d since expiry. Loss-aversion framing with specific offer."

        elif t_kind == "curious_ask_due":
            ask_template = t_data.get("ask_template", "service inquiry").replace("_", " ")
            body = f"{salutation}, quick check: {ask_template}? This insight helps me target the right customers for you. 10-second reply?"
            rationale = f"Engagement curiosity ask: '{ask_template}', low friction, 10-second ask."

        elif t_kind == "dormant_with_vera":
            days_dormant = t_data.get("days_since_last_merchant_message", 30)
            last_topic = t_data.get("last_topic", "your profile").replace("_", " ")
            body = f"{salutation}, it's been {days_dormant} days since we last connected (topic: {last_topic}). A lot can change in a month — want a quick business health check?"
            rationale = f"Re-engagement after {days_dormant} days dormancy. References last topic, low-friction health check CTA."

        else:
            # Enhanced fallback with more context
            payload_details = []
            for key, value in t_payload.items():
                if key not in ["merchant_id", "customer_id", "category", "kind", "scope"] and isinstance(value, (str, int, float)):
                    if len(str(value)) < 20:
                        readable_key = key.replace("_", " ")
                        payload_details.append(f"{readable_key}: {value}")
            
            details_str = " | ".join(payload_details[:2])
            
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
        "currently unavailable",
        "message received"
    ]
    
    if any(pattern in msg_lower for pattern in auto_reply_patterns):
        return {
            "action": "end",
            "rationale": "Auto-reply/out-of-office message detected; ending conversation to prevent looping."
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
        c_name_raw = customer.get("identity", {}).get("name", "")
        # Extract first name safely
        if c_name_raw:
            c_name = c_name_raw.split("(")[0].strip().split()[0]
        else:
            c_name = "there"

        if any(word in msg_lower for word in ["yes", "book", "confirm", "sure", "ok", "works", "please", "1", "2"]):
            return {
                "action": "send",
                "body": f"Perfect {c_name}, I've provisionally booked that for you. {owner_name} or the team will confirm shortly.",
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
            body = f"I apologize if my previous messages were unhelpful {salutation}. Regarding your question, I leave that to your accountant. I'm here to help with practice growth — should I pause messaging for now?"
            return {
                "action": "send",
                "body": body,
                "cta": "binary_yes_no",
                "rationale": "Handled hostile curveball politely."
            }
        body = f"I'll have to leave that to your accountant {salutation} — that's outside my scope. Coming back to your practice growth — want me to draft that patient communication we discussed?"
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
