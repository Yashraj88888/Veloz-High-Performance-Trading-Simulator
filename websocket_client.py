import os
import json
import time
import asyncio
import logging
import statistics
import requests
import websockets
from datetime import datetime
from PyQt5.QtCore import QThread, pyqtSignal
from models.impact import calculate_impact
from models.slippage import estimate_slippage
from models.maker_taker import predict_maker_taker
from utils.fees import calculate_fee
from utils.latency import measure_latency

LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "latency_metrics.log")
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("LatencyMetrics")
# All latency metrics are calculated and logged in this file

class WebSocketClient(QThread):
    tick_signal = pyqtSignal(str)
    connection_signal = pyqtSignal(bool)

    def __init__(self, asset, qty_usd, fee_tier, volatility, parent=None):
        super().__init__(parent)
        self.asset = asset
        self.qty_usd = float(qty_usd)
        self.fee_tier = fee_tier
        self.volatility = float(volatility)
        self._running = True
        self.connected = False
        self.ac_params = {
            'delta': 0.5,    # Gatheral: impact exponent
            'gamma': 0.45,   # Gatheral: decay exponent
            'lam': 1e-6,     # risk aversion
            'T': 1.0,        # trading horizon
            'N': 100         # intervals
        }
        
        # Latency tracking variables
        self._last_arrival = None
        self._arrival_times = []
        self._proc_times = []
        self._ui_times = []
        self._tick_count = 0
        self._window = 100

    def stop(self):
        self._running = False

    def run(self):
        asyncio.run(self._async_run())

    async def _async_run(self):
        uri = "wss://ws.okx.com:8443/ws/v5/public"
        sub_msg = {
            "op": "subscribe",
            "args": [{"channel": "books", "instId": self.asset}]
        }
        
        while self._running:
            try:
                async with websockets.connect(uri, ping_interval=25) as ws:
                    if not self.connected:
                        self.tick_signal.emit("Connected to OKX WebSocket...\n")
                        self.connected = True
                        self.connection_signal.emit(True)
                    await ws.send(json.dumps(sub_msg))
                    
                    while self._running:
                        # Arrival interval measurement
                        now = time.perf_counter()
                        if self._last_arrival is not None:
                            self._arrival_times.append(now - self._last_arrival)
                            if len(self._arrival_times) > self._window:
                                self._arrival_times.pop(0)
                        self._last_arrival = now
                        
                        try:
                            # Network latency measurement which will be used to calculate the latency
                            start_recv = time.time()
                            msg = await asyncio.wait_for(ws.recv(), timeout=5)
                            network_latency_ms = measure_latency(start_recv)
                            
                            # Processing latency
                            proc_start = time.perf_counter()
                            tick = json.loads(msg)
                            
                            if 'data' not in tick or not tick['data']:
                                continue
                                
                            book_data = tick['data'][0]
                            timestamp = int(book_data.get('ts', 0))
                            dt = datetime.fromtimestamp(timestamp / 1000.0)
                            formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                            
                            # Order book processing which will be used to calculate the slippage
                            asks = book_data.get('asks', [])
                            bids = book_data.get('bids', [])
                            if not asks or not bids:
                                continue
                                
                            try:
                                asks = [[float(p[0]), float(p[1])] for p in asks if float(p[0]) > 0 and float(p[1]) >= 0]
                                bids = [[float(p[0]), float(p[1])] for p in bids if float(p[0]) > 0 and float(p[1]) >= 0]
                            except Exception:
                                continue
                                
                            if not asks or not bids:
                                continue
                                
                            # Mid-price calculation which will be used to calculate the slippage
                            try:
                                top_bids = [p[0] for p in bids[:5]]
                                top_asks = [p[0] for p in asks[:5]]
                                if not top_bids or not top_asks:
                                    continue
                                mid_price = (sum(top_bids)/len(top_bids) + sum(top_asks)/len(top_asks)) / 2.0
                                if mid_price <= 0:
                                    continue
                            except Exception:
                                continue
                                
                            # Cost calculations which will be used to calculate the net cost
                            try:
                                slippage = estimate_slippage(asks, bids, self.qty_usd, self.asset)
                                fee = calculate_fee(self.fee_tier, self.qty_usd)
                                
                                try:
                                    impact_value, impact_breakdown = calculate_impact(
                                        orderbook=asks,
                                        qty_usd=self.qty_usd,
                                        sigma=self.volatility,
                                        **self.ac_params
                                    )
                                except ZeroDivisionError:
                                    impact_value = 0.0
                                    impact_breakdown = {'transient': 0, 'permanent': 0, 'risk': 0}
                                    
                                trade_price = float(book_data.get('lastPx', asks[0][0])) if asks else 0.0
                                trade_side = 'buy' if book_data.get('side') == 'bid' else 'sell'
                                trade_size = float(book_data.get('sz', self.qty_usd / trade_price)) if trade_price else 0.0
                                is_taker = predict_maker_taker(asks, bids, trade_price, trade_side, trade_size)
                                maker_taker = "Taker" if is_taker else "Maker"
                                net_cost = slippage + impact_value + fee
                                
                                proc_end = time.perf_counter()
                                self._proc_times.append(proc_end - proc_start)
                                if len(self._proc_times) > self._window:
                                    self._proc_times.pop(0)
                                
                                # UI update latency
                                ui_start = time.perf_counter()
                                ui_text = (
                                    f"Timestamp:   {formatted_time}\n"
                                    f"Slippage:    {slippage:.2f}\n"
                                    f"Impact:      {impact_value:.2f} "
                                    f"(transient={impact_breakdown.get('transient',0):.2f}, "
                                    f"perm={impact_breakdown.get('permanent',0):.2f}, "
                                    f"risk={impact_breakdown.get('risk',0):.2f})\n"
                                    f"Fee:         {fee:.2f}\n"
                                    f"Net Cost:    {net_cost:.2f}\n"
                                    f"Maker/Taker: {maker_taker}\n"
                                    f"Network Lat: {network_latency_ms:.3f} ms\n\n"
                                )
                                self.tick_signal.emit(ui_text)
                                ui_end = time.perf_counter()
                                self._ui_times.append(ui_end - ui_start)
                                if len(self._ui_times) > self._window:
                                    self._ui_times.pop(0)
                                
                                # Logging
                                data_proc_ms = (proc_end - proc_start) * 1000
                                ui_upd_ms = (ui_end - ui_start) * 1000
                                e2e_ms = (ui_end - now) * 1000
                                logger.info(
                                    f"DataProc={data_proc_ms:.2f}ms "
                                    f"UIUpdate={ui_upd_ms:.2f}ms "
                                    f"EndToEnd={e2e_ms:.2f}ms"
                                )
                                
                                # Periodic metrics
                                self._tick_count += 1
                                if self._tick_count % self._window == 0:
                                    p50_pr = statistics.median(self._proc_times) * 1000
                                    p99_pr = sorted(self._proc_times)[int(len(self._proc_times)*0.99)] * 1000
                                    p50_ui = statistics.median(self._ui_times) * 1000
                                    p99_ui = sorted(self._ui_times)[int(len(self._ui_times)*0.99)] * 1000
                                    print(f"[Metrics @ tick {self._tick_count}]")
                                    print(f" Processing p50={p50_pr:.1f}ms, p99={p99_pr:.1f}ms")
                                    print(f" UI update  p50={p50_ui:.1f}ms, p99={p99_ui:.1f}ms")
                                    self._arrival_times.clear()
                                    self._proc_times.clear()
                                    self._ui_times.clear()
                                    
                            except Exception as e:
                                self.tick_signal.emit(f"Processing error: {e}\n")
                                continue
                                
                        except (asyncio.TimeoutError, KeyError, IndexError) as e:
                            continue
                            
            except Exception as e:
                self.connected = False
                self.connection_signal.emit(False)
                self.tick_signal.emit(f"WebSocket error: {e}\n")
                await asyncio.sleep(2)

def fetch_available_assets():
    url = "https://www.okx.com/api/v5/public/instruments"
    try:
        resp = requests.get(url, params={"instType": "SPOT"}, timeout=10)
        resp.raise_for_status()
        data = resp.json().get("data", [])
        return [inst["instId"] for inst in data if inst.get("state") == "live"]
    except Exception as e:
        print("Error fetching assets:", e)
        return []
