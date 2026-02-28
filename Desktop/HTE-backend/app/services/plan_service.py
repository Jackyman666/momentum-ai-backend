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
    print(f"\n[PLAN SERVICE] Started - Goal ID: {plan.goal_id}")
    
    # Convert goal_content to dict for the prompt
    goal_content_dict = plan.goal_content.model_dump()
    print(f"[PLAN SERVICE] Goal content: {goal_content_dict}")
    
    # Build the prompt
    prompt = build_plan_generation_prompt(goal_content_dict)
    print(f"[PLAN SERVICE] Prompt built, length: {len(prompt)} characters")
    
    # Call LLM to generate tasks
    print(f"[PLAN SERVICE] Calling LLM (MiniMax)...")
    llm_response = await minimax_client.generate_completion(
        prompt=prompt,
        system_prompt=SYSTEM_PROMPT_PLANNER,
        max_tokens=4000
    )
    print(f"[PLAN SERVICE] LLM response received, length: {len(llm_response)} characters")
    
    # Parse the JSON response
    try:
        print(f"[PLAN SERVICE] Parsing LLM response...")
        # Extract JSON array from response (in case there's extra text)
        response_text = llm_response.strip()
        
        # Find JSON array boundaries
        start_idx = response_text.find('[')
        end_idx = response_text.rfind(']') + 1
        
        if start_idx == -1 or end_idx == 0:
            print(f"[PLAN SERVICE] ERROR: No JSON array found in response")
            raise ValueError("No JSON array found in LLM response")
        
        json_str = response_text[start_idx:end_idx]
        print(f"[PLAN SERVICE] Extracted JSON string, length: {len(json_str)} characters")
        
        tasks_data = json.loads(json_str)
        print(f"[PLAN SERVICE] JSON parsed successfully, found {len(tasks_data)} tasks")
        
        # Convert each task dict to TaskContent object
        task_objects: List[TaskContent] = []
        for i, task_dict in enumerate(tasks_data, 1):
            task_content = TaskContent(**task_dict)
            task_objects.append(task_content)
            print(f"[PLAN SERVICE] Task {i}/{len(tasks_data)}: {task_content.title}")
        
        # Append to plan's tasks_content
        plan.tasks_content.extend(task_objects)
        
        # Sort tasks by start_at date
        plan.tasks_content.sort(key=lambda t: t.start_at)
        print(f"[PLAN SERVICE] Tasks sorted by start date")
        
        print(f"[PLAN SERVICE] Completed - Returning plan with {len(plan.tasks_content)} tasks\n")
        return plan
        
    except json.JSONDecodeError as e:
        print(f"[PLAN SERVICE] ERROR: JSON decode failed - {str(e)}")
        raise ValueError(f"Failed to parse LLM response as JSON: {str(e)}")
    except Exception as e:
        print(f"[PLAN SERVICE] ERROR: {str(e)}")
        raise Exception(f"Error processing plan: {str(e)}")