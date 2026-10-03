from typing import Annotated

from fastapi import APIRouter, Query, status

from app.modules.leads.dependencies import LeadServiceDep
from app.modules.leads.schemas import LeadCreate, LeadDetail, LeadFilter, LeadRead, LeadUpdate

router = APIRouter(prefix="/leads", tags=["leads"])


@router.get("", response_model=list[LeadRead])
async def list_leads(filters: Annotated[LeadFilter, Query()], service: LeadServiceDep):
    return await service.list_all(filters)


@router.post("", response_model=LeadRead, status_code=status.HTTP_201_CREATED)
async def create_lead(data: LeadCreate, service: LeadServiceDep):
    return await service.create_manual(data)


@router.get("/{lead_id}", response_model=LeadDetail)
async def get_lead(lead_id: int, service: LeadServiceDep):
    return await service.get_detail(lead_id)


@router.patch("/{lead_id}", response_model=LeadRead)
async def update_lead(lead_id: int, data: LeadUpdate, service: LeadServiceDep):
    return await service.update(lead_id, data)


@router.delete("/{lead_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_lead(lead_id: int, service: LeadServiceDep) -> None:
    await service.delete(lead_id)


@router.post("/{lead_id}/tags/{tag_id}", response_model=LeadRead)
async def add_tag(lead_id: int, tag_id: int, service: LeadServiceDep):
    return await service.add_tag(lead_id, tag_id)


@router.delete("/{lead_id}/tags/{tag_id}", response_model=LeadRead)
async def remove_tag(lead_id: int, tag_id: int, service: LeadServiceDep):
    return await service.remove_tag(lead_id, tag_id)
