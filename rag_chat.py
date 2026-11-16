import os
import re
from functools import lru_cache
from dotenv import load_dotenv
from groq import Groq
from sentence_transformers import SentenceTransformer
from sqlalchemy import select, text
from db import SessionLocal, engine
from rag_schema import SpecChunk

load_dotenv(".env")

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
LLM = "openai/gpt-oss-20b"

@lru_cache(maxsize=1)
def _embedder():
    return SentenceTransformer(MODEL_NAME)

@lru_cache(maxsize=1)
def _client():
    return Groq(api_key=os.environ["GROQ_API_KEY"])

@lru_cache(maxsize=1)
def _phone_names():
    with SessionLocal() as s:
        return [r[0] for r in s.execute(
            text("select distinct phone_name from spec_chunks order by phone_name")
        )]

def retrieve(query: str, k: int = 6) -> list[SpecChunk]:
    q = _embedder().encode(query, normalize_embeddings=True).tolist()
    with SessionLocal() as s:
        return s.scalars(
            select(SpecChunk)
            .order_by(SpecChunk.embedding.cosine_distance(q))
            .limit(k)
        ).all()

def _mentioned_phones(query: str) -> list[str]:
    """Detect which DB phones the user is asking about (2+ → comparison)."""
    q = query.lower()
    q_models = {t.lower() for t in re.findall(r'\b[sSaA]\d+\b', q)}
    hits = []
    for name in _phone_names():
        short = name.lower().replace("samsung galaxy ", "").strip()
        m = re.match(r'([sa]\d+)(.*)', short)
        if not m:
            continue
        model, suffix = m.group(1), m.group(2).strip()
        if model not in q_models:
            continue
        if suffix:
            suffix_tokens = [t for t in suffix.split() if t != "5g"]
            if suffix_tokens and not all(t in q for t in suffix_tokens):
                continue
        hits.append(name)
    return hits

def retrieve_multi(query: str, k_per: int = 5) -> list[SpecChunk]:
    """For 2+ phone queries, retrieve k_per chunks per phone — not globally."""
    phones = _mentioned_phones(query)
    if len(phones) < 2:
        return retrieve(query, k=6)
    q = _embedder().encode(query, normalize_embeddings=True).tolist()
    chunks = []
    with SessionLocal() as s:
        for phone in phones:
            rows = s.scalars(
                select(SpecChunk)
                .where(SpecChunk.phone_name == phone)
                .order_by(SpecChunk.embedding.cosine_distance(q))
                .limit(k_per)
            ).all()
            chunks.extend(rows)
    return chunks

def structured_answer(query: str) -> dict | None:
    """For 'best X' queries, use SQL directly — with the RIGHT metric + tie handling."""
    q = query.lower()
    if not any(w in q for w in ("best", "highest", "largest", "biggest", "most")):
        return None

    if "battery" in q or "endurance" in q:
        with engine.connect() as c:
            for col, label, unit in (
                ("active_use_score_h", "active use score", "h"),
                ("endurance_rating_h", "endurance rating", "h"),
                ("battery_mah", "battery capacity", "mAh"),
            ):
                rows = c.execute(text(
                    f"select p.name, f.{col} from phones p "
                    f"join phone_features f on f.phone_id = p.id "
                    f"where f.{col} is not null "
                    f"order by f.{col} desc, p.name asc"
                )).all()
                if not rows:
                    continue
                top_val = rows[0][1]
                tied = [(n, v) for n, v in rows if v == top_val]
                runners = [(n, v) for n, v in rows if v < top_val][:3]
                if len(tied) == 1:
                    ans = f"By {label} ({unit}), the top phone is the {tied[0][0]} at {tied[0][1]}{unit}."
                else:
                    names = ", ".join(n for n, _ in tied)
                    ans = f"By {label} ({unit}), {len(tied)} phones tie at {top_val}{unit}: {names}."
                if runners:
                    ans += " Runners-up: " + ", ".join(f"{n} ({v}{unit})" for n, v in runners) + "."
                ans += f" Metric used: {col}."
                return {"answer": ans, "sources": [f"SQL: max({col}) from phone_features"]}

    fields = {
        "camera": ("main_camera_mp", "main camera", "MP"),
        "screen": ("display_size_in", "display size", "in"),
        "ram": ("ram_gb", "RAM", "GB"),
    }
    for kw, (col, label, unit) in fields.items():
        if kw in q:
            with engine.connect() as c:
                rows = c.execute(text(
                    f"select p.name, f.{col} from phones p "
                    f"join phone_features f on f.phone_id = p.id "
                    f"where f.{col} is not null "
                    f"order by f.{col} desc, p.name asc"
                )).all()
            if not rows:
                continue
            top_val = rows[0][1]
            tied = [(n, v) for n, v in rows if v == top_val]
            runners = [(n, v) for n, v in rows if v < top_val][:3]
            if len(tied) == 1:
                ans = f"By {label} ({unit}), the top phone is the {tied[0][0]} at {tied[0][1]}{unit}."
            else:
                names = ", ".join(n for n, _ in tied)
                ans = f"By {label} ({unit}), {len(tied)} phones tie at {top_val}{unit}: {names}."
            if runners:
                ans += " Runners-up: " + ", ".join(f"{n} ({v}{unit})" for n, v in runners) + "."
            return {"answer": ans, "sources": [f"SQL: max({col}) from phone_features"]}

    return None


def answer(query: str, k: int = 6) -> dict:
    if (r := structured_answer(query)):
        return r
    chunks = retrieve_multi(query)
    context = "\n".join(
        f"- {c.phone_name} | {c.category} | {c.label}: {c.value}" for c in chunks
    )
    prompt = (
        "You are a Samsung phone expert. Use ONLY the context below. "
        "If the answer is not in the context, say so.\n\n"
        f"Context:\n{context}\n\nQuestion: {query}\nAnswer concisely:"
    )
    resp = _client().chat.completions.create(
        model=LLM,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2, max_tokens=800, reasoning_effort="low",
    )
    text = (resp.choices[0].message.content or "").strip()
    return {
        "answer": text or "[empty answer — try again]",
        "sources": [f"{c.phone_name} → {c.category}/{c.label}" for c in chunks],
    }

if __name__ == "__main__":
    import sys
    q = " ".join(sys.argv[1:]) or "What is the camera of the Samsung Galaxy S23?"
    print(f"Q: {q}\n")
    r = answer(q)
    print(f"A: {r['answer']}\n")
    print("Sources:")
    for s in r["sources"]:
        print(f"  - {s}")
