from sentence_transformers import SentenceTransformer
from sqlalchemy import select, text
from db import SessionLocal, Phone, Specification
from rag_schema import SpecChunk

MODEL = "sentence-transformers/all-MiniLM-L6-v2"

def main():
    model = SentenceTransformer(MODEL)
    print(f"Loaded {MODEL} (dim={model.get_sentence_embedding_dimension()})")

    with SessionLocal() as s:
        # Fresh build every time
        s.execute(text("TRUNCATE spec_chunks RESTART IDENTITY"))
        phones = s.scalars(select(Phone)).all()
        total = 0
        for phone in phones:
            specs = s.scalars(
                select(Specification).where(Specification.phone_id == phone.id)
            ).all()
            texts = [f"{phone.name} — {sp.category} / {sp.label}: {sp.value}" for sp in specs]
            embs = model.encode(texts, batch_size=32, normalize_embeddings=True, show_progress_bar=False)
            for sp, emb, txt in zip(specs, embs, texts):
                s.add(SpecChunk(
                    phone_name=phone.name, category=sp.category,
                    label=sp.label, value=sp.value,
                    embedding=emb.tolist(),
                ))
            total += len(specs)
            print(f"  {phone.name:28} {len(specs):>3} chunks")
        s.commit()
        print(f"\nTotal chunks embedded: {total}")

if __name__ == "__main__":
    main()
