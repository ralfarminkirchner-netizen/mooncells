"""FastAPI-Anwendung — Mooncells REST-API + statische Oberfläche.

Start:
    uvicorn server.app:app --host 127.0.0.1 --port 8400
Oder:
    python -m server.app --port 8400 --data data/state.json
"""
from __future__ import annotations

import argparse
import os
import threading
from typing import Optional

import httpx
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .models import (Agent, AgentCreate, Edge, EdgeCreate, Finding,
                     FindingCreate, Variant, VariantCreate, Work, WorkCreate,
                     Worktree, utcnow)
from .store import JsonStore, new_uuid

STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")

store = JsonStore(os.environ.get("MOONCELLS_DATA", "data/state.json"))
INSTANCE_ID = os.environ.get("MOONCELLS_INSTANCE", "mooncells-local")

app = FastAPI(title="Mooncells", version="0.1.0")

# ------------------------------------------------------------- Auto-Sync

AUTOSYNC_LOG: list[dict] = []  # letzte Push-Ergebnisse (Ringpuffer)


def _autosync_push() -> None:
    """Export einmal an alle registrierten Peers pushen (Hintergrund-Thread)."""
    peers = store.list("peers")
    if not peers:
        return
    doc = store.export_document(INSTANCE_ID, exported_by="system")
    results = []
    for p in peers:
        try:
            with httpx.Client(timeout=5) as client:
                r = client.post(p["url"].rstrip("/") + "/api/import", json=doc)
            rep = r.json().get("report", {}) if r.status_code == 200 else {}
            results.append({"peer": p["url"], "ok": r.status_code == 200,
                            "status": r.status_code,
                            "added": sum(v.get("added", 0) for v in rep.values())})
        except Exception as e:  # Peer-Down darf Schreibzugriff nie blocken
            results.append({"peer": p["url"], "ok": False, "error": str(e)})
    AUTOSYNC_LOG.append({"at": utcnow(), "results": results})
    del AUTOSYNC_LOG[:-20]


def trigger_autosync() -> None:
    """Nach lokalen Create-Endpunkten aufrufen — asynchron, fehlerresistent."""
    threading.Thread(target=_autosync_push, daemon=True).start()


class PeerCreate(BaseModel):
    url: str  # z. B. http://127.0.0.1:8401


@app.get("/api/peers")
def list_peers():
    return store.list("peers")


@app.post("/api/peers", status_code=201)
def add_peer(body: PeerCreate):
    url = body.url.rstrip("/")
    if store.find_by("peers", "url", url):
        raise HTTPException(409, f"Peer '{url}' ist bereits registriert")
    if not url.startswith(("http://", "https://")):
        raise HTTPException(422, "Peer-URL muss mit http:// oder https:// beginnen")
    peer = {"id": new_uuid(), "url": url, "added_at": utcnow()}
    store.add("peers", peer)
    return peer


@app.delete("/api/peers/{peer_id}", status_code=204)
def remove_peer(peer_id: str):
    if not store.delete("peers", peer_id):
        raise HTTPException(404, "Peer nicht gefunden")


@app.get("/api/autosync-log")
def autosync_log():
    return list(AUTOSYNC_LOG)


# ==================================================================== API


@app.post("/api/agents", response_model=Agent, status_code=201)
def create_agent(body: AgentCreate):
    if store.find_by("agents", "handle", body.handle):
        raise HTTPException(409, f"Agent '{body.handle}' existiert bereits")
    result = store.add("agents", Agent(id=new_uuid(), **body.model_dump()).model_dump())
    trigger_autosync()
    return result


@app.get("/api/agents", response_model=list[Agent])
def list_agents():
    return store.list("agents")


@app.get("/api/agents/{agent_id}", response_model=Agent)
def get_agent(agent_id: str):
    a = store.get("agents", agent_id)
    if not a:
        raise HTTPException(404, "Agent nicht gefunden")
    return a


# -------------------------------------------------------------------- Works


@app.post("/api/works", status_code=201)
def create_work(body: WorkCreate):
    """Legt ein Werk samt Worktree an (ein Worktree pro Werk)."""
    if not store.get("agents", body.author_id):
        raise HTTPException(422, f"author_id '{body.author_id}' unbekannt")
    work = Work(id=new_uuid(), **body.model_dump()).model_dump()
    worktree = Worktree(id=new_uuid(), work_id=work["id"],
                        author_id=body.author_id,
                        created_at=utcnow()).model_dump()
    store.add("works", work)
    store.add("worktrees", worktree)
    trigger_autosync()
    return {"work": work, "worktree": worktree}


@app.get("/api/works")
def list_works():
    works = store.list("works")
    for w in works:
        wt = store.find_by("worktrees", "work_id", w["id"])
        w["worktree_id"] = wt[0]["id"] if wt else None
    return works


@app.get("/api/works/{work_id}")
def get_work(work_id: str):
    w = store.get("works", work_id)
    if not w:
        raise HTTPException(404, "Werk nicht gefunden")
    wt = store.find_by("worktrees", "work_id", work_id)
    variants = store.list("variants")
    return {
        "work": w,
        "worktree": wt[0] if wt else None,
        "variants": [v for v in variants if v["worktree_id"] == (wt[0]["id"] if wt else "")],
    }


# ----------------------------------------------------------------- Variants


@app.post("/api/variants", response_model=Variant, status_code=201)
def create_variant(body: VariantCreate):
    wt = store.get("worktrees", body.worktree_id)
    if not wt:
        raise HTTPException(422, f"worktree_id '{body.worktree_id}' unbekannt")
    if not store.get("agents", body.author_id):
        raise HTTPException(422, f"author_id '{body.author_id}' unbekannt")
    if body.derived_from is not None:
        parent = store.get("variants", body.derived_from)
        if not parent:
            raise HTTPException(422, f"derived_from '{body.derived_from}' unbekannt")
        if parent["worktree_id"] != body.worktree_id:
            raise HTTPException(422,
                                "Abgeleitete Variante muss im selben Worktree bleiben")
    else:
        # Wurzel-Regel: pro Worktree genau eine Wurzel
        roots = [v for v in store.find_by("variants", "worktree_id", body.worktree_id)
                 if v["derived_from"] is None]
        if roots:
            raise HTTPException(409,
                                f"Worktree hat bereits eine Wurzel: {roots[0]['id']}")
    result = store.add("variants",
                       Variant(id=new_uuid(), **body.model_dump()).model_dump())
    trigger_autosync()
    return result


# -------------------------------------------------------------------- Edges


@app.post("/api/edges", response_model=Edge, status_code=201)
def create_edge(body: EdgeCreate):
    for vid in (body.from_variant_id, body.to_variant_id):
        if not store.get("variants", vid):
            raise HTTPException(422, f"Variante '{vid}' unbekannt")
    if not store.get("agents", body.author_id):
        raise HTTPException(422, f"author_id '{body.author_id}' unbekannt")
    result = store.add("edges", Edge(id=new_uuid(), **body.model_dump()).model_dump())
    trigger_autosync()
    return result


# ----------------------------------------------------------------- Findings


@app.post("/api/findings", response_model=Finding, status_code=201)
def create_finding(body: FindingCreate):
    if (body.target_edge_id is None) == (body.target_variant_ids is None):
        raise HTTPException(422,
                            "Genau eines von target_edge_id / target_variant_ids setzen")
    if body.target_edge_id and not store.get("edges", body.target_edge_id):
        raise HTTPException(422, f"Kante '{body.target_edge_id}' unbekannt")
    if body.target_variant_ids:
        for vid in body.target_variant_ids:
            if not store.get("variants", vid):
                raise HTTPException(422, f"Variante '{vid}' unbekannt")
    if not store.get("agents", body.author_id):
        raise HTTPException(422, f"author_id '{body.author_id}' unbekannt")
    data = body.model_dump()
    if data.get("target_variant_ids"):
        data["target_variant_ids"] = list(data["target_variant_ids"])
    result = store.add("findings", Finding(id=new_uuid(), **data).model_dump())
    trigger_autosync()
    return result


# ------------------------------------------------------------------- Graph


@app.get("/api/graph")
def get_graph():
    """Alles auf einmal — Baustein für die Oberfläche."""
    return {coll: store.list(coll) for coll in
            ("agents", "works", "worktrees", "variants", "edges", "findings")}


# --------------------------------------------------- Export / Import (MDF)


@app.get("/api/export")
def export(work_ids: Optional[str] = Query(None),
           since: Optional[str] = Query(None)):
    """Mooncells Document Format. work_ids als Komma-separierte UUIDs."""
    ids = [s for s in (work_ids or "").split(",") if s] or None
    return store.export_document(INSTANCE_ID, exported_by="system",
                                 work_ids=ids, since=since)


@app.post("/api/import")
def import_document(doc: dict):
    """Merge per UUID-Dedupe — überschreibt niemals bestehende Einträge."""
    try:
        report = store.import_document(doc)
    except ValueError as e:
        raise HTTPException(422, str(e))
    return {"ok": True, "report": report}


# ----------------------------------------------------------- Live-Sync

@app.get("/api/changes")
def changes(since: str = Query(..., description="ISO-8601-Zeitstempel")):
    """Nur Neu-Einfügungen seit <since> — Baustein für Pull-Sync."""
    doc = store.export_document(INSTANCE_ID, exported_by="system", since=since)
    return doc


def _push_to_peer(peer: str) -> dict:
    """Eigener Export → POST an /api/import des Peers."""
    doc = store.export_document(INSTANCE_ID, exported_by="system")
    try:
        with httpx.Client(timeout=10) as client:
            r = client.post(peer.rstrip("/") + "/api/import", json=doc)
    except httpx.HTTPError as e:
        raise HTTPException(502, f"Peer nicht erreichbar: {e}")
    if r.status_code != 200:
        raise HTTPException(502, f"Peer antwortete {r.status_code}: {r.text[:300]}")
    return r.json()


def _pull_from_peer(peer: str) -> dict:
    """Export des Peers holen → lokal per UUID-Dedupe mergen."""
    try:
        with httpx.Client(timeout=10) as client:
            r = client.get(peer.rstrip("/") + "/api/export")
    except httpx.HTTPError as e:
        raise HTTPException(502, f"Peer nicht erreichbar: {e}")
    if r.status_code != 200:
        raise HTTPException(502, f"Peer antwortete {r.status_code}: {r.text[:300]}")
    try:
        return store.import_document(r.json())
    except ValueError as e:
        raise HTTPException(502, f"Peer lieferte kein gültiges Document: {e}")


class SyncRequest(BaseModel):
    peer: str  # z. B. http://127.0.0.1:8401


@app.post("/api/sync")
def sync_with_peer(body: SyncRequest):
    """Bidirektionale Synchronisation mit einer Peer-Instanz.

    1. Eigener Zustand wird an den Peer gepusht (dort per Dedupe gemergt).
    2. Peer-Zustand wird zurückgeholt und lokal gemergt.
    Beide Instanzen konvergieren — konfliktfrei durch Append-only + UUIDs.
    """
    pushed = _push_to_peer(body.peer)
    pulled = _pull_from_peer(body.peer)
    return {"ok": True, "peer": body.peer,
            "pushed": pushed, "pulled_report": pulled}


# ================================================================ Oberfläche


@app.get("/")
def index():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


if __name__ == "__main__":
    import uvicorn

    p = argparse.ArgumentParser()
    # PORT/MOONCELLS_HOST aus der Umgebung — so funktioniert derselbe Start-
    # Befehl lokal (127.0.0.1:8400) und auf Railway (0.0.0.0:$PORT).
    p.add_argument("--host", default=os.environ.get("MOONCELLS_HOST", "127.0.0.1"))
    p.add_argument("--port", type=int, default=int(os.environ.get("PORT", 8400)))
    p.add_argument("--data", default=os.environ.get("MOONCELLS_DATA", "data/state.json"))
    p.add_argument("--instance", default="mooncells-local")
    args = p.parse_args()

    store = JsonStore(args.data)          # noqa: F811 — bewusst neu setzen
    INSTANCE_ID = args.instance           # noqa: F811
    uvicorn.run(app, host=args.host, port=args.port)
