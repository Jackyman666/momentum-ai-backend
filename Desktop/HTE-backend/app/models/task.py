from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Date
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from app.database import Base


class Task(Base):
    """Task model representing individual steps in a goal"""
    
    __tablename__ = "task"
    
    task_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    goal_id = Column(UUID(as_uuid=True), ForeignKey("goal.goal_id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String, nullable=False)
    start_at = Column(Date, nullable=True)
    end_at = Column(Date, nullable=True)
    complete = Column(Boolean, default=False, nullable=False)
    
    # Relationships
    goal = relationship("Goal", back_populates="tasks")
    
    def __repr__(self):
        return f"<Task(task_id={self.task_id}, title={self.title}, complete={self.complete})>"
