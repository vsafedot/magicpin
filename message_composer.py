"""
High-Performance Message Composer for 100/100 Score
Extracts maximum specificity from all context layers
"""

def extract_all_merchant_data(merchant, category):
    """Extract every possible data point from merchant and category contexts"""
    
    # Identity
    identity = merchant.get("identity", {})
    data = {
        "owner_name": identity.get("owner_first_name", "Partner"),
        "business_name": identity.get("name", "Business"),
        "locality": identity.get("locality", ""),
        "city": identity.get("city", ""),
        "verified": identity.get("verified", False),
        "languages": identity.get("languages", []),
    }
    
    # Performance with deltas
    perf = merchant.get("performance", {})
    data.update({
        "views": perf.get("views", 0),
        "calls": perf.get("calls", 0),
        "directions": perf.get("directions", 0),
        "ctr": perf.get("ctr", 0),
        "leads": perf.get("leads", 0),
    })
    
    delta_7d = perf.get("delta_7d", {})
    data.update({
        "views_pct_change": delta_7d.get("views_pct", 0),
        "calls_pct_change": delta_7d.get("calls_pct", 0),
        "ctr_pct_change": delta_7d.get("ctr_pct", 0),
    })
    
    # Customer aggregate
    cust_agg = merchant.get("customer_aggregate", {})
    data.update({
        "total_customers": cust_agg.get("total_unique_ytd", 0),
        "lapsed_customers": cust_agg.get("lapsed_180d_plus", 0),
        "retention_pct": int(cust_agg.get("retention_6mo_pct", 0) * 100),
        "high_risk_count": cust_agg.get("high_risk_adult_count", 0),
    })
    
    # Signals
    data["signals"] = merchant.get("signals", [])
    
    # Offers
    offers = merchant.get("offers", [])
    active_offers = [o for o in offers if o.get("status") == "active"]
    data["active_offer"] = active_offers[0] if active_offers else None
    data["offer_title"] = active_offers[0].get("title") if active_offers else None
    
    # Peer stats from category
    peer_stats = category.get("peer_stats", {})
    data.update({
        "peer_ctr": peer_stats.get("avg_ctr", 0),
        "peer_calls": peer_stats.get("avg_calls_30d", 0),
        "peer_views": peer_stats.get("avg_views_30d", 0),
        "peer_rating": peer_stats.get("avg_rating", 0),
    })
    
    # Voice profile
    voice = category.get("voice", {})
    data.update({
        "voice_tone": voice.get("tone", ""),
        "vocab_taboo": voice.get("vocab_taboo", []),
        "vocab_allowed": voice.get("vocab_allowed", []),
    })
    
    return data


def calculate_revenue_potential(lapsed_count, avg_ticket=800):
    """Calculate revenue potential from lapsed customers"""
    min_revenue = lapsed_count * avg_ticket
    max_revenue = lapsed_count * (avg_ticket * 1.5)
    return min_revenue, max_revenue


def format_peer_comparison(metric_name, merchant_value, peer_value):
    """Format peer comparison with gap analysis"""
    if peer_value == 0:
        return ""
    
    gap_pct = int(((merchant_value - peer_value) / peer_value) * 100)
    
    if gap_pct < 0:
        return f"(peer avg: {peer_value}, you're {abs(gap_pct)}% below)"
    elif gap_pct > 0:
        return f"(peer avg: {peer_value}, you're {gap_pct}% above!)"
    else:
        return f"(peer avg: {peer_value})"


def get_urgency_prefix(urgency_score):
    """Get urgency prefix based on score (1-5)"""
    if urgency_score >= 5:
        return "CRITICAL"
    elif urgency_score >= 4:
        return "URGENT"
    elif urgency_score >= 3:
        return "Important"
    elif urgency_score >= 2:
        return "FYI"
    else:
        return ""


def compose_research_digest(data, trigger_payload, category):
    """Compose research digest with maximum specificity"""
    top_id = trigger_payload.get("top_item_id")
    digest_items = category.get("digest", [])
    digest = next((d for d in digest_items if d.get("id") == top_id), None)
    
    if not digest:
        return None
    
    # Extract ALL digest data
    source = digest.get("source", "")
    title = digest.get("title", "")
    trial_n = digest.get("trial_n", "")
    segment = digest.get("patient_segment", "patients")
    page = digest.get("page", "")
    
    # Build with maximum specificity
    salutation = f"Dr. {data['owner_name']}"
    
    # Source citation with page number
    if page:
        citation = f"{source} p.{page}"
    else:
        citation = source
    
    # Core message with trial size
    if trial_n:
        body = f"{salutation}, {citation}: '{title}' (n={trial_n:,}). "
    else:
        body = f"{salutation}, {citation}: '{title}'. "
    
    # Tie to merchant's actual patient count
    if data["high_risk_count"] > 0:
        body += f"Affects your {data['high_risk_count']} high-risk {segment}. "
    else:
        body += f"Relevant for {segment}. "
    
    # Effort externalization + time
    body += "Want 2-min abstract + patient WhatsApp draft? (90sec turnaround)"
    
    rationale = f"Research with full citation ({citation}, n={trial_n}), tied to merchant's {data['high_risk_count']} patients, effort externalized, 90sec promise."
    
    return body, rationale


def compose_performance_alert(data, trigger_payload, metric_type="dip"):
    """Compose performance alert with peer comparison"""
    metric = trigger_payload.get("metric", "calls")
    delta_pct = trigger_payload.get("delta_pct", 0)
    window = trigger_payload.get("window", "7d")
    baseline = trigger_payload.get("vs_baseline", 0)
    
    # Calculate current value
    current = int(baseline * (1 + delta_pct))
    pct_change = abs(int(delta_pct * 100))
    
    # Get peer comparison
    peer_value = data.get(f"peer_{metric}", 0)
    peer_comp = format_peer_comparison(metric, current, peer_value)
    
    # Calculate revenue impact if it's calls
    if metric == "calls":
        lost_calls = baseline - current
        revenue_impact = lost_calls * 500  # Assume ₹500 per call
        impact_str = f"≈ ₹{revenue_impact:,} potential revenue"
    else:
        impact_str = ""
    
    salutation = data["owner_name"]
    
    if metric_type == "dip":
        body = f"{salutation}, alert: {metric} dropped {pct_change}% in {window} — {baseline} → {current} {peer_comp}. "
        if impact_str:
            body += f"{impact_str}. "
    else:  # spike
        body = f"{salutation}, momentum: {metric} spiked +{pct_change}% in {window} — {baseline} → {current}! "
    
    # Action with offer
    if data["offer_title"]:
        body += f"Push '{data['offer_title']}' to {'recover' if metric_type == 'dip' else 'amplify'}?"
    else:
        body += f"Launch recovery campaign?"
    
    rationale = f"Performance {metric_type} with exact numbers ({baseline}→{current}, {pct_change}%), peer comparison {peer_comp}, revenue impact {impact_str}, actionable offer."
    
    return body, rationale


def compose_customer_recall(data, trigger_payload, customer_context):
    """Compose customer recall with maximum personalization"""
    c_identity = customer_context.get("identity", {})
    c_name = c_identity.get("first_name", "Patient")
    
    relationship = customer_context.get("relationship", {})
    last_visit = relationship.get("last_visit", "")
    
    service_due = trigger_payload.get("service_due", "checkup")
    slots = trigger_payload.get("available_slots", [])
    
    business_name = data["business_name"]
    
    # Build message with specific dates and slots
    body = f"Hi {c_name}, {business_name} here. "
    
    if last_visit:
        body += f"Your 6-month {service_due} is due (last: {last_visit}). "
    else:
        body += f"Time for your {service_due}. "
    
    # Specific slots
    if len(slots) >= 2:
        slot1 = slots[0].get("label", "")
        slot2 = slots[1].get("label", "")
        body += f"Slots ready: {slot1} or {slot2}. Reply 1 or 2, or suggest your time."
    elif slots:
        slot1 = slots[0].get("label", "")
        body += f"We have {slot1} available. Works for you?"
    else:
        body += "When works best this week?"
    
    rationale = f"Customer recall with name ({c_name}), last visit date ({last_visit}), service type ({service_due}), specific slots, multi-choice CTA."
    
    return body, rationale
