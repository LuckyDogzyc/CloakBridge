from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZIP_DEFLATED, ZipFile

from lxml import etree

from cloakbridge.domain.entities import Finding
from cloakbridge.domain.tokens import TokenMap


W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
TEXT_TAG = f"{{{W_NS}}}t"


class DocxProcessor:
    def sanitize(self, source: Path, output: Path, findings: list[Finding], token_map: TokenMap) -> None:
        replacements = {finding.text: token_map.token_for(finding) for finding in findings}
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            with ZipFile(source) as archive:
                archive.extractall(tmp_path)
            document_path = tmp_path / "word" / "document.xml"
            self._replace_in_xml(document_path, replacements)
            self._zip_dir(tmp_path, output)

    def _replace_in_xml(self, xml_path: Path, replacements: dict[str, str]) -> None:
        parser = etree.XMLParser(remove_blank_text=False)
        tree = etree.parse(str(xml_path), parser)
        paragraph_nodes = tree.xpath("//w:p", namespaces={"w": W_NS})
        for paragraph in paragraph_nodes:
            nodes = paragraph.xpath(".//w:t", namespaces={"w": W_NS})
            if not nodes:
                continue
            original_parts = [node.text or "" for node in nodes]
            combined = "".join(original_parts)
            replaced = self._replace_text(combined, replacements)
            if replaced == combined:
                continue
            self._redistribute_text(nodes, original_parts, replaced)
        tree.write(str(xml_path), encoding="UTF-8", xml_declaration=True, standalone=True)

    def _replace_text(self, text: str, replacements: dict[str, str]) -> str:
        result = text
        for original, token in sorted(replacements.items(), key=lambda item: -len(item[0])):
            result = result.replace(original, token)
        return result

    def _redistribute_text(
        self,
        nodes: list[etree._Element],
        original_parts: list[str],
        replaced: str,
    ) -> None:
        cursor = 0
        last_index = len(nodes) - 1
        for index, node in enumerate(nodes):
            if index == last_index:
                node.text = replaced[cursor:]
            else:
                width = len(original_parts[index])
                node.text = replaced[cursor : cursor + width]
                cursor += width
            if node.text == "":
                node.set(f"{{{W_NS}}}space", "preserve")

    def _zip_dir(self, source_dir: Path, output: Path) -> None:
        with ZipFile(output, "w", ZIP_DEFLATED) as archive:
            for path in sorted(source_dir.rglob("*")):
                if path.is_file():
                    archive.write(path, path.relative_to(source_dir).as_posix())
