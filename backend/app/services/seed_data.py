"""
Seed data for APEX development and testing.
Initializes demo users, portfolios, and goals.
"""
import uuid
from datetime import datetime, timedelta
from decimal import Decimal

from app.services.db import AsyncSessionLocal
from app.models.user import User
from app.models.portfolio import Portfolio
from app.models.goal import Goal
from app.services.security import PasswordService


async def seed_test_data():
    """
    Seed development database with test users and sample data.
    Only runs if test users don't already exist.
    """
    async with AsyncSessionLocal() as db:
        try:
            # Check if demo user already exists
            from sqlalchemy import select
            result = await db.execute(select(User).filter(User.username == "demo@apex.local"))
            existing_user = result.scalar_one_or_none()
            
            if existing_user:
                # Data already seeded
                return
            
            # Create demo user
            password_service = PasswordService()
            demo_user = User(
                id=uuid.uuid4(),
                username="demo@apex.local",
                email="demo@apex.local",
                hashed_password=password_service.hash_password("demo_password_123"),
                is_active=True,
                is_verified=True,
                first_name="Demo",
                last_name="User",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            db.add(demo_user)
            await db.flush()
            
            # Create demo portfolio
            demo_portfolio = Portfolio(
                id=uuid.uuid4(),
                user_id=demo_user.id,
                name="Demo Portfolio",
                account_number="PA0000001",
                total_value=Decimal("50000.00"),
                cash_balance=Decimal("10000.00"),
                buying_power=Decimal("20000.00"),
                broker_id="alpaca",
                settings={
                    "auto_rebalance": False,
                    "max_position_size": 0.3,
                    "risk_tolerance": "moderate"
                },
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            db.add(demo_portfolio)
            await db.flush()
            
            # Create demo goals
            goal_1 = Goal(
                id=uuid.uuid4(),
                user_id=demo_user.id,
                name="Retirement Fund",
                description="Build a $1M retirement portfolio by age 65",
                target_amount=Decimal("1000000.00"),
                current_amount=Decimal("50000.00"),
                target_date=(datetime.utcnow() + timedelta(days=30*12*25)).date(),  # 25 years from now
                priority="high",
                category="retirement",
                status="active",
                compound_interest_data={
                    "annual_rate": 0.07,
                    "years": 25,
                    "projections": []
                },
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            db.add(goal_1)
            
            goal_2 = Goal(
                id=uuid.uuid4(),
                user_id=demo_user.id,
                name="Home Down Payment",
                description="Save for 20% down payment on primary residence",
                target_amount=Decimal("100000.00"),
                current_amount=Decimal("25000.00"),
                target_date=(datetime.utcnow() + timedelta(days=30*12*3)).date(),  # 3 years from now
                priority="high",
                category="housing",
                status="active",
                compound_interest_data={
                    "annual_rate": 0.03,
                    "years": 3,
                    "projections": []
                },
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            db.add(goal_2)
            
            goal_3 = Goal(
                id=uuid.uuid4(),
                user_id=demo_user.id,
                name="Vacation Fund",
                description="Annual vacation to Europe",
                target_amount=Decimal("10000.00"),
                current_amount=Decimal("5000.00"),
                target_date=(datetime.utcnow() + timedelta(days=30*12*1)).date(),  # 1 year from now
                priority="medium",
                category="travel",
                status="active",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            db.add(goal_3)
            
            # Commit all seed data
            await db.commit()
            
        except Exception as e:
            await db.rollback()
            raise Exception(f"Failed to seed test data: {str(e)}")
