"""Small Markdown structure helpers for repository-facing validators."""

from __future__ import annotations

import re


FENCE_OPEN_RE = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")
HEADING_RE = re.compile(r"^ {0,3}(#{1,6})[ \t]+(.+?)[ \t]*#*[ \t]*$")
DETAILS_OPEN_RE = re.compile(r"<details(?=[\s>])([^>]*)>", re.IGNORECASE)
DETAILS_CLOSE_RE = re.compile(r"</details\s*>", re.IGNORECASE)
HTML_BLOCK_TAGS = frozenset(
    "address article aside base basefont blockquote body caption center col colgroup dd details dialog dir div dl dt "
    "fieldset figcaption figure footer form frame frameset h1 h2 h3 h4 h5 h6 head header hr html iframe legend "
    "li link main menu menuitem nav noframes ol optgroup option p param section source summary table "
    "tbody td tfoot th thead title tr track ul".split()
)
HTML_BLOCK_TAG_RE = re.compile(
    r"^ {0,3}</?(" + "|".join(sorted(HTML_BLOCK_TAGS, key=len, reverse=True)) + r")(?:[ \t]|/?>)",
    re.IGNORECASE,
)
HTML_TAG_LINE_RE = re.compile(r"^ {0,3}</?([A-Za-z][A-Za-z0-9-]*)(?:[ \t]+[^<>]*)?/?>[ \t]*$")
HTML_RAW_TAG_RE = re.compile(r"^ {0,3}<(script|pre|style)(?:[ \t]|/?>)", re.IGNORECASE)


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
    details_starts: list[int] = []
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
            if backslashes % 2:
                if hidden:
                    _blank_range(output, index, opening_end)
                index = opening_end
                continue
            closing_end = _inline_code_span_end(source, index, opening_end)
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
            details_starts.append(index)
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
            if not collapsed_details:
                _blank_range(output, index, len(source))
                break
            hidden = collapsed_details[-1]
            if hidden:
                _blank_range(output, index, closing.end())
            collapsed_details.pop()
            details_starts.pop()
            index = closing.end()
            continue

        if hidden and source[index] not in "\r\n":
            output[index] = " "
        index += 1

    if details_starts:
        _blank_range(output, min(details_starts), len(source))

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


def strip_raw_html_blocks(markdown: str) -> str:
    """Blank GFM raw HTML blocks while preserving line numbers.

    HTML block contents are raw HTML until their GFM terminator, so apparent
    Markdown headings inside them are not rendered headings. Types 6 and 7
    end at a blank line; the other block types end at their closing token.
    """
    output: list[str] = []
    block_kind: str | None = None
    can_start_type7 = True

    def blank_line(line: str) -> str:
        if line.endswith("\r\n"):
            return "\r\n"
        if line.endswith("\n"):
            return "\n"
        if line.endswith("\r"):
            return "\r"
        return ""

    def type1_terminates(body: str) -> bool:
        return bool(re.search(r"</(?:script|pre|style)\s*>", body, re.IGNORECASE))

    for line in markdown.splitlines(keepends=True):
        body = line.rstrip("\r\n")
        is_blank = not body.strip()

        if block_kind in {"type6", "type7"}:
            if is_blank:
                output.append(line)
                block_kind = None
                can_start_type7 = True
            else:
                output.append(blank_line(line))
                can_start_type7 = False
            continue

        if block_kind is not None:
            output.append(blank_line(line))
            terminates = (
                (block_kind == "type1" and type1_terminates(body))
                or (block_kind == "type3" and "]]>" in body)
                or (block_kind == "type4" and "?>" in body)
                or (block_kind == "type5" and ">" in body)
            )
            if terminates:
                block_kind = None
            can_start_type7 = bool(terminates)
            continue

        if HTML_RAW_TAG_RE.match(body):
            output.append(blank_line(line))
            terminates = type1_terminates(body)
            if not terminates:
                block_kind = "type1"
            can_start_type7 = terminates
            continue

        start_kind: str | None = None
        if re.match(r"^ {0,3}<!\[CDATA\[", body):
            start_kind = "type3"
        elif re.match(r"^ {0,3}<\?", body):
            start_kind = "type4"
        elif re.match(r"^ {0,3}<![A-Z]", body):
            start_kind = "type5"
        elif HTML_BLOCK_TAG_RE.match(body):
            start_kind = "type6"
        else:
            tag_line = HTML_TAG_LINE_RE.match(body)
            if can_start_type7 and tag_line and tag_line.group(1).casefold() not in HTML_BLOCK_TAGS:
                start_kind = "type7"

        if start_kind is not None:
            output.append(blank_line(line))
            terminates = (
                (start_kind == "type3" and "]]>" in body)
                or (start_kind == "type4" and "?>" in body)
                or (start_kind == "type5" and ">" in body)
            )
            block_kind = None if terminates else start_kind
            can_start_type7 = terminates
            continue

        output.append(line)
        can_start_type7 = (
            is_blank
            or bool(HEADING_RE.match(body))
            or bool(re.match(r"^ {0,3}(?:>|(?:[-+*]|\d+[.)])[ \t]+)", body))
            or bool(re.match(r"^ {0,3}(?:(?:\*[ \t]*){3,}|(?:-[ \t]*){3,}|(?:_[ \t]*){3,})$", body))
            or bool(re.match(r"^ {0,3}(?:=+|-+)[ \t]*$", body))
        )

    return "".join(output)


def markdown_headings(markdown: str) -> list[dict[str, int | str]]:
    """Return visible ATX headings with their zero-based line index."""
    visible = strip_raw_html_blocks(strip_nonvisible_markup(markdown))
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
