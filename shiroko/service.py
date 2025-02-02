
import os
import typing as t
from openai import OpenAI
import random
class ChatGPTService():
    
    __instance__=None
    
    def __new__(cls) :
        if cls.__instance__ is None:
            cls.__instance__=super().__new__(cls)
            cls.__instance__._initialize()
            
        
        
        return cls.__instance__
    
    
    def _initialize(self):
        self.API_KEY=os.getenv('OPENAI_API_KEY')
        self.model='gpt-3.5-turbo-0125'
        self.client=OpenAI(api_key=self.API_KEY)
        with open('static/shiroko_prompt.md','r') as f:
            self.system_prompt=f.read()
    
    
    def __repr__(self):
        return f'Model: {self.model} \n API_KEY: {self.API_KEY}'
    
    def prompt(self,user_prompt : str):
        chunks= self.client.chat.completions.create(model=self.model,stream=True,messages=[
            {"role": "developer","content":self.system_prompt},
            {"role": "user","content": user_prompt}
        ])
        for chunk in chunks:
            choices=chunk.choices
            random_choice=random.randint(0,choices.__len__()-1)
            chosen_message=choices[random_choice].delta.content
            if chosen_message is not None:
                yield chosen_message

        


        