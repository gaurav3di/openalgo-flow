# OpenAlgo Flow

A visual workflow editor for trading automation with OpenAlgo integration. Build complex trading workflows with a drag-and-drop interface similar to n8n.

## Features

- Visual workflow editor with ReactFlow
- 30+ node types for comprehensive trading automation
- Options trading with multi-leg strategies (Iron Condor, Straddle, Strangle, Spreads)
- Schedule-based and price alert triggers
- Conditional branching (If/Else logic)
- Variable system for data passing between nodes
- Real-time LTP updates via WebSocket
- SQLite database (zero configuration)
- Dark theme optimized for trading

## Prerequisites

- Python 3.11+
- Node.js 18+
- [uv](https://github.com/astral-sh/uv) (auto-installed by setup script)
- OpenAlgo running locally or remotely

## Quick Start

### Windows

1. Run setup (installs uv if needed):
```cmd
setup.bat
```

2. Start the application:
```cmd
start.bat
```

### Linux/Mac

1. Run setup:
```bash
chmod +x setup.sh start.sh
./setup.sh
```

2. Start the application:
```bash
./start.sh
```

## Running Separately

### Backend

```bash
cd backend
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### Frontend

```bash
cd frontend
npm run dev
```

Open http://localhost:5173 in your browser.

## First Time Setup

### Backend Setup

```bash
cd backend
uv sync
```

### Frontend Setup

```bash
cd frontend
npm install
```

## Configuration

1. Open http://localhost:5173
2. Go to Settings
3. Enter your OpenAlgo credentials:
   - **API Key**: Your OpenAlgo API key
   - **Host URL**: OpenAlgo REST API URL (default: http://127.0.0.1:5000)
   - **WebSocket URL**: OpenAlgo WebSocket URL (default: ws://127.0.0.1:8765)
4. Click "Test Connection" to verify
5. Save settings

## Creating Workflows

1. Click "New Workflow" on the Dashboard
2. Drag nodes from the left panel to the canvas
3. Connect nodes by dragging from one handle to another
4. Configure each node by clicking on it
5. Save the workflow
6. Click "Activate" to start the schedule

## Node Types

### Triggers

| Node | Description |
|------|-------------|
| Schedule | Start workflow at specified time (once/daily/weekly) |
| Price Alert | Trigger when price crosses threshold |

### Actions - Orders

| Node | Description |
|------|-------------|
| Place Order | Place a basic trading order |
| Smart Order | Position-aware ordering with auto quantity |
| Options Order | ATM/ITM/OTM options with expiry selection |
| Multi-Leg | Options strategies (Straddle, Strangle, Iron Condor, Spreads) |
| Basket Order | Execute multiple orders at once |
| Split Order | Split large orders into smaller chunks |
| Modify Order | Modify an existing order |
| Cancel Order | Cancel a specific order by ID |
| Cancel All | Cancel all open orders |
| Close Positions | Square off all positions |

### Options Expiry Types

| Type | Description |
|------|-------------|
| Current Week | Nearest weekly expiry |
| Next Week | Second weekly expiry |
| Current Month | Last expiry of current month |
| Next Month | Last expiry of next month |

### Options Strategies (Multi-Leg)

| Strategy | Description |
|----------|-------------|
| Straddle | ATM CE + ATM PE (same strike) |
| Strangle | OTM CE + OTM PE (different strikes) |
| Iron Condor | 4-leg neutral strategy |
| Bull Call Spread | Buy ATM CE, Sell OTM CE |
| Bear Put Spread | Buy ATM PE, Sell OTM PE |

### Conditions

| Node | Description |
|------|-------------|
| Position Check | Check if position exists or quantity threshold |
| Fund Check | Verify available margin |
| Price Condition | Compare price against threshold |
| Time Window | Check if within market hours |

### Data Nodes

| Node | Description |
|------|-------------|
| Get Quote | Fetch real-time quote (LTP, OHLC, volume) |
| Get Depth | 5-level bid/ask market depth |
| Order Status | Check status of a specific order |
| Open Position | Get current position details |
| History | Fetch OHLCV historical data |
| Expiry Dates | Get F&O expiry dates |

### Utilities

| Node | Description |
|------|-------------|
| Variable | Store and manipulate values |
| Log | Debug logging with levels (info/warn/error) |
| Telegram | Send alerts via Telegram |
| Delay | Wait for specified duration |
| Group | Organize nodes visually |

## Variable System

Use variables to pass data between nodes:

- Set variables with the Variable node
- Reference variables using `{{variableName}}` syntax
- Access nested properties: `{{quote.ltp}}`, `{{position.quantity}}`
- System variables: `{{timestamp}}`, `{{date}}`, `{{time}}`

## Supported Exchanges

- NSE (Equity)
- NFO (F&O)
- BSE (Equity)
- BFO (F&O)
- CDS (Currency)
- BCD (Currency)
- MCX (Commodity)
- NCDEX (Commodity)
- NSE_INDEX
- BSE_INDEX

## Supported Underlying Symbols

### NSE Index Symbols (F&O Exchange: NFO)

| Symbol | Lot Size |
|--------|----------|
| NIFTY | 75 |
| BANKNIFTY | 30 |
| FINNIFTY | 65 |
| MIDCPNIFTY | 120 |
| NIFTYNXT50 | 25 |

### BSE Index Symbols (F&O Exchange: BFO)

| Symbol | Lot Size |
|--------|----------|
| SENSEX | 20 |
| BANKEX | 30 |
| SENSEX50 | 25 |

## Order Types

| Type | Description |
|------|-------------|
| MARKET | Execute at market price |
| LIMIT | Execute at specified price |
| SL | Stop Loss with limit |
| SL-M | Stop Loss at market |

## Product Types

| Type | Description |
|------|-------------|
| MIS | Intraday (auto square-off) |
| CNC | Cash & Carry (delivery) |
| NRML | Normal (F&O) |

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/settings | Get settings |
| PUT | /api/settings | Update settings |
| POST | /api/settings/test | Test connection |
| GET | /api/workflows | List workflows |
| POST | /api/workflows | Create workflow |
| GET | /api/workflows/{id} | Get workflow |
| PUT | /api/workflows/{id} | Update workflow |
| DELETE | /api/workflows/{id} | Delete workflow |
| POST | /api/workflows/{id}/activate | Activate |
| POST | /api/workflows/{id}/deactivate | Deactivate |
| POST | /api/workflows/{id}/execute | Run now |

## Tech Stack

- **Frontend**: React, ReactFlow, shadcn/ui, TailwindCSS, Zustand
- **Backend**: FastAPI, SQLAlchemy, APScheduler
- **Database**: SQLite
- **Integration**: OpenAlgo Node SDK 1.0.5

## Security Notes

- API keys are stored in the local SQLite database
- Run on localhost for development only
- Do not expose to public internet without proper authentication

## License

AGPL V3
