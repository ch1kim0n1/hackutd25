import { openai } from "@ai-sdk/openai";
import { generateText, streamText } from "ai";

export interface PortfolioAnalysisRequest {
  assets: Array<{
    symbol: string;
    name: string;
    price: number;
    dailyChange: number;
    quantity?: number;
    value?: number;
  }>;
  totalValue?: number;
  riskTolerance?: "conservative" | "moderate" | "aggressive";
}

export interface AssetAnalysisRequest {
  symbol: string;
  name: string;
  currentPrice: number;
  dailyChange: number;
  dailyChangePercent: number;
  open: number;
  high: number;
  low: number;
  volume: number;
  previousClose: number;
  historicalData?: Array<{
    date: Date;
    close: number;
    volume: number;
  }>;
}

export interface AIAnalysisResponse {
  analysis: string;
  recommendations: string[];
  riskLevel: "low" | "medium" | "high";
  suggestedActions: Array<{
    action: "buy" | "sell" | "hold";
    symbol: string;
    reason: string;
  }>;
}

export class AIService {
  private apiKey: string;
  private model: string;

  constructor(apiKey?: string) {
    // Use environment variable or provided key
    this.apiKey = apiKey || import.meta.env.VITE_OPENAI_API_KEY || "";
    this.model = "gpt-4o-mini"; // Using gpt-4o-mini for cost-effective analysis
  }

  /**
   * Analyze a complete portfolio and provide recommendations
   */
  async analyzePortfolio(
    request: PortfolioAnalysisRequest,
  ): Promise<AIAnalysisResponse> {
    const prompt = this.buildPortfolioPrompt(request);

    try {
      const { text } = await generateText({
        model: openai(this.model),
        prompt,
        temperature: 0.7,
        maxSteps: 10,
      });

      return this.parseAnalysisResponse(text, request.assets);
    } catch (error) {
      console.error("AI Portfolio Analysis Error:", error);
      throw new Error(
        "Failed to analyze portfolio. Please check your API key.",
      );
    }
  }

  /**
   * Analyze a specific asset and provide buy/sell/hold recommendation
   */
  async analyzeAsset(
    request: AssetAnalysisRequest,
  ): Promise<AIAnalysisResponse> {
    const prompt = this.buildAssetPrompt(request);

    try {
      const { text } = await generateText({
        model: openai(this.model),
        prompt,
        temperature: 0.7,
        maxSteps: 10,
      });

      return this.parseAnalysisResponse(text, [
        {
          symbol: request.symbol,
          name: request.name,
          price: request.currentPrice,
          dailyChange: request.dailyChangePercent,
        },
      ]);
    } catch (error) {
      console.error("AI Asset Analysis Error:", error);
      throw new Error("Failed to analyze asset. Please check your API key.");
    }
  }

  /**
   * Stream chat responses for interactive conversations
   */
  async *streamChatResponse(
    message: string,
    context: {
      conversationHistory?: Array<{
        role: "user" | "assistant";
        content: string;
      }>;
      currentAsset?: AssetAnalysisRequest;
      portfolio?: PortfolioAnalysisRequest;
    },
  ): AsyncGenerator<string> {
    const prompt = this.buildChatPrompt(message, context);

    try {
      const result = await streamText({
        model: openai(this.model),
        prompt,
        temperature: 0.8,
      });

      for await (const chunk of result.textStream) {
        yield chunk;
      }
    } catch (error) {
      console.error("AI Chat Stream Error:", error);
      yield "I apologize, but I encountered an error processing your request. Please try again.";
    }
  }

  /**
   * Get a quick chat response (non-streaming)
   */
  async getChatResponse(
    message: string,
    context: {
      conversationHistory?: Array<{
        role: "user" | "assistant";
        content: string;
      }>;
      currentAsset?: AssetAnalysisRequest;
      portfolio?: PortfolioAnalysisRequest;
    },
  ): Promise<string> {
    const prompt = this.buildChatPrompt(message, context);

    try {
      const { text } = await generateText({
        model: openai(this.model),
        prompt,
        temperature: 0.8,
      });

      return text;
    } catch (error) {
      console.error("AI Chat Error:", error);

      return "I apologize, but I encountered an error processing your request. Please try again.";
    }
  }

  private buildPortfolioPrompt(request: PortfolioAnalysisRequest): string {
    const assetsList = request.assets
      .map(
        (asset) =>
          `- ${asset.symbol} (${asset.name}): $${asset.price.toFixed(2)}, ${asset.dailyChange >= 0 ? "+" : ""}${asset.dailyChange.toFixed(2)}%${asset.quantity ? `, Quantity: ${asset.quantity}, Value: $${asset.value?.toFixed(2)}` : ""}`,
      )
      .join("\n");

    return `You are a professional financial analyst AI assistant. Analyze the following investment portfolio and provide actionable insights.

Portfolio Assets:
${assetsList}

${request.totalValue ? `Total Portfolio Value: $${request.totalValue.toFixed(2)}` : ""}
${request.riskTolerance ? `Risk Tolerance: ${request.riskTolerance}` : ""}

Please provide a comprehensive analysis in the following format:

1. **Overall Portfolio Assessment**: Brief overview of portfolio health and diversification.

2. **Key Findings**: 3-5 bullet points highlighting important observations about performance, sector allocation, and risk exposure.

3. **Specific Recommendations**: For each asset or group of assets, provide specific buy/sell/hold recommendations with reasoning.

4. **Risk Assessment**: Evaluate the overall risk level (low/medium/high) and explain.

5. **Next Steps**: 2-3 actionable suggestions for the investor.

Keep your analysis professional, data-driven, and actionable. Focus on practical insights rather than generic advice.`;
  }

  private buildAssetPrompt(request: AssetAnalysisRequest): string {
    const priceMovement = request.dailyChangePercent >= 0 ? "up" : "down";
    const momentum =
      Math.abs(request.dailyChangePercent) > 3 ? "significant" : "moderate";

    return `You are a professional financial analyst AI assistant. Analyze the following stock and provide a clear buy/sell/hold recommendation.

Asset Information:
- Symbol: ${request.symbol}
- Name: ${request.name}
- Current Price: $${request.currentPrice.toFixed(2)}
- Daily Change: ${request.dailyChangePercent >= 0 ? "+" : ""}${request.dailyChangePercent.toFixed(2)}% ($${request.dailyChange >= 0 ? "+" : ""}${request.dailyChange.toFixed(2)})
- Today's Range: $${request.low.toFixed(2)} - $${request.high.toFixed(2)}
- Open: $${request.open.toFixed(2)}
- Previous Close: $${request.previousClose.toFixed(2)}
- Volume: ${request.volume.toLocaleString()}

Market Context:
The stock is ${priceMovement} ${Math.abs(request.dailyChangePercent).toFixed(2)}% today, showing ${momentum} momentum. Volume is ${request.volume > 1000000 ? "high" : "moderate"}.

Please provide your analysis in the following format:

1. **Recommendation**: Clear BUY/SELL/HOLD recommendation with confidence level.

2. **Key Analysis Points**: 3-4 bullet points about:
   - Price action and momentum
   - Volume analysis
   - Support/resistance levels based on today's range
   - Short-term outlook

3. **Risk Assessment**: Identify the risk level (low/medium/high) and explain.

4. **Action Plan**: If recommending buy or sell, suggest entry/exit points and position sizing guidance.

Be direct, specific, and actionable. This analysis will help an investor make a trading decision.`;
  }

  private buildChatPrompt(
    message: string,
    context: {
      conversationHistory?: Array<{
        role: "user" | "assistant";
        content: string;
      }>;
      currentAsset?: AssetAnalysisRequest;
      portfolio?: PortfolioAnalysisRequest;
    },
  ): string {
    let contextInfo = "";

    if (context.currentAsset) {
      contextInfo += `\n\nCurrent Asset Context:
- ${context.currentAsset.symbol} (${context.currentAsset.name})
- Price: $${context.currentAsset.currentPrice.toFixed(2)}
- Change: ${context.currentAsset.dailyChangePercent >= 0 ? "+" : ""}${context.currentAsset.dailyChangePercent.toFixed(2)}%
- Range: $${context.currentAsset.low.toFixed(2)} - $${context.currentAsset.high.toFixed(2)}`;
    }

    if (context.portfolio) {
      const topAssets = context.portfolio.assets
        .slice(0, 5)
        .map(
          (a) =>
            `${a.symbol}: $${a.price.toFixed(2)} (${a.dailyChange >= 0 ? "+" : ""}${a.dailyChange.toFixed(2)}%)`,
        )
        .join(", ");

      contextInfo += `\n\nPortfolio Context: ${topAssets}`;
    }

    let conversationContext = "";

    if (context.conversationHistory && context.conversationHistory.length > 0) {
      conversationContext =
        "\n\nPrevious Conversation:\n" +
        context.conversationHistory
          .slice(-6) // Last 3 exchanges
          .map(
            (msg) =>
              `${msg.role === "user" ? "User" : "Assistant"}: ${msg.content}`,
          )
          .join("\n");
    }

    return `You are a helpful financial AI assistant specializing in stock market analysis and portfolio management. You provide clear, actionable insights while being conversational and friendly.

${contextInfo}${conversationContext}

User Question: ${message}

Provide a helpful, concise response that directly addresses the user's question. If they're asking about specific stocks or portfolio actions, give data-driven insights. If they're asking follow-up questions, maintain context from the conversation. Keep responses focused and under 200 words unless detailed analysis is specifically requested.`;
  }

  private parseAnalysisResponse(
    text: string,
    assets: Array<{
      symbol: string;
      name: string;
      price: number;
      dailyChange: number;
    }>,
  ): AIAnalysisResponse {
    // Extract recommendations and risk level from the AI response
    const recommendations: string[] = [];
    const suggestedActions: Array<{
      action: "buy" | "sell" | "hold";
      symbol: string;
      reason: string;
    }> = [];

    // Simple parsing logic - can be enhanced with more sophisticated NLP
    const lines = text.split("\n").filter((line) => line.trim());

    // Look for recommendations
    let inRecommendationSection = false;

    for (const line of lines) {
      if (
        line.includes("Recommendation") ||
        line.includes("Key Finding") ||
        line.includes("Next Step")
      ) {
        inRecommendationSection = true;
        continue;
      }

      if (
        inRecommendationSection &&
        (line.startsWith("-") || line.startsWith("•") || line.match(/^\d+\./))
      ) {
        recommendations.push(
          line
            .replace(/^[-•]\s*/, "")
            .replace(/^\d+\.\s*/, "")
            .trim(),
        );
      }
    }

    // Determine risk level from the text
    let riskLevel: "low" | "medium" | "high" = "medium";
    const lowerText = text.toLowerCase();

    if (
      lowerText.includes("high risk") ||
      lowerText.includes("risky") ||
      lowerText.includes("volatile")
    ) {
      riskLevel = "high";
    } else if (
      lowerText.includes("low risk") ||
      lowerText.includes("stable") ||
      lowerText.includes("conservative")
    ) {
      riskLevel = "low";
    }

    // Extract action recommendations for each asset
    for (const asset of assets) {
      const symbolLower = asset.symbol.toLowerCase();
      let action: "buy" | "sell" | "hold" = "hold";
      let reason = "";

      if (
        lowerText.includes(`${symbolLower} buy`) ||
        lowerText.includes(`buy ${symbolLower}`)
      ) {
        action = "buy";
        reason = "AI recommends buying based on current analysis";
      } else if (
        lowerText.includes(`${symbolLower} sell`) ||
        lowerText.includes(`sell ${symbolLower}`)
      ) {
        action = "sell";
        reason = "AI recommends selling based on current analysis";
      } else {
        action = "hold";
        reason = "AI recommends holding position";
      }

      suggestedActions.push({ action, symbol: asset.symbol, reason });
    }

    // If no recommendations were parsed, extract from the full text
    if (recommendations.length === 0) {
      recommendations.push("Review the detailed analysis above for insights");
    }

    return {
      analysis: text,
      recommendations: recommendations.slice(0, 5), // Top 5 recommendations
      riskLevel,
      suggestedActions,
    };
  }

  /**
   * Check if the AI service is properly configured
   */
  isConfigured(): boolean {
    return this.apiKey.length > 0;
  }
}

// Export a singleton instance
export const aiService = new AIService();
