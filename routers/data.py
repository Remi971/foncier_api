from fastapi import APIRouter, Path
from services.data import get_data

router = APIRouter(
    prefix="/data"
)

@router.get('/')
def list_code_insee():
    ...
    
@router.get('/add/sqlite/{insee}')
def adding_data_to_db(
    insee: str = Path(min_length=5, max_length=5)
    ):
    return get_data(insee)
    
    
