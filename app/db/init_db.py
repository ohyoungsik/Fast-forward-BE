from sqlalchemy.orm import Session

from app.models.user import User


def init_db(db: Session) -> None:
    # Place for initial data seeding (admin user, etc.)
    _ = User

