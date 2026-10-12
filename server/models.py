"""Pydantic-Modelle für das Mooncells Document Format v1.

Entspricht exakt docs/schema.md. Referenzen sind bewusst schwach typisiert
(plain strings) — siehe Designentscheidung 3.1 in docs/schema.md.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal, Optional

from pydantic import BaseModel, Field


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------- Agents


class AgentCreate(BaseModel):
    handle: str
    agent_type: Literal["human", "model"]
    description: Optional[str] = None


class Agent(AgentCreate):
    id: str
    created_at: str = Field(default_factory=utcnow)


class SourceReference(BaseModel):
    """Belegte externe Identität; Titel allein begründen keine Zuordnung."""
    system: str = Field(min_length=1)
    kind: str = Field(min_length=1)
    source_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    locator: Optional[str] = None
    content_sha256: Optional[str] = None


# ----------------------------------------------------------------- Works


class WorkCreate(BaseModel):
    work_type: str
    title: str
    tags: list[str] = []
    author_id: str
    source_ref: Optional[SourceReference] = None


class Work(WorkCreate):
    id: str
    created_at: str = Field(default_factory=utcnow)


# ------------------------------------------------------------- Worktrees


class WorktreeCreate(BaseModel):
    work_id: str
    author_id: str


class Worktree(WorktreeCreate):
    id: str
    created_at: str = Field(default_factory=utcnow)


# -------------------------------------------------------------- Variants

VARIANT_STATUSES = ["entwurf", "geprüft", "grundformation", "verworfen"]


class VariantCreate(BaseModel):
    worktree_id: str
    derived_from: Optional[str] = None  # null = Wurzel des Baums
    label: str
    notes: str = ""
    content: Optional[str] = None
    status: Literal["entwurf", "geprüft", "grundformation", "verworfen"] = "entwurf"
    tags: list[str] = []
    author_id: str
    source_ref: Optional[SourceReference] = None


class Variant(VariantCreate):
    id: str
    created_at: str = Field(default_factory=utcnow)


class StatusUpdate(BaseModel):
    """Der einzige mutable Kern-Feld: semantischer Zustand (v2).

    Alles andere an Varianten bleibt append-only — „Änderung" = neue Variante.
    """
    status: Literal["entwurf", "geprüft", "grundformation", "verworfen"]


# ----------------------------------------------------------------- Edges

EDGE_TYPES = ["remixt-aus", "erweitert", "testet", "widerspricht", "bewertet", "verweist-auf"]


class EdgeCreate(BaseModel):
    edge_type: str
    from_variant_id: str
    to_variant_id: str
    note: Optional[str] = None
    author_id: str
    source_ref: Optional[SourceReference] = None


class Edge(EdgeCreate):
    id: str
    created_at: str = Field(default_factory=utcnow)


# -------------------------------------------------------------- Findings

VERDICTS = ["tragfähig", "teilweise", "nicht-tragfähig"]


class FindingCreate(BaseModel):
    # genau eines der Zielfelder muss gesetzt sein (target_finding_id = Meta-Befund v2)
    target_edge_id: Optional[str] = None
    target_variant_ids: Optional[tuple[str, str]] = None
    target_finding_id: Optional[str] = None
    criterion: str
    task: str
    verdict: Literal["tragfähig", "teilweise", "nicht-tragfähig"]
    rationale: str
    author_id: str


class Finding(FindingCreate):
    id: str
    created_at: str = Field(default_factory=utcnow)


# ------------------------------------------------------ Document Format


class DocumentData(BaseModel):
    agents: list[Agent] = []
    works: list[Work] = []
    worktrees: list[Worktree] = []
    variants: list[Variant] = []
    edges: list[Edge] = []
    findings: list[Finding] = []


class MooncellsDocument(BaseModel):
    format: Literal["mooncells-document"] = "mooncells-document"
    version: Literal["1"] = "1"
    instance_id: str
    exported_by: str
    exported_at: str = Field(default_factory=utcnow)
    scope: Optional[dict] = None
    data: DocumentData
