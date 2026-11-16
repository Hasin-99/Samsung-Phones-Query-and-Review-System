import os
from datetime import datetime, timezone

from dotenv import load_dotenv
from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text, create_engine, inspect
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
    sessionmaker,
)

load_dotenv()

engine = create_engine(os.environ["DATABASE_URL"], pool_pre_ping=True)
SessionLocal = sessionmaker(engine)


def now_utc():
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class Phone(Base):
    __tablename__ = "phones"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True)
    gsmarena_id: Mapped[int | None] = mapped_column(unique=True)
    url: Mapped[str | None] = mapped_column(String(300))
    image_url: Mapped[str | None] = mapped_column(String(300))
    scraped_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)

    specifications: Mapped[list["Specification"]] = relationship(
        back_populates="phone", cascade="all, delete-orphan"
    )
    features: Mapped["PhoneFeature | None"] = relationship(
        back_populates="phone", cascade="all, delete-orphan", uselist=False
    )
    prices: Mapped[list["Price"]] = relationship(
        back_populates="phone", cascade="all, delete-orphan"
    )


class Specification(Base):
    """Complete raw copy: one row per label/value row on the GSMArena spec page."""

    __tablename__ = "specifications"

    id: Mapped[int] = mapped_column(primary_key=True)
    phone_id: Mapped[int] = mapped_column(ForeignKey("phones.id", ondelete="CASCADE"), index=True)
    category: Mapped[str] = mapped_column(String(80))
    label: Mapped[str] = mapped_column(String(120))
    value: Mapped[str] = mapped_column(Text)

    phone: Mapped["Phone"] = relationship(back_populates="specifications")


class PhoneFeature(Base):
    """Clean typed values extracted from the raw rows, used for ranking and comparing."""

    __tablename__ = "phone_features"

    phone_id: Mapped[int] = mapped_column(
        ForeignKey("phones.id", ondelete="CASCADE"), primary_key=True
    )
    release_year: Mapped[int | None]
    os: Mapped[str | None] = mapped_column(String(200))
    chipset: Mapped[str | None] = mapped_column(String(200))
    display_size_in: Mapped[float | None]
    display_type: Mapped[str | None] = mapped_column(String(200))
    resolution: Mapped[str | None] = mapped_column(String(120))
    ram_gb: Mapped[int | None]
    storage_options: Mapped[str | None] = mapped_column(String(200))
    main_camera_mp: Mapped[float | None]
    selfie_camera_mp: Mapped[float | None]
    weight_g: Mapped[float | None]
    battery_mah: Mapped[int | None]
    charging_w: Mapped[int | None]
    active_use_score_h: Mapped[float | None]
    endurance_rating_h: Mapped[float | None]

    phone: Mapped["Phone"] = relationship(back_populates="features")


class Price(Base):
    __tablename__ = "prices"

    id: Mapped[int] = mapped_column(primary_key=True)
    phone_id: Mapped[int] = mapped_column(ForeignKey("phones.id", ondelete="CASCADE"), index=True)
    amount: Mapped[float | None] = mapped_column(Numeric(10, 2))
    currency: Mapped[str | None] = mapped_column(String(10))
    variant: Mapped[str | None] = mapped_column(String(60))
    store: Mapped[str | None] = mapped_column(String(80))
    source: Mapped[str] = mapped_column(String(20))
    raw_text: Mapped[str | None] = mapped_column(Text)
    scraped_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)

    phone: Mapped["Phone"] = relationship(back_populates="prices")


if __name__ == "__main__":
    Base.metadata.create_all(engine)
    inspector = inspect(engine)
    for table in inspector.get_table_names():
        columns = [c["name"] for c in inspector.get_columns(table)]
        print(f"{table}: {', '.join(columns)}")
