from pathlib import Path
from zipfile import ZipFile

from lxml import etree

from cloakbridge.documents.docx_processor import DocxProcessor
from cloakbridge.domain.entities import EntityType, Finding
from cloakbridge.domain.tokens import TokenMap
from fixtures import write_minimal_docx


W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


def read_docx_document_xml(path: Path) -> str:
    with ZipFile(path) as archive:
        return archive.read("word/document.xml").decode("utf-8")


def read_docx_text(path: Path) -> str:
    xml = read_docx_document_xml(path)
    root = etree.fromstring(xml.encode("utf-8"))
    return "".join(root.xpath("//w:t/text()", namespaces={"w": W_NS}))


def test_docx_processor_replaces_text_without_removing_run_style(tmp_path: Path):
    source = tmp_path / "input.docx"
    output = tmp_path / "sanitized.docx"
    write_minimal_docx(
        source,
        """
        <w:p>
          <w:r><w:rPr><w:b/><w:color w:val="FF0000"/></w:rPr><w:t>华东</w:t></w:r>
          <w:r><w:rPr><w:b/><w:color w:val="FF0000"/></w:rPr><w:t>三期项目</w:t></w:r>
        </w:p>
        """,
    )
    token_map = TokenMap()
    findings = [Finding("华东三期项目", EntityType.PROJECT, 0, 6, "user", 1.0)]

    DocxProcessor().sanitize(source, output, findings, token_map)

    xml = read_docx_document_xml(output)
    assert "<PROJECT_001>" in read_docx_text(output)
    assert 'w:val="FF0000"' in xml
    assert "<w:b" in xml


def test_docx_processor_reuses_shared_token_map_across_files(tmp_path: Path):
    first = tmp_path / "first.docx"
    second = tmp_path / "second.docx"
    first_output = tmp_path / "first.sanitized.docx"
    second_output = tmp_path / "second.sanitized.docx"
    write_minimal_docx(first, "<w:p><w:r><w:t>华东三期项目</w:t></w:r></w:p>")
    write_minimal_docx(second, "<w:p><w:r><w:t>复核华东三期项目</w:t></w:r></w:p>")
    token_map = TokenMap()

    DocxProcessor().sanitize(
        first,
        first_output,
        [Finding("华东三期项目", EntityType.PROJECT, 0, 6, "user", 1.0)],
        token_map,
    )
    DocxProcessor().sanitize(
        second,
        second_output,
        [Finding("华东三期项目", EntityType.PROJECT, 2, 8, "user", 1.0)],
        token_map,
    )

    assert "<PROJECT_001>" in read_docx_text(first_output)
    assert "<PROJECT_001>" in read_docx_text(second_output)
