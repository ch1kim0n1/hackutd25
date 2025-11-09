# backend/services/dao/goal_dao.py
"""
Data Access Object for Goal model.
Handles all database operations for financial goals.
"""
from typing import Optional, List
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from ...models.goal import Goal


class GoalDAO:
    """Goal Data Access Object"""

    @staticmethod
    async def create(
        db: AsyncSession,
        user_id: str,
        name: str,
        target_amount: Decimal,
        target_date: date,
        **kwargs
    ) -> Goal:
        """Create a new goal"""
        # Calculate years to goal
        years_to_goal = (target_date - date.today()).days / 365.25

        goal = Goal(
            user_id=user_id,
            name=name,
            target_amount=target_amount,
            target_date=target_date,
            years_to_goal=int(years_to_goal),
            **kwargs
        )
        db.add(goal)
        await db.commit()
        await db.refresh(goal)
        return goal

    @staticmethod
    async def get_by_id(db: AsyncSession, goal_id: str) -> Optional[Goal]:
        """Get goal by ID"""
        result = await db.execute(select(Goal).where(Goal.id == goal_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_user(db: AsyncSession, user_id: str) -> List[Goal]:
        """Get all goals for a user"""
        result = await db.execute(
            select(Goal).where(Goal.user_id == user_id).order_by(Goal.created_at.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_by_user_and_status(db: AsyncSession, user_id: str, status: str) -> List[Goal]:
        """Get goals by user and status"""
        result = await db.execute(
            select(Goal).where(
                Goal.user_id == user_id,
                Goal.status == status
            ).order_by(Goal.created_at.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_active_by_user(db: AsyncSession, user_id: str) -> List[Goal]:
        """Get active goals for a user"""
        result = await db.execute(
            select(Goal).where(
                Goal.user_id == user_id,
                Goal.status == "active",
                Goal.is_active == 1
            ).order_by(Goal.target_date.asc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_by_type(db: AsyncSession, user_id: str, goal_type: str) -> List[Goal]:
        """Get goals by type for a user"""
        result = await db.execute(
            select(Goal).where(
                Goal.user_id == user_id,
                Goal.goal_type == goal_type
            ).order_by(Goal.created_at.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def update(db: AsyncSession, goal_id: str, user_id: str, **kwargs) -> Optional[Goal]:
        """Update goal with user ownership validation (public API)"""
        # Verify goal belongs to user
        goal = await GoalDAO.get_by_id(db, goal_id)
        if not goal or str(goal.user_id) != str(user_id):
            return None
        
        return await GoalDAO._update_internal(db, goal_id, **kwargs)

    @staticmethod
    async def _update_internal(db: AsyncSession, goal_id: str, **kwargs) -> Optional[Goal]:
        """Internal update without user validation"""
        stmt = (
            update(Goal)
            .where(Goal.id == goal_id)
            .values(**kwargs, updated_at=datetime.utcnow())
            .returning(Goal)
        )
        result = await db.execute(stmt)
        await db.commit()
        return result.scalar_one_or_none()

    @staticmethod
    async def update_progress(
        db: AsyncSession,
        goal_id: str,
        user_id: str,
        current_amount: Decimal
    ) -> Optional[Goal]:
        """Update goal progress"""
        goal = await GoalDAO.get_by_id(db, goal_id)
        if not goal or str(goal.user_id) != str(user_id):
            return None

        progress_pct = (current_amount / goal.target_amount * 100) if goal.target_amount else 0

        return await GoalDAO._update_internal(
            db,
            goal_id,
            current_amount=current_amount,
            progress_percentage=progress_pct
        )

    @staticmethod
    async def update_projections(
        db: AsyncSession,
        goal_id: str,
        conservative: Decimal,
        moderate: Decimal,
        aggressive: Decimal,
        success_probability: float
    ) -> Optional[Goal]:
        """Update goal projections from Risk Agent"""
        return await GoalDAO._update_internal(
            db,
            goal_id,
            conservative_projection=conservative,
            moderate_projection=moderate,
            aggressive_projection=aggressive,
            success_probability=success_probability,
            last_reviewed_at=datetime.utcnow()
        )

    @staticmethod
    async def mark_agent_validated(
        db: AsyncSession,
        goal_id: str,
        strategy_validated: bool = False,
        risk_validated: bool = False,
        notes: str = None
    ) -> Optional[Goal]:
        """Mark goal as validated by agents"""
        update_data = {}
        if strategy_validated:
            update_data["strategy_agent_validated"] = 1
        if risk_validated:
            update_data["risk_agent_validated"] = 1
        if notes:
            update_data["validation_notes"] = notes

        return await GoalDAO._update_internal(db, goal_id, **update_data)

    @staticmethod
    async def add_milestone(
        db: AsyncSession,
        goal_id: str,
        milestone: dict
    ) -> Optional[Goal]:
        """Add a milestone to goal"""
        goal = await GoalDAO.get_by_id(db, goal_id)
        if not goal:
            return None

        milestones = goal.milestones or []
        milestones.append(milestone)

        return await GoalDAO._update_internal(db, goal_id, milestones=milestones)

    @staticmethod
    async def update_milestone(
        db: AsyncSession,
        goal_id: str,
        milestone_index: int,
        achieved: bool
    ) -> Optional[Goal]:
        """Mark a milestone as achieved"""
        goal = await GoalDAO.get_by_id(db, goal_id)
        if not goal or not goal.milestones or milestone_index >= len(goal.milestones):
            return None

        milestones = goal.milestones
        milestones[milestone_index]["achieved"] = achieved
        milestones[milestone_index]["achieved_at"] = datetime.utcnow().isoformat()

        return await GoalDAO._update_internal(db, goal_id, milestones=milestones)

    @staticmethod
    async def mark_achieved(db: AsyncSession, goal_id: str) -> Optional[Goal]:
        """Mark goal as achieved"""
        return await GoalDAO._update_internal(
            db,
            goal_id,
            status="achieved",
            achieved_at=datetime.utcnow(),
            progress_percentage=100.0
        )

    @staticmethod
    async def pause(db: AsyncSession, goal_id: str) -> Optional[Goal]:
        """Pause goal"""
        return await GoalDAO._update_internal(db, goal_id, status="paused")

    @staticmethod
    async def resume(db: AsyncSession, goal_id: str) -> Optional[Goal]:
        """Resume paused goal"""
        return await GoalDAO._update_internal(db, goal_id, status="active")

    @staticmethod
    async def abandon(db: AsyncSession, goal_id: str) -> Optional[Goal]:
        """Mark goal as abandoned"""
        return await GoalDAO._update_internal(db, goal_id, status="abandoned", is_active=0)

    @staticmethod
    async def delete(db: AsyncSession, goal_id: str, user_id: str) -> bool:
        """Delete goal with user ownership validation"""
        goal = await GoalDAO.get_by_id(db, goal_id)
        if not goal or str(goal.user_id) != str(user_id):
            return False
        
        stmt = delete(Goal).where(Goal.id == goal_id)
        result = await db.execute(stmt)
        await db.commit()
        return result.rowcount > 0
