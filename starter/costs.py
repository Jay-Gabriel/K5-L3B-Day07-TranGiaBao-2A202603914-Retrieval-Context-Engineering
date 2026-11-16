"""Explicit estimates; paid-equivalent cost is not an account invoice."""
import os
PRICE_SOURCE='https://ai.google.dev/gemini-api/docs/pricing#gemini-3.1-flash-lite'

def estimate_cost(usage,model):
    if model!='gemini-3.1-flash-lite':
        return {'cost_usd':None,'paid_equivalent_usd':None,'cost_note':'No verified rates for this model.'}
    value=(usage.get('promptTokenCount',0)*0.25 +
           (usage.get('candidatesTokenCount',0)+usage.get('thoughtsTokenCount',0))*1.50)/1_000_000
    tier=os.getenv('GEMINI_BILLING_TIER','unknown')
    return {'cost_usd':0.0 if tier=='free' else round(value,8) if tier=='paid' else None,'paid_equivalent_usd':round(value,8), 'billing_tier_assumption':tier, 'invoice_verified':False,
        'cost_note':'Estimated marginal text API charge under the configured billing tier; free=$0, paid=standard token estimate, unknown=null; not a billing invoice. Paid-equivalent uses standard $0.25/M input and $1.50/M output including thoughts. Excludes local compute/Qdrant hosting.',
        'cost_source':PRICE_SOURCE,'cost_rates_checked_at':'2026-11-16'}
