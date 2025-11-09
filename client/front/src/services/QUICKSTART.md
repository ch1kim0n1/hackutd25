# Alpaca Trading Services - Quick Start Guide

## 🚀 Get Started in 5 Minutes

### Step 1: Get API Keys

1. Go to [Alpaca Markets](https://alpaca.markets/)
2. Sign up for a free paper trading account
3. Navigate to Dashboard → API Keys
4. Generate your API Key and Secret Key

### Step 2: Configure Environment

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Add your credentials to `.env`:
```env
VITE_ALPACA_API_KEY=your_actual_key_here
VITE_ALPACA_SECRET_KEY=your_actual_secret_here
VITE_ALPACA_PAPER=true
```

### Step 3: Basic Usage

#### Option A: Use the All-in-One Service

```typescript
import { AlpacaService } from '@/services';

const alpaca = new AlpacaService();

// Initialize and check connection
const init = await alpaca.initialize();
console.log('Account:', init.account);

// Get complete dashboard
const dashboard = await alpaca.getDashboardData();
```

#### Option B: Use Individual Services

```typescript
import { AccountService, TradingService, MarketDataService } from '@/services';

const account = new AccountService();
const trading = new TradingService();
const market = new MarketDataService();

// Get account info
const accountData = await account.getAccount();

// Get current price
const price = await market.getCurrentPrice('AAPL');

// Place a trade
const order = await trading.buy('AAPL', 10);
```

#### Option C: Use React Hooks

```typescript
import { useDashboard, useStockPrice, useTrading } from '@/services/hooks';

function MyComponent() {
  const { dashboard, loading } = useDashboard();
  const { price } = useStockPrice('AAPL');
  const { buy, sell } = useTrading();
  
  return (
    <div>
      <h1>Portfolio: ${dashboard?.portfolioValue}</h1>
      <p>AAPL: ${price}</p>
      <button onClick={() => buy('AAPL', 1)}>Buy 1 Share</button>
    </div>
  );
}
```

## 📋 Common Tasks

### Check Account Balance
```typescript
const alpaca = new AlpacaService();
const account = await alpaca.account.getAccount();
console.log('Buying Power:', account.buying_power);
console.log('Portfolio Value:', account.portfolio_value);
```

### Get Current Stock Price
```typescript
const price = await alpaca.marketData.getCurrentPrice('AAPL');
console.log('AAPL Price:', price);
```

### Place a Market Order
```typescript
// Buy 10 shares of Apple
const order = await alpaca.trading.buy('AAPL', 10);
console.log('Order ID:', order.id);
```

### Get All Positions
```typescript
const positions = await alpaca.trading.getPositions();
positions.forEach(pos => {
  console.log(`${pos.symbol}: ${pos.qty} shares, P/L: $${pos.unrealized_pl}`);
});
```

### Check Market Status
```typescript
const status = await alpaca.clock.getMarketStatus();
console.log('Market Open:', status.isOpen);
console.log('Time until change:', status.timeUntilChangeFormatted);
```

### Get Historical Data
```typescript
// Get last 30 days of daily bars
const bars = await alpaca.marketData.getDailyBars('AAPL', 30);

// Get today's 5-minute bars
const intraday = await alpaca.marketData.getIntradayBars('AAPL', '5Min');
```

### Search for Stocks
```typescript
const results = await alpaca.assets.searchAssets('apple');
console.log(results); // [{symbol: 'AAPL', name: 'Apple Inc', ...}]
```

### Create a Watchlist
```typescript
const watchlist = await alpaca.watchlists.createWatchlist({
  name: 'My Stocks',
  symbols: ['AAPL', 'GOOGL', 'MSFT']
});
```

## 🎯 Example Components

### Simple Price Display
```typescript
import { useStockPrice } from '@/services/hooks';

export function PriceDisplay({ symbol }) {
  const { price, change, loading } = useStockPrice(symbol);
  
  if (loading) return <div>Loading...</div>;
  
  return (
    <div>
      <h2>{symbol}</h2>
      <p>${price?.toFixed(2)}</p>
      <p style={{ color: change?.change >= 0 ? 'green' : 'red' }}>
        {change?.change >= 0 ? '+' : ''}{change?.change.toFixed(2)} 
        ({change?.changePercent.toFixed(2)}%)
      </p>
    </div>
  );
}
```

### Trading Button
```typescript
import { useTrading } from '@/services/hooks';

export function BuyButton({ symbol, qty = 1 }) {
  const { buy, loading } = useTrading();
  
  const handleBuy = async () => {
    try {
      await buy(symbol, qty);
      alert(`Bought ${qty} shares of ${symbol}`);
    } catch (error) {
      alert('Purchase failed: ' + error.message);
    }
  };
  
  return (
    <button onClick={handleBuy} disabled={loading}>
      {loading ? 'Processing...' : `Buy ${qty} ${symbol}`}
    </button>
  );
}
```

### Portfolio Summary
```typescript
import { usePositions } from '@/services/hooks';

export function PortfolioSummary() {
  const { positions, loading } = usePositions();
  
  if (loading) return <div>Loading...</div>;
  
  const totalValue = positions.reduce((sum, pos) => 
    sum + parseFloat(pos.market_value), 0
  );
  
  const totalPL = positions.reduce((sum, pos) => 
    sum + parseFloat(pos.unrealized_pl), 0
  );
  
  return (
    <div>
      <h2>Portfolio</h2>
      <p>Total Value: ${totalValue.toFixed(2)}</p>
      <p style={{ color: totalPL >= 0 ? 'green' : 'red' }}>
        P/L: ${totalPL.toFixed(2)}
      </p>
      <p>Positions: {positions.length}</p>
    </div>
  );
}
```

## ⚠️ Important Notes

### Paper Trading vs Live Trading
- **Always test with paper trading first** (`VITE_ALPACA_PAPER=true`)
- Paper trading uses fake money - perfect for testing
- Switch to live trading only when ready and with real account

### Market Hours
- US stock market: 9:30 AM - 4:00 PM ET, Monday-Friday
- Pre-market: 4:00 AM - 9:30 AM ET
- After-hours: 4:00 PM - 8:00 PM ET
- Always check market status before trading

### Order Types
- **Market Order**: Buy/sell immediately at current price
- **Limit Order**: Buy/sell only at specified price or better
- **Stop Order**: Triggers market order when price reaches stop price
- **Stop Limit**: Triggers limit order when price reaches stop price

### Rate Limits
- Alpaca has rate limits (200 requests/minute typically)
- Services handle errors, but avoid excessive calls
- Use caching and reasonable refresh intervals

## 🆘 Troubleshooting

### "API credentials are required" Error
- Check your `.env` file has correct keys
- Make sure keys start with `VITE_` prefix
- Restart dev server after changing `.env`

### "Symbol not tradable" Error
- Verify the symbol exists and is correct
- Some stocks may not be tradable on Alpaca
- Check asset status: `await alpaca.assets.isAssetTradable('SYMBOL')`

### "Not enough buying power" Error
- Check your account balance
- Verify you have sufficient funds
- Remember: paper trading starts with $100,000

### Network/Connection Errors
- Check your internet connection
- Verify Alpaca API is online: https://status.alpaca.markets/
- Try again in a few seconds (could be rate limiting)

## 📚 Next Steps

1. **Read the full README**: `src/services/README.md`
2. **Check examples**: `src/services/examples.tsx`
3. **Explore utilities**: `src/services/utils.ts`
4. **Review types**: `src/services/alpaca.types.ts`
5. **API Documentation**: https://docs.alpaca.markets/

## 🎓 Learning Resources

- [Alpaca Docs](https://docs.alpaca.markets/)
- [Alpaca Learn](https://alpaca.markets/learn/)
- [Trading API Guide](https://docs.alpaca.markets/docs/trading-api)
- [Market Data Guide](https://docs.alpaca.markets/docs/market-data)

---

**You're all set! Start building your trading app! 🚀📈**
