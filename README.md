<div align="center">
  <h1>⚡ 期貨正逆價差即時監控與通知平台 V1.0</h1>
  <p><b>高效能、高可靠度之期貨／現貨價差即時監控、風控與通知系統原型</b></p>

  <p>
    <a href="https://github.com/AuroraShiao/NASA-Ultra-High-Resolution-Imagery-Cloud-Interactive-Platform">
      <img src="https://img.shields.io/badge/GitHub-Repository-blue?logo=github" alt="GitHub Repo" />
    </a>
    <img src="https://img.shields.io/badge/Python-3.10+-green?logo=python" alt="Python Version" />
    <img src="https://img.shields.io/badge/FastAPI-0.100+-009688?logo=fastapi" alt="FastAPI" />
    <img src="https://img.shields.io/badge/Docker-Supported-2496ED?logo=docker" alt="Docker" />
    <img src="https://img.shields.io/badge/SQLite-Database-003B57?logo=sqlite" alt="SQLite" />
    <img src="https://img.shields.io/badge/License-MIT-yellow" alt="License" />
  </p>
</div>

<hr />

<h2>⚠️ 重要責任與免責聲明</h2>
<blockquote style="background-color: #f8d7da; color: #721c24; padding: 12px; border-left: 5px solid #f5c6cb;">
  <p><b>1. 本系統僅進行市場資訊監控、計算與通知，絕對不進行任何自動或半自動下單。</b></p>
  <p>2. 所有交易決策與實際下單均由使用者自行負責。</p>
  <p>3. 系統所有通知與介面均明確附註：「<b>本通知僅為條件觸發之市場資訊提醒，不代表交易建議，請自行確認即時行情並人工下單。</b>」</p>
</blockquote>

<hr />

<h2>✨ 系統核心功能</h2>
<ul>
  <li><b>即時行情 Dashboard</b>：使用 WebSocket 長連線全雙工推播現貨與期貨 Bid/Ask 檔位與價格，前端無須刷新。</li>
  <li><b>實質可成交價差計算</b>：考量買賣雙邊深度，採用 Future Bid 與 Spot Ask 估算實質可成交價差。</li>
  <li><b>除息點數動態校正</b>：自動扣除合約到期日前預估發生之除息點數（Adjusted Basis）。</li>
  <li><b>VWAP 5 檔深度滑價估算</b>：超越固定滑價，依據委託簿 Order Book 5 檔流動性計算動態 VWAP 交易成本。</li>
  <li><b>保證金壓力測試</b>：提供 -1%、-3%、-5% 不利市場波動壓力測試與安全覆蓋率監控。</li>
  <li><b>防洗通知狀態機</b>：包含 Stale Quote（逾時停更）、Time Skew（現期時間差）、Cooldown 冷卻期、Re-trigger 門檻與風控轉置警示。</li>
  <li><b>30 分鐘視覺化走勢圖</b>：前端整合 Chart.js，即時繪製價差率與預估淨套利率歷史走勢。</li>
</ul>

<hr />

<h2>🚀 系統快速啟動方式 (Quick Start)</h2>

<h3>方式一：Docker Compose 一鍵啟動 (推薦)</h3>
<pre><code>docker compose up -d --build</code></pre>
<ul>
  <li><b>Dashboard 網址</b>: <code>http://localhost:8000</code></li>
  <li><b>Swagger API 文件</b>: <code>http://localhost:8000/docs</code></li>
  <li><b>執行容器內全自動測試</b>:
    <pre><code>docker compose exec arbitrage-platform pytest</code></pre>
  </li>
</ul>

<h3>方式二：本機 Python 環境啟動</h3>
<ol>
  <li><b>安裝依賴套件</b>:
    <pre><code>pip install -r requirements.txt</code></pre>
  </li>
  <li><b>啟動 FastAPI Web 服務</b>:
    <pre><code>uvicorn app.main:app --reload --port 8000</code></pre>
  </li>
  <li><b>執行單元測試</b>:
    <pre><code>pytest</code></pre>
  </li>
</ol>

<hr />

<h2>🏗️ 系統架構與 Clean Architecture 切分</h2>

<pre>
[ Market Data Feed ] ---> ( Market Data Adapter )
                                  |
                                  v
[ Rule Settings DB ] ---> ( Pricing Engine ) ---> ( Risk Engine )
                                  |                     |
                                  v                     v
                        ( Notification Engine / State Machine )
                                  |
                         +--------+--------+
                         |                 |
                         v                 v
                [ Web Alert / WS ]   [ Audit Log DB ]
</pre>

<table>
  <thead>
    <tr>
      <th>模組名稱</th>
      <th>程式碼路徑</th>
      <th>職責說明</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><b>Market Data Adapter</b></td>
      <td><code>app/mock_feed.py</code></td>
      <td>正規化市場數據，處理 Tick 資料結構與 5 檔 Order Book 深度推播。</td>
    </tr>
    <tr>
      <td><b>Pricing Engine</b></td>
      <td><code>app/pricing.py</code></td>
      <td>無狀態運算模組，負責算術價差、除息校正、VWAP 滑價與預估淨套利率。</td>
    </tr>
    <tr>
      <td><b>Risk Engine</b></td>
      <td><code>app/risk.py</code></td>
      <td>計算保證金覆蓋率，並執行 -1%~-5% 極端波動壓力測試。</td>
    </tr>
    <tr>
      <td><b>Rule Engine</b></td>
      <td><code>app/rule_engine.py</code></td>
      <td>具狀態防洗機制，處理 Cooldown、Re-trigger、Stale Quote 與風控轉置。</td>
    </tr>
    <tr>
      <td><b>Database & Log</b></td>
      <td><code>app/database.py</code></td>
      <td>使用 SQLite 持久化規則設定並保存完整的觸發 Audit Log 紀錄。</td>
    </tr>
  </tbody>
</table>
<hr />

<h2>📅 正式版除息資料擷取策略 (Dividend Data Retrieval Strategy)</h2>
<p>針對 Task 3 實務上正式版串接臺灣證券交易所 (TWSE) 與公開資訊觀測站 (MOPS) 之策略說明：</p>
<ul>
  <li><b>資料來源 (Data Sources)</b>：
    <ul>
      <li>臺灣證券交易所 (TWSE) OpenAPI / 每日除權除息預告表 (Daily Ex-Dividend Schedule)。</li>
      <li>公開資訊觀測站 (MOPS) 公司重大訊息與股利分派公告。</li>
    </ul>
  </li>
  <li><b>擷取機制 (ETL & Batch Scheduling)</b>：
    <ul>
      <li><b>每日排程 (Daily Cron Job)</b>：每日清晨 05:00 執行 ETL Pipeline，自動抓取當日及未來 30 天內預定除息之權值股名單、發放現金股利金額與配股資訊。</li>
      <li><b>快取機制 (Redis Caching)</b>：預期除息點數計算結果寫入 Redis 快取（Key: <code>div_points:{contract_month}</code>），供即時 Pricing Engine 毫秒級調用，避免每筆 Tick 重新查詢 DB。</li>
    </ul>
  </li>
  <li><b>除息點數動態換算邏輯 (Point Impact Calculation)</b>：
    <ul>
      <li>依據權值股佔大盤權重公式：$\text{影響點數} = \frac{\text{個股現金股利} \times \text{公司發行股數}}{\text{大盤總市值基期}} \times \text{當期大盤指數}$。</li>
      <li>僅動態採計「當前時間至該期貨合約到期日 (Settlement Date) 之間」發生的除息總點數。</li>
    </ul>
  </li>
  <li><b>資料異常與防呆機制 (Exception Handling)</b>：
    <ul>
      <li>若證交所 API 斷線或爬蟲抓取失敗，系統自動回退 (Fallback) 使用前一日的快取數據，並將系統除息狀態標記為 <code>DIVIDEND_UNVERIFIED</code>。</li>
      <li>前端畫面同步呈現風險警告標籤，避免交易員因數據缺損產生誤判。</li>
    </ul>
  </li>
</ul>
<hr />
<hr />

<h2>⚖️ 正式版 Legging Risk 動態估算策略 (Dynamic Legging Risk Engine)</h2>
<p>針對兩腿交易（買現貨、賣期貨）無法 100% 同步成交之執行風險 (Legging Risk)，正式版系統將從固定 Buffer 升級為動態風險估算模型，採計以下關鍵數據：</p>
<ul>
  <li><b>API 端到端延遲 (API Latency & Network Skew)</b>：即時監測券商 WebSocket/FIX 介面之往返延遲 (RTT) 與現期兩腿時間戳落差 (Time Skew)。延遲越高， Legging Risk Buffer 動態調升。</li>
  <li><b>委託簿深度與吃單耗損 (Order Book Depth & Sweep Cost)</b>：分析 5 檔 Bid/Ask 的檔位掛單量，若頂檔掛單量不足以消化目標張數，動態計入穿透滑價成本。</li>
  <li><b>市場即時波動率 (Real-time Volatility - IV / RV)</b>：採計標的資產近 1 分鐘與 5 分鐘之高頻波動率，當市場處於劇烈波動時，自動放寬風險緩衝區。</li>
  <li><b>歷史成交率與撤單率 (Historical Fill Rate & Cancel Rate)</b>：統計過去 100 筆觸發訂單在該券商 API 的平均成交時間與失敗/部分成交 (Partial Fill) 機率。</li>
  <li><b>即時市場成交量與流動性 (Market Volume & Liquidity Index)</b>：評估當前 Tick 的成交活絡度，避免在流動性枯竭時段發出虛假套利訊號。</li>
</ul>

<h2>📋 考題第十三區塊：題目與回答</h2>

<h3>Q1: 你如何切分 Market Data、Pricing、Risk、Rule、Notification 各模組？</h3>
<ul>
  <li><b>Market Data Adapter</b>: 負責解碼券商 API 原始封包，轉換為統一的 <code>MarketTick</code> Pydantic 模型，隔離特定券商 API 格式。</li>
  <li><b>Pricing Engine</b>: 無狀態（Stateless）純粹運算模組，接收現單與期單 Tick，輸出原始價差、可成交價差、除息調整後價差與預估淨套利率。</li>
  <li><b>Risk Engine</b>: 評估帳戶資金與期貨頭寸，進行 -1%~-5% 壓力測試並輸出保證金安全狀態。</li>
  <li><b>Rule Engine</b>: 具狀態（Stateful）模組，維護上次觸發時間與收益率，執行 Cooldown、Re-trigger 與風險轉置邏輯。</li>
  <li><b>Notification Engine</b>: 負責推送前台 Web Alert / Browser Notification 並寫入 Audit Log DB。</li>
</ul>

<h3>Q2: 你選用的資料庫與即時通訊技術是什麼？原因為何？</h3>
<ul>
  <li><b>即時通訊</b>: 選用 <b>WebSocket</b>。因為 WebSocket 為雙向長連線全雙工協定，延遲通常低於 5ms，適合每秒多 Tick 的行情推播與即時通知，且前端無需輪詢 (Polling)。</li>
  <li><b>資料庫</b>: 原型選擇 <b>SQLite</b>（正式上線擬擴充為 <b>PostgreSQL + Redis</b>）。SQLite 為輕量級嵌入式 DB，無需額外安裝 Docker 即可保存規則與紀錄；Redis 則用於高頻行情快取與 Cooldown 狀態過期控制。</li>
</ul>

<h3>Q3: 哪些欄位需要保留原始 Tick，哪些可只存計算結果？</h3>
<ul>
  <li><b>保留原始 Tick</b>: <code>symbol</code>、<code>timestamp_exchange</code>、<code>timestamp_receive</code>、<code>last_price</code>、<code>bid_price</code>、<code>ask_price</code>、<code>bid_size</code>、<code>ask_size</code>、<code>volume</code>。保留這些欄位才能在爭議時進行歷史行情重播 (Tick Replay) 與回測。</li>
  <li><b>僅存計算結果</b>: <code>raw_basis</code>、<code>adjusted_spread_pct</code>、<code>transaction_cost_pct</code>、<code>expected_net_profit_pct</code>、<code>margin_coverage</code>。這些屬於特定策略邏輯導出的中間產物，可直接保存於 Audit Log 供稽核查詢。</li>
</ul>

<h3>Q4: 正式版要串 Shioaji、富邦、群益三家，你會如何避免重寫核心邏輯？</h3>
<ul>
  <li>採用 <b>Adapter Pattern (適配器模式)</b> 與定義抽象介面 <code>BaseMarketDataAdapter</code>。</li>
  <li>針對 Shioaji, Fubon, Capital 分別實作 concrete class（如 <code>ShioajiAdapter</code>），將各家獨有的 API 封包統一轉換為標準的 <code>MarketTick</code> 數據模型。</li>
  <li>核心 Pricing, Risk, Rule Engine 僅與抽象的 <code>MarketTick</code> 互動，達到「新增券商來源時，完全不需改動核心金融邏輯」的解耦效果。</li>
</ul>

<h3>Q5: 你認為本 Prototype 最可能產生錯誤交易訊號的三個原因是什麼？</h3>
<ol>
  <li><b>除息點數預估失真或時間未更新</b>: 若上市櫃公司臨時變更除息日或股利金額，而除息資料庫未即時更新，會導致 <code>AdjustedBasis</code> 算錯，發出虛假的套利訊號。</li>
  <li><b>Order Book 瞬間流動性抽空 (Slippage Spikes)</b>: 行情劇烈波動時，單純依賴 Bid-Ask 頂檔價格計算可能會因委託薄太薄而產生嚴重滑價，導致實際下單無法達成預估淨套利率。</li>
  <li><b>現期兩腿行情時間未完全同步 (Time Skew)</b>: 當現貨與期貨來自不同券商 API 或 WebSocket 節點時，若時間戳落差超過 500ms，產生的價差可能是「歷史現貨對上最新期貨」的幻影價差。</li>
</ol>

<hr />

<h2>📝 未完成項目與正式上線建議 (One-Page Proposal)</h2>

<h3>未完成項目</h3>
<ul>
  <li><b>多商品與多策略 Rule 動態套用</b>: MVP 目前預設針對 TWSE_NDX / TXF 組合，未來需擴充可透過 UI 動態新增多組對應商品。</li>
  <li><b>分散式 Pub/Sub 架構</b>: 目前 WebSocket 廣播由單台 FastAPI 記憶體維持，未接入 Redis Pub/Sub。</li>
</ul>

<h3>正式上線架構建議</h3>
<ul>
  <li><b>行情降級機制 (Graceful Degradation)</b>:
    <p>當官方除息資料抓取失敗時，系統應自動將除息點數標示為 <code>UNVERIFIED</code>，並在前端標註風險警告，通知依原始價差進行保守判斷。</p>
  </li>
  <li><b>高頻數據抗壓 (High Throughput Architecture)</b>:
    <p>導入 Kafka 或 Redis Stream 作為 Event Bus，緩衝每秒數千筆 Tick；前端採用 LMAX Disruptor 思想或 Ring Buffer 進行 100ms 批次微渲染 (Throttling)，避免 DOM 刷新被壓垮。</p>
  </li>
  <li><b>自動下單風控模組擴充 (若未來開放自訂下單)</b>:
    <p>需強制新增：單筆最大委託張數限制、每日累積虧損斷路器 (Circuit Breaker)、Fat-finger 防呆、API Key 依 IP 綁定與雙重硬體鎖驗證。</p>
  </li>
</ul>