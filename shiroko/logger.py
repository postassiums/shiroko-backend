import typing as t
import logging

def get_logging(logger_name : t.Literal['uvicorn.error','uvicorn.access']):
    return logging.getLogger(logger_name)

def critical(text : str):
    return get_logging('uvicorn.error').critical(text)

def error(text : str):
    return get_logging('uvicorn.error').error(text)

def info(text : str):
    return get_logging('uvicorn.access').info(text)

def warning(text : str):
    return get_logging('uvicorn.access').warning(text)

def debug(text : str):
    return get_logging('uvicorn.access').debug(text)