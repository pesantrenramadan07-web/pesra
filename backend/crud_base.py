from fastapi import HTTPException
from bson import ObjectId
from bson.errors import InvalidId


def _clean(value):
    """Recursively convert ObjectId to str inside dicts/lists so JSON encoders don't choke."""
    if isinstance(value, ObjectId):
        return str(value)
    if isinstance(value, dict):
        return {k: _clean(v) for k, v in value.items() if k != "_id"}
    if isinstance(value, list):
        return [_clean(v) for v in value]
    return value


def doc_out(doc: dict) -> dict:
    if not doc:
        return doc
    doc = dict(doc)
    doc["id"] = str(doc.pop("_id"))
    return {k: _clean(v) for k, v in doc.items()}


def oid(id_str: str):
    try:
        return ObjectId(id_str)
    except (InvalidId, TypeError):
        raise HTTPException(status_code=404, detail="Data tidak ditemukan")


def is_oid(s) -> bool:
    try:
        ObjectId(s)
        return True
    except Exception:
        return False
