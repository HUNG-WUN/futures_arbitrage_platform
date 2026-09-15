class MarginRiskModule:
    """保證金風險與壓力測試模組 (Task 8)"""
    def __init__(
        self,
        contract_multiplier: float = 200.0,   # 台指期契約乘數 (200元/點)
        initial_margin_per_contract: float = 167000.0, # 原始保證金 (預設單口)
        maintenance_margin_per_contract: float = 128000.0, # 維持保證金
        safety_threshold: float = 120.0        # 保證金安全覆蓋率門檻 (120%)
    ):
        self.contract_multiplier = contract_multiplier
        self.initial_margin_per_contract = initial_margin_per_contract
        self.maintenance_margin_per_contract = maintenance_margin_per_contract
        self.safety_threshold = safety_threshold

    def evaluate_margin(
        self,
        future_price: float,
        available_capital: float = 500000.0, # 使用者可用資金
        position_lots: int = 1
    ) -> dict:
        notional_value = future_price * self.contract_multiplier * position_lots
        total_initial_margin = self.initial_margin_per_contract * position_lots
        total_maintenance_margin = self.maintenance_margin_per_contract * position_lots

        initial_margin_ratio = (total_initial_margin / notional_value) * 100.0
        margin_coverage = (available_capital / total_initial_margin) * 100.0 if total_initial_margin > 0 else 0.0

        # 不利市場波動壓力測試 (-1%, -3%, -5%) (Task 8)
        stress_tests = {}
        for shock_pct in [-1.0, -3.0, -5.0]:
            # 假設短期急漲/急跌對期貨頭寸的不利變動金額
            loss = notional_value * abs(shock_pct / 100.0)
            remaining_equity = available_capital - loss
            is_margin_call = remaining_equity < total_maintenance_margin
            stress_tests[f"shock_{abs(int(shock_pct))}_pct"] = {
                "remaining_equity": round(remaining_equity, 2),
                "is_margin_call": is_margin_call,
                "coverage_after_shock": round((remaining_equity / total_initial_margin) * 100.0, 2)
            }

        is_safe = margin_coverage >= self.safety_threshold and not any(
            t["is_margin_call"] for t in stress_tests.values()
        )

        return {
            "notional_value": round(notional_value, 2),
            "initial_margin_required": total_initial_margin,
            "maintenance_margin_required": total_maintenance_margin,
            "initial_margin_ratio": round(initial_margin_ratio, 2),
            "margin_coverage": round(margin_coverage, 2),
            "is_safe": is_safe,
            "stress_tests": stress_tests
        }

margin_risk_module = MarginRiskModule()