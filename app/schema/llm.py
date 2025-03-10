import typing as t
from pydantic import BaseModel
class UserPrompt(BaseModel):
    text: str

OpenAIModels=t.Literal['gpt-3.5-turbo-0125']