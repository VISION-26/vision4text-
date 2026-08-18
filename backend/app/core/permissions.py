from fastapi import HTTPException, status
from sqlalchemy import Select

from app.models.user import User


def owner_filter(statement: Select, model, current_user: User) -> Select:
    return statement if current_user.role == "Admin" else statement.where(model.user_id == current_user.id)


def require_owner(record, current_user: User):
    if not record or (current_user.role != "Admin" and record.user_id != current_user.id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found.")
    return record
