import time
from datetime import datetime
from app.models import MarketTick
from app.database import get_rule_settings, save_audit_log


class NotificationRuleEngine:
    """防洗通知狀態機 (Task 7, Task 9, 異常處理)"""

    def __init__(self):
        self.last_triggered_time = 0.0
        self.last_triggered_profit_pct = 0.0

    def evaluate(self, spot_tick: MarketTick, future_tick: MarketTick, metrics: dict, margin_risk: dict) -> dict:
        now = time.time()
        rules = get_rule_settings("TWSE_NDX/TXF")

        threshold = rules["net_profit_threshold"]
        cooldown = rules["cooldown_seconds"]
        re_trigger_step = rules["re_trigger_step"]

        status = "NORMAL"
        should_notify = False
        status_message = "行情正常，無觸發條件"

        # 1. 異常檢測：Stale Quote (超過 3 秒未更新) (五、必考項目)
        if (now - spot_tick.timestamp_receive > 3.0) or (now - future_tick.timestamp_receive > 3.0):
            status = "STALE_QUOTE"
            status_message = "警告：行情資料逾時未更新 (Stale Quote)，已暫停所有通知"
            return self._build_result(status, False, status_message, metrics, margin_risk, rules)

        # 2. 異常檢測：Time Skew (現貨與期貨時間戳差距 > 2 秒) (五、必考項目)
        skew = abs(spot_tick.timestamp_exchange - future_tick.timestamp_exchange)
        if skew > 2.0:
            status = "INVALID_TIME_SKEW"
            status_message = f"警告：現貨與期貨時間戳落差過大 ({skew:.2f}s)，判定為 Invalid"
            return self._build_result(status, False, status_message, metrics, margin_risk, rules)

        current_profit = metrics["expected_net_profit_pct"]

        # 3. 判斷預估淨套利率是否達標
        if current_profit >= threshold:
            # 檢查 Cooldown 週期
            time_passed = now - self.last_triggered_time
            in_cooldown = time_passed < cooldown

            # 檢查 Re-trigger 增幅條件
            profit_diff = current_profit - self.last_triggered_profit_pct

            if not in_cooldown or (profit_diff >= re_trigger_step):
                # 4. 保證金風險檢查轉置 (Task 9)
                if not margin_risk["is_safe"]:
                    status = "RISK_WARNING"
                    status_message = f"🚨 警示：淨套利率 {current_profit:.2f}% 已達標，但保證金安全覆蓋率低於安全值！請注意風險。"
                else:
                    status = "ARBITRAGE_ALERT"
                    status_message = f"⚡ 機會：預估淨套利率達 {current_profit:.2f}% (門檻: {threshold}%)！"

                should_notify = True
                self.last_triggered_time = now
                self.last_triggered_profit_pct = current_profit

                # 寫入 Audit Log
                log_entry = {
                    "timestamp": datetime.now().isoformat(),
                    "symbol_pair": f"{spot_tick.symbol}/{future_tick.symbol}",
                    "spot_price": spot_tick.last_price,
                    "future_price": future_tick.last_price,
                    "spot_ask": spot_tick.ask_price,
                    "future_bid": future_tick.bid_price,
                    "raw_basis": metrics["raw_basis"],
                    "raw_spread_pct": metrics["raw_spread_pct"],
                    "adjusted_spread_pct": metrics["adjusted_spread_pct"],
                    "transaction_cost_pct": metrics["cost_details"]["total_cost_pct"],
                    "slippage_pct": metrics["cost_details"]["slippage_pct"],
                    "execution_risk_pct": metrics["legging_risk_pct"],
                    "expected_net_profit_pct": current_profit,
                    "initial_margin": margin_risk["initial_margin_required"],
                    "maintenance_margin": margin_risk["maintenance_margin_required"],
                    "margin_coverage": margin_risk["margin_coverage"],
                    "rule_id": 1,
                    "threshold": threshold,
                    "notification_status": status
                }
                save_audit_log(log_entry)
            else:
                status = "COOLDOWN_SUPPRESSED"
                status_message = f"行情符合門檻，但處於 Cooldown 冷卻期內 ({int(cooldown - time_passed)}s 剩餘)，抑制發送"

        return self._build_result(status, should_notify, status_message, metrics, margin_risk, rules)

    def _build_result(self, status: str, notify: bool, msg: str, metrics: dict, margin_risk: dict, rules: dict) -> dict:
        return {
            "status": status,
            "should_notify": notify,
            "message": msg,
            "disclaimer": "本通知僅為條件觸發之市場資訊提醒，不代表交易建議，請自行確認即時行情並人工下單。",
            "threshold": rules["net_profit_threshold"],
            "metrics": metrics,
            "margin_risk": margin_risk
        }


rule_engine = NotificationRuleEngine()