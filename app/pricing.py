from typing import List
from app.models import MarketTick, OrderBookItem

class DividendEngine:
    """除息點數校正引擎 (Task 3)"""
    def __init__(self):
        # 模擬除息資料：日期與預估影響點數
        self.mock_dividends = [
            {"ex_date": "2026-10-05", "points": 45.0},
            {"ex_date": "2026-10-12", "points": 30.0},
        ]

    def get_expected_dividend_points(self) -> float:
        """計算到期日前預計發生的總除息點數"""
        return sum(item["points"] for item in self.mock_dividends)

class CostEngine:
    """交易成本與滑價估算引擎 (Task 4)"""
    def __init__(
        self,
        future_fee_per_contract: float = 50.0,    # 期貨單邊手續費(NTD)
        future_tax_rate: float = 0.00002,         # 期交稅 10萬分之2
        spot_fee_rate: float = 0.001425 * 0.6,    # 現貨手續費 (打6折)
        spot_tax_rate: float = 0.003,             # 現貨證券交易稅 0.3%
        stock_borrow_rate_annual: float = 0.02,   # 借券年化利率 2%
        holding_days: int = 30,                   # 預計持有天數
        fixed_slippage_pct: float = 0.05          # 預設固定滑價 %
    ):
        self.future_fee_per_contract = future_fee_per_contract
        self.future_tax_rate = future_tax_rate
        self.spot_fee_rate = spot_fee_rate
        self.spot_tax_rate = spot_tax_rate
        self.stock_borrow_rate_annual = stock_borrow_rate_annual
        self.holding_days = holding_days
        self.fixed_slippage_pct = fixed_slippage_pct

    def calculate_vwap_slippage(self, order_book: List[OrderBookItem], target_size: int, base_price: float) -> float:
        """
        加分項：使用 Order Book 5 檔深度估算 VWAP 實際滑價 %
        """
        if not order_book or target_size <= 0:
            return self.fixed_slippage_pct

        accumulated_size = 0
        total_cost = 0.0

        for item in order_book:
            needed = target_size - accumulated_size
            if item.size >= needed:
                total_cost += needed * item.price
                accumulated_size += needed
                break
            else:
                total_cost += item.size * item.price
                accumulated_size += item.size

        if accumulated_size < target_size:
            # 深度不足，回退使用固定滑價
            return self.fixed_slippage_pct

        vwap_price = total_cost / target_size
        slippage_pct = abs(vwap_price - base_price) / base_price * 100.0
        return round(slippage_pct, 4)

    def calculate_total_cost_pct(
        self,
        spot_price: float,
        future_price: float,
        contract_multiplier: float = 200.0,
        target_size: int = 2,
        spot_asks: List[OrderBookItem] = None,
        future_bids: List[OrderBookItem] = None
    ) -> dict:
        """計算總成本百分比"""
        # 現貨成本 %
        spot_cost_pct = (self.spot_fee_rate + self.spot_tax_rate) * 100.0
        # 借券成本 % (依持有天數年化)
        borrow_cost_pct = (self.stock_borrow_rate_annual * (self.holding_days / 365.0)) * 100.0

        # 期貨成本 %
        future_notional = future_price * contract_multiplier
        future_fee_pct = (self.future_fee_per_contract / future_notional) * 100.0
        future_tax_pct = self.future_tax_rate * 100.0
        future_cost_pct = (future_fee_pct + future_tax_pct) * 2  # 進出雙邊

        # VWAP 滑價 (現貨 Ask 深度與期貨 Bid 深度)
        spot_slippage = self.calculate_vwap_slippage(spot_asks, target_size, spot_price) if spot_asks else self.fixed_slippage_pct
        future_slippage = self.calculate_vwap_slippage(future_bids, target_size, future_price) if future_bids else self.fixed_slippage_pct
        total_slippage_pct = spot_slippage + future_slippage

        total_cost_pct = spot_cost_pct + borrow_cost_pct + future_cost_pct + total_slippage_pct

        return {
            "total_cost_pct": round(total_cost_pct, 4),
            "spot_cost_pct": round(spot_cost_pct, 4),
            "future_cost_pct": round(future_cost_pct, 4),
            "borrow_cost_pct": round(borrow_cost_pct, 4),
            "slippage_pct": round(total_slippage_pct, 4)
        }

class PricingCalculator:
    """價差與淨套利核心運算引擎 (Task 2, Task 3, Task 6)"""
    def __init__(self):
        self.dividend_engine = DividendEngine()
        self.cost_engine = CostEngine()

    def calculate_metrics(self, spot_tick: MarketTick, future_tick: MarketTick, legging_risk_pct: float = 0.15) -> dict:
        # 1. Raw Basis & Spread % (使用 Last Price) (Task 2)
        raw_basis = future_tick.last_price - spot_tick.last_price
        raw_spread_pct = (raw_basis / spot_tick.last_price) * 100.0

        # 2. Executable Spread (可成交價差: 買現貨 Spot Ask, 賣期貨 Future Bid) (Task 2)
        executable_basis = future_tick.bid_price - spot_tick.ask_price
        executable_spread_pct = (executable_basis / spot_tick.ask_price) * 100.0

        # 3. 除息點數校正 (Task 3)
        expected_div_points = self.dividend_engine.get_expected_dividend_points()
        adjusted_basis = executable_basis + expected_div_points
        adjusted_spread_pct = (adjusted_basis / spot_tick.ask_price) * 100.0

        # 4. 交易成本與 VWAP 滑價計算 (Task 4)
        cost_details = self.cost_engine.calculate_total_cost_pct(
            spot_price=spot_tick.ask_price,
            future_price=future_tick.bid_price,
            spot_asks=spot_tick.asks,
            future_bids=future_tick.bids
        )

        # 5. 預估淨套利率 (Task 5 & Task 6)
        # ExpectedNetProfit% = AdjustedSpread% - TransactionCost% - ExecutionRisk%
        transaction_cost_pct = cost_details["total_cost_pct"]
        expected_net_profit_pct = adjusted_spread_pct - transaction_cost_pct - legging_risk_pct

        return {
            "raw_basis": round(raw_basis, 2),
            "raw_spread_pct": round(raw_spread_pct, 4),
            "executable_basis": round(executable_basis, 2),
            "executable_spread_pct": round(executable_spread_pct, 4),
            "expected_div_points": expected_div_points,
            "adjusted_basis": round(adjusted_basis, 2),
            "adjusted_spread_pct": round(adjusted_spread_pct, 4),
            "cost_details": cost_details,
            "legging_risk_pct": legging_risk_pct,
            "expected_net_profit_pct": round(expected_net_profit_pct, 4)
        }

pricing_calculator = PricingCalculator()