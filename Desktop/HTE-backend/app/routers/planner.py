from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse
from uuid import UUID
from typing import AsyncIterator, Dict, Any, Optional
import json
import asyncio

from app.schemas.plan import Plan
from app.services.plan_service import plan as generate_plan_tasks

router = APIRouter(tags=["planner"])

# Simple in-memory storage for SSE queues
sse_queues: Dict[UUID, list[asyncio.Queue]] = {}

# Store background task results
task_results: Dict[UUID, Dict[str, Any]] = {}


async def _process_plan_in_background(plan: Plan):
    """
    Background task that processes plan generation with LLM.
    Sends updates via SSE to all connected clients.
    """
    goal_id = plan.goal_id
    
    try:
        # Send status update: Processing started
        await _broadcast_to_sse(goal_id, {
            "event": "status",
            "data": {"message": "Starting plan generation with AI..."}
        })
        
        # Call the plan service to generate tasks using LLM
        updated_plan = await generate_plan_tasks(plan)
        
        # Send status update: Generation completed
        await _broadcast_to_sse(goal_id, {
            "event": "status",
            "data": {"message": f"Generated {len(updated_plan.tasks_content)} tasks"}
        })
        
        # Convert Plan object to dict for JSON serialization
        plan_dict = updated_plan.model_dump(mode='json')
        
        # Send completed event with full plan
        result = plan_dict
        await _broadcast_to_sse(goal_id, {
            "event": "completed",
            "data": result
        })
        
        # Store result for late-joining SSE connections
        task_results[goal_id] = result
        
    except Exception as e:
        # Send error event
        error_data = {"error": str(e)}
        await _broadcast_to_sse(goal_id, {
            "event": "error",
            "data": error_data
        })
        
        # Store error result
        task_results[goal_id] = error_data
    
    finally:
        # Cleanup SSE queues after a delay
        await asyncio.sleep(1)
        if goal_id in sse_queues:
            del sse_queues[goal_id]


async def _broadcast_to_sse(goal_id: UUID, message: Dict[str, Any]):
    """
    Broadcast a message to all SSE connections for a given goal_id.
    
    Args:
        goal_id: The goal ID to broadcast to
        message: Dict with 'event' and 'data' keys
    """
    if goal_id not in sse_queues:
        return
    
    # Send message to all connected SSE clients
    for queue in sse_queues[goal_id]:
        await queue.put(message)


@router.post(
    "/plans/generate",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Start plan generation",
    description="Submit plan with goal_content. Returns immediately with goal_id."
)
async def generate_plan(plan: Plan) -> Dict[str, Any]:
    """
    Start async plan generation with AI.
    
    Frontend sends:
    - user_id: UUID from Supabase SDK
    - goal_id: UUID generated on frontend
    - goal_content: {duration, current_situation, attachment_id}
    - tasks_content: [] (empty list - LLM will generate tasks)
    
    Returns immediately with:
    - success: True/False
    - message: Status message
    - goal_id: Track the plan generation
    
    Frontend should then connect to: GET /plans/stream/{goal_id}
    """
    try:
        # Initialize SSE queue list for this goal_id
        sse_queues[plan.goal_id] = []
        
        # Start background processing - LLM generates tasks and sends via SSE
        asyncio.create_task(_process_plan_in_background(plan))
        
        return {
            "success": True,
            "message": "Plan generation started. Connect to /plans/stream/{goal_id} for updates.",
            "goal_id": str(plan.goal_id)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start plan generation: {str(e)}"
        )


@router.get(
    "/plans/stream/{goal_id}",
    summary="Stream plan generation updates",
    description="Server-Sent Events endpoint for real-time plan generation updates"
)
async def stream_plan_updates(goal_id: UUID):
    """
    SSE endpoint for real-time plan generation updates.
    
    Full URL: GET /plans/stream/{goal_id}
    
    Events sent:
    - status: Processing status updates
    - completed: Returns full Plan object as JSON with LLM-generated tasks (connection closes after this)
    - error: Error message if generation fails (connection closes after this)
    
    Completed event returns Plan object:
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
    
    Connect with EventSource in JavaScript:
    ```javascript
    const eventSource = new EventSource(`/plans/stream/${goal_id}`);
    
    eventSource.addEventListener('status', (e) => {
        const data = JSON.parse(e.data);
        console.log('Status:', data.message);
    });
    
    eventSource.addEventListener('completed', (e) => {
        const plan = JSON.parse(e.data);  // Full Plan object
        console.log('Plan ready:', plan);
        console.log('Generated tasks:', plan.tasks_content);
        eventSource.close();
    });
    
    eventSource.addEventListener('error', (e) => {
        const error = JSON.parse(e.data);
        console.error('Error:', error.error);
        eventSource.close();
    });
    ```
    """
    # Check if task exists
    if goal_id not in sse_queues and goal_id not in task_results:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plan generation task for goal {goal_id} not found"
        )
    
    async def event_generator() -> AsyncIterator[str]:
        """Generate SSE events"""
        # Create a queue for this SSE connection
        queue: asyncio.Queue = asyncio.Queue()
        
        # Check if task already completed
        if goal_id in task_results:
            result = task_results[goal_id]
            if "error" in result:
                yield f"event: error\ndata: {json.dumps(result)}\n\n"
            else:
                yield f"event: completed\ndata: {json.dumps(result)}\n\n"
            return
        
        # Register this queue to receive updates
        if goal_id in sse_queues:
            sse_queues[goal_id].append(queue)
        
        try:
            # Stream updates as they come
            while True:
                try:
                    # Wait for message with timeout
                    message = await asyncio.wait_for(queue.get(), timeout=30.0)
                    
                    event = message.get("event")
                    data = message.get("data")
                    
                    # Send SSE message
                    yield f"event: {event}\ndata: {json.dumps(data)}\n\n"
                    
                    # Close connection after completed or error event
                    if event in ["completed", "error"]:
                        break
                        
                except asyncio.TimeoutError:
                    # Send keepalive ping every 30 seconds
                    yield f": keepalive\n\n"
                    
        finally:
            # Cleanup: remove queue from list
            if goal_id in sse_queues and queue in sse_queues[goal_id]:
                sse_queues[goal_id].remove(queue)
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )