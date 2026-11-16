from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from pgvector.sqlalchemy import Vector
from db import Base, engine

class SpecChunk(Base):
    __tablename__ = "spec_chunks"

    id: Mapped[int] = mapped_column(primary_key=True)
    phone_name: Mapped[str] = mapped_column(String(120), index=True)
    category: Mapped[str] = mapped_column(String(80))
    label: Mapped[str] = mapped_column(String(120))
    value: Mapped[str] = mapped_column(Text)
    embedding: Mapped[list[float]] = mapped_column(Vector(384))

if __name__ == "__main__":
    Base.metadata.create_all(engine)
    from sqlalchemy import inspect
    print("tables:", inspect(engine).get_table_names())
