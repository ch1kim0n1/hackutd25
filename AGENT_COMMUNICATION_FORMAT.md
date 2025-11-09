# Agent Communication Format Specification

## Overview

All agents in the APEX system follow a standardized, professional communication format. Agent output is designed to be:
- **Plain English**: No emojis, ASCII art, or formatting symbols in message content
- **Professional**: Suitable for institutional/enterprise use
- **Clear**: Unambiguous decision information with structured reporting
- **Transparent**: All reasoning and logic explicitly stated

---

## Message Structure

### Standard Agent Message Format

```
FROM: <Agent Name>
TO: <Recipient Agent or User>
TIME: <HH:MM:SS> [<IMPORTANCE_LEVEL>]
─────────────────────────────────────────────────
<Message Content>
```

### Field Definitions

| Field | Description |
|-------|-------------|
| **FROM** | Sending agent name (e.g., "Market Agent", "Strategy Agent") |
| **TO** | Receiving agent or user name |
| **TIME** | Timestamp in 24-hour format |
| **IMPORTANCE** | [OPTIONAL] One of: NORMAL, HIGH, CRITICAL |

### Importance Levels

- **NORMAL**: Routine communication, informational messages
- **HIGH**: Important recommendations or proposals
- **CRITICAL**: Risk alerts, approval required, trade execution

---

## Message Content Format

### 1. Market Agent Output

**Purpose**: Report current market conditions and identify relevant events

**Format**:
```
Market Scan Report

Current Market Conditions:
- Market Sentiment: <sentiment>
- VIX Index: <value> (<interpretation>)
- S&P 500 Performance: <percentage>
- Technology Sector: <percentage>
- Bond Market: <percentage>
- Federal Reserve Status: <status>
- Key News: <headlines>

Analysis:
<brief analysis of conditions>
<recommendation for next steps>
```

**Example**:
```
Market Scan Report

Current Market Conditions:
- Market Sentiment: cautiously optimistic
- VIX Index: 14.2 (Low volatility environment)
- S&P 500 Performance: +2.1%
- Technology Sector: +3.2%
- Bond Market: -0.5%
- Federal Reserve Status: held rates steady
- Key News: Tech earnings beat expectations

Analysis:
Technology sector is outperforming significantly. Current conditions support 
equity-heavy allocation strategy for long-term investors. Recommend proceeding 
with portfolio construction.
```

---

### 2. Strategy Agent Output

**Purpose**: Create portfolio allocation recommendations

**Format**:
```
Portfolio Allocation Recommendation

Investor Profile:
- Risk Tolerance: <level>
- Investment Horizon: <duration>
- Initial Capital: <amount>

Proposed Allocation:
<JSON or formatted table with holdings>

Allocation Summary:
- Total Equity Exposure: <percentage>
- Number of Holdings: <count>

Rationale:
<explanation of allocation logic>

<Next steps or awaiting action>
```

**Example**:
```
Portfolio Allocation Recommendation

Investor Profile:
- Risk Tolerance: aggressive
- Investment Horizon: 20 years
- Initial Capital: $5,000

Proposed Allocation:
{
  "VOO": {"amount": 4000, "percent": 80},
  "VXUS": {"amount": 1000, "percent": 20}
}

Allocation Summary:
- Total Equity Exposure: 100%
- Number of Holdings: 2

Rationale:
Long-term horizon allows higher equity exposure

This allocation aligns with the investor's profile and current market conditions. 
Awaiting risk validation.
```

---

### 3. Risk Agent Output

**Purpose**: Validate portfolios against risk constraints

**Format**:
```
Portfolio Risk Assessment Report

Status: <APPROVED or REJECTED>

Constraint Validation Results:
- <Constraint 1>: <PASS/FAIL> - <description>
- <Constraint 2>: <PASS/FAIL> - <description>
[... more constraints ...]

Risk Assessment Notes:
<additional analysis>

<Permission for next action or reasons for rejection>
```

**Example**:
```
Portfolio Risk Assessment Report

Status: APPROVED

Constraint Validation Results:
- Maximum Position Size: PASS - No single position exceeds account limit
- Diversification Requirement: PASS - Portfolio contains 2 positions
- Margin Usage Policy: PASS - No margin trading detected
- Capital Limit: PASS - Total allocation within available capital
- Volatility Tolerance: PASS - Portfolio aligns with investor risk profile

Risk Assessment Notes:
All safety limits verified

This allocation satisfies all risk management constraints and is approved 
for execution. Executor Agent may proceed with order placement.
```

---

### 4. Executor Agent Output

**Purpose**: Report order execution status

**Format**:
```
Order Execution Report

Status: <SUCCESS or FAILED>

Executed Orders:
- <Symbol>: <quantity> shares at ~$<price> per share = $<amount>
[... more orders ...]

Execution Summary:
- Total Capital Deployed: $<amount>
- Number of Transactions: <count>
- Order Status: <All FILLED, Partially FILLED, FAILED>
- Execution Time: <HH:MM:SS>

<Additional notes or next steps>
```

**Example**:
```
Order Execution Report

Status: SUCCESS - All orders filled

Executed Orders:
- VOO: 80 shares at approximately $50 per share = $4000
- VXUS: 20 shares at approximately $50 per share = $1000

Execution Summary:
- Total Capital Deployed: $5000
- Number of Transactions: 2
- Order Status: All orders FILLED
- Execution Time: 11:21:57

All orders have been successfully executed at market prices. Portfolio 
construction is complete. Summary ready for user communication.
```

---

### 5. Explainer Agent Output

**Purpose**: Translate complex decisions into user-friendly language

**Format**:
```
[Title of Explanation]

Introduction:
<Plain English greeting and summary>

<Explanation Sections with clear headers>

Key Points:
- <Important point 1>
- <Important point 2>
- <Important point 3>

Next Steps:
<What to expect next>
```

**Example**:
```
Portfolio Setup Complete - Investor Summary

Hello Alex,

Your investment portfolio has been successfully established with the following 
allocation:

Portfolio Composition:
- VOO: $4000 (80%)
- VXUS: $1000 (20%)

What This Means:
Your portfolio is structured to balance growth potential with your aggressive 
risk tolerance and long-term investment horizon. Each holding serves a specific 
purpose in your overall strategy:
- Growth stocks provide market upside participation
- International exposure adds geographic diversification
- This multi-holding approach reduces risk through diversification

Investment Strategy Going Forward:
- Regular monitoring of market conditions
- Quarterly portfolio rebalancing review
- Continued investment through monthly contributions
- Real-time alerts on significant market events

Your accounts are fully funded and active. You will receive regular updates on 
portfolio performance and market developments.
```

---

### 6. User Input Format

**Purpose**: User provides feedback or requests to agents

**Format**:
```
<Context or Subject>

<Main message or feedback>

Action Items:
1. <Item 1>
2. <Item 2>
3. <Item 3>

<Closing statement>
```

**Example**:
```
Portfolio Feedback and Requests

This looks excellent. I appreciate the aggressive approach given my 20-year timeline. 
I'm confident in this strategy.

Action Items:
1. Please monitor market developments and notify me of significant changes
2. Set up automatic monthly contributions to the portfolio
3. Alert me to major portfolio impacts (earnings announcements, policy changes, etc.)
4. Quarterly performance reviews

I'm ready to get started with long-term investing.
```

---

## Professional Standards

### Language Guidelines

1. **Use active voice**: "Portfolio has been approved" instead of "Portfolio was approved"
2. **Be specific**: "VIX Index at 14.2" instead of "VIX is low"
3. **Use financial terminology**: "VaR", "allocation", "rebalancing" are acceptable
4. **Explain financial concepts**: When speaking to users, provide plain English context
5. **No contractions**: Use formal writing style (e.g., "cannot" instead of "can't")

### Structure Guidelines

1. **Start with status**: Begin with clear status (APPROVED, FILLED, ALERT, etc.)
2. **Provide context**: Explain why decisions are made
3. **List constraints/validations**: Use bullet points for clarity
4. **Include reasoning**: Always explain the "why" behind recommendations
5. **Clear next steps**: End with what happens next

### Data Presentation

- **Currency**: Always use dollar sign and amounts (e.g., "$5,000")
- **Percentages**: Include context (e.g., "+2.1% vs previous close")
- **Time**: Use 24-hour HH:MM:SS format
- **Importance**: Use standard labels (NORMAL, HIGH, CRITICAL)

---

## Agent Communication Flow

```
Step 1: Market Agent reports current conditions
        ↓
Step 2: Strategy Agent proposes allocation
        ↓
Step 3: Risk Agent validates constraints
        ↓
Step 4: Executor Agent executes orders
        ↓
Step 5: Explainer Agent communicates to user
        ↓
Step 6: User provides feedback
        ↓
Step 7: Market Agent acknowledges and monitors
```

---

## War Room Display Format

### Message List View

```
1. Market Agent → Strategy Agent
   Market Scan Report
   Current Market Conditions: [summary...]

2. Strategy Agent → Risk Agent [HIGH]
   Portfolio Allocation Recommendation
   Proposed Allocation: [summary...]

3. Risk Agent → Executor Agent [CRITICAL]
   Portfolio Risk Assessment Report
   Status: APPROVED
```

### Full Message View

```
────────────────────────────────────────────
FROM: Market Agent
TO: Strategy Agent
TIME: 11:21:56
────────────────────────────────────────────
[Full message content here...]
```

---

## Error and Alert Messages

### Standard Alert Format

```
<Agent Name> Alert

Issue: <Description of problem>

Details:
- <Detail 1>
- <Detail 2>

Impact: <How this affects the user>

Recommended Action: <Next steps>
```

### Rejection Format

```
Portfolio Rejected - Risk Constraints Violated

Status: REJECTED

Failed Constraints:
- <Constraint 1>: <Reason>
- <Constraint 2>: <Reason>

Reason for Rejection:
<Explanation of why constraints were violated>

Corrective Action Required:
<What needs to change before approval>
```

---

## Documentation Requirements

All agent communications must include:

1. **Clear sender/recipient identification**
2. **Timestamp of communication**
3. **Importance level (if not NORMAL)**
4. **Specific metrics and numbers**
5. **Reasoning and justification**
6. **Next steps or required actions**
7. **Plain English explanation (for user-facing messages)**

---

## Examples Summary

| Agent | Message Type | Key Elements |
|-------|--------------|--------------|
| Market Agent | Market Scan Report | VIX, sentiment, sector performance |
| Strategy Agent | Allocation Recommendation | Holdings, percentages, rationale |
| Risk Agent | Risk Assessment | Constraint status, approval, notes |
| Executor Agent | Execution Report | Orders filled, capital deployed |
| Explainer Agent | Summary | Plain English, key points, next steps |
| User | Feedback/Requests | Action items, preferences, confirmation |

---

## Version History

- **v1.0** (2025-11-09): Initial professional format specification
  - Removed all emoji/ASCII art
  - Standardized all agent message templates
  - Created professional output schemas
  - Documented best practices for clarity and transparency
