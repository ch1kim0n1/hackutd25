# Local JSON Data Storage

This directory contains all local JSON data files for the application.

## Structure

- `users/` - User account data and authentication info
- `portfolios/` - User portfolio data and holdings
- `trades/` - Trade history and orders
- `goals/` - Financial goals and progress tracking
- `accounts/` - Linked financial accounts
- `transactions/` - Transaction history
- `subscriptions/` - User subscription data
- `plaid/` - Plaid integration data (link tokens, account connections)
- `voice_commands/` - Voice command history and confirmations
- `rag_documents/` - RAG system document embeddings and metadata

## File Format

All files follow the pattern: `{entity_type}_{id}.json` or collections use `{entity_type}_index.json`

Example:
- `users/user_123.json` - Individual user data
- `users/index.json` - User index for lookups
- `portfolios/portfolio_456.json` - Portfolio data

## Backup

Data files are automatically backed up to `.backup/` subdirectories with timestamps.
