# Frontend-Backend Integration Guide

This document provides a step-by-step guide for completing the frontend-backend integration in the APEX platform.

## Current Status

### ✅ Completed
- Backend API service created (`BackendAPI.ts`)
- WebSocket client created (`WebSocketClient.ts`)
- Vite proxy configured for development
- Authentication flow implemented
- Token management (automatic refresh)
- Example components created

### ⏳ Remaining Work
- Update existing frontend components to use BackendAPI
- Replace direct Alpaca API calls
- Replace direct OpenAI API calls
- Connect War Room to WebSocket
- Update all pages to use backend authentication

---

## Migration Strategy

### Phase 1: Authentication (Priority: Critical)

**Files to Update:**
1. Any login/signup components
2. Protected route wrappers
3. User profile components

**Migration Steps:**
```typescript
// Before: Direct auth implementation
const login = async (username, password) => {
  const response = await fetch('/api/login', {
    method: 'POST',
    body: JSON.stringify({ username, password })
  });
  const data = await response.json();
  localStorage.setItem('token', data.token);
};

// After: Use BackendAPI
import BackendAPI from '@/services/BackendAPI';

const login = async (username, password) => {
  const response = await BackendAPI.auth.login(username, password);
  // Tokens are automatically stored!
};
```

**Example Component:**
See [`/client/front/src/components/examples/AuthExample.tsx`](client/front/src/components/examples/AuthExample.tsx)

---

### Phase 2: Trading Operations (Priority: High)

**Files to Update:**
1. `src/services/AlpacaClient.ts` → Use BackendAPI as proxy
2. Trading dashboard components
3. Order placement components
4. Position/portfolio displays

**Migration Steps:**
```typescript
// Before: Direct Alpaca calls
import { AlpacaClient } from '@/services/AlpacaClient';

const alpaca = new AlpacaClient(apiKey, secret);
const positions = await alpaca.getPositions();
await alpaca.placeOrder({ symbol: 'AAPL', qty: 10, side: 'buy' });

// After: Use BackendAPI
import BackendAPI from '@/services/BackendAPI';

const positions = await BackendAPI.portfolio.getPositions();
await BackendAPI.trading.placeTrade({
  symbol: 'AAPL',
  qty: 10,
  side: 'buy'
});
```

**Benefits:**
- Backend logs all trades
- Agents can monitor trades
- Better security (no API keys in frontend)
- Centralized error handling

**Example Component:**
See [`/client/front/src/components/examples/TradingExample.tsx`](client/front/src/components/examples/TradingExample.tsx)

---

### Phase 3: AI Services (Priority: High)

**Files to Update:**
1. `src/services/AIService.ts` → Proxy through backend
2. Chat components
3. Analysis components

**Migration Steps:**
```typescript
// Before: Direct OpenAI calls
import { OpenAI } from '@ai-sdk/openai';

const openai = new OpenAI({ apiKey: process.env.VITE_OPENAI_API_KEY });
const response = await openai.chat.completions.create({
  model: 'gpt-4',
  messages: [{ role: 'user', content: 'Analyze AAPL' }]
});

// After: Use backend RAG system
import BackendAPI from '@/services/BackendAPI';

const response = await BackendAPI.rag.query('Analyze AAPL stock');
// Backend handles AI calls + RAG context
```

**Benefits:**
- RAG system integration
- Agent insights included
- Cost control (backend rate limiting)
- No API keys in frontend

---

### Phase 4: War Room WebSocket (Priority: High)

**Files to Update:**
1. War Room page/component
2. Real-time agent display
3. Message handling

**Migration Steps:**
```typescript
// Import WebSocket client
import { WarRoomWebSocket } from '@/services/WebSocketClient';

// In component
const ws = new WarRoomWebSocket(userId);

React.useEffect(() => {
  ws.connect();

  // Listen for agent messages
  ws.onMessage((message) => {
    console.log('Agent update:', message);
    // Update UI with agent decisions, debates, etc.
  });

  return () => ws.disconnect();
}, [userId]);

// Send user input to agents
const sendUserOpinion = (opinion: string) => {
  ws.send({
    type: 'user_input',
    data: { message: opinion }
  });
};
```

**React Hook Example:**
```typescript
import { useWarRoomWebSocket } from '@/services/WebSocketClient';

function WarRoom() {
  const { isConnected, messages, sendMessage } = useWarRoomWebSocket(userId);

  return (
    <div>
      <div>Status: {isConnected ? 'Connected' : 'Disconnected'}</div>
      {messages.map((msg, idx) => (
        <div key={idx}>{msg.data}</div>
      ))}
      <button onClick={() => sendMessage({ action: 'pause' })}>
        Pause Agents
      </button>
    </div>
  );
}
```

---

### Phase 5: Goals & Personal Finance (Priority: Medium)

**Files to Update:**
1. Goal tracking components
2. Personal finance dashboard
3. Plaid integration components

**Migration Steps:**
```typescript
// Goals
import BackendAPI from '@/services/BackendAPI';

// Create goal
const goal = await BackendAPI.goals.create({
  title: 'Retirement Fund',
  target_amount: 1000000,
  target_date: '2045-01-01'
});

// Update progress
await BackendAPI.goals.updateProgress(goal.id, 50000);

// Personal Finance
const accounts = await BackendAPI.finance.getAccounts();
const netWorth = await BackendAPI.finance.getNetWorth();
const healthScore = await BackendAPI.finance.getHealthScore();
```

---

### Phase 6: Market Data (Priority: Low)

**Files to Update:**
1. Stock search components
2. Chart/price displays
3. Market news components

**Migration Steps:**
```typescript
import BackendAPI from '@/services/BackendAPI';

// Get quote
const quote = await BackendAPI.market.getQuote('AAPL');

// Get historical data
const historicalData = await BackendAPI.market.getHistoricalData(
  'AAPL',
  '1D',
  100
);
```

---

## File-by-File Migration Checklist

### High Priority Files

- [ ] `src/services/AlpacaClient.ts` - Update or wrap with BackendAPI
- [ ] `src/services/AIService.ts` - Proxy through backend
- [ ] `src/pages/` - Update all pages using direct API calls
- [ ] `src/components/` - Search for `fetch(` and replace with BackendAPI

### Search Commands

Find files that need updating:
```bash
# Find direct fetch calls
cd client/front
grep -r "fetch(" src/ --include="*.ts" --include="*.tsx"

# Find Alpaca usage
grep -r "alpaca" src/ --include="*.ts" --include="*.tsx" -i

# Find OpenAI usage
grep -r "openai" src/ --include="*.ts" --include="*.tsx" -i

# Find localStorage token usage
grep -r "localStorage.*token" src/ --include="*.ts" --include="*.tsx"
```

---

## Testing After Migration

### 1. Authentication Flow
```bash
# Test login
POST /auth/login
# Verify token stored in localStorage
# Test protected endpoint
GET /api/portfolio (with auth header)
```

### 2. Trading Flow
```bash
# Test trade placement
POST /api/trade
# Verify backend logging
# Check agent notification
```

### 3. WebSocket Connection
```bash
# Open War Room page
# Verify WebSocket connection in browser DevTools
# Check for agent messages
# Test sending user input
```

---

## Environment Variables Update

### Frontend `.env`
```bash
# Use backend proxy (recommended)
VITE_USE_BACKEND_PROXY=true
VITE_BACKEND_URL=http://localhost:8000
VITE_BACKEND_WS_URL=ws://localhost:8000

# Remove or comment out direct API keys (security)
# VITE_ALPACA_API_KEY=...
# VITE_OPENAI_API_KEY=...
```

### Backend `.env`
Ensure backend has all required API keys:
```bash
ALPACA_API_KEY=your_key_here
ALPACA_SECRET_KEY=your_secret_here
OPENAI_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here
```

---

## Common Issues & Solutions

### Issue 1: CORS Errors
**Problem:** Browser blocks requests to backend

**Solution:**
- Ensure Vite proxy is configured (`vite.config.ts`)
- Check CORS settings in backend (`server.py`)
- Use relative URLs in development (`/api/...` not `http://localhost:8000/api/...`)

### Issue 2: 401 Unauthorized
**Problem:** Requests fail with 401 even after login

**Solution:**
- Check token is stored: `console.log(TokenManager.getAccessToken())`
- Verify token not expired
- Check backend JWT validation
- Ensure Authorization header is included

### Issue 3: WebSocket Connection Failed
**Problem:** War Room WebSocket won't connect

**Solution:**
- Check backend is running on correct port
- Verify WebSocket route (`/ws/warroom`) exists
- Check browser console for errors
- Test WebSocket endpoint with tool like `wscat`

### Issue 4: Type Errors
**Problem:** TypeScript errors after adding BackendAPI

**Solution:**
- Add proper types to BackendAPI responses
- Use `any` temporarily, then add proper interfaces
- Check import paths are correct

---

## Code Quality Checklist

Before committing changes:

- [ ] All `fetch()` calls replaced with BackendAPI
- [ ] No API keys in frontend code
- [ ] Error handling added for all API calls
- [ ] Loading states implemented
- [ ] TypeScript types are correct
- [ ] No console errors in browser
- [ ] Authentication works end-to-end
- [ ] WebSocket connects successfully
- [ ] Trading operations work
- [ ] Tests updated (if applicable)

---

## Performance Considerations

### Reduce API Calls
```typescript
// Use React Query or SWR for caching
import { useQuery } from 'react-query';

function Portfolio() {
  const { data, isLoading } = useQuery(
    'portfolio',
    () => BackendAPI.portfolio.get(),
    { refetchInterval: 60000 } // Refresh every minute
  );
}
```

### Batch Requests
```typescript
// Instead of multiple separate calls
const positions = await BackendAPI.portfolio.getPositions();
const orders = await BackendAPI.portfolio.getOrders();
const account = await BackendAPI.portfolio.getAccount();

// Use Promise.all
const [positions, orders, account] = await Promise.all([
  BackendAPI.portfolio.getPositions(),
  BackendAPI.portfolio.getOrders(),
  BackendAPI.portfolio.getAccount(),
]);
```

---

## Next Steps

1. **Start with Authentication** - This unblocks everything else
2. **Update Trading Components** - Core functionality
3. **Connect War Room** - Key differentiator
4. **Add Loading States** - Better UX
5. **Add Error Boundaries** - Handle failures gracefully
6. **Test Everything** - End-to-end testing

---

## Resources

- **BackendAPI Documentation**: [src/services/BackendAPI.ts](client/front/src/services/BackendAPI.ts)
- **WebSocket Documentation**: [src/services/WebSocketClient.ts](client/front/src/services/WebSocketClient.ts)
- **Example Components**: [src/components/examples/](client/front/src/components/examples/)
- **Backend API Docs**: http://localhost:8000/docs (when running)

---

## Getting Help

If you encounter issues:

1. Check browser console for errors
2. Check backend logs
3. Test API endpoints with Swagger UI (http://localhost:8000/docs)
4. Review example components
5. Check this documentation

---

**Last Updated:** 2025-01-10
**Status:** Migration in progress
**Priority:** Complete authentication and trading flows first
