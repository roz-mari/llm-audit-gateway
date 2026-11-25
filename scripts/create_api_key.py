"""Usage: python -m scripts.create_api_key "my laptop" """

import sys

from app.db import Base, SessionLocal, engine
from app.models import ApiKey
from app.security import generate_key, hash_key

name = sys.argv[1] if len(sys.argv) > 1 else "default"
Base.metadata.create_all(engine)

key = generate_key()
with SessionLocal() as db:
    db.add(ApiKey(name=name, key_hash=hash_key(key)))
    db.commit()

print(f"API key for {name} (save it, it won't be shown again):")
print(key)
