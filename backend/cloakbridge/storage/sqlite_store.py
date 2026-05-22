from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any


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
            """
            create table if not exists alias_groups (
              id integer primary key autoincrement,
              entity_type text not null,
              canonical text not null,
              scope text not null,
              created_at text not null default current_timestamp,
              updated_at text not null default current_timestamp
            )
            """
        )
        self.connection.execute(
            """
            create table if not exists alias_entries (
              id integer primary key autoincrement,
              group_id integer not null references alias_groups(id) on delete cascade,
              text text not null,
              surface_index integer not null,
              status text not null default 'confirmed',
              created_at text not null default current_timestamp,
              unique(group_id, text)
            )
            """
        )
        self.connection.execute(
            """
            create table if not exists model_configs (
              id integer primary key autoincrement,
              name text not null,
              provider text not null,
              model text not null,
              base_url text not null default '',
              secret_ref text,
              masked_api_key text not null default '未设置',
              enabled integer not null default 1,
              created_at text not null default current_timestamp,
              updated_at text not null default current_timestamp
            )
            """
        )
        self.connection.execute(
            "create index if not exists idx_dictionary_scope_status on dictionary_entries(scope, status)"
        )
        self.connection.execute(
            "create index if not exists idx_alias_groups_scope_type on alias_groups(scope, entity_type)"
        )
        self.connection.execute(
            "create index if not exists idx_alias_entries_text_status on alias_entries(text, status)"
        )
        self.connection.execute(
            "create index if not exists idx_model_configs_provider_enabled on model_configs(provider, enabled)"
        )
        self.connection.commit()

    def create_alias_group(
        self,
        entity_type: str,
        canonical: str,
        aliases: list[str],
        scope: str,
    ) -> dict[str, Any]:
        normalized_aliases = self._dedupe_aliases([canonical, *aliases])
        with self.connection:
            cursor = self.connection.execute(
                "insert into alias_groups (entity_type, canonical, scope) values (?, ?, ?)",
                (entity_type, canonical, scope),
            )
            group_id = int(cursor.lastrowid)
            self.connection.executemany(
                "insert into alias_entries (group_id, text, surface_index) values (?, ?, ?)",
                [
                    (group_id, alias, surface_index)
                    for surface_index, alias in enumerate(normalized_aliases, start=1)
                ],
            )
        return {
            "id": group_id,
            "entity_type": entity_type,
            "canonical": canonical,
            "aliases": normalized_aliases,
            "scope": scope,
        }

    def list_alias_groups(self, scope: str | None = None) -> list[dict[str, Any]]:
        params: tuple[str, ...] = () if scope is None else (scope,)
        where = "" if scope is None else "where scope = ?"
        rows = self.connection.execute(
            f"""
            select id, entity_type, canonical, scope
            from alias_groups
            {where}
            order by id
            """,
            params,
        ).fetchall()
        return [self._alias_group_from_row(row) for row in rows]

    def create_model_config(
        self,
        name: str,
        provider: str,
        model: str,
        base_url: str,
        secret_ref: str | None = None,
        masked_api_key: str = "未设置",
        enabled: bool = True,
    ) -> dict[str, Any]:
        with self.connection:
            cursor = self.connection.execute(
                """
                insert into model_configs
                  (name, provider, model, base_url, secret_ref, masked_api_key, enabled)
                values (?, ?, ?, ?, ?, ?, ?)
                """,
                (name, provider, model, base_url, secret_ref, masked_api_key, int(enabled)),
            )
            config_id = int(cursor.lastrowid)
        return self.get_model_config(config_id)

    def update_model_config_secret(self, config_id: int, secret_ref: str, masked_api_key: str) -> dict[str, Any]:
        with self.connection:
            self.connection.execute(
                """
                update model_configs
                set secret_ref = ?, masked_api_key = ?, updated_at = current_timestamp
                where id = ?
                """,
                (secret_ref, masked_api_key, config_id),
            )
        return self.get_model_config(config_id)

    def list_model_configs(self) -> list[dict[str, Any]]:
        rows = self.connection.execute(
            """
            select id, name, provider, model, base_url, secret_ref, masked_api_key, enabled
            from model_configs
            order by id
            """
        ).fetchall()
        return [self._model_config_from_row(row) for row in rows]

    def get_model_config(self, config_id: int) -> dict[str, Any]:
        row = self.connection.execute(
            """
            select id, name, provider, model, base_url, secret_ref, masked_api_key, enabled
            from model_configs
            where id = ?
            """,
            (config_id,),
        ).fetchone()
        if row is None:
            raise KeyError(f"Model config not found: {config_id}")
        return self._model_config_from_row(row)

    def _alias_group_from_row(self, row: tuple[int, str, str, str]) -> dict[str, Any]:
        group_id, entity_type, canonical, scope = row
        alias_rows = self.connection.execute(
            """
            select text
            from alias_entries
            where group_id = ? and status = 'confirmed'
            order by surface_index
            """,
            (group_id,),
        ).fetchall()
        return {
            "id": group_id,
            "entity_type": entity_type,
            "canonical": canonical,
            "aliases": [alias_row[0] for alias_row in alias_rows],
            "scope": scope,
        }

    def _model_config_from_row(self, row: tuple[int, str, str, str, str, str | None, str, int]) -> dict[str, Any]:
        config_id, name, provider, model, base_url, secret_ref, masked_api_key, enabled = row
        return {
            "id": config_id,
            "name": name,
            "provider": provider,
            "model": model,
            "base_url": base_url,
            "secret_ref": secret_ref,
            "masked_api_key": masked_api_key,
            "enabled": bool(enabled),
        }

    def _dedupe_aliases(self, aliases: list[str]) -> list[str]:
        seen: set[str] = set()
        result: list[str] = []
        for alias in aliases:
            cleaned = alias.strip()
            if not cleaned or cleaned in seen:
                continue
            seen.add(cleaned)
            result.append(cleaned)
        return result
