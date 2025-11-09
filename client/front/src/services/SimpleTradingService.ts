/**
 * Simple Trading Service
 * Super simplified - just buy shares and deduct money
 */

import LocalStorageService from './LocalStorageService';
import YahooFinanceService from './YahooFinanceService';
import type { Position } from './alpaca.types';

export class SimpleTradingService {
  /**
   * Buy shares - just deduct money from balance
   */
  async buy(symbol: string, qty: number): Promise<void> {
    const quote = await YahooFinanceService.getQuote(symbol);
    const currentPrice = quote.regularMarketPrice;
    const totalCost = qty * currentPrice;

    const account = LocalStorageService.getAccount();
    const currentCash = parseFloat(account.cash);

    if (totalCost > currentCash) {
      throw new Error('Insufficient funds');
    }

    // Deduct money
    const newCash = currentCash - totalCost;
    LocalStorageService.updateAccount({ cash: newCash.toFixed(2) });

    // Update position
    const existingPosition = LocalStorageService.getPosition(symbol);
    
    if (existingPosition) {
      const existingQty = parseFloat(existingPosition.qty);
      const existingCost = parseFloat(existingPosition.cost_basis);
      const newQty = existingQty + qty;
      const newCostBasis = existingCost + totalCost;
      const newAvgPrice = newCostBasis / newQty;
      const marketValue = newQty * currentPrice;

      LocalStorageService.addOrUpdatePosition({
        ...existingPosition,
        qty: newQty.toString(),
        avg_entry_price: newAvgPrice.toFixed(2),
        cost_basis: newCostBasis.toFixed(2),
        market_value: marketValue.toFixed(2),
        current_price: currentPrice.toFixed(2),
        unrealized_pl: (marketValue - newCostBasis).toFixed(2),
        unrealized_plpc: (((marketValue - newCostBasis) / newCostBasis) * 100).toFixed(4),
        qty_available: newQty.toString(),
      });
    } else {
      LocalStorageService.addOrUpdatePosition({
        asset_id: `asset_${symbol}`,
        symbol: symbol,
        exchange: 'NYSE',
        asset_class: 'us_equity',
        asset_marginable: true,
        qty: qty.toString(),
        avg_entry_price: currentPrice.toFixed(2),
        side: 'long',
        market_value: totalCost.toFixed(2),
        cost_basis: totalCost.toFixed(2),
        unrealized_pl: '0.00',
        unrealized_plpc: '0.0000',
        unrealized_intraday_pl: '0.00',
        unrealized_intraday_plpc: '0.0000',
        current_price: currentPrice.toFixed(2),
        lastday_price: currentPrice.toFixed(2),
        change_today: '0.0000',
        qty_available: qty.toString(),
      });
    }

    LocalStorageService.recalculateAccountValues();
  }

  /**
   * Sell shares - add money to balance
   */
  async sell(symbol: string, qty: number): Promise<void> {
    const existingPosition = LocalStorageService.getPosition(symbol);
    if (!existingPosition) {
      throw new Error('No position to sell');
    }

    const existingQty = parseFloat(existingPosition.qty);
    if (qty > existingQty) {
      throw new Error('Cannot sell more than owned');
    }

    const quote = await YahooFinanceService.getQuote(symbol);
    const currentPrice = quote.regularMarketPrice;
    const totalProceeds = qty * currentPrice;

    // Add money
    const account = LocalStorageService.getAccount();
    const newCash = parseFloat(account.cash) + totalProceeds;
    LocalStorageService.updateAccount({ cash: newCash.toFixed(2) });

    // Update position
    if (qty === existingQty) {
      // Sold all shares
      LocalStorageService.removePosition(symbol);
    } else {
      // Sold partial shares
      const newQty = existingQty - qty;
      const costBasis = parseFloat(existingPosition.cost_basis);
      const newCostBasis = costBasis * (newQty / existingQty);
      const marketValue = newQty * currentPrice;

      LocalStorageService.addOrUpdatePosition({
        ...existingPosition,
        qty: newQty.toString(),
        cost_basis: newCostBasis.toFixed(2),
        market_value: marketValue.toFixed(2),
        current_price: currentPrice.toFixed(2),
        unrealized_pl: (marketValue - newCostBasis).toFixed(2),
        unrealized_plpc: (((marketValue - newCostBasis) / newCostBasis) * 100).toFixed(4),
        qty_available: newQty.toString(),
      });
    }

    LocalStorageService.recalculateAccountValues();
  }

  /**
   * Get all positions with updated prices
   */
  async getPositions(): Promise<Position[]> {
    const positions = LocalStorageService.getPositions();
    
    await Promise.all(positions.map(async (position) => {
      try {
        const quote = await YahooFinanceService.getQuote(position.symbol);
        const currentPrice = quote.regularMarketPrice;
        const qty = parseFloat(position.qty);
        const costBasis = parseFloat(position.cost_basis);
        const marketValue = qty * currentPrice;
        const unrealizedPL = marketValue - costBasis;
        const unrealizedPLPercent = (unrealizedPL / costBasis) * 100;

        position.current_price = currentPrice.toFixed(2);
        position.market_value = marketValue.toFixed(2);
        position.unrealized_pl = unrealizedPL.toFixed(2);
        position.unrealized_plpc = unrealizedPLPercent.toFixed(4);
        position.change_today = quote.regularMarketChangePercent.toFixed(4);
      } catch (error) {
        console.error(`Error updating position for ${position.symbol}:`, error);
      }
    }));

    LocalStorageService.savePositions(positions);
    LocalStorageService.recalculateAccountValues();
    return positions;
  }

  /**
   * Get a single position with updated price
   */
  async getPosition(symbol: string): Promise<Position | null> {
    const position = LocalStorageService.getPosition(symbol);
    if (!position) return null;

    try {
      const quote = await YahooFinanceService.getQuote(symbol);
      const currentPrice = quote.regularMarketPrice;
      const qty = parseFloat(position.qty);
      const costBasis = parseFloat(position.cost_basis);
      const marketValue = qty * currentPrice;
      const unrealizedPL = marketValue - costBasis;
      const unrealizedPLPercent = (unrealizedPL / costBasis) * 100;

      position.current_price = currentPrice.toFixed(2);
      position.market_value = marketValue.toFixed(2);
      position.unrealized_pl = unrealizedPL.toFixed(2);
      position.unrealized_plpc = unrealizedPLPercent.toFixed(4);
      position.change_today = quote.regularMarketChangePercent.toFixed(4);

      LocalStorageService.addOrUpdatePosition(position);
    } catch (error) {
      console.error(`Error updating position for ${symbol}:`, error);
    }

    return position;
  }
}

export default new SimpleTradingService();
