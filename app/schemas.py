"""Pydantic v2 request/response models (the API contract).

Request models forbid unknown fields and strip whitespace. ``*Update`` models
are partial: only fields actually sent by the client are applied, which is what
lets two devices edit different attributes of the same item concurrently.
"""

from __future__ import annotations

from datetime import date as _date
from typing import Annotated, Any, ClassVar, Literal

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, StringConstraints, model_validator


def _validate_iso_date(v: str) -> str:
    _date.fromisoformat(v)
    return v


Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)]
MemberName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=40)]
Note = Annotated[str, StringConstraints(strip_whitespace=True, max_length=500)]
Emoji = Annotated[str, StringConstraints(strip_whitespace=True, max_length=16)]
Color = Annotated[str, StringConstraints(pattern=r"^#[0-9a-fA-F]{6}$")]
IsoDate = Annotated[
    str,
    StringConstraints(strip_whitespace=True, pattern=r"^\d{4}-\d{2}-\d{2}$"),
    AfterValidator(_validate_iso_date),
]
Quantity = Annotated[int, Field(ge=1, le=999)]
Id = Annotated[int, Field(ge=1)]


class _Request(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class _Partial(_Request):
    """Partial update: fields listed in ``NON_NULLABLE`` may be omitted but not null."""

    NON_NULLABLE: ClassVar[tuple[str, ...]] = ()

    @model_validator(mode="after")
    def _reject_explicit_nulls(self) -> "_Partial":
        for name in self.NON_NULLABLE:
            if name in self.model_fields_set and getattr(self, name) is None:
                raise ValueError(f"'{name}' may not be null")
        return self

    def changes(self) -> dict[str, Any]:
        return {k: getattr(self, k) for k in self.model_fields_set}


# --------------------------------------------------------------------- members
class MemberCreate(_Request):
    name: MemberName
    color: Color = "#6366f1"
    emoji: Emoji | None = None


class MemberUpdate(_Partial):
    NON_NULLABLE: ClassVar[tuple[str, ...]] = ("name", "color", "position")
    name: MemberName | None = None
    color: Color | None = None
    emoji: Emoji | None = None
    position: Annotated[int, Field(ge=0)] | None = None


class Member(BaseModel):
    id: int
    name: str
    color: str
    emoji: str | None
    position: int


# ----------------------------------------------------------------------- items
class ItemCreate(_Request):
    name: Name
    quantity: Quantity = 1
    note: Note | None = None
    packed: bool = False
    assignee_ids: list[Id] = Field(default_factory=list, max_length=50)
    sort_order: Annotated[int, Field(ge=0)] | None = None


class ItemUpdate(_Partial):
    NON_NULLABLE: ClassVar[tuple[str, ...]] = ("name", "quantity", "packed", "assignee_ids", "category_id", "sort_order")
    name: Name | None = None
    quantity: Quantity | None = None
    note: Note | None = None
    packed: bool | None = None
    assignee_ids: list[Id] | None = Field(default=None, max_length=50)
    category_id: Id | None = None
    sort_order: Annotated[int, Field(ge=0)] | None = None


class Item(BaseModel):
    id: int
    category_id: int
    name: str
    packed: bool
    quantity: int
    note: str | None
    sort_order: int
    assignee_ids: list[int]
    updated_at: str


# ------------------------------------------------------------------ categories
class CategoryCreate(_Request):
    name: Name
    icon: Emoji = "📦"
    sort_order: Annotated[int, Field(ge=0)] | None = None


class CategoryUpdate(_Partial):
    NON_NULLABLE: ClassVar[tuple[str, ...]] = ("name", "icon", "sort_order")
    name: Name | None = None
    icon: Emoji | None = None
    sort_order: Annotated[int, Field(ge=0)] | None = None


class Category(BaseModel):
    id: int
    trip_id: int
    name: str
    icon: str
    sort_order: int
    items: list[Item] = Field(default_factory=list)


class PackAllRequest(_Request):
    packed: bool = True


# ----------------------------------------------------------------------- trips
class TripCreate(_Request):
    name: Name
    emoji: Emoji | None = None
    is_template: bool = False
    departure_date: IsoDate | None = None
    source_trip_id: Id | None = Field(
        default=None, description="If given, categories and items are cloned (all unpacked)."
    )


class TripUpdate(_Partial):
    NON_NULLABLE: ClassVar[tuple[str, ...]] = ("name", "is_template")
    name: Name | None = None
    emoji: Emoji | None = None
    is_template: bool | None = None
    departure_date: IsoDate | None = None


class CloneRequest(_Request):
    name: Name
    emoji: Emoji | None = None
    is_template: bool = False
    departure_date: IsoDate | None = None


class TripSummary(BaseModel):
    id: int
    name: str
    emoji: str | None
    is_template: bool
    departure_date: str | None = None
    total_items: int
    packed_items: int
    created_at: str
    updated_at: str


class TripDetail(TripSummary):
    categories: list[Category]


# --------------------------------------------------------------- import/export
EXPORT_FORMAT = "family-packing-list"
EXPORT_VERSION = 1


class ExportMember(_Request):
    name: MemberName
    color: Color = "#6366f1"
    emoji: Emoji | None = None


class ExportItem(_Request):
    name: Name
    quantity: Quantity = 1
    note: Note | None = None
    packed: bool = False
    assignees: list[MemberName] = Field(default_factory=list, max_length=50)


class ExportCategory(_Request):
    name: Name
    icon: Emoji = "📦"
    items: list[ExportItem] = Field(default_factory=list, max_length=2000)


class ExportTrip(_Request):
    name: Name
    emoji: Emoji | None = None
    is_template: bool = False
    departure_date: IsoDate | None = None
    categories: list[ExportCategory] = Field(default_factory=list, max_length=200)


class ExportDocument(_Request):
    format: Literal["family-packing-list"] = EXPORT_FORMAT
    version: Literal[1] = EXPORT_VERSION
    exported_at: str | None = None
    members: list[ExportMember] = Field(default_factory=list, max_length=200)
    trips: list[ExportTrip] = Field(min_length=1, max_length=500)


class ImportResult(BaseModel):
    trips: list[TripSummary]
    members_created: int


# ---------------------------------------------------------------------- events
EventType = Literal[
    "trip.created",
    "trip.updated",
    "trip.deleted",
    "trip.snapshot",
    "category.created",
    "category.updated",
    "category.deleted",
    "item.created",
    "item.updated",
    "item.deleted",
    "member.created",
    "member.updated",
    "member.deleted",
]


class Event(BaseModel):
    type: EventType
    trip_id: int | None = None
    origin: str | None = None
    data: dict[str, Any]


class Health(BaseModel):
    status: Literal["ok"]
    version: str
    schema_version: int
    connections: int
