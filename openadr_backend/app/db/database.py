from databases import Database
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost/openadr")

database = Database(DATABASE_URL)
