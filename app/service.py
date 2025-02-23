
import os
import typing as t
from openai import OpenAI,Stream
from openai.types.chat.chat_completion_chunk import ChatCompletionChunk
import random
from app.database import *
from app.schema import *
from app.service import *
from math import ceil
from pathlib import Path
from enum import Enum
from fastapi import Query
import httpx
import edge_tts
from dotenv import load_dotenv
from rvc_python.infer import RVCInference
from minio import Minio
import tempfile
import abc
import io
from datetime import timedelta

class ConversationService():
    def __init__(self,db : databaseDependency):
        self.db=db
        self.conversations=get_collection(self.db,'conversations')
    
    def create(self,new_conversation : CreateConversation):
        
        result=self.conversations.insert_one(new_conversation.model_dump())
        inserted_id=result.inserted_id
        
        inserted_document=self.conversations.find_one({"_id": inserted_id})
        if inserted_document is None:
            return False
        return ConversationWithId(**inserted_document).model_dump(by_alias=True)
    
    def update(self,id : str,data : UpdateConversation):
        target_id=ObjectId(id)
        return self.conversations.update_one({"_id": target_id },{'$set': data.model_dump()})

        

    
    def get_specific_conversation(self, id : str):
        fields=Conversation.get_projected_fields()
        pipeline=[{"$match":{"_id": ObjectId(id)}},{"$project": fields}]
        conversation=self.conversations.aggregate(pipeline).next()
        if conversation is None:
            return False
        return ConversationWithId(**conversation).model_dump(by_alias=True)
    
    def list_paginated(self,page : t.Annotated[int,Query(1,ge=1)], limit : t.Annotated[int,Query(10,ge=1)]):

        offset=(page-1)*limit
        fields=Conversation.get_projected_fields()
        pipeline=[
            {"$project":fields},
            {"$sort": {"created_at":-1}},
            {"$skip": offset},
            {"$limit": limit}
            ]
        data=self.conversations.aggregate(pipeline).to_list()
        data.reverse()
        remaining_items=self.conversations.count_documents(skip=offset+limit,filter={})
        results={
            "total_documents": self.conversations.count_documents(filter={}),
            "count_remaining_items": remaining_items,
            "data":data,
            "remaining_pages":int(ceil(remaining_items/limit))
        }
        return Pagination[ConversationWithId](**results).model_dump(by_alias=True)

   
ConversationServiceDependency=t.Annotated[ConversationService,Depends(ConversationService)]  


class ChatGPT():
    
    def __init__(self,model : OpenAIModels | OpenAITTSModels='gpt-3.5-turbo-0125'):
        debug('Called chatgpt Constructor')
        print('Chat gpt constructor')
        self.API_KEY=os.getenv('OPENAI_API_KEY')
        self.model=model
        self.client=OpenAI(api_key=self.API_KEY)
        
        if self.model_exists()==False:
            raise HTTPException(500,detail=f'The fallowing model: {self.model} does not exists on OPENAI')
        
    def model_exists(self):
        models_response=self.client.models.list().data
        result=list(filter(lambda item: item.id==self.model,models_response))
        return result.__len__()>0
        
    def __repr__(self):
        return f'Model: {self.model} \n API_KEY: {self.API_KEY}'

class LLMService(ChatGPT):
    
    __instance__=None
    
    def __new__(cls,*args,**kwargs) :
        if cls.__instance__ is None:
            cls.__instance__=super().__new__(cls,*args,**kwargs)
            cls.__instance__._set_system_prompt()
            
        
        
        return cls.__instance__
    
    
    def _set_system_prompt(self):
        with open('static/shiroko_prompt.md','r') as f:
            self.system_prompt=f.read()
    
    

    
    def prompt(self,user_prompt : str):
        chunks= self.client.chat.completions.create(model=self.model,stream=True,messages=[
            {"role": "developer","content":"You are Sunnaokami Shiroko from the game Blue Archieve"},
            {"role": "user","content": user_prompt}
        ])
        first_chunk=chunks.__next__()
        choices=first_chunk.choices
        chonsen_index=random.randint(0,choices.__len__()-1)
        first_message=choices[chonsen_index].delta.content
        yield first_message or ''
        for chunk in chunks:
            chosen_message=chunk.choices[chonsen_index].delta.content
            yield chosen_message or ''


class TTSBase(abc.ABC):
    
    
    
    @abc.abstractmethod
    def get_mime_type() -> str:
        pass
    
    @abc.abstractmethod
    def get_audio_format() -> str:
        pass
    
    
class EdgeTTSService(TTSBase):
    
    def __init__(self,body : EdgeTTSBody):
        self.voice=body.voice
        
        if not(self._voice_exists()):
            raise RuntimeError(f'The specific voice {body.voice} does not exists')
            
        self.audio_format='mp3'
        self.STREAM_CHUNK=body.STREAM_CHUNK
        self.content=body.content
        

        
    def get_audio_format(self):
        return self.audio_format

    def get_mime_type(self):
        return 'audio/mp3'
  
    


    
    async def tts_stream(self):
        communication=edge_tts.Communicate(self.content,self.voice)
        response=await communication.stream()
        return response

        
    async def _voice_exists(self):
        voice_manager=await edge_tts.VoicesManager.create()
        found_voices=voice_manager.find(ShortName=self.voice)
        return type(found_voices)==list and found_voices.__len__()>0
          
            
    @staticmethod  
    async def list_edge_tts_voices(page: int,limit : int,filter : dict[str,str]):   
        voice_manager=await edge_tts.VoicesManager.create()
        voices=voice_manager.voices
        
        if filter is not None:
            voices=voice_manager.find(**filter)
        total=voices.__len__()
        remaining_items=total-(page*limit)
        remaining_items=remaining_items if remaining_items>0 else 0
        remaning_pages=int(ceil(remaining_items/limit))
        data=voices[page-1:limit]
        
         
        return Pagination[edge_tts.voices.Voice](total_documents=total,count_remaining_items=remaining_items,data=data,remaining_pages=remaning_pages)
         

class OpenAITTSService(ChatGPT,TTSBase):


        
  

    
    
    def __init__(self,body : OpenAITTSBody):
        self.voice=body.voice
        if not(self._voice_exists()):
            raise RuntimeError(f'The specific voice {self.voice} does not exists')
        
        super().__init__(body.model)
        
            
        self.STREAM_CHUNK=body.STREAM_CHUNK
        self.speed=body.speed
        self.audio_format=body.format
        self.content=body.content
        
    def get_mime_type(self):
        mime_type_dict={
            "mp3": 'mpeg',
            'opus': 'ogg'
        }
        return f'audio/{self.audio_format}' if self.audio_format not in mime_type_dict.keys() else f'audio/{mime_type_dict.get(self.audio_format)}'
        
    def get_audio_format(self):
        return self.audio_format

    def _voice_exists(self):
        return self.voice in t.get_args(OpenAITTSVoices)

    
    
    def tts_stream(self):
        response=self.client.audio.speech.create(model=self.model,voice=self.voice,input=self.content,speed=self.speed,response_format=self.audio_format)
        for chunk in response.iter_bytes(self.STREAM_CHUNK):
            yield chunk
    

class VoiceService():
    
    __instance__=None
    
    def __new__(cls) :
        if cls.__instance__ is None:
            cls.__instance__=super().__new__(cls)
            cls.__instance__._initialize()
            
        
        
        return cls.__instance__
        
    def _initialize(self):
        try:
            self.rvc=RVCInference()
            self.rvc.load_model(self.rvc.list_models()[0])
        except Exception as e:
            critical(e)
            raise HTTPException(500,detail='Failed to load models')
        


RVCServiceDependency=t.Annotated[VoiceService,Depends(VoiceService)] 
AudioType=t.Literal['rvc','tts']
class StorageService():
    class Buckets(Enum):
        AUDIOS='audios'
        
    EXPIRE_IN=timedelta(days=7)
        
    def __init__(self):
        try:
            HOST=f"{os.getenv('MINIO_HOST')}:9000"
            ACCESS_KEY=os.getenv('MINIO_ACCESS_KEY')
            SECRET_KEY=os.getenv('MINIO_SECRET_KEY')
            
            self._client=Minio(HOST,ACCESS_KEY,SECRET_KEY,secure=False)
            if not(self._client.bucket_exists(self.Buckets.AUDIOS.value)):
                self._client.make_bucket(self.Buckets.AUDIOS.value)
        except Exception as e:
            
            critical(e)
            raise HTTPException(500,detail='Failed to connect to Minio')
    @classmethod 
    def getNewExpirationDate(cls):
        return datetime.now(tz=timezone.utc)+cls.EXPIRE_IN
        
            
    def getClient(self):
        return self._client
    
    def putAudioObject(self,id : str,audio : io.BytesIO,length : int, mime_type : str):
        result=self._client.put_object(f'{self.Buckets.AUDIOS.value}',id,audio,length=length,content_type=mime_type)
        return result
    
    def getAudioUrl(self, id: str):
        return self._client.presigned_get_object(self.Buckets.AUDIOS.value,id,expires=self.EXPIRE_IN)
    
    
    
        
        
StorageServiceDependency=t.Annotated[StorageService,Depends(StorageService)]

        
    
         
 

OpenAITTSDependency=t.Annotated[OpenAITTSService,Depends(OpenAITTSService)]
EdgeTTSDependency=t.Annotated[EdgeTTSService,Depends(EdgeTTSService)]


            
            