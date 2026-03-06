"""AI Agent service for interacting with LLMs"""
import asyncio
import logging
from typing import Dict, List, Optional
from fastapi import HTTPException
from emergentintegrations.llm.chat import LlmChat, UserMessage

from core.config import EMERGENT_LLM_KEY
from agents import AGENT_PROMPTS


async def get_agent_response(
    query: str, 
    agent_type: str, 
    session_id: str, 
    chat_history: Optional[List[Dict[str, str]]] = None
) -> str:
    """Get response from specific agent with Claude/GPT fallback"""
    system_prompt = AGENT_PROMPTS.get(agent_type, AGENT_PROMPTS["product_sourcing"])
    
    models = [
        ("anthropic", "claude-opus-4-6"),
        ("anthropic", "claude-sonnet-4-5-20250929"),
        ("openai", "gpt-5.2"),
    ]
    
    last_error = None
    
    for provider, model in models:
        try:
            chat = LlmChat(
                api_key=EMERGENT_LLM_KEY,
                session_id=f"{agent_type}_{session_id}",
                system_message=system_prompt
            )
            chat.with_model(provider, model)
            
            context = ""
            if chat_history:
                for msg in chat_history[-6:]:
                    role = "User" if msg.get("role") == "user" else "Assistant"
                    context += f"{role}: {msg.get('content', '')}\n\n"
            
            full_query = f"{context}User: {query}" if context else query
            user_message = UserMessage(text=full_query)
            
            try:
                response = await asyncio.wait_for(
                    chat.send_message(user_message),
                    timeout=90.0
                )
                logging.info(f"Agent {agent_type} response from {provider}/{model} successful")
                return response
            except asyncio.TimeoutError:
                logging.warning(f"Timeout with {provider}/{model} for agent {agent_type}")
                last_error = f"Timeout with {model}"
                continue
                
        except Exception as e:
            logging.warning(f"Error with {provider}/{model} for agent {agent_type}: {str(e)}")
            last_error = str(e)
            continue
    
    logging.error(f"All AI models failed for agent {agent_type}. Last error: {last_error}")
    
    error_msg = "AI service temporarily unavailable. Please try again in a moment."
    if "budget" in str(last_error).lower() or "cost" in str(last_error).lower():
        error_msg = "AI usage limit reached. Please go to Profile → Universal Key → Add Balance to continue."
    
    raise HTTPException(status_code=503, detail=error_msg)
