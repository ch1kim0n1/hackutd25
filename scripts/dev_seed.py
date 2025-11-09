"""
APEX Demo Data Seeder
Seeds the database with realistic demo data for local testing
"""
import asyncio
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / "src" / "backend"
sys.path.insert(0, str(backend_path))

from datetime import datetime, timedelta
from services.postgres_db import async_session_maker, Base, engine
from models import User, Portfolio, Position, Trade, Goal
from services.security import hash_password


async def seed_demo_data():
    """Seed database with demo data"""
    print("🌱 Seeding demo data...")

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_maker() as session:
        # Check if demo user exists
        from sqlalchemy import select
        result = await session.execute(select(User).where(User.email == "demo@apex.local"))
        existing_user = result.scalar_one_or_none()

        if existing_user:
            print("  ✓ Demo data already exists, skipping...")
            return

        # Create demo user
        demo_user = User(
            email="demo@apex.local",
            username="demo",
            hashed_password=hash_password("demo123"),
            full_name="Demo User",
            is_verified=True,
            created_at=datetime.utcnow()
        )
        session.add(demo_user)
        await session.flush()

        # Create demo portfolio
        demo_portfolio = Portfolio(
            user_id=demo_user.id,
            name="Demo Portfolio",
            description="Sample portfolio for APEX demo",
            total_value=150000.00,
            cash_balance=25000.00,
            created_at=datetime.utcnow() - timedelta(days=365)
        )
        session.add(demo_portfolio)
        await session.flush()

        # Create positions
        positions = [
            Position(
                portfolio_id=demo_portfolio.id,
                symbol="SPY",
                shares=100,
                avg_cost=450.00,
                current_price=475.32,
                total_value=47532.00,
                unrealized_gain_loss=2532.00,
                created_at=datetime.utcnow() - timedelta(days=180)
            ),
            Position(
                portfolio_id=demo_portfolio.id,
                symbol="AAPL",
                shares=150,
                avg_cost=175.00,
                current_price=185.50,
                total_value=27825.00,
                unrealized_gain_loss=1575.00,
                created_at=datetime.utcnow() - timedelta(days=90)
            ),
            Position(
                portfolio_id=demo_portfolio.id,
                symbol="MSFT",
                shares=75,
                avg_cost=350.00,
                current_price=375.00,
                total_value=28125.00,
                unrealized_gain_loss=1875.00,
                created_at=datetime.utcnow() - timedelta(days=120)
            ),
            Position(
                portfolio_id=demo_portfolio.id,
                symbol="NVDA",
                shares=50,
                avg_cost=450.00,
                current_price=495.00,
                total_value=24750.00,
                unrealized_gain_loss=2250.00,
                created_at=datetime.utcnow() - timedelta(days=60)
            )
        ]
        for position in positions:
            session.add(position)

        # Create some trades
        trades = [
            Trade(
                portfolio_id=demo_portfolio.id,
                symbol="SPY",
                side="buy",
                quantity=100,
                price=450.00,
                total_amount=45000.00,
                status="filled",
                executed_at=datetime.utcnow() - timedelta(days=180)
            ),
            Trade(
                portfolio_id=demo_portfolio.id,
                symbol="AAPL",
                side="buy",
                quantity=150,
                price=175.00,
                total_amount=26250.00,
                status="filled",
                executed_at=datetime.utcnow() - timedelta(days=90)
            ),
            Trade(
                portfolio_id=demo_portfolio.id,
                symbol="MSFT",
                side="buy",
                quantity=75,
                price=350.00,
                total_amount=26250.00,
                status="filled",
                executed_at=datetime.utcnow() - timedelta(days=120)
            )
        ]
        for trade in trades:
            session.add(trade)

        # Create financial goals
        goals = [
            Goal(
                user_id=demo_user.id,
                name="Retirement Fund",
                target_amount=1000000.00,
                current_amount=150000.00,
                target_date=datetime.utcnow() + timedelta(days=365*20),
                category="retirement",
                priority="high",
                status="in_progress"
            ),
            Goal(
                user_id=demo_user.id,
                name="Emergency Fund",
                target_amount=50000.00,
                current_amount=25000.00,
                target_date=datetime.utcnow() + timedelta(days=365),
                category="savings",
                priority="high",
                status="in_progress"
            ),
            Goal(
                user_id=demo_user.id,
                name="Vacation Fund",
                target_amount=10000.00,
                current_amount=3500.00,
                target_date=datetime.utcnow() + timedelta(days=180),
                category="lifestyle",
                priority="medium",
                status="in_progress"
            )
        ]
        for goal in goals:
            session.add(goal)

        await session.commit()

    print("  ✓ Demo user created: demo@apex.local / demo123")
    print("  ✓ Portfolio created with 4 positions (SPY, AAPL, MSFT, NVDA)")
    print("  ✓ 3 historical trades added")
    print("  ✓ 3 financial goals created")
    print("")
    print("🎉 Demo data seeding complete!")


if __name__ == "__main__":
    asyncio.run(seed_demo_data())
