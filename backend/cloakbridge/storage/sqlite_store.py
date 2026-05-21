from __future__ import annotations

import sqlite3
from pathlib import Path


class SQLiteStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.path)

    def initialize(self) -> None:
        self.connection.execute(
            """
            create table if not exists dictionary_entries (
              id integer primary key autoincrement,
              text text not null,
              entity_type text not null,
              scope text not null,
              status text not null,
              source text not null default 'user',
              confidence real not null default 1.0,
              created_at text not null default current_timestamp,
              updated_at text not null default current_timestamp
            )
            """
        )
        self.connection.execute(
            "create index if not exists idx_dictionary_scope_status on dictionary_entries(scope, status)"
        )
        self.connection.commit()
