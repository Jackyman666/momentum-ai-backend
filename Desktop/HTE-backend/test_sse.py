"""
Test SSE (Server-Sent Events) plan generation
This demonstrates how to use the new SSE-based plan generation API
"""
import asyncio
import httpx
import json
from uuid import uuid4


async def test_sse_plan_generation():
    """Test the complete SSE flow"""
    
    base_url = "http://localhost:8000"
    
    # Step 1: Start plan generation
    print("🚀 Step 1: Starting plan generation...\n")
    
    request_data = {
        "user_id": str(uuid4()),  # Replace with actual user_id from your frontend
        "requirements": {
            "goal": "Learn Python Programming",
            "timeline": "2 weeks",
            "skill_level": "beginner",
            "daily_hours": 2
        }
    }
    
    async with httpx.AsyncClient() as client:
        # POST to start generation
        response = await client.post(
            f"{base_url}/api/plans/generate",
            json=request_data,
            timeout=10.0
        )
        
        if response.status_code != 202:
            print(f"❌ Failed to start generation: {response.text}")
            return
        
        result = response.json()
        print(f"✅ Plan generation started!")
        print(f"   Goal ID: {result['goal_id']}")
        print(f"   Stream URL: {result['stream_url']}\n")
        
        goal_id = result['goal_id']
        
        # Step 2: Connect to SSE stream
        print("📡 Step 2: Connecting to SSE stream for real-time updates...\n")
        
        async with client.stream(
            "GET",
            f"{base_url}/api/plans/stream/{goal_id}",
            timeout=120.0
        ) as stream_response:
            if stream_response.status_code != 200:
                print(f"❌ Failed to connect to stream: {stream_response.text}")
                return
            
            print("✅ Connected to event stream\n")
            print("─" * 60)
            
            async for line in stream_response.aiter_lines():
                line = line.strip()
                
                if not line or line.startswith(":"):
                    # Skip empty lines and keepalive comments
                    continue
                
                if line.startswith("event:"):
                    current_event = line.split(":", 1)[1].strip()
                elif line.startswith("data:"):
                    data = line.split(":", 1)[1].strip()
                    
                    if current_event == "status":
                        status_data = json.loads(data)
                        print(f"📊 Status Update: {status_data['message']}")
                        print(f"   Time: {status_data['timestamp']}\n")
                    
                    elif current_event == "completed":
                        print("\n🎉 Plan Generation Completed!\n")
                        plan = json.loads(data)
                        print(f"Goal: {plan['title']}")
                        print(f"Description: {plan['description']}")
                        print(f"\nTasks ({len(plan['tasks'])}):")
                        for i, task in enumerate(plan['tasks'], 1):
                            print(f"  {i}. {task['title']}")
                            print(f"     📅 {task['start_at']} → {task['end_at']}")
                        print("\n" + "─" * 60)
                        break
                    
                    elif current_event == "error":
                        error_data = json.loads(data)
                        print(f"\n❌ Error: {error_data['error']}\n")
                        print("─" * 60)
                        break
    
    print("\n✅ Test completed!")


async def test_task_update():
    """Test updating a task"""
    print("\n🔧 Testing task update...\n")
    
    base_url = "http://localhost:8000"
    
    # You'll need to replace this with an actual task_id from your database
    task_id = "your-task-uuid-here"
    
    update_data = {
        "complete": True
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.patch(
            f"{base_url}/api/tasks/{task_id}",
            json=update_data
        )
        
        if response.status_code == 200:
            print(f"✅ Task updated: {response.json()}")
        else:
            print(f"❌ Failed: {response.text}")


if __name__ == "__main__":
    print("=" * 60)
    print("SSE Plan Generation Test")
    print("=" * 60)
    print("\n⚠️  Make sure the server is running:")
    print("   uvicorn app.main:app --reload\n")
    print("=" * 60 + "\n")
    
    asyncio.run(test_sse_plan_generation())
    
    # Uncomment to test task update:
    # asyncio.run(test_task_update())
