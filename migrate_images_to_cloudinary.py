"""
Migration : base64 DB → Cloudinary URLs
Usage: python migrate_images_to_cloudinary.py
"""
import asyncio
import base64
import os
import sys
import cloudinary
import cloudinary.uploader
from dotenv import load_dotenv
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

load_dotenv()

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
    secure=True,
)

DATABASE_URL = os.getenv("DATABASE_URL", "").replace("postgresql://", "postgresql+psycopg://")


async def migrate():
    from models import Product

    engine = create_async_engine(DATABASE_URL, echo=False)
    Session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with Session() as session:
        result = await session.execute(select(Product))
        products = result.scalars().all()
        print(f"Found {len(products)} products")

        for product in products:
            if not product.images:
                continue

            new_images = []
            changed = False

            for img in product.images:
                if img.startswith("data:"):
                    # Extract base64 content
                    header, b64data = img.split(",", 1)
                    mime = header.split(":")[1].split(";")[0]
                    raw = base64.b64decode(b64data)

                    print(f"  Uploading image for '{product.name}' ({len(raw)//1024} KB)...")
                    upload_result = cloudinary.uploader.upload(
                        raw,
                        folder="genetics/products",
                        resource_type="image",
                        public_id=f"product_{product.id}_{len(new_images)}",
                        overwrite=True,
                    )
                    new_images.append(upload_result["secure_url"])
                    changed = True
                    print(f"    → {upload_result['secure_url']}")
                else:
                    new_images.append(img)

            if changed:
                product.images = new_images
                await session.flush()
                print(f"  ✓ Product '{product.name}' updated")

        await session.commit()
        print("\nMigration complete!")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(migrate(), loop_factory=asyncio.SelectorEventLoop)
