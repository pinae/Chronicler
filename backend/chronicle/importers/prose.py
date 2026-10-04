"""Plain-text and Project Gutenberg books as `literature` story transcripts (concept §9.1, R1).

Each paragraph becomes one narrator utterance, numbered by the chapter it belongs to."""

import re
from dataclasses import dataclass

GUTENBERG_START = re.compile(
    r"^\*\*\*\s*START OF (THE|THIS) PROJECT GUTENBERG EBOOK.*$", re.IGNORECASE | re.MULTILINE
)
GUTENBERG_END = re.compile(
    r"^\*\*\*\s*END OF (THE|THIS) PROJECT GUTENBERG EBOOK.*$", re.IGNORECASE | re.MULTILINE
)
GUTENBERG_TITLE = re.compile(r"^Title:\s*(.+)$", re.MULTILINE)
GUTENBERG_EBOOK = re.compile(r"\[e-?book #(\d+)\]", re.IGNORECASE)
CHAPTER_HEADING = re.compile(r"^chapter\s+([ivxlcdm]+|\d+)\b", re.IGNORECASE)
MAX_HEADING_LINES = 3  # "CHAPTER I." plus a title of a line or two
BLANK_LINES = re.compile(r"\n\s*\n")


@dataclass(frozen=True)
class ProseParagraph:
    chapter: int
    text: str


@dataclass(frozen=True)
class ProseTranscript:
    title: str | None
    gutenberg_ebook: int | None
    paragraphs: list[ProseParagraph]

    @property
    def chapter_count(self) -> int:
        return len({paragraph.chapter for paragraph in self.paragraphs})


def parse_prose(text: str) -> ProseTranscript:
    header, body = split_gutenberg(text.replace("\r\n", "\n"))
    title = GUTENBERG_TITLE.search(header)
    ebook = GUTENBERG_EBOOK.search(header)
    return ProseTranscript(
        title=title.group(1).strip() if title else None,
        gutenberg_ebook=int(ebook.group(1)) if ebook else None,
        paragraphs=paragraphs_by_chapter(blocks(body)),
    )


def split_gutenberg(text: str) -> tuple[str, str]:
    """(Project Gutenberg header, the book itself). A text without the markers is all book."""
    start = GUTENBERG_START.search(text)
    if start is None:
        return "", text
    end = GUTENBERG_END.search(text, start.end())
    return text[: start.start()], text[start.end() : end.start() if end else len(text)]


def blocks(body: str) -> list[list[str]]:
    """Runs of non-blank lines, each line stripped."""
    return [
        [line.strip() for line in block.splitlines() if line.strip()]
        for block in BLANK_LINES.split(body)
        if block.strip()
    ]


def paragraphs_by_chapter(text_blocks: list[list[str]]) -> list[ProseParagraph]:
    """Chapters are counted from the headings that are followed by text, so a table of contents
    adds none. Text before the first heading is front matter, unless the book has no headings."""
    has_headings = any(is_heading(block) for block in text_blocks)
    chapter = 0 if has_headings else 1
    heading_pending = False
    paragraphs = []
    for block in text_blocks:
        if is_heading(block):
            heading_pending = True
            continue
        if not is_prose(block):
            continue
        if heading_pending:
            chapter, heading_pending = chapter + 1, False
        if chapter > 0:
            paragraphs.append(ProseParagraph(chapter=chapter, text=" ".join(" ".join(block).split())))
    return paragraphs


def is_heading(block: list[str]) -> bool:
    return len(block) <= MAX_HEADING_LINES and CHAPTER_HEADING.match(block[0]) is not None


def is_prose(block: list[str]) -> bool:
    """Skips decorations ("* * *") and editorial notes ("[Illustration]")."""
    text = " ".join(block)
    is_editorial_note = text.startswith("[") and text.endswith("]")
    return any(character.isalpha() for character in text) and not is_editorial_note
