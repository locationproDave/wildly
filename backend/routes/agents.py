"""AI Agent routes"""
from fastapi import APIRouter, Depends, HTTPException
from typing import Optional, List
from datetime import datetime, timezone
import uuid

from core.database import db
from models.schemas import AgentQuery
from services.auth import get_current_user, require_user
from services.agents import get_agent_response
from agents import AGENT_METADATA

router = APIRouter(prefix="/agents", tags=["AI Agents"])


@router.get("", response_model=dict)
async def get_agents():
    return {"agents": AGENT_METADATA}


@router.post("/chat", response_model=dict)
async def agent_chat(query: AgentQuery, user: Optional[dict] = Depends(get_current_user)):
    session_id = query.session_id or str(uuid.uuid4())
    user_id = user["id"] if user else None
    agent_type = query.agent_type
    
    agent_session_id = f"{agent_type}_{session_id}"
    session = await db.agent_sessions.find_one({"id": agent_session_id}, {"_id": 0})
    
    if not session:
        session = {
            "id": agent_session_id,
            "user_id": user_id,
            "agent_type": agent_type,
            "messages": [],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        await db.agent_sessions.insert_one(session)
    
    user_message = {
        "role": "user",
        "content": query.query,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    response = await get_agent_response(query.query, agent_type, session_id, session.get("messages", []))
    
    assistant_message = {
        "role": "assistant",
        "content": response,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    await db.agent_sessions.update_one(
        {"id": agent_session_id},
        {
            "$push": {"messages": {"$each": [user_message, assistant_message]}},
            "$set": {"updated_at": datetime.now(timezone.utc).isoformat()}
        }
    )
    
    return {
        "session_id": session_id,
        "agent_type": agent_type,
        "response": response,
        "message": assistant_message
    }


@router.get("/sessions", response_model=List[dict])
async def get_agent_sessions(agent_type: Optional[str] = None, user: dict = Depends(require_user)):
    query_filter = {"user_id": user["id"]}
    if agent_type:
        query_filter["agent_type"] = agent_type
    
    sessions = await db.agent_sessions.find(query_filter, {"_id": 0}).sort("updated_at", -1).to_list(50)
    return sessions
