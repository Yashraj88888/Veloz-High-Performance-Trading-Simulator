def calculate_fee(tier, qty_usd):
    fee_tiers = {
        "Tier 1": 0.001,
        "Tier 2": 0.0008,
        "Tier 3": 0.0005
    }
    return qty_usd * fee_tiers[tier]
