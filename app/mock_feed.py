import asyncio
import random
import time
from typing import Tuple
from app.models import MarketTick, OrderBookItem


class MockMarketFeed:
    def __init__(self):
        self.base_spot = 22000.0
        self.base_future = 22900.0  # 預設正價差 900 點（利於淨套利測試）
        self.stale_mode = False  # 用於測試 Stale Quote 異常
        self.skew_mode = False  # 用於測試 Time Skew 異常

    def generate_depth(self, base_price: float, is_bid: bool) -> list[OrderBookItem]:
        depth = []
        current_price = base_price
        for i in range(5):
            step = random.uniform(0.5, 2.0)
            current_price = (current_price - step) if is_bid else (current_price + step)
            size = random.randint(5, 30)
            depth.append(OrderBookItem(price=round(current_price, 2), size=size))
        return depth

    def get_next_pair(self) -> Tuple[MarketTick, MarketTick]:
        now = time.time()

        # 隨機價格微幅波動
        self.base_spot += random.uniform(-1.5, 1.5)
        self.base_future += random.uniform(-1.5, 1.5)

        spot_last = round(self.base_spot, 2)
        future_last = round(self.base_future, 2)

        spot_bid = round(spot_last - 0.5, 2)
        spot_ask = round(spot_last + 0.5, 2)
        future_bid = round(future_last - 1.0, 2)
        future_ask = round(future_last + 1.0, 2)

        # 模擬時間差 (Time Skew) 測試
        future_ts = now - 5.0 if self.skew_mode else now

        spot_tick = MarketTick(
            symbol="TWSE_NDX",
            market="TWSE",
            broker="MOCK_ADAPTER",
            contract_month="SPOT",
            timestamp_exchange=now,
            timestamp_receive=now,
            last_price=spot_last,
            bid_price=spot_bid,
            bid_size=10,
            ask_price=spot_ask,
            ask_size=10,
            volume=50000,
            bids=self.generate_depth(spot_bid, is_bid=True),
            asks=self.generate_depth(spot_ask, is_bid=False)
        )

        future_tick = MarketTick(
            symbol="TXF",
            market="TAIFEX",
            broker="MOCK_ADAPTER",
            contract_month="202610",
            timestamp_exchange=future_ts,
            timestamp_receive=now,
            last_price=future_last,
            bid_price=future_bid,
            bid_size=15,
            ask_price=future_ask,
            ask_size=15,
            volume=12000,
            bids=self.generate_depth(future_bid, is_bid=True),
            asks=self.generate_depth(future_ask, is_bid=False)
        )

        return spot_tick, future_tick


feed_instance = MockMarketFeed()