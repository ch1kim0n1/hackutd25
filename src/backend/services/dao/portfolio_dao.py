# backend/services/dao/portfolio_dao.py
"""
Data Access Object for Portfolio and Position models.
"""
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ...models.portfolio import Portfolio, Position


class PortfolioDAO:
    """Portfolio Data Access Object"""

    @staticmethod
    async def create(
        db: AsyncSession,
        user_id: str,
        name: str = "Main Portfolio",
        **kwargs
    ) -> Portfolio:
        """Create a new portfolio"""
        portfolio = Portfolio(user_id=user_id, name=name, **kwargs)
        db.add(portfolio)
        await db.commit()
        await db.refresh(portfolio)
        return portfolio

    @staticmethod
    async def get_by_id(db: AsyncSession, portfolio_id: str) -> Optional[Portfolio]:
        """Get portfolio by ID with positions loaded"""
        result = await db.execute(
            select(Portfolio)
            .where(Portfolio.id == portfolio_id)
            .options(selectinload(Portfolio.positions))
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_user(db: AsyncSession, user_id: str) -> List[Portfolio]:
        """Get all portfolios for a user"""
        result = await db.execute(
            select(Portfolio)
            .where(Portfolio.user_id == user_id)
            .options(selectinload(Portfolio.positions))
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_active_by_user(db: AsyncSession, user_id: str) -> List[Portfolio]:
        """Get all active portfolios for a user"""
        result = await db.execute(
            select(Portfolio)
            .where(Portfolio.user_id == user_id, Portfolio.is_active == 1)
            .options(selectinload(Portfolio.positions))
        )
        return list(result.scalars().all())

    @staticmethod
    async def update(db: AsyncSession, portfolio_id: str, **kwargs) -> Optional[Portfolio]:
        """Update portfolio"""
        stmt = (
            update(Portfolio)
            .where(Portfolio.id == portfolio_id)
            .values(**kwargs, updated_at=datetime.utcnow())
            .returning(Portfolio)
        )
        result = await db.execute(stmt)
        await db.commit()
        return result.scalar_one_or_none()

    @staticmethod
    async def update_metrics(
        db: AsyncSession,
        portfolio_id: str,
        total_value: Decimal,
        cash_balance: Decimal,
        **kwargs
    ) -> Optional[Portfolio]:
        """Update portfolio metrics"""
        return await PortfolioDAO.update(
            db,
            portfolio_id,
            total_value=total_value,
            cash_balance=cash_balance,
            last_synced_at=datetime.utcnow(),
            **kwargs
        )

    @staticmethod
    async def update_risk_metrics(
        db: AsyncSession,
        portfolio_id: str,
        **risk_metrics
    ) -> Optional[Portfolio]:
        """Update risk metrics"""
        return await PortfolioDAO.update(db, portfolio_id, **risk_metrics)

    @staticmethod
    async def delete(db: AsyncSession, portfolio_id: str) -> bool:
        """Delete portfolio"""
        stmt = delete(Portfolio).where(Portfolio.id == portfolio_id)
        result = await db.execute(stmt)
        await db.commit()
        return result.rowcount > 0


class PositionDAO:
    """Position Data Access Object"""

    @staticmethod
    async def create(
        db: AsyncSession,
        portfolio_id: str,
        symbol: str,
        quantity: Decimal,
        average_entry_price: Decimal,
        **kwargs
    ) -> Position:
        """Create a new position"""
        position = Position(
            portfolio_id=portfolio_id,
            symbol=symbol,
            quantity=quantity,
            average_entry_price=average_entry_price,
            cost_basis=quantity * average_entry_price,
            **kwargs
        )
        db.add(position)
        await db.commit()
        await db.refresh(position)
        return position

    @staticmethod
    async def get_by_id(db: AsyncSession, position_id: str) -> Optional[Position]:
        """Get position by ID"""
        result = await db.execute(select(Position).where(Position.id == position_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_portfolio(db: AsyncSession, portfolio_id: str) -> List[Position]:
        """Get all positions for a portfolio"""
        result = await db.execute(
            select(Position).where(Position.portfolio_id == portfolio_id)
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_by_symbol(
        db: AsyncSession,
        portfolio_id: str,
        symbol: str
    ) -> Optional[Position]:
        """Get position by symbol for a specific portfolio"""
        result = await db.execute(
            select(Position).where(
                Position.portfolio_id == portfolio_id,
                Position.symbol == symbol
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def update(db: AsyncSession, position_id: str, **kwargs) -> Optional[Position]:
        """Update position"""
        stmt = (
            update(Position)
            .where(Position.id == position_id)
            .values(**kwargs, last_updated_at=datetime.utcnow())
            .returning(Position)
        )
        result = await db.execute(stmt)
        await db.commit()
        return result.scalar_one_or_none()

    @staticmethod
    async def update_market_data(
        db: AsyncSession,
        position_id: str,
        current_price: Decimal
    ) -> Optional[Position]:
        """Update position with current market price"""
        # Get current position to calculate P&L
        position = await PositionDAO.get_by_id(db, position_id)
        if not position:
            return None

        market_value = position.quantity * current_price
        unrealized_pl = market_value - position.cost_basis
        unrealized_pl_pct = (unrealized_pl / position.cost_basis * 100) if position.cost_basis else 0

        return await PositionDAO.update(
            db,
            position_id,
            current_price=current_price,
            market_value=market_value,
            unrealized_pl=unrealized_pl,
            unrealized_pl_pct=unrealized_pl_pct
        )

    @staticmethod
    async def delete(db: AsyncSession, position_id: str) -> bool:
        """Delete position"""
        stmt = delete(Position).where(Position.id == position_id)
        result = await db.execute(stmt)
        await db.commit()
        return result.rowcount > 0

    @staticmethod
    async def delete_by_symbol(db: AsyncSession, portfolio_id: str, symbol: str) -> bool:
        """Delete position by symbol"""
        stmt = delete(Position).where(
            Position.portfolio_id == portfolio_id,
            Position.symbol == symbol
        )
        result = await db.execute(stmt)
        await db.commit()
        return result.rowcount > 0
