from pydantic import BaseModel
import typing as t
from .minio import MinioItem


class Voice(BaseModel):
    total_parts : int
    full: t.Optional[MinioItem]=None
    
    