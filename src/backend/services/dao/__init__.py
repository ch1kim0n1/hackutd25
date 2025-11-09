# backend/services/dao/__init__.py
"""
Data Access Objects for all database models.
"""

from .user_dao import UserDAO
from .portfolio_dao import PortfolioDAO, PositionDAO
from .goal_dao import GoalDAO

__all__ = [
    "UserDAO",
    "PortfolioDAO",
    "PositionDAO",
    "GoalDAO",
]
