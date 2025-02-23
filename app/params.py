from fastapi import Query,Depends
import typing as t
def pagination_params(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1)
) -> tuple[int, int]:
    return page, limit

def edge_tts_filter_params(short_name: str=None,locale: str=None,gender : t.Literal['Male','Female']=None):
    applied_filters={}
    if short_name is not None:
        applied_filters['ShortName']=short_name
    if locale is not None:
        applied_filters['Locale']=locale
    if gender is not None:
        applied_filters['Gender']=gender
    if applied_filters.keys().__len__()>0:
        return applied_filters
    
    return None

    
EdgeTTSFilterDependency=t.Annotated[dict[str,str] | None,Depends(edge_tts_filter_params)]

PaginationDependency=t.Annotated[tuple[int,int],Depends(pagination_params)]

