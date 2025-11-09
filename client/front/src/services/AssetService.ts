/**
 * Asset Service
 * Manages asset information and queries
 */

import type { Asset } from "./alpaca.types";

import { AlpacaClient } from "./AlpacaClient";

export class AssetService extends AlpacaClient {
  /**
   * Get all assets
   */
  async getAssets(params?: {
    status?: "active" | "inactive";
    asset_class?: "us_equity" | "crypto";
    exchange?: string;
  }): Promise<Asset[]> {
    const queryParams = new URLSearchParams(params as any).toString();
    const endpoint = `/v2/assets${queryParams ? `?${queryParams}` : ""}`;

    return this.request<Asset[]>("GET", endpoint);
  }

  /**
   * Get a specific asset by symbol
   */
  async getAsset(symbol: string): Promise<Asset> {
    return this.request<Asset>("GET", `/v2/assets/${symbol}`);
  }

  /**
   * Get all active tradable assets
   */
  async getTradableAssets(
    assetClass?: "us_equity" | "crypto",
  ): Promise<Asset[]> {
    try {
      const assets = await this.getAssets({
        status: "active",
        asset_class: assetClass,
      });

      return assets.filter((asset) => asset.tradable);
    } catch (error) {
      return this.handleError(error);
    }
  }

  /**
   * Get all marginable assets
   */
  async getMarginableAssets(): Promise<Asset[]> {
    try {
      const assets = await this.getAssets({ status: "active" });

      return assets.filter((asset) => asset.marginable);
    } catch (error) {
      return this.handleError(error);
    }
  }

  /**
   * Get all shortable assets
   */
  async getShortableAssets(): Promise<Asset[]> {
    try {
      const assets = await this.getAssets({ status: "active" });

      return assets.filter((asset) => asset.shortable);
    } catch (error) {
      return this.handleError(error);
    }
  }

  /**
   * Get all fractionable assets (can buy fractional shares)
   */
  async getFractionableAssets(): Promise<Asset[]> {
    try {
      const assets = await this.getAssets({ status: "active" });

      return assets.filter((asset) => asset.fractionable);
    } catch (error) {
      return this.handleError(error);
    }
  }

  /**
   * Search assets by name or symbol
   */
  async searchAssets(query: string, limit: number = 20): Promise<Asset[]> {
    try {
      const assets = await this.getAssets({ status: "active" });
      const lowercaseQuery = query.toLowerCase();

      return assets
        .filter(
          (asset) =>
            asset.symbol.toLowerCase().includes(lowercaseQuery) ||
            asset.name.toLowerCase().includes(lowercaseQuery),
        )
        .slice(0, limit);
    } catch (error) {
      return this.handleError(error);
    }
  }

  /**
   * Check if an asset is tradable
   */
  async isAssetTradable(symbol: string): Promise<boolean> {
    try {
      const asset = await this.getAsset(symbol);

      return asset.tradable && asset.status === "active";
    } catch (error) {
      return false;
    }
  }

  /**
   * Get asset trading constraints
   */
  async getAssetConstraints(symbol: string): Promise<{
    tradable: boolean;
    marginable: boolean;
    shortable: boolean;
    fractionable: boolean;
    easyToBorrow: boolean;
    minOrderSize?: string;
    minTradeIncrement?: string;
    priceIncrement?: string;
  }> {
    try {
      const asset = await this.getAsset(symbol);

      return {
        tradable: asset.tradable,
        marginable: asset.marginable,
        shortable: asset.shortable,
        fractionable: asset.fractionable,
        easyToBorrow: asset.easy_to_borrow,
        minOrderSize: asset.min_order_size,
        minTradeIncrement: asset.min_trade_increment,
        priceIncrement: asset.price_increment,
      };
    } catch (error) {
      return this.handleError(error);
    }
  }

  /**
   * Get assets by exchange
   */
  async getAssetsByExchange(exchange: string): Promise<Asset[]> {
    try {
      const assets = await this.getAssets({ status: "active", exchange });

      return assets;
    } catch (error) {
      return this.handleError(error);
    }
  }

  /**
   * Get crypto assets
   */
  async getCryptoAssets(): Promise<Asset[]> {
    try {
      return await this.getAssets({
        status: "active",
        asset_class: "crypto",
      });
    } catch (error) {
      return this.handleError(error);
    }
  }

  /**
   * Get US equity assets
   */
  async getEquityAssets(): Promise<Asset[]> {
    try {
      return await this.getAssets({
        status: "active",
        asset_class: "us_equity",
      });
    } catch (error) {
      return this.handleError(error);
    }
  }

  /**
   * Validate symbols exist and are tradable
   */
  async validateSymbols(symbols: string[]): Promise<{
    valid: string[];
    invalid: string[];
    details: Record<
      string,
      { exists: boolean; tradable: boolean; reason?: string }
    >;
  }> {
    const results = {
      valid: [] as string[],
      invalid: [] as string[],
      details: {} as Record<
        string,
        { exists: boolean; tradable: boolean; reason?: string }
      >,
    };

    for (const symbol of symbols) {
      try {
        const asset = await this.getAsset(symbol);
        const isTradable = asset.tradable && asset.status === "active";

        results.details[symbol] = {
          exists: true,
          tradable: isTradable,
          reason: !isTradable
            ? `Status: ${asset.status}, Tradable: ${asset.tradable}`
            : undefined,
        };

        if (isTradable) {
          results.valid.push(symbol);
        } else {
          results.invalid.push(symbol);
        }
      } catch (error) {
        results.invalid.push(symbol);
        results.details[symbol] = {
          exists: false,
          tradable: false,
          reason: "Asset not found",
        };
      }
    }

    return results;
  }
}

export default AssetService;
