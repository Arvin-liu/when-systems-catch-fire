"""Small Markdown structure helpers for repository-facing validators."""

from __future__ import annotations

import re


FENCE_OPEN_RE = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")
HEADING_RE = re.compile(r"^(#{1,6})[ \t]+(.+?)[ \t]*#*[ \t]*$")
DETAILS_OPEN_RE = re.compile(r"<details(?=[\s>])([^>]*)>", re.IGNORECASE)
DETAILS_CLOSE_RE = re.compile(r"</details\s*>", re.IGNORECASE)


def _blank_range(output: list[str], start: int, end: int) -> None:
    for index in range(start, end):
        if output[index] not in "\r\n":
            output[index] = " "


def _backtick_run_end(text: str, start: int) -> int:
    end = start + 1
    while end < len(text) and text[end] == "`":
        end += 1
    return end


def _inline_code_span_end(text: str, start: int, opening_end: int) -> int | None:
    width = opening_end - start
    cursor = opening_end
    while True:
        candidate = text.find("`", cursor)
        if candidate < 0:
            return None
        end = _backtick_run_end(text, candidate)
        if end - candidate == width:
            return end
        cursor = end


def strip_nonvisible_markup(markdown: str) -> str:
    """Blank fenced code, HTML comments, and collapsed details blocks.

    Newlines are preserved so heading line numbers remain stable. Inline code
    spans are skipped while recognizing HTML markers, since their contents are
    rendered as code rather than interpreted as comments or details tags.
    Unclosed comments or details tags hide the remaining input (fail closed).
    """
    source = strip_fenced_code(markdown)
    output = list(source)
    collapsed_details: list[bool] = []
    index = 0

    while index < len(source):
        hidden = collapsed_details[-1] if collapsed_details else False

        if source[index] == "`":
            backslashes = 0
            previous = index - 1
            while previous >= 0 and source[previous] == "\\":
                backslashes += 1
                previous -= 1
            opening_end = _backtick_run_end(source, index)
            closing_end = None if backslashes % 2 else _inline_code_span_end(source, index, opening_end)
            if closing_end is not None:
                if hidden:
                    _blank_range(output, index, closing_end)
                index = closing_end
                continue

        if source.startswith("<!--", index):
            close_start = source.find("-->", index + 4)
            close_end = len(source) if close_start < 0 else close_start + 3
            _blank_range(output, index, close_end)
            index = close_end
            if close_start < 0:
                break
            continue

        opening = DETAILS_OPEN_RE.match(source, index)
        if opening:
            inherited_hidden = collapsed_details[-1] if collapsed_details else False
            is_expanded = re.search(r"(?:^|\s)open(?:\s|=|$)", opening.group(1), re.IGNORECASE) is not None
            hidden = inherited_hidden or not is_expanded
            collapsed_details.append(hidden)
            if hidden:
                _blank_range(output, index, opening.end())
            index = opening.end()
            continue

        # A malformed opening details tag has uncertain visibility. Hide the
        # remainder instead of allowing headings after it to satisfy a gate.
        if source[index:index + 8].casefold() == "<details" and (
            index + 8 == len(source) or source[index + 8].isspace() or source[index + 8] == ">"
        ):
            _blank_range(output, index, len(source))
            break

        closing = DETAILS_CLOSE_RE.match(source, index)
        if closing:
            hidden = collapsed_details[-1] if collapsed_details else False
            if hidden:
                _blank_range(output, index, closing.end())
            if collapsed_details:
                collapsed_details.pop()
            index = closing.end()
            continue

        if hidden and source[index] not in "\r\n":
            output[index] = " "
        index += 1

    return "".join(output)


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
    """Return visible ATX headings with their zero-based line index."""
    visible = strip_nonvisible_markup(markdown)
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
