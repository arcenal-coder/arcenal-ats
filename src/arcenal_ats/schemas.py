"""HTTP contracts; public payloads deliberately omit internal candidate data."""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class PublicJob(BaseModel):
    slug: str
    title: str
    location: str
    contract_type: str
    summary: str


class PublicApplicationCreate(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    location: str | None = Field(default=None, max_length=200)
    cover_letter: str | None = Field(default=None, max_length=20_000)
    consent: bool


class ApplicationAccepted(BaseModel):
    application_id: UUID
    message: str


class DocumentAccepted(BaseModel):
    document_id: UUID
    message: str


class AacpCapability(BaseModel):
    name: str
    description: str
    requires_human_confirmation: bool


class JobCreate(BaseModel):
    slug: str = Field(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$", max_length=160)
    title: str = Field(min_length=1, max_length=200)
    location: str = Field(min_length=1, max_length=200)
    contract_type: str = Field(min_length=1, max_length=100)
    summary: str = Field(min_length=1, max_length=5_000)
    description: str = Field(min_length=1, max_length=50_000)


class PipelineMove(BaseModel):
    stage: str = Field(pattern=r"^(new|qualifying|interview|offer|hired|rejected)$")


class InternalCandidate(BaseModel):
    id: UUID
    email: EmailStr
    first_name: str
    last_name: str
    location: str | None
    skills: str | None
