import joblib
import requests
import os


HERE = os.path.dirname(__file__)
model_path = os.path.join(HERE, "slippage_model.pkl")

# Load the pre-trained slippage model once

_slip_model = joblib.load(model_path)
            

def estimate_slippage(asks, bids, qty_usd, inst_id):
    """
    Predict slippage ($) using a linear regression model.
    Features:
      - spread = (best_ask - best_bid) / mid_price
      - depth5 = sum of volumes at top 5 levels on both sides
      - vol24h = 24h trading volume in USD (fetched via OKX REST)
      - order_size = qty_usd
    """

    best_ask = float(asks[0][0])
    best_bid = float(bids[0][0])
    mid_price = (best_ask + best_bid) / 2


    spread = (best_ask - best_bid) / mid_price             

   
    depth_ask = sum(float(level[1]) for level in asks[:5])
    depth_bid = sum(float(level[1]) for level in bids[:5])
    depth5 = depth_ask + depth_bid                       

    #Fetch 24h volume from OKX ticker endpoint
    resp = requests.get(
        f"https://www.okx.com/api/v5/market/ticker?instId={inst_id}",
        timeout=2
    )                                                       
    data24 = resp.json().get("data", [{}])[0]
    vol24h = float(data24.get("vol24h", 0.0))               

    #Feature vector for prediction
    X = [[spread, depth5, vol24h, qty_usd]]

   
    slippage = _slip_model.predict(X)[0]                    
    return slippage
