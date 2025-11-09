from backend.services.db import get_user_portfolio

async def get_portfolio(user_id: str, db):
    portfolio = await get_user_portfolio(user_id, db)
    return {"user_id": user_id, "portfolio": portfolio}
