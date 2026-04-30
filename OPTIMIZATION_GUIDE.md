# Path to 100/100 Score - Optimization Guide

## Current Status: 74% (37/50)
## Target: 100% (50/50)
## Gap Analysis: +26% needed

---

## Scoring Breakdown & Improvements Needed

### 1. Specificity: 7/10 → 10/10 (+3 points)

**Current Issues:**
- Missing specific numbers from payload
- Not using trial sizes, dates, exact metrics
- Generic fallbacks

**Required Improvements:**
```python
# BAD (Current - 6/10):
"Dr. Meera, I found new clinical research relevant to your practice."

# GOOD (Target - 10/10):
"Dr. Meera, JIDA Oct 2026 p.14: '3-mo fluoride recall cuts caries 38% (n=2,100, high-risk adults)'. 
Affects your 124 high-risk patients. Want 2-min abstract + patient WhatsApp draft?"
```

**Action Items:**
- Extract ALL numbers: trial_n, percentages, patient counts, dates
- Use exact source citations: "JIDA Oct 2026 p.14" not "JIDA"
- Include merchant's actual data: "your 124 high-risk patients" not "your patients"
- Add peer comparisons: "peer avg: 12 calls" when showing performance

### 2. Category Fit: 8/10 → 10/10 (+2 points)

**Current Issues:**
- Not using voice profile vocabulary from category context
- Missing code-mix (Hindi-English) where appropriate
- Not adapting tone precisely

**Required Improvements:**
```python
# Extract voice profile
voice = category.get("voice", {})
tone = voice.get("tone", "")  # "peer_clinical" for dentists
vocab_allowed = voice.get("vocab_allowed", [])  # Technical terms OK
vocab_taboo = voice.get("vocab_taboo", [])  # Avoid "guaranteed", "cure"

# Use Hindi-English mix for Indian context
"Dr. Meera, aapke 124 high-risk adult patients ke liye..."
```

**Action Items:**
- Check vocab_taboo and never use those words
- Use vocab_allowed technical terms when relevant
- Add Hindi-English code-mix for authenticity
- Match tone exactly: "peer_clinical" vs "warm_friendly" vs "operator_to_operator"

### 3. Merchant Fit: 7/10 → 10/10 (+3 points)

**Current Issues:**
- Not using conversation_history
- Missing performance delta comparisons
- Not referencing signals array
- Not using customer_aggregate data

**Required Improvements:**
```python
# Use conversation history
conv_history = merchant.get("conversation_history", [])
last_topic = conv_history[-1].get("body", "") if conv_history else ""

# Use signals
signals = merchant.get("signals", [])
if "stale_posts:22d" in signals:
    "Your posts are 22 days stale (last: Apr 4). Fresh content boosts CTR 18%."

# Use customer aggregate
cust_agg = merchant.get("customer_aggregate", {})
lapsed = cust_agg.get("lapsed_180d_plus", 0)
retention = cust_agg.get("retention_6mo_pct", 0)
"Your 78 lapsed patients (>180d) represent ₹39k-78k recovery potential."

# Use performance deltas
delta_7d = perf.get("delta_7d", {})
views_change = delta_7d.get("views_pct", 0)
"Views up 18% this week (2,410 → 2,844). Momentum is hot!"
```

**Action Items:**
- Reference conversation_history for context continuity
- Use ALL signals in the signals array
- Calculate revenue potential from customer_aggregate
- Show week-over-week deltas from delta_7d
- Reference locality and city for local context

### 4. Trigger Relevance: 8/10 → 10/10 (+2 points)

**Current Issues:**
- Not explaining WHY NOW clearly enough
- Missing urgency framing
- Not using expires_at for deadline pressure

**Required Improvements:**
```python
# Use trigger urgency
urgency = trigger.get("urgency", 1)  # 1-5 scale
expires_at = trigger.get("expires_at", "")

if urgency >= 4:
    "URGENT: DCI deadline Dec 15 (38 days). Non-compliance = ₹50k fine + license review."
elif urgency >= 3:
    "Reminder: Registration closes May 3 (7 days)."

# Explain WHY NOW
"Why now? Bridal bookings spike 3-4 weeks before Diwali. You're in the sweet spot."
```

**Action Items:**
- Always explain WHY NOW explicitly
- Use urgency score to frame message tone
- Reference expires_at for deadline pressure
- Connect trigger to merchant's current state

### 5. Engagement Compulsion: 7/10 → 10/10 (+3 points)

**Current Issues:**
- Not using compulsion levers systematically
- Missing loss aversion framing
- Weak CTAs

**Required Improvements:**

**Compulsion Levers to Use:**
1. **Loss Aversion**: "78 lapsed patients = ₹39k-78k lost revenue"
2. **Curiosity**: "JIDA found something surprising about 3-mo recalls..."
3. **Social Proof**: "Peer avg CTR: 0.030. Yours: 0.021. Gap = 30% fewer calls."
4. **Effort Externalization**: "I'll draft it. You just review + approve."
5. **Time Scarcity**: "Registration closes in 7 days. Spots filling fast."
6. **Authority**: "DCI mandates this by Dec 15."

```python
# WEAK CTA:
"Want details?"

# STRONG CTA:
"Reply YES and I'll have the draft ready in 90 seconds. Just review + send."
```

**Action Items:**
- Use 2-3 compulsion levers per message
- Frame as loss avoided, not gain achieved
- Make CTA ultra-specific and low-friction
- Add time pressure when relevant

---

## Implementation Priority

### Phase 1: Quick Wins (+8 points) - 30 minutes
1. Add ALL numeric data extraction (trial_n, dates, counts)
2. Use customer_aggregate for patient counts
3. Add peer comparisons
4. Use signals array
5. Add revenue calculations

### Phase 2: Voice & Personalization (+6 points) - 20 minutes
1. Extract and use voice profile
2. Add Hindi-English code-mix
3. Reference conversation_history
4. Use performance deltas

### Phase 3: Engagement Psychology (+5 points) - 20 minutes
1. Add loss aversion framing
2. Strengthen CTAs
3. Add time scarcity
4. Use effort externalization

### Phase 4: Polish (+7 points) - 30 minutes
1. Perfect WHY NOW explanations
2. Add urgency-based framing
3. Optimize message length (150-200 chars)
4. Test all trigger types

---

## Code Template for 10/10 Messages

```python
# EXTRACT EVERYTHING
merchant = contexts["merchant"][merchant_id]["payload"]
category = contexts["category"][category_slug]["payload"]

# Identity
identity = merchant.get("identity", {})
owner_name = identity.get("owner_first_name", "")
locality = identity.get("locality", "")
city = identity.get("city", "")

# Performance with deltas
perf = merchant.get("performance", {})
views = perf.get("views", 0)
calls = perf.get("calls", 0)
ctr = perf.get("ctr", 0)
delta_7d = perf.get("delta_7d", {})
views_pct = delta_7d.get("views_pct", 0)

# Customer aggregate
cust_agg = merchant.get("customer_aggregate", {})
lapsed = cust_agg.get("lapsed_180d_plus", 0)
retention_pct = int(cust_agg.get("retention_6mo_pct", 0) * 100)
high_risk = cust_agg.get("high_risk_adult_count", 0)

# Signals
signals = merchant.get("signals", [])

# Peer stats
peer_stats = category.get("peer_stats", {})
peer_ctr = peer_stats.get("avg_ctr", 0)
peer_calls = peer_stats.get("avg_calls_30d", 0)

# Voice profile
voice = category.get("voice", {})
vocab_taboo = voice.get("vocab_taboo", [])

# Trigger details
urgency = trigger.get("urgency", 1)
expires_at = trigger.get("expires_at", "")

# BUILD MESSAGE WITH ALL DATA
if t_kind == "research_digest":
    digest = get_digest_item(t_payload, category)
    source = digest.get("source", "")
    title = digest.get("title", "")
    trial_n = digest.get("trial_n", "")
    segment = digest.get("patient_segment", "")
    
    # MAXIMUM SPECIFICITY
    body = f"Dr. {owner_name}, {source}: '{title}' (n={trial_n}, {segment}). "
    
    # MERCHANT FIT - use actual data
    if high_risk > 0:
        body += f"Affects your {high_risk} high-risk patients. "
    
    # ENGAGEMENT - effort externalization + time
    body += f"Want 2-min abstract + patient WhatsApp draft? (90 sec turnaround)"
    
    # RATIONALE - explain everything
    rationale = f"Research with full citation ({source}, n={trial_n}), tied to merchant's {high_risk} high-risk patients, effort externalized (90sec draft), clear binary CTA."
```

---

## Testing Checklist

Before resubmission, verify:

- [ ] Every message has 3+ specific numbers/dates
- [ ] Peer comparisons included where relevant
- [ ] Customer aggregate data used
- [ ] Signals array referenced
- [ ] Performance deltas shown
- [ ] Voice profile respected (no taboo words)
- [ ] Hindi-English mix where appropriate
- [ ] 2+ compulsion levers per message
- [ ] WHY NOW explicitly stated
- [ ] CTA is ultra-specific and low-friction
- [ ] Message length 150-250 chars
- [ ] Revenue/loss calculations included
- [ ] Urgency framing matches trigger urgency score

---

## Expected Score After Implementation

| Dimension | Current | Target | Improvement |
|-----------|---------|--------|-------------|
| Specificity | 7/10 | 10/10 | +3 |
| Category Fit | 8/10 | 10/10 | +2 |
| Merchant Fit | 7/10 | 10/10 | +3 |
| Trigger Relevance | 8/10 | 10/10 | +2 |
| Engagement | 7/10 | 10/10 | +3 |
| **TOTAL** | **37/50** | **50/50** | **+13** |

**Result: 100% Score (50/50) 🎯**

