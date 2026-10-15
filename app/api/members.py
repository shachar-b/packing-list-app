"""Family member endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Response, status

from app.api.deps import DB, Bus, ClientId
from app.repositories import members as repo
from app.schemas import Member, MemberCreate, MemberUpdate

router = APIRouter(prefix="/members", tags=["members"])


@router.get("", response_model=list[Member])
async def list_members(db: DB) -> list[dict]:
    return repo.list_members(db)


@router.post("", response_model=Member, status_code=status.HTTP_201_CREATED)
async def create_member(body: MemberCreate, db: DB, bus: Bus, origin: ClientId) -> dict:
    with db.transaction():
        member = repo.create_member(db, body.name, body.color, body.emoji)
    await bus.publish("member.created", member, origin=origin)
    return member


@router.patch("/{member_id}", response_model=Member)
async def update_member(member_id: int, body: MemberUpdate, db: DB, bus: Bus, origin: ClientId) -> dict:
    with db.transaction():
        member = repo.update_member(db, member_id, body.changes())
    await bus.publish("member.updated", member, origin=origin)
    return member


@router.delete("/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_member(member_id: int, db: DB, bus: Bus, origin: ClientId) -> Response:
    with db.transaction():
        repo.delete_member(db, member_id)
    await bus.publish("member.deleted", {"id": member_id}, origin=origin)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
