
from fastapi import APIRouter,HTTPException,Query
from fastapi.responses import StreamingResponse,PlainTextResponse,FileResponse
from app.service import *
from app.database import databaseDependency,get_collection
from app.logger import *
from app.schema import *
from pprint import pprint
from app.params import *



router=APIRouter(prefix='/audio',tags=['Audio Endpoints'],redirect_slashes=False)



@router.post('/openai/tts',response_model=None)
async def convert_text_to_speech_using_openai(voice_service : OpenAITTSDependency):
    result=voice_service.tts_stream()
    return StreamingResponse(result,media_type=voice_service.get_mime_type())

@router.post('/edge/tts',response_model=None)
async def conter_text_to_speech_using_microsoft_edge(voice_service : EdgeTTSDependency):
    result=await voice_service.tts_stream()
    return StreamingResponse(result,media_type='audio/mpeg')

@router.get('/edge/voices')
async def list_all_edge_tts_available_voices(pagination : PaginationDependency,filter : EdgeTTSFilterDependency):
    page,limit=pagination
    voices=await EdgeTTSService.list_edge_tts_voices(page,limit,filter)
    return voices.model_dump()




