"""Small Markdown structure helpers for repository-facing validators."""

from __future__ import annotations

import re


FENCE_OPEN_RE = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")
HEADING_RE = re.compile(r"^(#{1,6})[ \t]+(.+?)[ \t]*#*[ \t]*$")


def strip_fenced_code(markdown: str) -> str:
    """Blank fenced code while preserving line boundaries for Markdown checks."""
    output: list[str] = []
    fence_char: str | None = None
    fence_length = 0
    for line in markdown.splitlines(keepends=True):
        body = line.rstrip("\r\n")
        if fence_char is not None:
            match = re.match(r"^ {0,3}(`+|~+)[ \t]*$", body)
            if match and match.group(1)[0] == fence_char and len(match.group(1)) >= fence_length:
                fence_char = None
                fence_length = 0
            output.append("\r\n" if line.endswith("\r\n") else "\n" if line.endswith("\n") else "")
            continue

        match = FENCE_OPEN_RE.match(body)
        if match:
            marker, info = match.groups()
            if marker[0] != "`" or "`" not in info:
                fence_char = marker[0]
                fence_length = len(marker)
                output.append("\r\n" if line.endswith("\r\n") else "\n" if line.endswith("\n") else "")
                continue
        output.append(line)
    return "".join(output)


def markdown_headings(markdown: str) -> list[dict[str, int | str]]:
    """Return ATX headings outside fenced code with their zero-based line index."""
    visible = strip_fenced_code(markdown)
    headings: list[dict[str, int | str]] = []
    for line_number, line in enumerate(visible.splitlines()):
        match = HEADING_RE.match(line)
        if not match:
            continue
        headings.append({
            "level": len(match.group(1)),
            "title": match.group(2).strip(),
            "line": line_number,
        })
    return headings


def markdown_section_block(markdown: str, heading_level: int, heading_title: str) -> str | None:
    """Return one raw heading section, using visible headings for its bounds.

    Fenced code cannot create or satisfy a heading boundary, but it remains
    section content: code examples can carry current-state or operating-method
    meaning and therefore participate in change classification.
    """
    lines = markdown.splitlines()
    headings = markdown_headings(markdown)
    matches = [item for item in headings if item["level"] == heading_level and item["title"] == heading_title]
    if len(matches) != 1:
        return None
    start = int(matches[0]["line"])
    end = next(
        (int(item["line"]) for item in headings if int(item["line"]) > start and int(item["level"]) <= heading_level),
        len(lines),
    )
    return "\n".join(lines[start:end]).rstrip()
