import csv
import time
import requests

API      = "https://www.okx.com"
SYMBOL   = "BTC-USDT"
BATCH    = 100
MAX_REC  = 5000
RATE_LIM = 0.2

def fetch_trades(after_id):
    params = {"instId": SYMBOL, "limit": BATCH, "after": after_id}
    r = requests.get("https://www.okx.com/api/v5/market/history-trades", params=params, timeout=5)
    r.raise_for_status()
    return r.json().get("data", [])

def fetch_book():
    params = {"instId": SYMBOL, "sz": 5}
    r = requests.get("https://www.okx.com/api/v5/market/books", params=params, timeout=5)
    r.raise_for_status()
    data = r.json().get("data", [{}])[0]
    
    return data.get("bids", []), data.get("asks", [])

def fetch_vol24h():
    r = requests.get("https://www.okx.com/api/v5/market/ticker", params={"instId": SYMBOL}, timeout=5)
    r.raise_for_status()
    data = r.json().get("data", [{}])[0]
    return float(data.get("vol24h", 0.0))

def main():
    out_file = "slippage_history.csv"
    with open(out_file, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "exec_price",
            "mid_price_at_submit",
            "spread",
            "depth5",
            "vol24h",
            "order_size"
        ])

        after = ""
        count = 0
        vol24h = fetch_vol24h()
        print(f"24h volume = {vol24h}")

        while count < MAX_REC:
            trades = fetch_trades(after)
            if not trades:
                print("No more trades; stopping.")
                break

            bids, asks = fetch_book()
            best_bid = float(bids[0][0])
            best_ask = float(asks[0][0])
            mid = (best_bid + best_ask) / 2
            spread = (best_ask - best_bid) / mid

          
            depth5 = sum(float(level[1]) for level in bids[:5]) \
                   + sum(float(level[1]) for level in asks[:5])

            for t in trades:
                exec_price = float(t["px"])
                order_size = float(t["sz"]) * mid
                writer.writerow([
                    exec_price,
                    mid,
                    spread,
                    depth5,
                    vol24h,
                    order_size
                ])
                count += 1
                if count >= MAX_REC:
                    break

            after = trades[-1]["tradeId"]
            print(f"Fetched {count}/{MAX_REC} trades (cursor={after})")
            time.sleep(RATE_LIM)

    print(f"Done — wrote {count} rows to {out_file}")

if __name__ == "__main__":
    main()
