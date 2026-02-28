from fastapi import APIRouter, HTTPException, status
from typing import Dict, Any

from app.schemas.plan import Plan
from app.services.plan_service import plan as generate_plan_tasks

router = APIRouter(tags=["planner"])


@router.post(
    "/plans/generate",
    status_code=status.HTTP_200_OK,
    summary="Generate plan with AI",
    description="Generate a plan with LLM-generated tasks and return the complete plan as JSON."
)
async def generate_plan(plan: Plan) -> Dict[str, Any]:
    """
    Generate a plan with AI-generated tasks.
    
    Frontend sends:
    - user_id: UUID from Supabase SDK
    - goal_id: UUID generated on frontend
    - goal_content: {duration, current_situation, attachment_id}
    - tasks_content: [] (empty list - LLM will generate tasks)
    
    Returns complete Plan object with generated tasks:
    {
      "user_id": "uuid",
      "goal_id": "uuid",
      "goal_content": {
        "duration": "2 weeks",
        "current_situation": "...",
        "attachment_id": null
      },
      "tasks_content": [
        {
          "task_id": "uuid",
          "start_at": "2026-03-01",
          "end_at": "2026-03-03",
          "title": "Task 1",
          "action_plan": "Detailed plan...",
          "expected_outcome": "Expected result...",
          "complete": false
        }
      ]
    }
    """
    try:
        # Call the plan service to generate tasks using LLM
        updated_plan = await generate_plan_tasks(plan)
        
        # Convert Plan object to dict for JSON serialization
        return updated_plan.model_dump(mode='json')
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate plan: {str(e)}"
        )