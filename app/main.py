import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from app.database import init_db, get_rule_settings, update_rule_settings, fetch_audit_logs
from app.mock_feed import feed_instance
from app.pricing import pricing_calculator
from app.risk import margin_risk_module
from app.rule_engine import rule_engine

app = FastAPI(title="期貨正逆價差即時監控與通知平台")


@app.on_event("startup")
def startup_event():
    init_db()


class RuleUpdateRequest(BaseModel):
    net_profit_threshold: float
    cooldown_seconds: int
    re_trigger_step: float
    available_capital: float
    legging_risk_pct: float


@app.get("/api/rules")
def read_rules():
    return get_rule_settings("TWSE_NDX/TXF")


@app.post("/api/rules")
def save_rules(rules: RuleUpdateRequest):
    update_rule_settings(
        symbol_pair="TWSE_NDX/TXF",
        threshold=rules.net_profit_threshold,
        cooldown=rules.cooldown_seconds,
        re_trigger=rules.re_trigger_step,
        capital=rules.available_capital,
        legging_risk=rules.legging_risk_pct
    )
    return {"status": "success"}


@app.get("/api/logs")
def read_logs(limit: int = 50):
    return fetch_audit_logs(limit=limit)


@app.post("/api/test_mode")
def set_test_mode(stale: bool = False, skew: bool = False):
    feed_instance.stale_mode = stale
    feed_instance.skew_mode = skew
    return {"stale_mode": stale, "skew_mode": skew}


@app.websocket("/ws/market")
async def websocket_market(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            spot_tick, future_tick = feed_instance.get_next_pair()
            rules = get_rule_settings("TWSE_NDX/TXF")

            metrics = pricing_calculator.calculate_metrics(
                spot_tick, future_tick, legging_risk_pct=rules["legging_risk_pct"]
            )

            margin_risk = margin_risk_module.evaluate_margin(
                future_price=future_tick.bid_price,
                available_capital=rules["available_capital"]
            )

            eval_result = rule_engine.evaluate(spot_tick, future_tick, metrics, margin_risk)

            payload = {
                "spot": spot_tick.dict(),
                "future": future_tick.dict(),
                "eval": eval_result
            }

            await websocket.send_json(payload)
            await asyncio.sleep(1.0)
    except WebSocketDisconnect:
        pass


@app.get("/", response_class=HTMLResponse)
def get_index():
    with open("frontend/index.html", "r", encoding="utf-8") as f:
        return f.read()