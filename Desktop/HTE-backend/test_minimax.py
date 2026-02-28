"""
Quick test script for MiniMax LLM integration
Run: python test_minimax.py
"""
import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import only what we need - bypass all schema imports
from app.config import settings
import anthropic


async def test_minimax():
    """Test MiniMax LLM with a simple prompt - no schemas needed"""
    
    print("🧪 Testing MiniMax LLM connection...\n")
    print(f"📍 Base URL: {settings.minimax_api_url}")
    print(f"📍 Model: {settings.minimax_model_M25}\n")
    
    try:
        # Create client directly
        client = anthropic.AsyncAnthropic(
            api_key=settings.minimax_api_key,
            base_url=settings.minimax_api_url
        )
        
        # Simple test prompt
        prompt = "Say hello and introduce yourself in one sentence."
        
        print(f"📤 Sending prompt: {prompt}\n")
        
        # Call MiniMax directly
        message = await client.messages.create(
            model=settings.minimax_model_M25,
            max_tokens=100,
            system="You are a helpful AI assistant.",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }
            ]
        )
        
        # Extract response
        text_content = []
        for block in message.content:
            if block.type == "text":
                text_content.append(block.text)
        
        response = "\n".join(text_content)
        print(f"✅ Success! MiniMax Response:\n{response}\n")
        
        # Test with plan generation prompt
        print("\n🧪 Testing plan generation...\n")
        
        plan_prompt = """Create a simple 3-task plan for learning Python basics.
Return JSON format:
{
  "title": "Learn Python Basics",
  "description": "A beginner plan",
  "tasks": [
    {"title": "Task 1", "start_at": "2026-03-01", "end_at": "2026-03-03"},
    {"title": "Task 2", "start_at": "2026-03-04", "end_at": "2026-03-07"},
    {"title": "Task 3", "start_at": "2026-03-08", "end_at": "2026-03-10"}
  ]
}"""
        
        plan_message = await client.messages.create(
            model=settings.minimax_model_M25,
            max_tokens=1000,
            system="You are a professional goal planning assistant. You help users break down their goals into actionable tasks with realistic timelines.",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": plan_prompt
                        }
                    ]
                }
            ]
        )
        
        # Extract plan response
        plan_text = []
        for block in plan_message.content:
            if block.type == "text":
                plan_text.append(block.text)
        
        plan_response = "\n".join(plan_text)
        print(f"✅ Plan Response:\n{plan_response}\n")
        
    except anthropic.APIError as e:
        print(f"❌ MiniMax API Error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = asyncio.run(test_minimax())
    
    if success:
        print("\n🎉 MiniMax integration is working!")
    else:
        print("\n⚠️  MiniMax test failed. Check your API key and configuration.")

