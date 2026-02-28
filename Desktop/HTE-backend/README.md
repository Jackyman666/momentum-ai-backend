# HTE Backend API

FastAPI backend application for the HTE project with AI-powered goal planning using Server-Sent Events (SSE).

## Features

- 🤖 **AI Goal Planner**: Generate actionable task plans from user requirements using MiniMax LLM
- 📡 **Real-time Updates**: Server-Sent Events (SSE) for live plan generation status
- 📊 **Database Persistence**: Store goals and tasks in Supabase (PostgreSQL)
- 🔄 **Task Management**: Update task completion status and track progress
- 🚀 **Async Operations**: High-performance async API with SQLAlchemy
- ⚡ **Non-blocking**: Plan generation happens in background, API responds immediately

## Architecture

### SSE Flow

1. **Frontend → POST /api/plans/generate**: Submit requirements
2. **Backend responds immediately** with `goal_id` and `stream_url` (202 Accepted)
3. **Frontend → GET /api/plans/stream/{goal_id}**: Connect to SSE stream
4. **Backend processes** plan generation in background:
   - Calls MiniMax LLM
   - Parses response
   - Saves to database
   - Broadcasts real-time updates via SSE
5. **Frontend receives** status updates and final plan via SSE events

```
Frontend                    Backend                     LLM
   |                           |                         |
   |-- POST requirements ------>|                         |
   |<--- 202 + goal_id ---------|                         |
   |                           |                         |
   |-- GET stream/{goal_id} --->|                         |
   |<--- SSE: "processing" -----|---- Call LLM ---------->|
   |<--- SSE: "parsing" --------|<--- JSON plan ---------|
   |<--- SSE: "saving" ---------|---- Save to DB -------->|
   |<--- SSE: "completed" ------|                         |
   |    + full plan JSON        |                         |
   X (close connection)         |                         |
```

## Setup

### 1. Prerequisites

- Python 3.9+
- Supabase account (for database)
- MiniMax API key (for LLM)

### 2. Activate virtual environment

```bash
source venv/bin/activate  # On macOS/Linux
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Copy the example environment file and update with your credentials:

```bash
cp .env.example .env
```

Edit `.env` and configure:

```env
# Database (Supabase)
DATABASE_URL=postgresql+asyncpg://postgres.[ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres

# MiniMax LLM API
MINIMAX_API_KEY=your_minimax_api_key_here
MINIMAX_API_URL=https://api.minimax.chat/v1/text/chatcompletion_v2
```

**Getting Supabase Connection String:**
1. Go to your Supabase Dashboard
2. Navigate to: Settings → Database → Connection string
3. Select "URI" mode and "Transaction" pooler
4. Copy the connection string and replace `[password]` with your database password
5. Change `postgresql://` to `postgresql+asyncpg://` (required for async driver)

**Getting MiniMax API Key:**
1. Sign up at https://www.minimaxi.com/
2. Navigate to API settings in your dashboard
3. Generate a new API key
4. Copy and paste into `.env` file

### 5. Set Up Database Tables

Create the following tables in Supabase SQL Editor:

```sql
-- User Profile Table
CREATE TABLE user_profile (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_name VARCHAR NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

-- Goal Table
CREATE TABLE goal (
    goal_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES user_profile(user_id) ON DELETE CASCADE,
    title VARCHAR NOT NULL,
    description TEXT,
    requirements JSONB,
    status VARCHAR NOT NULL DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

-- Task Table
CREATE TABLE task (
    task_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    goal_id UUID NOT NULL REFERENCES goal(goal_id) ON DELETE CASCADE,
    title VARCHAR NOT NULL,
    start_at DATE,
    end_at DATE,
    complete BOOLEAN NOT NULL DEFAULT FALSE
);

-- Create indexes for better query performance
CREATE INDEX idx_goal_user_id ON goal(user_id);
CREATE INDEX idx_goal_status ON goal(status);
CREATE INDEX idx_task_goal_id ON task(goal_id);
CREATE INDEX idx_task_complete ON task(complete);

-- Create updated_at trigger for goal table
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_goal_updated_at BEFORE UPDATE ON goal
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_profile_updated_at BEFORE UPDATE ON user_profile
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

### 6. Run the development server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 7. Access the API

- API: http://localhost:8000
- Interactive API docs: http://localhost:8000/docs
- Alternative API docs: http://localhost:8000/redoc

## API Endpoints

### AI Planner Endpoints (SSE-based)

#### 1. Start Plan Generation

**POST** `/api/plans/generate`

Submit requirements and start background plan generation. Returns immediately.

**Request Body:**
```json
{
  "user_id": "123e4567-e89b-12d3-a456-426614174000",
  "requirements": {
    "goal": "Learn Python programming",
    "timeline": "3 months",
    "skill_level": "beginner",
    "daily_hours": 2
  }
}
```

**Response (202 Accepted):**
```json
{
  "success": true,
  "message": "Plan generation started. Connect to stream_url for updates.",
  "goal_id": "456e7890-e89b-12d3-a456-426614174001",
  "stream_url": "http://localhost:8000/api/plans/stream/456e7890-e89b-12d3-a456-426614174001"
}
```

#### 2. Stream Plan Generation Updates (SSE)

**GET** `/api/plans/stream/{goal_id}`

Server-Sent Events endpoint for real-time plan generation updates.

**SSE Events:**

**Event: `status`** - Processing status update
```json
{
  "status": "processing",
  "message": "Generating plan with AI...",
  "timestamp": "2026-02-28T10:00:05Z"
}
```

**Event: `completed`** - Plan generation completed
```json
{
  "goal_id": "456e7890-e89b-12d3-a456-426614174001",
  "user_id": "123e4567-e89b-12d3-a456-426614174000",
  "title": "Master Python Programming Fundamentals",
  "description": "A comprehensive 3-month plan to learn Python from scratch",
  "requirements": { /* original requirements */ },
  "status": "active",
  "tasks": [
    {
      "task_id": "789e0123-e89b-12d3-a456-426614174002",
      "title": "Set up Python development environment",
      "start_at": "2026-03-01",
      "end_at": "2026-03-03",
      "complete": false
    },
    {
      "task_id": "012e3456-e89b-12d3-a456-426614174003",
      "title": "Learn Python basics: variables, data types, operators",
      "start_at": "2026-03-04",
      "end_at": "2026-03-10",
      "complete": false
    }
    // ... more tasks
  ]
}
```

**Event: `error`** - Plan generation failed
```json
{
  "error": "Failed to generate plan: connection timeout",
  "timestamp": "2026-02-28T10:00:30Z"
}
```

**JavaScript Example:**
```javascript
// Step 1: Start plan generation
const response = await fetch('http://localhost:8000/api/plans/generate', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    user_id: 'your-user-id',
    requirements: {
      goal: 'Learn Python',
      timeline: '2 weeks',
      skill_level: 'beginner',
      daily_hours: 2
    }
  })
});

const { goal_id } = await response.json();

// Step 2: Connect to SSE stream
const eventSource = new EventSource(`http://localhost:8000/api/plans/stream/${goal_id}`);

eventSource.addEventListener('status', (e) => {
  const data = JSON.parse(e.data);
  console.log('Status:', data.message);
});

eventSource.addEventListener('completed', (e) => {
  const plan = JSON.parse(e.data);
  console.log('Plan ready:', plan);
  eventSource.close();
});

eventSource.addEventListener('error', (e) => {
  const error = JSON.parse(e.data);
  console.error('Error:', error.error);
  eventSource.close();
});
```

#### 3. Update Task

**PATCH** `/api/tasks/{task_id}`

Update a task's completion status or other fields.

**Request Body (all fields optional):**
```json
{
  "complete": true,
  "title": "Updated task title",
  "start_at": "2026-03-05",
  "end_at": "2026-03-12"
}
```

**Response:**
```json
{
  "task_id": "789e0123-e89b-12d3-a456-426614174002",
  "goal_id": "456e7890-e89b-12d3-a456-426614174001",
  "title": "Updated task title",
  "start_at": "2026-03-05",
  "end_at": "2026-03-12",
  "complete": true
}
```

## Testing

### 1. Test MiniMax LLM Integration

```bash
python test_minimax.py
```

### 2. Test SSE Plan Generation (Python)

```bash
python test_sse.py
```

### 3. Test SSE in Browser

Open `demo_sse.html` in your browser (make sure server is running):

```bash
# Start server
uvicorn app.main:app --reload

# Open demo_sse.html in your browser
open demo_sse.html  # macOS
```

## Project Structure

```
HTE-backend/
├── app/
│   ├── __init__.py
│   ├── main.py               # FastAPI application entry point
│   ├── config.py             # Configuration management
│   ├── database.py           # Database connection and session
│   ├── routers/              # API route handlers
│   │   ├── __init__.py
│   │   └── planner.py        # SSE-based planner endpoints
│   ├── models/               # SQLAlchemy database models
│   │   ├── __init__.py
│   │   ├── user.py           # UserProfile model
│   │   ├── goal.py           # Goal model
│   │   └── task.py           # Task model
│   ├── schemas/              # Pydantic schemas for validation
│   │   ├── __init__.py
│   │   ├── goal.py           # Goal schemas (minimal)
│   │   ├── task.py           # Task schemas
│   │   └── plan.py           # Plan generation schemas
│   └── services/             # Business logic
│       ├── __init__.py
│       ├── llm_service.py    # MiniMax LLM integration
│       ├── prompts.py        # LLM prompt templates
│       ├── plan_service.py   # Plan generation logic
│       └── task_manager.py   # Background task manager for SSE
├── venv/                     # Virtual environment
├── test_minimax.py           # Test MiniMax LLM connection
├── test_sse.py               # Test SSE plan generation (Python)
├── demo_sse.html             # Demo SSE in browser (JavaScript)
├── requirements.txt          # Python dependencies
├── .env                      # Environment variables (NOT in git)
├── .env.example              # Example environment variables
├── .gitignore
└── README.md
```

## Database Schema

### Tables

**user_profile**
- `user_id` (UUID, PK): Unique user identifier
- `user_name` (VARCHAR): User's name
- `created_at` (TIMESTAMP): Account creation timestamp
- `updated_at` (TIMESTAMP): Last update timestamp

**goal**
- `goal_id` (UUID, PK): Unique goal identifier
- `user_id` (UUID, FK): Reference to user_profile
- `title` (VARCHAR): Goal title
- `description` (TEXT): Detailed goal description
- `requirements` (JSONB): Original requirements JSON
- `status` (VARCHAR): Goal status (active/completed/archived)
- `created_at` (TIMESTAMP): Goal creation timestamp
- `updated_at` (TIMESTAMP): Last update timestamp

**task**
- `task_id` (UUID, PK): Unique task identifier
- `goal_id` (UUID, FK): Reference to goal
- `title` (VARCHAR): Task title
- `start_at` (DATE): Task start date
- `end_at` (DATE): Task end date
- `complete` (BOOLEAN): Completion status

### Relationships

- `user_profile` → `goal`: One-to-many (one user has many goals)
- `goal` → `task`: One-to-many (one goal has many tasks)

## Development

### Adding New Features

1. **Add new API routes**: Create/update files in `app/routers/`
2. **Define data models**: Add SQLAlchemy models in `app/models/`
3. **Create schemas**: Add Pydantic schemas in `app/schemas/`
4. **Implement logic**: Add business logic in `app/services/`

### Testing with cURL

```bash
# Generate a plan
curl -X POST "http://localhost:8000/api/plans/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "123e4567-e89b-12d3-a456-426614174000",
    "requirements": {
      "goal": "Learn Python",
      "timeline": "3 months"
    }
  }'

# Get a goal
curl "http://localhost:8000/api/goals/{goal_id}"

# Update a task
curl -X PATCH "http://localhost:8000/api/tasks/{task_id}" \
  -H "Content-Type: application/json" \
  -d '{"complete": true}'
```

## Troubleshooting

### Database Connection Issues

- Verify your Supabase connection string in `.env`
- Ensure you're using `postgresql+asyncpg://` (not just `postgresql://`)
- Check that your Supabase project is active and not paused
- Verify the database password is correct

### MiniMax API Issues

- Verify your API key is correct and active
- Check your MiniMax account has available credits
- Ensure the API URL is correct
- Review API rate limits

### Import Errors

```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

## License

[Your License]

