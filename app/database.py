import sqlite3
import json
from datetime import datetime

DB_PATH = "arbitrage.db"


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 規則設定表 (Task 7)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rule_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol_pair TEXT UNIQUE,
            net_profit_threshold REAL DEFAULT 4.0,
            cooldown_seconds INTEGER DEFAULT 60,
            re_trigger_step REAL DEFAULT 0.5,
            available_capital REAL DEFAULT 500000.0,
            legging_risk_pct REAL DEFAULT 0.15,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 歷史訊號 Audit Log 表 (Task 10)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            symbol_pair TEXT,
            spot_price REAL,
            future_price REAL,
            spot_ask REAL,
            future_bid REAL,
            raw_basis REAL,
            raw_spread_pct REAL,
            adjusted_spread_pct REAL,
            transaction_cost_pct REAL,
            slippage_pct REAL,
            execution_risk_pct REAL,
            expected_net_profit_pct REAL,
            initial_margin REAL,
            maintenance_margin REAL,
            margin_coverage REAL,
            rule_id INTEGER,
            threshold REAL,
            notification_status TEXT,
            details_json TEXT
        )
    """)

    # 預設寫入一組預設設定
    cursor.execute("""
        INSERT OR IGNORE INTO rule_settings (id, symbol_pair, net_profit_threshold)
        VALUES (1, 'TWSE_NDX/TXF', 4.0)
    """)

    conn.commit()
    conn.close()


def get_rule_settings(symbol_pair: str = "TWSE_NDX/TXF") -> dict:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT net_profit_threshold, cooldown_seconds, re_trigger_step, available_capital, legging_risk_pct FROM rule_settings WHERE symbol_pair = ?",
        (symbol_pair,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {
            "net_profit_threshold": row[0],
            "cooldown_seconds": row[1],
            "re_trigger_step": row[2],
            "available_capital": row[3],
            "legging_risk_pct": row[4]
        }
    return {
        "net_profit_threshold": 4.0,
        "cooldown_seconds": 60,
        "re_trigger_step": 0.5,
        "available_capital": 500000.0,
        "legging_risk_pct": 0.15
    }


def update_rule_settings(symbol_pair: str, threshold: float, cooldown: int, re_trigger: float, capital: float,
                         legging_risk: float):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO rule_settings (symbol_pair, net_profit_threshold, cooldown_seconds, re_trigger_step, available_capital, legging_risk_pct)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(symbol_pair) DO UPDATE SET
            net_profit_threshold = excluded.net_profit_threshold,
            cooldown_seconds = excluded.cooldown_seconds,
            re_trigger_step = excluded.re_trigger_step,
            available_capital = excluded.available_capital,
            legging_risk_pct = excluded.legging_risk_pct,
            updated_at = CURRENT_TIMESTAMP
    """, (symbol_pair, threshold, cooldown, re_trigger, capital, legging_risk))
    conn.commit()
    conn.close()


def save_audit_log(log_data: dict):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO audit_logs (
            timestamp, symbol_pair, spot_price, future_price, spot_ask, future_bid,
            raw_basis, raw_spread_pct, adjusted_spread_pct, transaction_cost_pct,
            slippage_pct, execution_risk_pct, expected_net_profit_pct, initial_margin,
            maintenance_margin, margin_coverage, rule_id, threshold, notification_status, details_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        log_data["timestamp"], log_data["symbol_pair"], log_data["spot_price"], log_data["future_price"],
        log_data["spot_ask"], log_data["future_bid"], log_data["raw_basis"], log_data["raw_spread_pct"],
        log_data["adjusted_spread_pct"], log_data["transaction_cost_pct"], log_data["slippage_pct"],
        log_data["execution_risk_pct"], log_data["expected_net_profit_pct"], log_data["initial_margin"],
        log_data["maintenance_margin"], log_data["margin_coverage"], log_data["rule_id"],
        log_data["threshold"], log_data["notification_status"], json.dumps(log_data)
    ))
    conn.commit()
    conn.close()


def fetch_audit_logs(limit: int = 50) -> list:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM audit_logs ORDER BY id DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()

    logs = []
    for r in rows:
        logs.append({
            "id": r[0], "timestamp": r[1], "symbol_pair": r[2], "spot_price": r[3], "future_price": r[4],
            "raw_basis": r[7], "raw_spread_pct": r[8], "adjusted_spread_pct": r[9],
            "expected_net_profit_pct": r[13], "margin_coverage": r[16], "notification_status": r[19]
        })
    return logs