# AI Integration Guide

## Overview

This application now features AI-powered portfolio analysis and asset recommendations using OpenAI's GPT-4o-mini model. The AI can analyze your portfolio, provide buy/sell/hold recommendations for individual assets, and engage in conversational follow-up questions through an interactive chat interface.

## Features

### 1. **Portfolio Analysis (Dashboard)**
- Click the "Analyze Portfolio" button to get comprehensive AI-powered analysis
- Real-time AI communication visualization showing the analysis process
- Receive insights on:
  - Portfolio diversification
  - Top performers and underperformers
  - Risk assessment
  - Specific buy/sell/hold recommendations
  - Actionable next steps

### 2. **Asset Analysis (Asset Page)**
- Click the "Analyze" button on any asset page
- Get detailed analysis for individual stocks including:
  - Clear BUY/SELL/HOLD recommendations
  - Price action and momentum analysis
  - Volume analysis
  - Support/resistance levels
  - Risk assessment
  - Entry/exit point suggestions

### 3. **Interactive AI Chat**
- Available on both Dashboard and Asset pages
- Ask follow-up questions about the analysis
- Get contextual responses based on:
  - Current asset data
  - Previous conversation history
  - Portfolio composition
  - Market conditions

### 4. **AI Loading Animation**
- Visual representation of AI agents communicating
- Real-time logs showing analysis progress
- Pentagon network visualization with animated connections

## Setup Instructions

### 1. Get Your OpenAI API Key

1. Go to [OpenAI Platform](https://platform.openai.com/api-keys)
2. Sign in or create an account
3. Navigate to API Keys section
4. Click "Create new secret key"
5. Copy your API key

### 2. Configure Environment Variables

Add your OpenAI API key to the `.env` file in the `front` directory:

```env
# OpenAI API Configuration
VITE_OPENAI_API_KEY=sk-proj-your-actual-api-key-here
```

**Important Security Notes:**
- Never commit your `.env` file to version control
- The `.env` file is already in `.gitignore`
- Keep your API key secret and secure
- Use different API keys for development and production

### 3. Restart Development Server

After adding your API key, restart the development server:

```bash
npm run dev
# or
pnpm dev
```

## Usage Examples

### Portfolio Analysis

1. Navigate to the Dashboard
2. Click the "Analyze Portfolio" button
3. Watch the AI communication logs as the analysis runs
4. Review the comprehensive analysis including:
   - Overall portfolio health assessment
   - Key findings about performance and diversification
   - Specific asset recommendations
   - Risk evaluation

### Asset Analysis

1. Navigate to any asset page (e.g., `/market/AAPL`)
2. Click the "Analyze" button
3. Receive detailed analysis including:
   - Clear recommendation (BUY/SELL/HOLD)
   - Technical analysis points
   - Risk assessment
   - Action plan with entry/exit suggestions

### Interactive Chat

After receiving an analysis, you can ask follow-up questions like:

- "Why do you recommend buying NVDA?"
- "What's the risk level of my portfolio?"
- "Should I increase my position in TSLA?"
- "What's your outlook for tech stocks?"
- "Tell me more about the support levels for AAPL"

## AI Service Architecture

### AIService Class

Located at `src/services/AIService.ts`, this service provides:

```typescript
// Portfolio analysis
const analysis = await aiService.analyzePortfolio({
  assets: [...],
  totalValue: 50000,
  riskTolerance: 'moderate'
});

// Asset analysis
const analysis = await aiService.analyzeAsset({
  symbol: 'AAPL',
  name: 'Apple Inc.',
  currentPrice: 178.23,
  dailyChangePercent: 2.5,
  // ... other price data
});

// Chat interactions
const response = await aiService.getChatResponse(
  "Should I buy more NVDA?",
  {
    currentAsset: { ... },
    portfolio: { ... },
    conversationHistory: [...]
  }
);
```

### Response Format

The AI service returns structured responses:

```typescript
interface AIAnalysisResponse {
  analysis: string;              // Full markdown-formatted analysis
  recommendations: string[];      // Key actionable recommendations
  riskLevel: 'low' | 'medium' | 'high';
  suggestedActions: Array<{
    action: 'buy' | 'sell' | 'hold';
    symbol: string;
    reason: string;
  }>;
}
```

## Components

### LoadingAI Component

Visual feedback during AI analysis with:
- Pentagon network of AI agents
- Animated connections showing data flow
- Real-time communication logs
- Professional card design

Usage:
```tsx
<LoadingAI 
  messages={aiMessages} 
  showLogs={true} 
/>
```

### ChatBox Component

Interactive chat interface with:
- Message history
- Typing indicators
- Timestamp display
- Auto-scroll to latest messages
- Markdown rendering for AI responses

Usage:
```tsx
<ChatBox
  messages={messages}
  onSend={handleSendMessage}
  placeholder="Ask about this stock..."
  disabled={isAnalyzing}
/>
```

## Cost Considerations

Using GPT-4o-mini (the most cost-effective model):

- **Portfolio Analysis**: ~1,500 tokens per analysis (~$0.0002)
- **Asset Analysis**: ~1,000 tokens per analysis (~$0.00015)
- **Chat Messages**: ~500-800 tokens per exchange (~$0.0001)

Estimated costs for typical usage:
- **Light usage** (5 analyses/day): ~$0.005/day
- **Moderate usage** (20 analyses/day): ~$0.02/day
- **Heavy usage** (100 analyses/day): ~$0.10/day

## Fallback Behavior

If the OpenAI API key is not configured:

1. A warning message will appear in the chat
2. Basic rule-based responses will be provided for chat
3. Analysis features will display an error message with setup instructions
4. All other app functionality continues to work normally

## Troubleshooting

### "API key not configured" Error

**Solution:** Make sure you've added `VITE_OPENAI_API_KEY` to your `.env` file and restarted the dev server.

### "Analysis failed" Error

**Possible causes:**
1. Invalid API key
2. Insufficient API credits
3. Network connectivity issues
4. Rate limiting

**Solutions:**
- Verify your API key is correct
- Check your OpenAI account has available credits
- Check your internet connection
- Wait a moment and try again if rate limited

### Chat Not Responding

**Solutions:**
1. Check browser console for errors
2. Verify API key is configured
3. Ensure you're not hitting rate limits
4. Check OpenAI service status

## Best Practices

1. **Context Management**: The AI uses the last 6 messages for context to optimize token usage
2. **Specific Questions**: Ask clear, specific questions for better responses
3. **Follow-ups**: Use the chat for follow-up questions instead of re-running full analysis
4. **Analysis Frequency**: Avoid excessive analysis requests to manage API costs
5. **Data Privacy**: Avoid sharing sensitive personal information in chat

## Future Enhancements

Potential improvements for the AI integration:

- [ ] Streaming responses for real-time chat
- [ ] Historical analysis tracking
- [ ] Custom risk profiles
- [ ] Multi-asset comparison
- [ ] Sentiment analysis from news
- [ ] Technical indicator integration
- [ ] Portfolio optimization suggestions
- [ ] Automated trading signals
- [ ] Voice input/output support
- [ ] Export analysis reports

## Technical Details

### Models Used
- **Primary**: GPT-4o-mini (cost-effective, fast, capable)
- **Temperature**: 0.7-0.8 (balanced creativity and accuracy)
- **Max Tokens**: 800-1500 (optimized for concise responses)

### Security
- API keys stored in environment variables
- Keys never exposed to client-side code in production
- All API calls made server-side (in production setup)
- No sensitive data logged or cached

### Performance
- Typical response time: 2-5 seconds
- Loading animation provides visual feedback
- Non-blocking UI updates
- Error handling with graceful fallbacks

## Support

For issues or questions:
1. Check this documentation
2. Review console errors
3. Verify OpenAI API configuration
4. Check OpenAI service status
5. Contact support if issues persist

## License

This AI integration uses OpenAI's API subject to their terms of service.
