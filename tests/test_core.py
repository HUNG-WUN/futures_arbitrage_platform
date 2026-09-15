import pytest
import time
from app.models import MarketTick
from app.pricing import pricing_calculator, DividendEngine, CostEngine
from app.risk import margin_risk_module
from app.rule_engine import NotificationRuleEngine
from app.database import init_db, update_rule_settings


@pytest.fixture(autouse=True)
def setup_db():
    init_db()
    update_rule_settings("TWSE_NDX/TXF", threshold=4.0, cooldown=60, re_trigger=0.5, capital=500000.0,
                         legging_risk=0.15)


def create_mock_ticks(spot_last=22000.0, future_last=22900.0, spot_delay=0.0, future_delay=0.0):
    now = time.time()
    spot_tick = MarketTick(
        symbol="TWSE_NDX", market="TWSE", broker="TEST", contract_month="SPOT",
        timestamp_exchange=now - spot_delay, timestamp_receive=now - spot_delay,
        last_price=spot_last, bid_price=spot_last - 0.5, bid_size=10, ask_price=spot_last + 0.5, ask_size=10,
        volume=1000
    )
    future_tick = MarketTick(
        symbol="TXF", market="TAIFEX", broker="TEST", contract_month="202610",
        timestamp_exchange=now - future_delay, timestamp_receive=now - future_delay,
        last_price=future_last, bid_price=future_last - 1.0, bid_size=10, ask_price=future_last + 1.0, ask_size=10,
        volume=1000
    )
    return spot_tick, future_tick


def test_executable_spread_and_dividend_adjustment():
    """驗收情境：驗證可成交價差 (Bid/Ask) 與除息點數校正"""
    spot, future = create_mock_ticks(spot_last=20000.0, future_last=20800.0)
    metrics = pricing_calculator.calculate_metrics(spot, future)

    # Executable Basis = Future Bid (20799) - Spot Ask (20000.5) = 798.5
    assert metrics["executable_basis"] == pytest.approx(798.5, 0.1)
    # 應包含 75 點預估除息校正
    assert metrics["expected_div_points"] == 75.0
    assert metrics["adjusted_basis"] == pytest.approx(873.5, 0.1)


def test_notification_trigger_and_cooldown():
    """驗收情境：4.1% 觸發通知，震盪時 Cooldown 機制抑制重複洗通知"""
    engine = NotificationRuleEngine()
    spot, future = create_mock_ticks(spot_last=20000.0, future_last=21100.0)

    metrics = pricing_calculator.calculate_metrics(spot, future)
    margin = margin_risk_module.evaluate_margin(future.bid_price, available_capital=1000000.0)

    # 第一次 4.1% 達到門檻 (4.0%) -> 應觸發 ARBITRAGE_ALERT
    res1 = engine.evaluate(spot, future, metrics, margin)
    assert res1["status"] == "ARBITRAGE_ALERT"
    assert res1["should_notify"] is True

    # 4.1% -> 3.99% -> 4.02% 震盪 (處於 Cooldown 內) -> 應被抑制
    res2 = engine.evaluate(spot, future, metrics, margin)
    assert res2["status"] == "COOLDOWN_SUPPRESSED"
    assert res2["should_notify"] is False


def test_stale_quote_suppression():
    """驗收情境：行情停止更新 3 秒以上 -> 顯示 STALE_QUOTE，不發通知"""
    engine = NotificationRuleEngine()
    spot, future = create_mock_ticks(spot_last=20000.0, future_last=21100.0, spot_delay=4.0)

    metrics = pricing_calculator.calculate_metrics(spot, future)
    margin = margin_risk_module.evaluate_margin(future.bid_price)

    res = engine.evaluate(spot, future, metrics, margin)
    assert res["status"] == "STALE_QUOTE"
    assert res["should_notify"] is False


def test_margin_risk_warning_override():
    """驗收情境：淨套利率達標，但 Margin Coverage 低於安全值 -> 轉為 RISK_WARNING 警示"""
    engine = NotificationRuleEngine()
    spot, future = create_mock_ticks(spot_last=20000.0, future_last=21100.0)

    metrics = pricing_calculator.calculate_metrics(spot, future)
    # 設定可用資金過低 (僅 150,000，低於原始保證金 167,000)
    margin = margin_risk_module.evaluate_margin(future.bid_price, available_capital=150000.0)

    res = engine.evaluate(spot, future, metrics, margin)
    assert res["status"] == "RISK_WARNING"
    assert res["should_notify"] is True
    assert "警示" in res["message"]