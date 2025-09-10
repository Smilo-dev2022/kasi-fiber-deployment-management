from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
import uuid
import csv
from io import StringIO
from app.core.deps import get_scoped_db
from app.models.topology import TopoNode, TopoEdge
from app.schemas.topology import TopologyOut, TopologyEdgesImportResult, TopoNodeOut, TopoEdgeOut


router = APIRouter(prefix="/topology", tags=["topology"])


@router.get("/pon/{pon_id}", response_model=TopologyOut)
def get_topology(pon_id: str, db: Session = Depends(get_scoped_db)):
    pon_uuid = UUID(pon_id)
    nodes = db.query(TopoNode).filter(TopoNode.pon_id == pon_uuid).all()
    edges = db.query(TopoEdge).filter(TopoEdge.pon_id == pon_uuid).all()
    return TopologyOut(nodes=nodes, edges=edges)


@router.post("/edges", response_model=TopologyEdgesImportResult)
def import_edges_csv(pon_id: str, file: UploadFile = File(...), db: Session = Depends(get_scoped_db)):
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(400, "CSV required")
    content = file.file.read().decode("utf-8")
    reader = csv.DictReader(StringIO(content))
    required = {"a_code", "b_code", "cable_code", "length_m"}
    if not required.issubset(set(reader.fieldnames or [])):
        raise HTTPException(400, "CSV headers must include a_code,b_code,cable_code,length_m")
    created_nodes = 0
    created_edges = 0
    updated_edges = 0
    skipped = 0
    pon_uuid = UUID(pon_id)

    code_to_node: dict[str, TopoNode] = {}
    existing_nodes: List[TopoNode] = db.query(TopoNode).filter(TopoNode.pon_id == pon_uuid).all()
    for n in existing_nodes:
        code_to_node[n.code] = n

    for row in reader:
        a_code = (row.get("a_code") or "").strip()
        b_code = (row.get("b_code") or "").strip()
        cable_code = (row.get("cable_code") or "").strip()
        length_m = row.get("length_m")
        if not a_code or not b_code:
            skipped += 1
            continue
        # ensure nodes exist
        for code in (a_code, b_code):
            if code not in code_to_node:
                node = TopoNode(id=uuid.uuid4(), pon_id=pon_uuid, type="closure", code=code)
                db.add(node)
                db.flush()
                code_to_node[code] = node
                created_nodes += 1
        a_id = code_to_node[a_code].id
        b_id = code_to_node[b_code].id
        # upsert edge: try find existing by pair and cable_code
        edge = (
            db.query(TopoEdge)
            .filter(TopoEdge.pon_id == pon_uuid)
            .filter(TopoEdge.a_id == a_id)
            .filter(TopoEdge.b_id == b_id)
            .first()
        )
        if edge:
            edge.cable_code = cable_code or edge.cable_code
            try:
                edge.length_m = float(length_m) if length_m not in (None, "") else edge.length_m
            except ValueError:
                pass
            updated_edges += 1
        else:
            try:
                length_val = float(length_m) if length_m not in (None, "") else None
            except ValueError:
                length_val = None
            new_edge = TopoEdge(id=uuid.uuid4(), pon_id=pon_uuid, a_id=a_id, b_id=b_id, cable_code=cable_code or None, length_m=length_val)
            db.add(new_edge)
            created_edges += 1

    db.commit()
    return TopologyEdgesImportResult(created_nodes=created_nodes, created_edges=created_edges, updated_edges=updated_edges, skipped=skipped)

