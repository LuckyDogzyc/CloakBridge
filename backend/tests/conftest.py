from __future__ import annotations

import pytest


@pytest.fixture()
def sample_chinese_text() -> str:
    return "华东三期项目由上海明远科技有限公司负责，服务器IP为10.18.2.4。"
