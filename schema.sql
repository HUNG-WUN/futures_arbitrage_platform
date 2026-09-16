-- ============================================================
-- 1. 使用者風控與通知門檻設定表 (Rule Settings)
-- ============================================================
CREATE TABLE IF NOT EXISTS rule_settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol_pair TEXT UNIQUE NOT NULL,       -- 商品對標示 (例如: 'TWSE_NDX/TXF')
    contango_threshold REAL NOT NULL,      -- 正價差通知門檻 (%)
    backwardation_threshold REAL NOT NULL,  -- 逆價差通知門檻 (%)
    cooldown_seconds INTEGER NOT NULL,     -- 防洗通知冷卻時間 (秒)
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- 2. 交易訊號 Audit Trail 歷史日誌表 (Audit Logs)
-- ============================================================
CREATE TABLE IF NOT EXISTS audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    symbol_spot TEXT NOT NULL,
    symbol_future TEXT NOT NULL,
    spot_price REAL NOT NULL,
    future_price REAL NOT NULL,
    spot_bid REAL NOT NULL,
    spot_ask REAL NOT NULL,
    future_bid REAL NOT NULL,
    future_ask REAL NOT NULL,
    raw_basis REAL NOT NULL,
    raw_spread_pct REAL NOT NULL,
    adjusted_spread_pct REAL NOT NULL,
    transaction_cost_pct REAL NOT NULL,
    slippage_cost_pct REAL NOT NULL,
    execution_risk_buffer REAL NOT NULL,
    expected_net_profit_pct REAL NOT NULL,
    initial_margin REAL NOT NULL,
    maintenance_margin REAL NOT NULL,
    margin_coverage REAL NOT NULL,
    rule_id INTEGER,
    threshold_used REAL NOT NULL,
    notification_status TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
