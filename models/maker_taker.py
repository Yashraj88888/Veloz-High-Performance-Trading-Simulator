import os, joblib

#Load classifier once
HERE = os.path.dirname(__file__)
model_path = os.path.join(HERE, "maker_taker_model.pkl")
clf = joblib.load(model_path)

def predict_maker_taker(asks, bids, price, side, size):

    best_bid = float(bids[0][0])
    best_ask = float(asks[0][0])
    spread = best_ask - best_bid

    # Aggressiveness
    if side == "buy":
        aggr = price - best_bid
    else:
        aggr = best_ask - price
    rel_aggr = aggr / spread if spread>0 else 0.0

    # Depth ratio (using top 5 pre-fetched)
    depth5 = sum(float(l[1]) for l in bids[:5]) + sum(float(l[1]) for l in asks[:5])
    size_depth_ratio = size / depth5 if depth5>0 else 0.0

    # Predicting probability
    prob_taker = clf.predict_proba([[rel_aggr, size_depth_ratio]])[0][1]
    return 1 if prob_taker >= 0.5 else 0
