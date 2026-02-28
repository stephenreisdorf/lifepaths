from fastapi import APIRouter, HTTPException

from content.loader import all_configs, get_config
from models.content import LifePathConfig

router = APIRouter(prefix="/api/content", tags=["content"])


@router.get("/lifepaths", response_model=list[LifePathConfig])
def list_lifepaths() -> list[LifePathConfig]:
    return list(all_configs().values())


@router.get("/lifepaths/{config_id}", response_model=LifePathConfig)
def get_lifepath(config_id: str) -> LifePathConfig:
    try:
        return get_config(config_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"LifePathConfig '{config_id}' not found")
