from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime

from app.core.database import Base


class Log(Base):
    __tablename__ = "logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    level = Column(String(50), nullable=False, default="INFO")
    message = Column(Text, nullable=False)
    module = Column(String(255), nullable=True, default="system")
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<Log(id={self.id}, level='{self.level}', module='{self.module}')>"
