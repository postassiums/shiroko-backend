from .conversation import router as router_conversations
from .audio import router as applio_router
from fastapi import APIRouter,Query




main_router=APIRouter(prefix='/api')

main_router.include_router(router_conversations)
main_router.include_router(applio_router)
