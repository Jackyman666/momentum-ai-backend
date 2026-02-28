from pydantic import BaseModel, Field
from uuid import UUID
from typing import Dict, Any, List, Optional

class GoalContent(BaseModel):
    """Goal content structure"""
    duration: str = Field(..., description="Duration of the goal (e.g., '2 weeks', '3 months')")
    current_situation: str = Field(..., description="User's current situation")
    task: str = Field(..., description="Specific task or objective related to the goal")
    attachment_id: Optional[str] = Field(None, description="Optional attachment ID")


class TaskContent(BaseModel):
    """Task content structure"""
    task_id: UUID = Field(..., description="Unique identifier for the task")
    start_at: str = Field(..., description="Task start date (YYYY-MM-DD)")
    end_at: str = Field(..., description="Task end date (YYYY-MM-DD)")
    title: str = Field(..., description="Task title")
    action_plan: str = Field(..., description="Detailed action plan for the task")
    expected_outcome: str = Field(..., description="Expected outcome after completing the task")
    complete: bool = Field(default=False, description="Task completion status")

class Plan(BaseModel):
    user_id: UUID = Field(..., description="User ID from Supabase SDK")
    goal_id: UUID = Field(..., description="Goal ID generated on frontend")
    goal_content: GoalContent = Field(..., description="Goal details")
    tasks_content: List[TaskContent] = Field(default=[], description="List of tasks, sorted by start_at")