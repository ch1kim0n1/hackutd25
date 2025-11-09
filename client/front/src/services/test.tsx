/**
 * Alpaca Services Test/Demo
 * Use this file to test your Alpaca integration
 * 
 * To run: Import this in your app or create a test component
 */

import { AlpacaService } from './index';

/**
 * Test all services
 */
export async function testAlpacaServices() {
  console.log('🚀 Starting Alpaca Services Test...\n');

  try {
    // Initialize service
    console.log('📡 Initializing Alpaca Service...');
    const alpaca = new AlpacaService();
    
    // Test 1: Initialize and get account
    console.log('\n✅ Test 1: Initialize & Get Account');
    const init = await alpaca.initialize();
    
    if (!init.success) {
      throw new Error(`Initialization failed: ${init.error}`);
    }
    
    console.log('   ✓ Connected successfully!');
    console.log('   ✓ Account ID:', init.account?.account_number);
    console.log('   ✓ Market Open:', init.marketOpen);
    console.log('   ✓ Portfolio Value:', init.account?.portfolio_value);
    
    // Test 2: Get account metrics
    console.log('\n✅ Test 2: Get Account Metrics');
    const metrics = await alpaca.account.getAccountMetrics();
    console.log('   ✓ Total Value:', metrics.totalValue);
    console.log('   ✓ Buying Power:', metrics.buyingPower);
    console.log('   ✓ P/L:', metrics.profitLoss);
    
    // Test 3: Check market status
    console.log('\n✅ Test 3: Check Market Status');
    const marketStatus = await alpaca.clock.getMarketStatus();
    console.log('   ✓ Market is', marketStatus.isOpen ? 'OPEN' : 'CLOSED');
    console.log('   ✓ Time until change:', marketStatus.timeUntilChangeFormatted);
    
    // Test 4: Get stock price
    console.log('\n✅ Test 4: Get Stock Price (AAPL)');
    const price = await alpaca.marketData.getCurrentPrice('AAPL');
    const change = await alpaca.marketData.getPriceChange('AAPL');
    console.log('   ✓ Current Price: $' + price.toFixed(2));
    console.log('   ✓ Change: $' + change.change.toFixed(2), `(${change.changePercent.toFixed(2)}%)`);
    
    // Test 5: Search assets
    console.log('\n✅ Test 5: Search Assets (apple)');
    const assets = await alpaca.assets.searchAssets('apple', 3);
    console.log('   ✓ Found', assets.length, 'assets');
    assets.forEach(asset => {
      console.log('     -', asset.symbol, ':', asset.name);
    });
    
    // Test 6: Get positions
    console.log('\n✅ Test 6: Get Positions');
    const positions = await alpaca.trading.getPositions();
    console.log('   ✓ You have', positions.length, 'open positions');
    if (positions.length > 0) {
      positions.forEach(pos => {
        console.log(`     - ${pos.symbol}: ${pos.qty} shares, P/L: $${pos.unrealized_pl}`);
      });
    }
    
    // Test 7: Get open orders
    console.log('\n✅ Test 7: Get Open Orders');
    const orders = await alpaca.trading.getOrders({ status: 'open' });
    console.log('   ✓ You have', orders.length, 'open orders');
    if (orders.length > 0) {
      orders.forEach(order => {
        console.log(`     - ${order.symbol}: ${order.side} ${order.qty} @ ${order.type}`);
      });
    }
    
    // Test 8: Get historical data
    console.log('\n✅ Test 8: Get Historical Data (AAPL)');
    const bars = await alpaca.marketData.getDailyBars('AAPL', 5);
    console.log('   ✓ Retrieved', bars.length, 'daily bars');
    if (bars.length > 0) {
      const latest = bars[bars.length - 1];
      console.log(`     Latest: Open: $${latest.o}, Close: $${latest.c}, Volume: ${latest.v}`);
    }
    
    // Test 9: Check if can trade
    console.log('\n✅ Test 9: Check Trading Permissions');
    const canTrade = await alpaca.account.canTrade();
    console.log('   ✓ Can trade:', canTrade.canTrade);
    if (!canTrade.canTrade) {
      console.log('   ✗ Reasons:', canTrade.reasons.join(', '));
    }
    
    // Test 10: Get watchlists
    console.log('\n✅ Test 10: Get Watchlists');
    const watchlists = await alpaca.watchlists.getWatchlists();
    console.log('   ✓ You have', watchlists.length, 'watchlists');
    watchlists.forEach(wl => {
      console.log(`     - ${wl.name}: ${wl.assets.length} symbols`);
    });
    
    console.log('\n🎉 All tests passed! Your Alpaca integration is working!\n');
    
    return {
      success: true,
      account: init.account,
      metrics,
      marketStatus,
      positions,
      orders,
    };
    
  } catch (error: any) {
    console.error('\n❌ Test failed:', error.message);
    console.error('   Make sure your API keys are configured in .env');
    return {
      success: false,
      error: error.message,
    };
  }
}

/**
 * Quick test - just check if connected
 */
export async function quickTest() {
  try {
    const alpaca = new AlpacaService();
    const init = await alpaca.initialize();
    
    if (init.success) {
      console.log('✅ Alpaca Connected!');
      console.log('Portfolio Value: $' + init.account?.portfolio_value);
      console.log('Market Open:', init.marketOpen);
      return true;
    } else {
      console.error('❌ Connection failed:', init.error);
      return false;
    }
  } catch (error: any) {
    console.error('❌ Error:', error.message);
    return false;
  }
}

/**
 * Test market data functions
 */
export async function testMarketData(symbol: string = 'AAPL') {
  console.log(`📊 Testing Market Data for ${symbol}...\n`);
  
  try {
    const alpaca = new AlpacaService();
    
    // Get current price
    const price = await alpaca.marketData.getCurrentPrice(symbol);
    console.log('Current Price: $' + price.toFixed(2));
    
    // Get price change
    const change = await alpaca.marketData.getPriceChange(symbol);
    console.log('Today Change: $' + change.change.toFixed(2), `(${change.changePercent.toFixed(2)}%)`);
    
    // Get snapshot
    const snapshot = await alpaca.marketData.getSnapshot(symbol);
    console.log('\nSnapshot:');
    console.log('  High: $' + snapshot.dailyBar.h.toFixed(2));
    console.log('  Low: $' + snapshot.dailyBar.l.toFixed(2));
    console.log('  Volume:', snapshot.dailyBar.v);
    
    // Get historical data
    const bars = await alpaca.marketData.getDailyBars(symbol, 30);
    console.log('\nHistorical Data:', bars.length, 'days');
    
    // Get news
    const news = await alpaca.marketData.getNews({ symbols: symbol, limit: 3 });
    console.log('\nRecent News:', news.length, 'articles');
    news.forEach((article, i) => {
      console.log(`  ${i + 1}. ${article.headline.substring(0, 60)}...`);
    });
    
    return { price, change, snapshot, bars, news };
  } catch (error: any) {
    console.error('❌ Error:', error.message);
    return null;
  }
}

/**
 * Test trading functions (without actually placing orders)
 */
export async function testTradingValidation(symbol: string = 'AAPL', qty: number = 1) {
  console.log(`🔍 Testing Trading Validation for ${symbol}...\n`);
  
  try {
    const alpaca = new AlpacaService();
    
    // Check if asset is tradable
    const asset = await alpaca.assets.getAsset(symbol);
    console.log('Asset:', asset.name);
    console.log('  Tradable:', asset.tradable);
    console.log('  Marginable:', asset.marginable);
    console.log('  Fractionable:', asset.fractionable);
    
    // Check if can trade
    const canTrade = await alpaca.account.canTrade();
    console.log('\nAccount Trading Status:', canTrade.canTrade ? '✅' : '❌');
    if (!canTrade.canTrade) {
      console.log('  Reasons:', canTrade.reasons);
    }
    
    // Check buying power
    const price = await alpaca.marketData.getCurrentPrice(symbol);
    const buyingPower = await alpaca.account.getBuyingPowerForSymbol(symbol, price);
    console.log('\nBuying Power:');
    console.log('  Available: $' + buyingPower.buyingPower.toFixed(2));
    console.log('  Can buy:', buyingPower.maxShares, 'shares');
    console.log('  Requested:', qty, 'shares');
    console.log('  Can fulfill:', qty <= buyingPower.maxShares ? '✅' : '❌');
    
    return {
      asset,
      canTrade,
      buyingPower,
      canBuy: qty <= buyingPower.maxShares,
    };
  } catch (error: any) {
    console.error('❌ Error:', error.message);
    return null;
  }
}

// Export a simple test component for React
export function AlpacaTest() {
  const runTest = async () => {
    await testAlpacaServices();
  };

  return (
    <div style={{ padding: '20px', fontFamily: 'monospace' }}>
      <h1>🧪 Alpaca Services Test</h1>
      <p>Open the browser console and click the button below to test all services.</p>
      <button 
        onClick={runTest}
        style={{
          padding: '10px 20px',
          fontSize: '16px',
          backgroundColor: '#4CAF50',
          color: 'white',
          border: 'none',
          borderRadius: '4px',
          cursor: 'pointer'
        }}
      >
        Run Full Test
      </button>
      <div style={{ marginTop: '20px' }}>
        <p>Or test individual functions:</p>
        <button onClick={() => quickTest()} style={{ margin: '5px', padding: '8px 15px' }}>
          Quick Test
        </button>
        <button onClick={() => testMarketData('AAPL')} style={{ margin: '5px', padding: '8px 15px' }}>
          Test Market Data
        </button>
        <button onClick={() => testTradingValidation('AAPL')} style={{ margin: '5px', padding: '8px 15px' }}>
          Test Trading Validation
        </button>
      </div>
      <p style={{ marginTop: '20px', color: '#666' }}>
        Check the browser console for test results.
      </p>
    </div>
  );
}

export default testAlpacaServices;
