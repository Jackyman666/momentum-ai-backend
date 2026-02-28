import json
from typing import List
from app.schemas.plan import Plan, TaskContent
from app.services.llm_service import minimax_client
from app.services.prompts import build_plan_generation_prompt, SYSTEM_PROMPT_PLANNER


async def plan(plan: Plan) -> Plan:
    """
    Generate tasks for a plan based on the goal content using LLM
    
    Args:
        plan: Plan object containing goal_content
        
    Returns:
        Updated Plan object with tasks_content populated
    """
    # Convert goal_content to dict for the prompt
    goal_content_dict = plan.goal_content.model_dump()
    
    # Build the prompt
    prompt = build_plan_generation_prompt(goal_content_dict)
    
    # Call LLM to generate tasks
    llm_response = await minimax_client.generate_completion(
        prompt=prompt,
        system_prompt=SYSTEM_PROMPT_PLANNER,
        max_tokens=4000
    )
    
    # Parse the JSON response
    try:
        # Extract JSON array from response (in case there's extra text)
        response_text = llm_response.strip()
        
        # Find JSON array boundaries
        start_idx = response_text.find('[')
        end_idx = response_text.rfind(']') + 1
        
        if start_idx == -1 or end_idx == 0:
            raise ValueError("No JSON array found in LLM response")
        
        json_str = response_text[start_idx:end_idx]
        tasks_data = json.loads(json_str)
        
        # Convert each task dict to TaskContent object
        task_objects: List[TaskContent] = []
        for task_dict in tasks_data:
            task_content = TaskContent(**task_dict)
            task_objects.append(task_content)
        
        # Append to plan's tasks_content
        plan.tasks_content.extend(task_objects)
        
        # Sort tasks by start_at date
        plan.tasks_content.sort(key=lambda t: t.start_at)
        
        return plan
        
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse LLM response as JSON: {str(e)}")
    except Exception as e:
        raise Exception(f"Error processing plan: {str(e)}")