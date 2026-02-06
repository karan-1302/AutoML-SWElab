# lab8/backend/dal/repositories/user_repository.py
# ─────────────────────────────────────────────────────────────
# Data Access Layer — User Repository
#
# Provides CRUD operations for the `users` table.
# All database interaction for users is centralised here,
# keeping the BLL free of SQL or ORM concerns.
# ─────────────────────────────────────────────────────────────

from typing import Optional, List
from sqlalchemy.orm import Session

from dal.db_models import User


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """
    Retrieve a user by their email address.

    Parameters
    ----------
    db : Session
        Active SQLAlchemy session.
    email : str
        Email address to look up (case-insensitive).

    Returns
    -------
    User or None
    """
    return db.query(User).filter(User.email == email.lower()).first()


def get_user_by_id(db: Session, user_id: str) -> Optional[User]:
    """
    Retrieve a user by their unique user_id.

    Parameters
    ----------
    db : Session
        Active SQLAlchemy session.
    user_id : str
        The unique user identifier.

    Returns
    -------
    User or None
    """
    return db.query(User).filter(User.user_id == user_id).first()


def create_user(
    db: Session,
    user_id: str,
    email: str,
    full_name: str,
    hashed_password: str,
) -> User:
    """
    Insert a new user into the database.

    Parameters
    ----------
    db : Session
        Active SQLAlchemy session.
    user_id, email, full_name, hashed_password : str
        User attributes.

    Returns
    -------
    User
        The newly created user record.
    """
    user = User(
        user_id=user_id,
        email=email.lower(),
        full_name=full_name,
        hashed_password=hashed_password,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_all_users(db: Session) -> List[User]:
    """Return all registered users."""
    return db.query(User).all()


def delete_user(db: Session, user_id: str) -> bool:
    """
    Delete a user by user_id.

    Returns True if a user was deleted, False if not found.
    """
    user = db.query(User).filter(User.user_id == user_id).first()
    if user:
        db.delete(user)
        db.commit()
        return True
    return False
