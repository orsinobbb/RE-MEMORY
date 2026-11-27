"""Validated local-only chat endpoints."""
from pathlib import Path
from typing import Literal
from fastapi import HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from app.engines.chat import ChatEngine

class ConversationRequest(BaseModel):
    project_id:str=Field(default='PERSONAL',min_length=1,max_length=200)
class MessageRequest(BaseModel):
    content:str=Field(min_length=1,max_length=20000)
    idempotency_key:str=Field(min_length=1,max_length=200)
    mode:Literal['SMART','FIXED']='SMART'
    model:str|None=None
    budget:int=Field(default=4096,ge=2048,le=16384)
class MemoryRequest(BaseModel):
    action:Literal['CONFIRM','EDIT','FORGET']
    content:str|None=Field(default=None,max_length=4000)

def mount_chat_routes(app,store,provider):
    engine=ChatEngine(store,provider)
    def action(fn):
        try:return fn()
        except ValueError as error:raise HTTPException(409,str(error)) from error
    @app.get('/api/chat')
    def state(project_id:str='PERSONAL'):return action(lambda:engine.state('demo',project_id))
    @app.post('/api/chat/conversations')
    def create(r:ConversationRequest):return action(lambda:engine.create('demo',r.project_id))
    @app.get('/api/chat/conversations/{id}')
    def conversation(id:str):return action(lambda:engine.conversation('demo',id))
    @app.post('/api/chat/conversations/{id}/messages')
    def send(id:str,r:MessageRequest):return action(lambda:engine.send('demo',id,r.content,r.idempotency_key,r.mode,r.model,r.budget))
    @app.post('/api/chat/memories/{id}')
    def mutate(id:str,r:MemoryRequest):return action(lambda:engine.mutate('demo',id,r.action,r.content))
    @app.get('/chat.js')
    def script():return FileResponse(Path(__file__).resolve().parents[1]/'frontend/chat.js')
