#!/usr/bin/env python3
"""Quick test to verify perf_dip calculation"""

import requests
import json

BOT_URL = "http://localhost:8085"

# Push merchant context
merchant_ctx = {
    "scope": "merchant",
    "context_id": "m_002_bharat_dentist_mumbai",
    "version": 1,
    "payload": {
        "merchant_id": "m_002_bharat_dentist_mumbai",
        "category_slug": "dentists",
        "identity": {
            "name": "Bharat Dental Clinic",
            "owner_first_name": "Bharat",
            "city": "Mumbai",
            "locality": "Andheri"
        },
        "offers": [{"id": "o1", "title": "Dental Checkup @ ₹199", "status": "active"}],
        "performance": {"views": 100, "calls": 12, "ctr": 0.02},
        "customer_aggregate": {"lapsed_180d_plus": 5, "high_risk_adult_count": 10}
    },
    "delivered_at": "2026-05-03T10:00:00Z"
}

# Push category context
category_ctx = {
    "scope": "category",
    "context_id": "dentists",
    "version": 1,
    "payload": {
        "slug": "dentists",
        "peer_stats": {"avg_ctr": 0.025, "avg_calls_30d": 15}
    },
    "delivered_at": "2026-05-03T10:00:00Z"
}

# Push trigger with delta_pct = -0.5 (50% drop)
trigger_ctx = {
    "scope": "trigger",
    "context_id": "trg_004_perf_dip_bharat",
    "version": 1,
    "payload": {
        "id": "trg_004_perf_dip_bharat",
        "scope": "merchant",
        "kind": "perf_dip",
        "merchant_id": "m_002_bharat_dentist_mumbai",
        "customer_id": None,
        "payload": {
            "metric": "calls",
            "delta_pct": -0.5,
            "window": "7d",
            "vs_baseline": 12
        }
    },
    "delivered_at": "2026-05-03T10:00:00Z"
}

print("Pushing contexts...")
for ctx in [merchant_ctx, category_ctx, trigger_ctx]:
    r = requests.post(f"{BOT_URL}/v1/context", json=ctx)
    print(f"  {ctx['scope']}/{ctx['context_id']}: {r.status_code}")

print("\nCalling tick...")
tick_resp = requests.post(f"{BOT_URL}/v1/tick", json={
    "now": "2026-05-03T10:05:00Z",
    "available_triggers": ["trg_004_perf_dip_bharat"]
})

print(f"Status: {tick_resp.status_code}")
data = tick_resp.json()
print(f"Actions: {len(data.get('actions', []))}")

if data.get('actions'):
    action = data['actions'][0]
    body = action['body']
    print(f"\nMessage body:\n{body}")
    print(f"\nRationale:\n{action['rationale']}")
    
    # Check if it says 50% or 0.5%
    if "50%" in body:
        print("\n✓ CORRECT: Message shows 50% drop")
    elif "0.5%" in body or "0.5 %" in body:
        print("\n✗ ERROR: Message shows 0.5% instead of 50%")
    else:
        print("\n? UNCLEAR: Can't find percentage in message")
        
    # Check the calculation: baseline=12, delta=-0.5, current should be 6
    if "12" in body and "6" in body:
        print("✓ CORRECT: Shows baseline 12 → current 6")
    else:
        print("? Check baseline→current calculation")
