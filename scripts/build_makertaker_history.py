import csv
import time
import requests

BINANCE_API = "https://api.binance.com"
SYMBOL      = "BTCUSDT"
LIMIT       = 1000     
PAGES       = 10        
DEPTH_SZ    = 5         # top-5 levels


def fetch_trades():
    """Yield batches of historical trades from Binance."""
    url = f"{BINANCE_API}/api/v3/historicalTrades"
 
    for i in range(PAGES):
        params = {"symbol": SYMBOL, "limit": LIMIT}
        resp = requests.get(url, params=params, timeout=5)
        resp.raise_for_status()
        trades = resp.json()
        if not trades:
            break
        yield trades
        # Binance uses fromId param for pagination in production,
        # but for simplicity I will just fetch the latest PAGES batches.
        time.sleep(0.5)

def fetch_orderbook():
    """Return top-5 bids and asks from Binance order book."""
    url = f"{BINANCE_API}/api/v3/depth"
    params = {"symbol": SYMBOL, "limit": DEPTH_SZ}
    resp = requests.get(url, params=params, timeout=5)
    resp.raise_for_status()
    book = resp.json()
    return book["bids"], book["asks"]

def main():
    out_csv = "maker_taker_history.csv"
    with open(out_csv, "w", newline="") as f:
        writer = csv.writer(f)
     
        writer.writerow([
            "trade_price","trade_size","side",
            "best_bid","best_ask",
            "bid_depth5","ask_depth5",
            "is_taker"
        ])

        for trades in fetch_trades():
            bids, asks = fetch_orderbook()

            best_bid = float(bids[0][0])
            best_ask = float(asks[0][0])
            bid_depth5 = sum(float(lvl[1]) for lvl in bids[:5])
            ask_depth5 = sum(float(lvl[1]) for lvl in asks[:5])

            for t in trades:
                price = float(t["price"])
                size  = float(t["qty"])
                
                side = "sell" if t["isBuyerMaker"] else "buy"
                is_taker = int(t["isBuyerMaker"])

                writer.writerow([
                    price, size, side,
                    best_bid, best_ask,
                    bid_depth5, ask_depth5,
                    is_taker
                ])
        print(f"Built {out_csv}")

if __name__ == "__main__":
    main()
