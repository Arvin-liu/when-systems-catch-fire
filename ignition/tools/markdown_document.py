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
    r"^ {0,3}</?(" + "|".join(sorted(HTML_BLOCK_TAGS, key=len, reverse=True)) + r")(?:[ \t]|/?>|$)",
    re.IGNORECASE,
)
HTML_TAG_LINE_RE = re.compile(r"^ {0,3}</?([A-Za-z][A-Za-z0-9-]*)(?:[ \t]+[^<>]*)?/?>[ \t]*$")
HTML_RAW_TAG_RE = re.compile(r"^ {0,3}<(script|pre|style)(?:[ \t]|/?>|$)", re.IGNORECASE)
LIST_ITEM_RE = re.compile(r"^( {0,3})([-+*]|\d{1,9}[.)])([ \t]+)(.*)$")
TABLE_DELIMITER_CELL_RE = re.compile(r":?-{1,}:?")


def _blank_range(output: list[str], start: int, end: int) -> None:
    for index in range(start, end):
        if output[index] not in "\r\n":
            output[index] = " "


def _list_item_segment(
    lines: list[str], index: int,
) -> tuple[int, list[str], list[str]] | None:
    """Return one list item body, with its container indentation removed."""
    line = lines[index]
    body = line.rstrip("\r\n")
    match = LIST_ITEM_RE.match(body)
    if not match:
        return None

    indent, marker, spacing, content = match.groups()
    base_indent = len(indent)
    content_indent = base_indent + len(marker) + min(len(spacing), 4)
    if len(spacing) > 4:
        first_content = spacing[1:] + content
        first_prefix = body[:base_indent + len(marker) + 1]
    else:
        first_content = content
        first_prefix = body[:content_indent]

    item_end = index + 1
    inner_lines = [first_content + line[len(body):]]
    prefixes = [first_prefix]
    while item_end < len(lines):
        candidate = lines[item_end]
        candidate_body = candidate.rstrip("\r\n")
        if not candidate_body.strip():
            inner_lines.append(candidate)
            prefixes.append("")
            item_end += 1
            continue
        sibling = LIST_ITEM_RE.match(candidate_body)
        if sibling and len(sibling.group(1)) == base_indent:
            break
        candidate_indent = len(candidate_body) - len(candidate_body.lstrip(" "))
        if candidate_indent < content_indent:
            break
        prefixes.append(candidate_body[:content_indent])
        inner_lines.append(candidate[content_indent:])
        item_end += 1

    return item_end, inner_lines, prefixes


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
    def scan(lines: list[str]) -> list[str]:
        output: list[str] = []
        fence_char: str | None = None
        fence_length = 0
        index = 0
        while index < len(lines):
            line = lines[index]
            body = line.rstrip("\r\n")
            list_item = _list_item_segment(lines, index) if fence_char is None else None
            if list_item:
                item_end, inner_lines, prefixes = list_item
                transformed = scan(inner_lines)
                output.extend(prefix + inner for prefix, inner in zip(prefixes, transformed))
                index = item_end
                continue

            if fence_char is not None:
                match = re.match(r"^ {0,3}(`+|~+)[ \t]*$", body)
                if match and match.group(1)[0] == fence_char and len(match.group(1)) >= fence_length:
                    fence_char = None
                    fence_length = 0
                output.append("\r\n" if line.endswith("\r\n") else "\n" if line.endswith("\n") else "")
                index += 1
                continue

            match = FENCE_OPEN_RE.match(body)
            if match:
                marker, info = match.groups()
                if marker[0] != "`" or "`" not in info:
                    fence_char = marker[0]
                    fence_length = len(marker)
                    output.append("\r\n" if line.endswith("\r\n") else "\n" if line.endswith("\n") else "")
                    index += 1
                    continue
            output.append(line)
            index += 1
        return output

    return "".join(scan(markdown.splitlines(keepends=True)))


def strip_raw_html_blocks(markdown: str) -> str:
    """Blank GFM raw HTML blocks while preserving line numbers.

    HTML block contents are raw HTML until their GFM terminator, so apparent
    Markdown headings inside them are not rendered headings. Types 6 and 7
    end at a blank line; the other block types end at their closing token.
    """
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

    def table_cells(body: str) -> list[str] | None:
        stripped = body.strip()
        if not re.search(r"(?<!\\)\|", stripped):
            return None
        if stripped.startswith("|"):
            stripped = stripped[1:]
        if stripped.endswith("|") and not stripped.endswith(r"\|"):
            stripped = stripped[:-1]
        return [cell.strip() for cell in re.split(r"(?<!\\)\|", stripped)]

    def table_row_indices(lines: list[str]) -> set[int]:
        rows: set[int] = set()
        bodies = [line.rstrip("\r\n") for line in lines]
        for index in range(len(bodies) - 1):
            header = table_cells(bodies[index])
            delimiter = table_cells(bodies[index + 1])
            if (
                header is None
                or delimiter is None
                or len(header) != len(delimiter)
                or not all(TABLE_DELIMITER_CELL_RE.fullmatch(cell) for cell in delimiter)
            ):
                continue
            rows.update((index, index + 1))
            cursor = index + 2
            while cursor < len(bodies) and bodies[cursor].strip() and table_cells(bodies[cursor]) is not None:
                rows.add(cursor)
                cursor += 1
        return rows

    def scan(lines: list[str]) -> list[str]:
        output: list[str] = []
        block_kind: str | None = None
        can_start_type7 = True
        table_rows = table_row_indices(lines)
        index = 0

        while index < len(lines):
            line = lines[index]
            body = line.rstrip("\r\n")
            is_blank = not body.strip()

            # A list item's first block starts after its marker on the same
            # line. Scan the item body as its own Markdown container so raw
            # HTML opened there also hides indented continuation headings.
            list_item = _list_item_segment(lines, index) if block_kind is None else None
            if list_item:
                item_end, inner_lines, prefixes = list_item
                transformed = scan(inner_lines)
                output.extend(prefix + inner for prefix, inner in zip(prefixes, transformed))
                can_start_type7 = True
                index = item_end
                continue

            if block_kind in {"type6", "type7"}:
                if is_blank:
                    output.append(line)
                    block_kind = None
                    can_start_type7 = True
                else:
                    output.append(blank_line(line))
                    can_start_type7 = False
                index += 1
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
                index += 1
                continue

            if HTML_RAW_TAG_RE.match(body):
                output.append(blank_line(line))
                terminates = type1_terminates(body)
                if not terminates:
                    block_kind = "type1"
                can_start_type7 = terminates
                index += 1
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
                index += 1
                continue

            output.append(line)
            can_start_type7 = (
                is_blank
                or index in table_rows
                or bool(HEADING_RE.match(body))
                or bool(re.match(r"^ {0,3}(?:>|(?:[-+*]|\d+[.)])[ \t]+)", body))
                or bool(re.match(r"^ {0,3}(?:(?:\*[ \t]*){3,}|(?:-[ \t]*){3,}|(?:_[ \t]*){3,})$", body))
                or bool(re.match(r"^ {0,3}(?:=+|-+)[ \t]*$", body))
                or bool(re.match(r"^ {4,}\S", body))
            )
            index += 1

        return output

    return "".join(scan(markdown.splitlines(keepends=True)))


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
