from fastapi import APIRouter,HTTPException,Query
from fastapi.responses import StreamingResponse
from app.service import *
from app.database import databaseDependency,get_collection
from app.logger import *
from app.schema import *
import pymongo
import app.routes as routes

router=APIRouter(prefix='/api')

router.include_router(routes.router_conversations)
    
    


