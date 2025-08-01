from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
import uuid
from datetime import datetime, timedelta
from passlib.context import CryptContext
import jwt
from email_validator import validate_email, EmailNotValidError
import secrets


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI(title="Manifest 12 API", description="12-Week Goal Manifestation Platform")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Security configuration
SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-here-change-in-production')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# Authentication Models
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    
class UserLogin(BaseModel):
    email: EmailStr
    password: str

class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    full_name: str
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    is_active: bool
    created_at: datetime

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

# 12-Week Cycle Models
class CycleCreate(BaseModel):
    title: str
    description: str
    law_of_attraction_statement: str
    start_date: datetime = Field(default_factory=datetime.utcnow)

class Cycle(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    title: str
    description: str
    start_date: datetime
    end_date: datetime
    status: str = "active"  # active, completed, paused, archived
    current_week: int = 1
    law_of_attraction_statement: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

# Goal Models
class Milestone(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    completed: bool = False
    completed_date: Optional[datetime] = None

class GoalCreate(BaseModel):
    cycle_id: str
    title: str
    description: str
    category: str
    start_week: int = 1
    target_week: int = 12
    why_statement: str  # Law of Attraction "why"
    visualization_note: str  # Neville Goddard visualization
    milestones: List[Milestone] = []

class Goal(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    cycle_id: str
    user_id: str
    title: str
    description: str
    category: str
    start_week: int = 1
    target_week: int = 12
    progress: int = 0  # 0-100
    status: str = "not_started"  # not_started, in_progress, completed, on_hold
    why_statement: str  # Law of Attraction
    visualization_note: str  # Neville Goddard
    milestones: List[Milestone] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class GoalUpdate(BaseModel):
    progress: Optional[int] = None
    status: Optional[str] = None
    milestones: Optional[List[Milestone]] = None

# Weekly Reflection Models  
class WeeklyReflectionCreate(BaseModel):
    cycle_id: str
    week_number: int
    progress_review: str
    law_of_attraction_manifestations: List[str] = []
    neville_goddard_practice: str
    challenges: str
    insights: str
    next_week_focus: List[str] = []
    mood_rating: int = 5  # 1-10 scale

class WeeklyReflection(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    cycle_id: str
    user_id: str
    week_number: int
    week_start_date: datetime
    progress_review: str
    law_of_attraction_manifestations: List[str] = []
    neville_goddard_practice: str
    challenges: str
    insights: str
    next_week_focus: List[str] = []
    mood_rating: int = 5
    created_at: datetime = Field(default_factory=datetime.utcnow)

# Password Reset Models
class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str

class PasswordResetToken(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    token: str
    expires_at: datetime
    used: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)

# Enhanced Analytics Models
class GoalProgressSnapshot(BaseModel):
    date: datetime
    progress: int
    notes: str = ""

class GoalProgressHistory(BaseModel):
    goal_id: str
    snapshots: List[GoalProgressSnapshot] = []

class CycleAnalytics(BaseModel):
    cycle_id: str
    completion_rate: float
    goals_completed: int
    goals_total: int
    average_mood: float
    manifestation_count: int
    weeks_completed: int
    start_date: datetime
    current_week: int

class DashboardAnalytics(BaseModel):
    total_cycles: int
    active_cycles: int
    completed_cycles: int
    total_goals: int
    completed_goals: int
    average_completion_rate: float
    recent_manifestations: List[str] = []
    mood_trend: List[int] = []

# Enhanced Models
class GoalProgressUpdate(BaseModel):
    progress: int
    notes: str = ""
    milestone_updates: Optional[List[Milestone]] = None

class CycleComplete(BaseModel):
    completion_notes: str
    success_story: str = ""
    overall_satisfaction: int = 5  # 1-10 scale
class CycleUpdate(BaseModel):
    current_week: Optional[int] = None
    status: Optional[str] = None
    law_of_attraction_statement: Optional[str] = None
class StatusCheck(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class StatusCheckCreate(BaseModel):
    client_name: str

# Authentication helper functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception
    
    user = await db.users.find_one({"id": user_id})
    if user is None:
        raise credentials_exception
    return User(**user)

# Authentication Routes
@api_router.post("/auth/register", response_model=Token)
async def register(user_data: UserCreate):
    # Check if user already exists
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    user = User(
        email=user_data.email,
        full_name=user_data.full_name
    )
    
    user_dict = user.dict()
    user_dict["password_hash"] = hashed_password
    
    await db.users.insert_one(user_dict)
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.id}, expires_delta=access_token_expires
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse(**user.dict())
    )

@api_router.post("/auth/login", response_model=Token)
async def login(user_data: UserLogin):
    user = await db.users.find_one({"email": user_data.email})
    if not user or not verify_password(user_data.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["id"]}, expires_delta=access_token_expires
    )
    
    user_response = UserResponse(**user)
    return Token(
        access_token=access_token,
        token_type="bearer",
        user=user_response
    )

@api_router.get("/auth/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    return UserResponse(**current_user.dict())

# Password Reset Routes
@api_router.post("/auth/forgot-password")
async def forgot_password(request: PasswordResetRequest):
    user = await db.users.find_one({"email": request.email})
    if not user:
        # For security, don't reveal if email exists or not
        return {"message": "If the email exists, a password reset token will be provided"}
    
    # Generate secure reset token
    reset_token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(hours=1)  # Token expires in 1 hour
    
    # Store reset token
    password_reset = PasswordResetToken(
        user_id=user["id"],
        token=reset_token,
        expires_at=expires_at
    )
    
    await db.password_reset_tokens.insert_one(password_reset.dict())
    
    # In a real application, you would send this token via email
    # For development, we'll return it in the response
    return {
        "message": "Password reset token generated",
        "reset_token": reset_token,  # Remove this in production
        "expires_in_minutes": 60
    }

@api_router.post("/auth/reset-password")
async def reset_password(request: PasswordResetConfirm):
    # Find valid reset token
    reset_token_doc = await db.password_reset_tokens.find_one({
        "token": request.token,
        "used": False,
        "expires_at": {"$gt": datetime.utcnow()}
    })
    
    if not reset_token_doc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    
    # Validate new password
    if len(request.new_password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 6 characters long"
        )
    
    # Update user password
    new_password_hash = get_password_hash(request.new_password)
    await db.users.update_one(
        {"id": reset_token_doc["user_id"]},
        {"$set": {"password_hash": new_password_hash, "updated_at": datetime.utcnow()}}
    )
    
    # Mark token as used
    await db.password_reset_tokens.update_one(
        {"id": reset_token_doc["id"]},
        {"$set": {"used": True, "updated_at": datetime.utcnow()}}
    )
    
    return {"message": "Password reset successful"}

@api_router.post("/auth/validate-reset-token")
async def validate_reset_token(token: str):
    """Validate if a reset token is still valid"""
    reset_token_doc = await db.password_reset_tokens.find_one({
        "token": token,
        "used": False,
        "expires_at": {"$gt": datetime.utcnow()}
    })
    
    if not reset_token_doc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    
    return {"valid": True, "expires_at": reset_token_doc["expires_at"]}

# Cycle Management Routes
@api_router.post("/cycles", response_model=Cycle)
async def create_cycle(cycle_data: CycleCreate, current_user: User = Depends(get_current_user)):
    cycle = Cycle(
        user_id=current_user.id,
        title=cycle_data.title,
        description=cycle_data.description,
        start_date=cycle_data.start_date,
        end_date=cycle_data.start_date + timedelta(weeks=12),
        law_of_attraction_statement=cycle_data.law_of_attraction_statement
    )
    
    await db.cycles.insert_one(cycle.dict())
    return cycle

@api_router.get("/cycles", response_model=List[Cycle])
async def get_user_cycles(current_user: User = Depends(get_current_user)):
    cycles = await db.cycles.find({"user_id": current_user.id}).to_list(1000)
    return [Cycle(**cycle) for cycle in cycles]

@api_router.get("/cycles/{cycle_id}", response_model=Cycle)
async def get_cycle(cycle_id: str, current_user: User = Depends(get_current_user)):
    cycle = await db.cycles.find_one({"id": cycle_id, "user_id": current_user.id})
    if not cycle:
        raise HTTPException(status_code=404, detail="Cycle not found")
    return Cycle(**cycle)

@api_router.put("/cycles/{cycle_id}", response_model=Cycle)
async def update_cycle(cycle_id: str, cycle_update: CycleUpdate, current_user: User = Depends(get_current_user)):
    cycle = await db.cycles.find_one({"id": cycle_id, "user_id": current_user.id})
    if not cycle:
        raise HTTPException(status_code=404, detail="Cycle not found")
    
    update_data = cycle_update.dict(exclude_unset=True)
    update_data["updated_at"] = datetime.utcnow()
    
    await db.cycles.update_one(
        {"id": cycle_id, "user_id": current_user.id},
        {"$set": update_data}
    )
    
    updated_cycle = await db.cycles.find_one({"id": cycle_id, "user_id": current_user.id})
    return Cycle(**updated_cycle)

# Goal Management Routes
@api_router.post("/goals", response_model=Goal)
async def create_goal(goal_data: GoalCreate, current_user: User = Depends(get_current_user)):
    # Verify cycle belongs to user
    cycle = await db.cycles.find_one({"id": goal_data.cycle_id, "user_id": current_user.id})
    if not cycle:
        raise HTTPException(status_code=404, detail="Cycle not found")
    
    goal = Goal(
        cycle_id=goal_data.cycle_id,
        user_id=current_user.id,
        title=goal_data.title,
        description=goal_data.description,
        category=goal_data.category,
        start_week=goal_data.start_week,
        target_week=goal_data.target_week,
        why_statement=goal_data.why_statement,
        visualization_note=goal_data.visualization_note,
        milestones=goal_data.milestones
    )
    
    await db.goals.insert_one(goal.dict())
    return goal

@api_router.get("/goals", response_model=List[Goal])
async def get_user_goals(cycle_id: str = None, current_user: User = Depends(get_current_user)):
    query = {"user_id": current_user.id}
    if cycle_id:
        query["cycle_id"] = cycle_id
    
    goals = await db.goals.find(query).to_list(1000)
    return [Goal(**goal) for goal in goals]

@api_router.get("/goals/{goal_id}", response_model=Goal)
async def get_goal(goal_id: str, current_user: User = Depends(get_current_user)):
    goal = await db.goals.find_one({"id": goal_id, "user_id": current_user.id})
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    return Goal(**goal)

@api_router.put("/goals/{goal_id}", response_model=Goal)
async def update_goal(goal_id: str, goal_update: GoalUpdate, current_user: User = Depends(get_current_user)):
    goal = await db.goals.find_one({"id": goal_id, "user_id": current_user.id})
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    
    update_data = goal_update.dict(exclude_unset=True)
    update_data["updated_at"] = datetime.utcnow()
    
    await db.goals.update_one(
        {"id": goal_id, "user_id": current_user.id},
        {"$set": update_data}
    )
    
    updated_goal = await db.goals.find_one({"id": goal_id, "user_id": current_user.id})
    return Goal(**updated_goal)

# Weekly Reflection Routes
@api_router.post("/reflections", response_model=WeeklyReflection)
async def create_reflection(reflection_data: WeeklyReflectionCreate, current_user: User = Depends(get_current_user)):
    # Verify cycle belongs to user
    cycle = await db.cycles.find_one({"id": reflection_data.cycle_id, "user_id": current_user.id})
    if not cycle:
        raise HTTPException(status_code=404, detail="Cycle not found")
    
    # Calculate week start date based on cycle start date and week number
    cycle_start = cycle["start_date"]
    week_start_date = cycle_start + timedelta(weeks=reflection_data.week_number - 1)
    
    reflection = WeeklyReflection(
        cycle_id=reflection_data.cycle_id,
        user_id=current_user.id,
        week_number=reflection_data.week_number,
        week_start_date=week_start_date,
        progress_review=reflection_data.progress_review,
        law_of_attraction_manifestations=reflection_data.law_of_attraction_manifestations,
        neville_goddard_practice=reflection_data.neville_goddard_practice,
        challenges=reflection_data.challenges,
        insights=reflection_data.insights,
        next_week_focus=reflection_data.next_week_focus,
        mood_rating=reflection_data.mood_rating
    )
    
    await db.reflections.insert_one(reflection.dict())
    return reflection

@api_router.get("/reflections", response_model=List[WeeklyReflection])
async def get_reflections(cycle_id: str = None, current_user: User = Depends(get_current_user)):
    query = {"user_id": current_user.id}
    if cycle_id:
        query["cycle_id"] = cycle_id
    
    reflections = await db.reflections.find(query).sort("week_number", 1).to_list(1000)
    return [WeeklyReflection(**reflection) for reflection in reflections]

@api_router.get("/reflections/{reflection_id}", response_model=WeeklyReflection)
async def get_reflection(reflection_id: str, current_user: User = Depends(get_current_user)):
    reflection = await db.reflections.find_one({"id": reflection_id, "user_id": current_user.id})
    if not reflection:
        raise HTTPException(status_code=404, detail="Reflection not found")
    return WeeklyReflection(**reflection)

# Enhanced Goal Analytics Routes
@api_router.post("/goals/{goal_id}/progress", response_model=Goal)
async def update_goal_progress(goal_id: str, progress_update: GoalProgressUpdate, current_user: User = Depends(get_current_user)):
    goal = await db.goals.find_one({"id": goal_id, "user_id": current_user.id})
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    
    # Create progress snapshot
    snapshot = GoalProgressSnapshot(
        date=datetime.utcnow(),
        progress=progress_update.progress,
        notes=progress_update.notes
    )
    
    # Update goal progress
    update_data = {
        "progress": progress_update.progress,
        "updated_at": datetime.utcnow()
    }
    
    if progress_update.milestone_updates:
        update_data["milestones"] = [m.dict() for m in progress_update.milestone_updates]
    
    if progress_update.progress >= 100:
        update_data["status"] = "completed"
    elif progress_update.progress > 0:
        update_data["status"] = "in_progress"
    
    # Store progress history
    history_doc = await db.goal_progress_history.find_one({"goal_id": goal_id})
    if history_doc:
        await db.goal_progress_history.update_one(
            {"goal_id": goal_id},
            {"$push": {"snapshots": snapshot.dict()}}
        )
    else:
        history = GoalProgressHistory(goal_id=goal_id, snapshots=[snapshot])
        await db.goal_progress_history.insert_one(history.dict())
    
    await db.goals.update_one(
        {"id": goal_id, "user_id": current_user.id},
        {"$set": update_data}
    )
    
    updated_goal = await db.goals.find_one({"id": goal_id, "user_id": current_user.id})
    return Goal(**updated_goal)

@api_router.get("/goals/{goal_id}/progress-history", response_model=GoalProgressHistory)
async def get_goal_progress_history(goal_id: str, current_user: User = Depends(get_current_user)):
    # Verify goal belongs to user
    goal = await db.goals.find_one({"id": goal_id, "user_id": current_user.id})
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    
    history = await db.goal_progress_history.find_one({"goal_id": goal_id})
    if not history:
        # Return empty history if none exists
        return GoalProgressHistory(goal_id=goal_id, snapshots=[])
    
    return GoalProgressHistory(**history)

# Cycle Analytics Routes
@api_router.get("/cycles/{cycle_id}/analytics", response_model=CycleAnalytics)
async def get_cycle_analytics(cycle_id: str, current_user: User = Depends(get_current_user)):
    cycle = await db.cycles.find_one({"id": cycle_id, "user_id": current_user.id})
    if not cycle:
        raise HTTPException(status_code=404, detail="Cycle not found")
    
    # Get cycle goals
    goals = await db.goals.find({"cycle_id": cycle_id, "user_id": current_user.id}).to_list(1000)
    goals_total = len(goals)
    goals_completed = len([g for g in goals if g.get("status") == "completed"])
    completion_rate = (goals_completed / goals_total * 100) if goals_total > 0 else 0
    
    # Get reflections for average mood
    reflections = await db.reflections.find({"cycle_id": cycle_id, "user_id": current_user.id}).to_list(1000)
    average_mood = sum([r.get("mood_rating", 5) for r in reflections]) / len(reflections) if reflections else 5
    
    # Count manifestations
    manifestation_count = sum([len(r.get("law_of_attraction_manifestations", [])) for r in reflections])
    
    analytics = CycleAnalytics(
        cycle_id=cycle_id,
        completion_rate=completion_rate,
        goals_completed=goals_completed,
        goals_total=goals_total,
        average_mood=average_mood,
        manifestation_count=manifestation_count,
        weeks_completed=cycle["current_week"] - 1,
        start_date=cycle["start_date"],
        current_week=cycle["current_week"]
    )
    
    return analytics

@api_router.post("/cycles/{cycle_id}/complete", response_model=Cycle)
async def complete_cycle(cycle_id: str, completion_data: CycleComplete, current_user: User = Depends(get_current_user)):
    cycle = await db.cycles.find_one({"id": cycle_id, "user_id": current_user.id})
    if not cycle:
        raise HTTPException(status_code=404, detail="Cycle not found")
    
    update_data = {
        "status": "completed",
        "current_week": 12,
        "completion_notes": completion_data.completion_notes,
        "success_story": completion_data.success_story,
        "overall_satisfaction": completion_data.overall_satisfaction,
        "completed_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    await db.cycles.update_one(
        {"id": cycle_id, "user_id": current_user.id},
        {"$set": update_data}
    )
    
    completed_cycle = await db.cycles.find_one({"id": cycle_id, "user_id": current_user.id})
    return Cycle(**completed_cycle)

# Dashboard Analytics
@api_router.get("/analytics/dashboard", response_model=DashboardAnalytics)
async def get_dashboard_analytics(current_user: User = Depends(get_current_user)):
    # Get user cycles and goals
    cycles = await db.cycles.find({"user_id": current_user.id}).to_list(1000)
    goals = await db.goals.find({"user_id": current_user.id}).to_list(1000)
    reflections = await db.reflections.find({"user_id": current_user.id}).sort("created_at", -1).limit(10).to_list(10)
    
    total_cycles = len(cycles)
    active_cycles = len([c for c in cycles if c.get("status") == "active"])
    completed_cycles = len([c for c in cycles if c.get("status") == "completed"])
    
    total_goals = len(goals)
    completed_goals = len([g for g in goals if g.get("status") == "completed"])
    average_completion_rate = (completed_goals / total_goals * 100) if total_goals > 0 else 0
    
    # Recent manifestations from last 5 reflections
    recent_manifestations = []
    for reflection in reflections[:5]:
        manifestations = reflection.get("law_of_attraction_manifestations", [])
        recent_manifestations.extend(manifestations[:2])  # Take up to 2 per reflection
    
    # Mood trend from recent reflections
    mood_trend = [r.get("mood_rating", 5) for r in reflections]
    
    analytics = DashboardAnalytics(
        total_cycles=total_cycles,
        active_cycles=active_cycles,
        completed_cycles=completed_cycles,
        total_goals=total_goals,
        completed_goals=completed_goals,
        average_completion_rate=average_completion_rate,
        recent_manifestations=recent_manifestations[:10],
        mood_trend=mood_trend[:10]
    )
    
    return analytics

# Legacy Models
class StatusCheck(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class StatusCheckCreate(BaseModel):
    client_name: str

# Legacy Routes (keeping for backward compatibility)
@api_router.get("/")
async def root():
    return {"message": "Manifest 12 API - Transform Your Life in 12 Weeks"}

@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.dict()
    status_obj = StatusCheck(**status_dict)
    _ = await db.status_checks.insert_one(status_obj.dict())
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    status_checks = await db.status_checks.find().to_list(1000)
    return [StatusCheck(**status_check) for status_check in status_checks]

# Include the router in the main app
app.include_router(api_router)

# Add CORS for your IONOS domain
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", 
        "https://your-domain.ionos.space",  # Replace with your IONOS domain
        "https://your-custom-domain.com"    # Replace with your custom domain
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
