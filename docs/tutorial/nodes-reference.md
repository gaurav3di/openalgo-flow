# Nodes Reference

Complete documentation for all workflow nodes in OpenAlgo Flow.

---

## Node Categories

| Category | Purpose |
|----------|---------|
| [Triggers](#triggers) | Start workflow execution |
| [Actions](#actions) | Execute trading operations |
| [Conditions](#conditions) | Branch based on logic |
| [Logic Gates](#logic-gates) | Combine multiple conditions |
| [Data](#data) | Fetch market data |
| [Utilities](#utilities) | Helper operations |

---

## Triggers

Triggers are entry points that start workflow execution.

### Schedule

**Purpose**: Start workflow on a schedule (daily, weekly, interval, or once).

**Configuration**:
| Field | Description |
|-------|-------------|
| Schedule Type | `Daily`, `Weekly`, `Interval`, or `Once` |
| Time | Execution time (HH:MM format) |
| Days | Select which days to run (for Daily/Weekly) |
| Interval | For interval: Value + Unit (seconds/minutes/hours) |
| Date | For once: Specific date |

**Day Selection** (for Daily/Weekly):
| Preset | Days |
|--------|------|
| Weekdays | Mon, Tue, Wed, Thu, Fri |
| Weekends | Sat, Sun |
| All Days | Every day |
| Custom | Select individual days |

**Examples**:
```
Daily at 9:15 AM on weekdays only
Weekly on Mon, Wed, Fri at 9:30 AM
Every 5 minutes
Once on 2025-01-15 at 10:00 AM
Daily at 9:15 AM only on Tue, Thu (custom selection)
```

---

### Price Alert

**Purpose**: Trigger when price meets a condition.

**Configuration**:
| Field | Description |
|-------|-------------|
| Symbol | Trading symbol (e.g., `RELIANCE`) |
| Exchange | `NSE`, `BSE`, `NFO`, etc. |
| Condition | Alert condition type |
| Price/Percentage | Target value |
| Trigger | When to fire (Once, Every time, etc.) |

**Conditions**:
| Condition | Description |
|-----------|-------------|
| Crossing | Price crosses the target |
| Crossing Up | Price crosses above target |
| Crossing Down | Price crosses below target |
| Greater Than | Price is above target |
| Less Than | Price is below target |
| Entering Channel | Price enters range (upper/lower) |
| Exiting Channel | Price exits range |
| Inside Channel | Price is within range |
| Outside Channel | Price is outside range |
| Moving Up % | Price moved up by percentage |
| Moving Down % | Price moved down by percentage |

**Output**: Follows **Yes** path when condition is met, **No** path otherwise.

---

### Webhook Trigger

**Purpose**: Start workflow from external HTTP request.

**Configuration**:
| Field | Description |
|-------|-------------|
| Label | Optional description |

**Usage**:
1. Enable webhook in workflow settings
2. Get your unique webhook URL: `/api/webhook/{token}`
3. POST to the URL with JSON payload
4. Payload is available as `{{webhook}}` variable

**Example Payload**:
```json
{
  "symbol": "NIFTY",
  "action": "BUY",
  "price": 24500,
  "quantity": 75
}
```

**Access in nodes**: `{{webhook.symbol}}`, `{{webhook.action}}`, etc.

---

## Actions

Actions execute trading operations.

### Place Order

**Purpose**: Place a basic market/limit order.

**Configuration**:
| Field | Description |
|-------|-------------|
| Symbol | Trading symbol |
| Exchange | `NSE`, `BSE`, `NFO`, `BFO`, `CDS`, `BCD`, `MCX` |
| Action | `BUY` or `SELL` |
| Quantity | Number of shares/lots |
| Product | `MIS` (Intraday), `CNC` (Delivery), `NRML` (F&O) |
| Price Type | `MARKET`, `LIMIT`, `SL`, `SL-M` |
| Price | For LIMIT/SL orders |
| Trigger Price | For SL/SL-M orders |
| Output Variable | Store result (e.g., `orderResult`) |

**Output Variable Access**:
```
{{orderResult.orderid}}    - Order ID
{{orderResult.status}}     - Order status
{{orderResult.message}}    - Response message
```

---

### Smart Order

**Purpose**: Position-aware order that checks existing positions.

**Configuration**: Same as Place Order, plus:
| Field | Description |
|-------|-------------|
| Position Action | `Enter`, `Exit`, `Reverse` |

**Behavior**:
- **Enter**: Only places order if no existing position
- **Exit**: Closes existing position
- **Reverse**: Closes and reverses position direction

---

### Options Order

**Purpose**: Place options order with ATM/ITM/OTM strike selection.

**Configuration**:
| Field | Description |
|-------|-------------|
| Underlying | `NIFTY`, `BANKNIFTY`, `FINNIFTY`, `SENSEX`, etc. |
| Expiry | `Current Week`, `Next Week`, `Current Month`, `Next Month` |
| Strike Offset | `ATM`, `ITM1-5`, `OTM1-10` |
| Option Type | `CE` (Call) or `PE` (Put) |
| Action | `BUY` or `SELL` |
| Quantity | Lot size (auto-filled based on underlying) |
| Product | `MIS` (Intraday) or `NRML` (Overnight) |
| Price Type | `MARKET` or `LIMIT` |

**Supported Underlyings**:
| Symbol | Exchange | Lot Size |
|--------|----------|----------|
| NIFTY | NFO | 75 |
| BANKNIFTY | NFO | 30 |
| FINNIFTY | NFO | 65 |
| MIDCPNIFTY | NFO | 120 |
| NIFTYNXT50 | NFO | 25 |
| SENSEX | BFO | 20 |
| BANKEX | BFO | 30 |
| SENSEX50 | BFO | 25 |

---

### Multi-Leg Options

**Purpose**: Execute multi-leg options strategies.

**Configuration**:
| Field | Description |
|-------|-------------|
| Strategy | Pre-built strategy type |
| Underlying | Index symbol |
| Expiry | Expiry type |
| Action | `BUY` (Long) or `SELL` (Short) |
| Quantity | Lots per leg |

**Strategies**:
| Strategy | Legs | Description |
|----------|------|-------------|
| Straddle | 2 | ATM CE + ATM PE |
| Strangle | 2 | OTM CE + OTM PE |
| Iron Condor | 4 | Sell OTM2 CE/PE, Buy OTM4 CE/PE |
| Bull Call Spread | 2 | Buy ATM CE, Sell OTM2 CE |
| Bear Put Spread | 2 | Buy ATM PE, Sell OTM2 PE |
| Custom | N | Build your own legs |

---

### Basket Order

**Purpose**: Place multiple orders at once.

**Configuration**:
| Field | Description |
|-------|-------------|
| Basket Name | Identifier for the basket |
| Orders | One per line: `SYMBOL,EXCHANGE,ACTION,QTY` |
| Product | Product type for all orders |
| Price Type | Price type for all orders |

**Example Orders**:
```
RELIANCE,NSE,BUY,10
INFY,NSE,BUY,5
SBIN,NSE,SELL,20
TCS,NSE,BUY,3
```

---

### Split Order

**Purpose**: Split large orders into smaller chunks.

**Configuration**:
| Field | Description |
|-------|-------------|
| Symbol | Trading symbol |
| Exchange | Exchange |
| Action | `BUY` or `SELL` |
| Total Quantity | Total shares to trade |
| Split Size | Size of each order |
| Product | Product type |

**Example**:
- Total: 100 shares, Split: 10
- Creates 10 orders of 10 shares each

---

### Modify Order

**Purpose**: Modify an existing order.

**Configuration**:
| Field | Description |
|-------|-------------|
| Order ID | ID of order to modify (or `{{variable.orderid}}`) |
| New Price | Updated price |
| New Quantity | Updated quantity |
| New Trigger Price | Updated trigger price (for SL orders) |

---

### Cancel Order

**Purpose**: Cancel a specific order.

**Configuration**:
| Field | Description |
|-------|-------------|
| Order ID | ID of order to cancel |

---

### Cancel All Orders

**Purpose**: Cancel all open orders.

**Configuration**: None required.

---

### Close Positions

**Purpose**: Square off all open positions.

**Configuration**:
| Field | Description |
|-------|-------------|
| Product | `MIS`, `CNC`, `NRML`, or `ALL` |

---

## Conditions

Conditions branch the workflow based on logic.

### Time Condition

**Purpose**: Check if current time meets a condition.

**Configuration**:
| Field | Description |
|-------|-------------|
| Condition Type | `Entry`, `Exit`, or `Custom` |
| Operator | `=`, `>=`, `<=`, `>`, `<` |
| Target Time | Time to compare against (HH:MM) |

**Outputs**: **Yes** (condition met) / **No** (not met)

**Examples**:
```
Entry at or after 9:30 AM:  Operator >= , Time 09:30
Exit before 3:15 PM:        Operator < , Time 15:15
Exactly at 10:00 AM:        Operator = , Time 10:00
```

---

### Time Window

**Purpose**: Check if current time is within a range.

**Configuration**:
| Field | Description |
|-------|-------------|
| Start Time | Window start (HH:MM) |
| End Time | Window end (HH:MM) |
| Invert | If true, triggers outside the window |

**Example**:
- Start: 09:30, End: 15:15 → True during market hours
- Invert: True → True outside market hours

---

### Position Check

**Purpose**: Check position status for a symbol.

**Configuration**:
| Field | Description |
|-------|-------------|
| Symbol | Symbol to check |
| Exchange | Exchange |
| Product | Product type |
| Condition | Check type |
| Threshold | For quantity/P&L checks |

**Conditions**:
| Condition | Description |
|-----------|-------------|
| Has Position | Position exists |
| No Position | Position doesn't exist |
| Quantity Above | Position size > threshold |
| Quantity Below | Position size < threshold |
| P&L Above | Profit/loss > threshold |
| P&L Below | Profit/loss < threshold |

---

### Fund Check

**Purpose**: Check if available funds meet minimum requirement.

**Configuration**:
| Field | Description |
|-------|-------------|
| Minimum Available | Minimum required funds |

**Output**: **Yes** if funds >= minimum, **No** otherwise.

---

### Price Condition

**Purpose**: Check current price against a value.

**Configuration**:
| Field | Description |
|-------|-------------|
| Symbol | Symbol to check |
| Exchange | Exchange |
| Field | `LTP`, `Open`, `High`, `Low`, `Prev Close`, `Change %` |
| Operator | `>`, `<`, `=`, `>=`, `<=`, `!=` |
| Value | Price to compare against |

---

## Logic Gates

Combine multiple conditions.

### AND Gate

**Purpose**: True only if ALL inputs are true.

**Configuration**:
| Field | Description |
|-------|-------------|
| Input Count | Number of inputs (2-5) |

**Truth Table**:
| Input A | Input B | Output |
|---------|---------|--------|
| Yes | Yes | Yes |
| Yes | No | No |
| No | Yes | No |
| No | No | No |

---

### OR Gate

**Purpose**: True if ANY input is true.

**Configuration**:
| Field | Description |
|-------|-------------|
| Input Count | Number of inputs (2-5) |

**Truth Table**:
| Input A | Input B | Output |
|---------|---------|--------|
| Yes | Yes | Yes |
| Yes | No | Yes |
| No | Yes | Yes |
| No | No | No |

---

### NOT Gate

**Purpose**: Inverts the input condition.

**Truth Table**:
| Input | Output |
|-------|--------|
| Yes | No |
| No | Yes |

---

## Data

Fetch market data.

### Get Quote

**Purpose**: Get real-time quote for a symbol.

**Configuration**:
| Field | Description |
|-------|-------------|
| Symbol | Symbol to fetch |
| Exchange | Exchange |
| Output Variable | Variable name (e.g., `quote`) |

**Output Access**:
```
{{quote.data.ltp}}        - Last traded price
{{quote.data.open}}       - Open price
{{quote.data.high}}       - High price
{{quote.data.low}}        - Low price
{{quote.data.prev_close}} - Previous close
{{quote.data.volume}}     - Volume
```

---

### Get Depth

**Purpose**: Get order book depth.

**Configuration**:
| Field | Description |
|-------|-------------|
| Symbol | Symbol |
| Exchange | Exchange |
| Output Variable | Variable name |

**Output Access**:
```
{{depth.data.bids[0].price}}    - Best bid price
{{depth.data.bids[0].quantity}} - Best bid quantity
{{depth.data.asks[0].price}}    - Best ask price
{{depth.data.asks[0].quantity}} - Best ask quantity
```

---

### Order Status

**Purpose**: Check status of an order.

**Configuration**:
| Field | Description |
|-------|-------------|
| Order ID | Order ID to check |
| Output Variable | Variable name |

---

### Open Position

**Purpose**: Get position details for a symbol.

**Configuration**:
| Field | Description |
|-------|-------------|
| Symbol | Symbol |
| Exchange | Exchange |
| Product | Product type |
| Output Variable | Variable name |

**Output Access**:
```
{{position.quantity}}     - Position size
{{position.pnl}}         - Profit/Loss
{{position.average_price}} - Average price
```

---

### History

**Purpose**: Get historical OHLCV data.

**Configuration**:
| Field | Description |
|-------|-------------|
| Symbol | Symbol |
| Exchange | Exchange |
| Interval | `1m`, `5m`, `15m`, `30m`, `1h`, `1d` |
| Days | Number of days to fetch |
| Output Variable | Variable name |

---

### Expiry Dates

**Purpose**: Get F&O expiry dates.

**Configuration**:
| Field | Description |
|-------|-------------|
| Symbol | Underlying symbol |
| Exchange | `NFO`, `BFO`, `MCX`, `CDS` |
| Output Variable | Variable name |

**Output Access**:
```
{{expiries.data[0]}}  - Nearest expiry
{{expiries.data[1]}}  - Next expiry
```

---

### Multi Quotes

**Purpose**: Get quotes for multiple symbols at once.

**Configuration**:
| Field | Description |
|-------|-------------|
| Symbols | Comma-separated symbols (e.g., `RELIANCE,INFY,TCS`) |
| Exchange | Exchange |
| Output Variable | Variable name |

---

### Symbol Info

**Purpose**: Get symbol details (lot size, tick size, expiry, etc.).

**Configuration**:
| Field | Description |
|-------|-------------|
| Symbol | Symbol to fetch (supports `{{variable}}`) |
| Exchange | Exchange |
| Output Variable | Variable name |

**Output Access**:
```
{{symbolInfo.data.lotsize}}     - Lot size
{{symbolInfo.data.tick_size}}   - Tick size
{{symbolInfo.data.expiry}}      - Expiry date (for F&O)
{{symbolInfo.data.instrument}}  - Instrument type
```

---

### Option Symbol

**Purpose**: Resolve option symbol from underlying (ATM/ITM/OTM).

**Configuration**:
| Field | Description |
|-------|-------------|
| Underlying | Index symbol (e.g., `NIFTY`, `BANKNIFTY`) |
| Exchange | `NSE_INDEX` or `BSE_INDEX` |
| Expiry Date | Expiry in format `30DEC25` (supports `{{variable}}`) |
| Offset | `ATM`, `ITM1-10`, `OTM1-10` |
| Option Type | `CE` (Call) or `PE` (Put) |
| Output Variable | Variable name |

**Output Access**:
```
{{optSym.data.symbol}}      - Resolved option symbol
{{optSym.data.strike}}      - Strike price
{{optSym.data.underlying}}  - Underlying symbol
```

**Example**:
```
Underlying: NIFTY
Expiry: 02JAN25
Offset: ATM
Option Type: CE
Output: optSymbol

Result: NIFTY02JAN25C24500 (assuming NIFTY at 24500)
```

---

### Order Book

**Purpose**: Fetch all orders for the day.

**Configuration**:
| Field | Description |
|-------|-------------|
| Output Variable | Variable name |

**Output Access**:
```
{{orderbook.data}}           - Array of all orders
{{orderbook.data[0].orderid}} - First order ID
{{orderbook.data[0].status}}  - First order status
{{orderbook.data[0].symbol}}  - First order symbol
```

---

### Trade Book

**Purpose**: Fetch all executed trades for the day.

**Configuration**:
| Field | Description |
|-------|-------------|
| Output Variable | Variable name |

**Output Access**:
```
{{tradebook.data}}              - Array of all trades
{{tradebook.data[0].tradeid}}   - First trade ID
{{tradebook.data[0].price}}     - First trade price
{{tradebook.data[0].quantity}}  - First trade quantity
```

---

### Position Book

**Purpose**: Fetch all open positions.

**Configuration**:
| Field | Description |
|-------|-------------|
| Output Variable | Variable name |

**Output Access**:
```
{{positions.data}}                 - Array of all positions
{{positions.data[0].symbol}}       - First position symbol
{{positions.data[0].quantity}}     - First position quantity
{{positions.data[0].pnl}}          - First position P&L
{{positions.data[0].average_price}} - Average entry price
```

---

### Synthetic Future

**Purpose**: Calculate synthetic future price from options.

**Configuration**:
| Field | Description |
|-------|-------------|
| Underlying | Index symbol |
| Exchange | `NSE_INDEX` or `BSE_INDEX` |
| Expiry Date | Expiry in format `30DEC25` |
| Output Variable | Variable name |

**Output Access**:
```
{{synthetic.data.price}}        - Synthetic future price
{{synthetic.data.atm_strike}}   - ATM strike price
{{synthetic.data.call_price}}   - ATM call price
{{synthetic.data.put_price}}    - ATM put price
```

**Use Case**: More accurate fair value than spot for options strategies.

---

### Option Chain

**Purpose**: Fetch complete option chain data.

**Configuration**:
| Field | Description |
|-------|-------------|
| Underlying | Index symbol |
| Exchange | `NSE_INDEX` or `BSE_INDEX` |
| Expiry Date | Expiry in format `30DEC25` |
| Strike Count | Number of strikes around ATM (default: 10) |
| Output Variable | Variable name |

**Output Access**:
```
{{chain.data}}                    - Full option chain array
{{chain.data[0].strike}}          - First strike price
{{chain.data[0].call_ltp}}        - Call LTP at strike
{{chain.data[0].put_ltp}}         - Put LTP at strike
{{chain.data[0].call_oi}}         - Call open interest
{{chain.data[0].put_oi}}          - Put open interest
{{chain.data[0].call_iv}}         - Call implied volatility
{{chain.data[0].put_iv}}          - Put implied volatility
```

---

## Utilities

Helper operations.

### Variable

**Purpose**: Store and manipulate values.

**Configuration**:
| Field | Description |
|-------|-------------|
| Variable Name | Name for the variable |
| Operation | Operation to perform |
| Value | Value for the operation |

**Operations**:
| Operation | Description | Example |
|-----------|-------------|---------|
| Set | Set value | `myVar = 100` |
| Get | Copy from another variable | `myVar = quote.ltp` |
| Add | Add to variable | `myVar = myVar + 10` |
| Subtract | Subtract from variable | `myVar = myVar - 10` |
| Multiply | Multiply variable | `myVar = myVar * 2` |
| Divide | Divide variable | `myVar = myVar / 2` |
| Increment | Add 1 | `myVar = myVar + 1` |
| Decrement | Subtract 1 | `myVar = myVar - 1` |
| Parse JSON | Parse string to object | `myVar = JSON.parse(str)` |
| Stringify | Convert to JSON string | `myVar = JSON.stringify(obj)` |
| Append | Append to string | `myVar = myVar + "text"` |

---

### Log

**Purpose**: Log a message for debugging.

**Configuration**:
| Field | Description |
|-------|-------------|
| Level | `Info`, `Warning`, or `Error` |
| Message | Message to log (supports `{{variables}}`) |

**Example**:
```
Level: Info
Message: Order placed for {{symbol}} at {{quote.ltp}}
```

---

### Telegram Alert

**Purpose**: Send Telegram notification.

**Configuration**:
| Field | Description |
|-------|-------------|
| OpenAlgo Username | Your OpenAlgo login ID |
| Message | Alert message (supports `{{variables}}`) |

**Example Message**:
```
Order Executed!
Symbol: {{orderResult.symbol}}
Order ID: {{orderResult.orderid}}
Price: {{quote.ltp}}
Time: {{timestamp}}
```

---

### Delay

**Purpose**: Wait for a duration.

**Configuration**:
| Field | Description |
|-------|-------------|
| Value | Duration value |
| Unit | `Seconds`, `Minutes`, or `Hours` |

**Examples**:
- Wait 30 seconds: Value=30, Unit=Seconds
- Wait 5 minutes: Value=5, Unit=Minutes
- Wait 1 hour: Value=1, Unit=Hours

---

### Wait Until

**Purpose**: Pause until a specific time.

**Configuration**:
| Field | Description |
|-------|-------------|
| Target Time | Time to wait for (HH:MM) |
| Label | Optional description |

**Behavior**:
- Pauses workflow until target time
- If time has passed, continues immediately

---

### HTTP Request

**Purpose**: Make external API calls.

**Configuration**:
| Field | Description |
|-------|-------------|
| Method | `GET`, `POST`, `PUT`, `DELETE`, `PATCH` |
| URL | API endpoint (supports `{{variables}}`) |
| Headers | JSON headers |
| Body | JSON body (for POST/PUT/PATCH) |
| Timeout | Request timeout in milliseconds |
| Output Variable | Variable name |

**Example**:
```
Method: POST
URL: https://api.example.com/notify
Headers: {"Authorization": "Bearer {{token}}"}
Body: {"symbol": "{{symbol}}", "price": {{quote.ltp}}}
Output: apiResponse
```

**Output Access**:
```
{{apiResponse.status}}  - HTTP status code
{{apiResponse.data}}    - Response body
{{apiResponse.success}} - true/false
```

---

### Group

**Purpose**: Visually organize nodes.

**Configuration**:
| Field | Description |
|-------|-------------|
| Group Name | Label for the group |
| Color | Visual color (Default, Blue, Green, Red, Purple, Orange) |

**Usage**: Drag nodes inside the group for organization.

---

### Holidays

**Purpose**: Get market holidays for a year.

**Configuration**:
| Field | Description |
|-------|-------------|
| Year | Year to fetch holidays for (default: current year) |
| Output Variable | Variable name |

**Output Access**:
```
{{holidays.data}}              - Array of all holidays
{{holidays.data[0].date}}      - First holiday date
{{holidays.data[0].name}}      - First holiday name
{{holidays.data[0].exchange}}  - Exchange(s) closed
```

**Use Cases**:
- Skip trading on holidays
- Plan around market closures
- Build holiday-aware strategies

---

### Timings

**Purpose**: Get market timings for a specific date.

**Configuration**:
| Field | Description |
|-------|-------------|
| Date | Date to check (YYYY-MM-DD format, default: today) |
| Output Variable | Variable name |

**Output Access**:
```
{{timings.data.market_open}}   - Market open time
{{timings.data.market_close}}  - Market close time
{{timings.data.is_holiday}}    - Whether it's a holiday
{{timings.data.is_weekend}}    - Whether it's a weekend
```

**Use Cases**:
- Dynamic time-based entry/exit
- Handle special trading sessions
- Muhurat trading detection

---

## Real-time Streaming (WebSocket)

Live data streaming via WebSocket connection for low-latency trading.

**How It Works**:
- Connects to OpenAlgo WebSocket server (default: `ws://127.0.0.1:8765`)
- Subscribes using official OpenAlgo SDK methods
- Waits for first data tick (5 second timeout)
- Falls back to REST API if WebSocket times out
- Stores data in output variable for workflow use

**WebSocket vs REST API**:
| Aspect | WebSocket | REST API (Fallback) |
|--------|-----------|---------------------|
| Latency | Ultra-low (real-time) | Higher (HTTP request) |
| Connection | Persistent | Per-request |
| Use Case | Active trading | Occasional queries |

### Subscribe LTP

**Purpose**: Subscribe to real-time Last Traded Price streaming.

**Configuration**:
| Field | Description |
|-------|-------------|
| Symbol | Symbol to stream (supports `{{variable}}`) |
| Exchange | Exchange |
| Output Variable | Variable name (default: `ltp`) |

**Behavior**:
1. Connects to WebSocket if not connected
2. Sends subscribe message for LTP
3. Waits for first LTP tick (5 sec timeout)
4. Stores LTP value in output variable
5. Falls back to quotes API if timeout

**Output Access**:
```
{{ltp}}  - Current LTP value (number)
```

**Use Cases**:
- Real-time price monitoring
- Dynamic stop-loss/target
- Trailing stop implementations

---

### Subscribe Quote

**Purpose**: Subscribe to real-time quote streaming (OHLC + volume).

**Configuration**:
| Field | Description |
|-------|-------------|
| Symbol | Symbol to stream (supports `{{variable}}`) |
| Exchange | Exchange |
| Output Variable | Variable name (default: `quote`) |

**Behavior**:
1. Connects to WebSocket if not connected
2. Sends subscribe message for Quote
3. Waits for first quote tick (5 sec timeout)
4. Stores quote object in output variable
5. Falls back to quotes API if timeout

**Output Access**:
```
{{quote.ltp}}      - Last traded price
{{quote.open}}     - Today's open
{{quote.high}}     - Today's high
{{quote.low}}      - Today's low
{{quote.volume}}   - Volume
{{quote.bid}}      - Best bid
{{quote.ask}}      - Best ask
```

---

### Subscribe Depth

**Purpose**: Subscribe to real-time order book streaming.

**Configuration**:
| Field | Description |
|-------|-------------|
| Symbol | Symbol to stream (supports `{{variable}}`) |
| Exchange | Exchange |
| Output Variable | Variable name (default: `depth`) |

**Behavior**:
1. Connects to WebSocket if not connected
2. Sends subscribe message for Depth
3. Waits for first depth tick (5 sec timeout)
4. Stores depth object in output variable
5. Falls back to depth API if timeout

**Output Access**:
```
{{depth.bids[0].price}}     - Best bid price
{{depth.bids[0].quantity}}  - Best bid quantity
{{depth.asks[0].price}}     - Best ask price
{{depth.asks[0].quantity}}  - Best ask quantity
{{depth.totalbuyqty}}       - Total buy quantity
{{depth.totalsellqty}}      - Total sell quantity
```

---

### Unsubscribe

**Purpose**: Stop real-time streaming and clean up WebSocket connection.

**Configuration**:
| Field | Description |
|-------|-------------|
| Stream Type | `LTP Only`, `Quote Only`, `Depth Only`, or `All Streams` |
| Symbol | Symbol to unsubscribe (leave empty for all) |
| Exchange | Exchange |

**Behavior**:
- Unsubscribes from specified stream type
- If "All Streams" with no symbol: disconnects WebSocket entirely
- Safe to call even if not connected

---

## Risk Management

Portfolio and risk analysis nodes for traders.

### Holdings

**Purpose**: Get portfolio holdings.

**Configuration**:
| Field | Description |
|-------|-------------|
| Output Variable | Variable name |

**Output Access**:
```
{{holdings.data.holdings}}           - Array of holdings
{{holdings.data.holdings[0].symbol}} - First holding symbol
{{holdings.data.holdings[0].pnl}}    - First holding P&L
{{holdings.data.statistics.totalholdingvalue}}  - Total value
{{holdings.data.statistics.totalprofitandloss}} - Total P&L
```

---

### Funds

**Purpose**: Get account funds and margins.

**Configuration**:
| Field | Description |
|-------|-------------|
| Output Variable | Variable name |

**Output Access**:
```
{{funds.data.availablecash}}    - Available cash
{{funds.data.collateral}}       - Collateral value
{{funds.data.m2mrealized}}      - Realized M2M
{{funds.data.m2munrealized}}    - Unrealized M2M
{{funds.data.utiliseddebits}}   - Used margin
```

**Use Cases**:
- Check available funds before order
- Monitor margin utilization
- Risk management

---

### Margin Calculator

**Purpose**: Calculate margin requirements before placing orders.

**Configuration**:
| Field | Description |
|-------|-------------|
| Positions | JSON array of positions to calculate |
| Output Variable | Variable name |

**Position Format**:
```json
[
  {
    "symbol": "NIFTY25DEC25FUT",
    "exchange": "NFO",
    "action": "BUY",
    "quantity": 75,
    "product": "NRML",
    "pricetype": "MARKET"
  }
]
```

**Output Access**:
```
{{marginResult.data.total_margin_required}}  - Total margin needed
{{marginResult.data.span_margin}}            - SPAN margin
{{marginResult.data.exposure_margin}}        - Exposure margin
```

**Use Cases**:
- Pre-trade margin check
- Position sizing based on available capital
- Risk limit enforcement
