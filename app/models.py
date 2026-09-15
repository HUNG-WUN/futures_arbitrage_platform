from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class OrderBookItem(BaseModel):
    price: float
    size: int

class MarketTick(BaseModel):
    symbol: str               # 商品代號 (如: TXF)
    market: str               # 市場別 (如: TAIFEX / TWSE)
    broker: str               # 資料來源 / Adapter 名稱 (如: MOCK_FEED)
    contract_month: str       # 合約月份 (如: 202610)
    timestamp_exchange: float # 交易所時間戳 (Epoch Unix seconds)
    timestamp_receive: float  # 系統接收時間戳 (Epoch Unix seconds)
    last_price: float         # 成交價
    bid_price: float          # 買一價
    bid_size: int             # 買一量
    ask_price: float          # 賣一價
    ask_size: int             # 賣一量
    volume: int               # 成交量
    # 加分項：5檔委託簿深度 (Order Book Depth)
    bids: List[OrderBookItem] = []
    asks: List[OrderBookItem] = []

class SpreadPair(BaseModel):
    spot_tick: MarketTick
    future_tick: MarketTick