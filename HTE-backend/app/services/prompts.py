"""Prompt templates for LLM interactions"""
import json
from typing import Dict, Any


def build_plan_generation_prompt(goal_content: Dict[str, Any]) -> str:
    """
    Build a prompt for generating multiple plans from a goal
    
    Args:
        goal_content: Dictionary containing the goal information
        
    Returns:
        Formatted prompt string for the LLM
    """
    prompt = f"""Based on the following goal, create multiple actionable plans to achieve it.

Goal Information:
{json.dumps(goal_content, indent=2)}

Please generate 3-5 different plans that approach this goal from different angles or break it down in different ways. Each plan should contain 5-10 actionable tasks.

For each plan, provide:
1. A unique title that describes the approach
2. A brief description of what this plan will achieve
3. A list of tasks, where each task has:
   - A clear, specific title (what needs to be done)
   - A start date (when to begin this task - format: YYYY-MM-DD)
   - An end date (estimated completion date - format: YYYY-MM-DD)

Return your response as a JSON array with this exact structure:
[
  {{task_id: UUID = Field(..., description="Unique identifier for the task")
    start_at: str = Field(..., description="Task start date (YYYY-MM-DD)")
    end_at: str = Field(..., description="Task end date (YYYY-MM-DD)")
    title: str = Field(..., description="Task title")
    action_plan: str = Field(..., description="Detailed action plan for the task")
    expected_outcome: str = Field(..., description="Expected outcome after completing the task")
    complete: bool = Field(default=False, description="Task completion status")}}, ... more tasks ...
]

IMPORTANT: 
- Return ONLY a valid JSON array, no additional text
- Ensure start_at comes before end_at for each task
- Make the timelines realistic based on the goal
- Tasks within each plan should be ordered logically from first to last
- Each plan should offer a distinct approach or breakdown of the goal
"""
    return prompt


# System prompts for different LLM interactions
SYSTEM_PROMPT_PLANNER = "You are a professional goal planning assistant. You help users break down their goals into multiple actionable plans with realistic timelines. You provide diverse approaches to achieve the same goal."