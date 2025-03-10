
import os
from openai import OpenAI
import random
from app.database import *
from app.schema.llm import OpenAIModels 
from app.schema.tts import OpenAITTSModels


class ChatGPT():
    
    def __init__(self,model : OpenAIModels | OpenAITTSModels='gpt-3.5-turbo-0125'):
        
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

