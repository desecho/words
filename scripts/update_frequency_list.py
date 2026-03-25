#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import re
import shutil
import tempfile
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
import zipfile
from dataclasses import dataclass
from pathlib import Path


MAIN_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
NS = {"a": MAIN_NS, "r": REL_NS}
ET.register_namespace("", MAIN_NS)
ET.register_namespace("r", REL_NS)

DELIMITER = " <#> "
RU_COL = 4
FR_COL = 5
POS_COL = 3
WORD_COL = 2
FREQUENCY_COL = 1

FW_MAP = {
    "'s": "abbr",
    "I": "pro",
    "about": "pre",
    "above": "pre",
    "according": "pre",
    "across": "pre",
    "after": "pre",
    "against": "pre",
    "all": "d",
    "along": "pre",
    "although": "c",
    "among": "pre",
    "and": "c",
    "another": "d",
    "any": "d",
    "anybody": "pro",
    "anyone": "pro",
    "anything": "pro",
    "around": "pre",
    "as": "c",
    "at": "pre",
    "because": "c",
    "before": "pre",
    "behind": "pre",
    "below": "pre",
    "beneath": "pre",
    "beside": "pre",
    "besides": "pre",
    "between": "pre",
    "beyond": "pre",
    "both": "d",
    "but": "c",
    "by": "pre",
    "despite": "pre",
    "during": "pre",
    "each": "d",
    "either": "d",
    "enough": "d",
    "every": "d",
    "everybody": "pro",
    "everyone": "pro",
    "everything": "pro",
    "except": "pre",
    "few": "d",
    "for": "pre",
    "from": "pre",
    "half": "d",
    "he": "pro",
    "her": "pro",
    "hers": "pro",
    "herself": "pro",
    "him": "pro",
    "himself": "pro",
    "his": "d",
    "however": "r",
    "if": "c",
    "in": "pre",
    "including": "pre",
    "inside": "pre",
    "into": "pre",
    "it": "pro",
    "its": "d",
    "itself": "pro",
    "least": "r",
    "less": "d",
    "like": "pre",
    "little": "d",
    "many": "d",
    "me": "pro",
    "mine": "pro",
    "minus": "pre",
    "more": "d",
    "most": "d",
    "much": "d",
    "my": "d",
    "myself": "pro",
    "near": "pre",
    "neither": "d",
    "next": "d",
    "no": "d",
    "no-one": "pro",
    "nobody": "pro",
    "non": "j",
    "none": "pro",
    "nor": "c",
    "not": "r",
    "nothing": "pro",
    "of": "pre",
    "off": "r",
    "on": "pre",
    "onto": "pre",
    "or": "c",
    "others": "pro",
    "otherwise": "r",
    "our": "d",
    "ours": "pro",
    "ourselves": "pro",
    "outside": "pre",
    "over": "pre",
    "past": "pre",
    "per": "pre",
    "plus": "pre",
    "regarding": "pre",
    "several": "d",
    "she": "pro",
    "since": "c",
    "some": "d",
    "somebody": "pro",
    "someone": "pro",
    "something": "pro",
    "such": "d",
    "than": "c",
    "thanks": "u",
    "that": "c",
    "thee": "pro",
    "their": "d",
    "theirs": "pro",
    "them": "pro",
    "themselves": "pro",
    "there": "r",
    "therefore": "r",
    "these": "d",
    "they": "pro",
    "this": "d",
    "those": "d",
    "thou": "pro",
    "though": "c",
    "through": "pre",
    "throughout": "pre",
    "thy": "d",
    "till": "c",
    "to": "pre",
    "toward": "pre",
    "towards": "pre",
    "under": "pre",
    "underneath": "pre",
    "unless": "c",
    "unlike": "pre",
    "until": "c",
    "upon": "pre",
    "us": "pro",
    "versus": "pre",
    "we": "pro",
    "what": "pro",
    "whatever": "pro",
    "whatsoever": "pro",
    "when": "c",
    "whenever": "c",
    "where": "r",
    "wherever": "c",
    "whether": "c",
    "which": "pro",
    "while": "c",
    "who": "pro",
    "whoever": "pro",
    "whom": "pro",
    "whose": "pro",
    "with": "pre",
    "within": "pre",
    "without": "pre",
    "yet": "c",
    "you": "pro",
    "your": "d",
    "yours": "pro",
    "yourself": "pro",
}

K_MAP = {
    "African-American": "j",
    "American": "j",
    "April": "n",
    "Asian": "j",
    "Bible": "n",
    "British": "j",
    "Canadian": "j",
    "Catholic": "j",
    "Chinese": "j",
    "Christian": "j",
    "Christmas": "n",
    "Coke": "n",
    "Congress": "n",
    "December": "n",
    "Dutch": "j",
    "Earth": "n",
    "Easter": "n",
    "English": "j",
    "European": "j",
    "French": "j",
    "Friday": "n",
    "Frisbee": "n",
    "German": "j",
    "God": "n",
    "Halloween": "n",
    "Indian": "j",
    "Internet": "n",
    "Irish": "j",
    "Italian": "j",
    "Japanese": "j",
    "Jell-O": "n",
    "Jew": "n",
    "Jewish": "j",
    "July": "n",
    "June": "n",
    "Korean": "j",
    "Latin": "j",
    "Lord": "n",
    "Mafia": "n",
    "March": "n",
    "May": "n",
    "Mexican": "j",
    "Monday": "n",
    "Muslim": "j",
    "Nazi": "n",
    "November": "n",
    "Olympic": "j",
    "Olympics": "n",
    "Republican": "j",
    "Russian": "j",
    "Santa": "n",
    "Saturday": "n",
    "Spanish": "j",
    "Sunday": "n",
    "Thai": "j",
    "Thanksgiving": "n",
    "Thursday": "n",
    "Tuesday": "n",
    "Valentine": "n",
    "Web": "n",
    "Wednesday": "n",
    "Yankee": "n",
}

VERB_OVERRIDES = {
    "can": ("мочь", "pouvoir"),
    "like": ("нравиться", "aimer"),
    "may": ("мочь", "pouvoir"),
    "must": ("быть должным", "devoir"),
    "need": ("нуждаться", "avoir besoin"),
    "shall": ("быть должным", "devoir"),
    "will": ("желать", "vouloir"),
}


@dataclass
class CellModel:
    attrib: dict[str, str]
    value: str


@dataclass
class RowModel:
    attrib: dict[str, str]
    cells: dict[int, CellModel]


def column_index(cell_ref: str) -> int:
    index = 0
    for char in cell_ref:
        if char.isalpha():
            index = (index * 26) + (ord(char.upper()) - 64)
            continue
        break
    return index


def column_letter(index: int) -> str:
    letters: list[str] = []
    while index:
        index, remainder = divmod(index - 1, 26)
        letters.append(chr(65 + remainder))
    return "".join(reversed(letters))


def shared_string_text(item: ET.Element) -> str:
    return "".join(text.text or "" for text in item.findall(".//a:t", NS))


def load_archive(path: Path) -> tuple[dict[str, bytes], str, ET.Element, list[RowModel]]:
    with zipfile.ZipFile(path) as archive:
        members = {name: archive.read(name) for name in archive.namelist()}

    strings_root = ET.fromstring(members["xl/sharedStrings.xml"])
    shared_strings = [shared_string_text(item) for item in strings_root.findall("a:si", NS)]

    workbook_root = ET.fromstring(members["xl/workbook.xml"])
    rels_root = ET.fromstring(members["xl/_rels/workbook.xml.rels"])
    relmap = {rel.attrib["Id"]: rel.attrib["Target"] for rel in rels_root}
    first_sheet = workbook_root.find("a:sheets/a:sheet", NS)
    if first_sheet is None:
        raise RuntimeError("Workbook does not contain a sheet.")
    rel_id = first_sheet.attrib[f"{{{REL_NS}}}id"]
    sheet_path = "xl/" + relmap[rel_id]
    sheet_root = ET.fromstring(members[sheet_path])

    rows: list[RowModel] = []
    for row in sheet_root.findall("a:sheetData/a:row", NS):
        cells: dict[int, CellModel] = {}
        for cell in row.findall("a:c", NS):
            idx = column_index(cell.attrib["r"])
            value_node = cell.find("a:v", NS)
            value = "" if value_node is None else value_node.text or ""
            if cell.attrib.get("t") == "s" and value:
                value = shared_strings[int(value)]
            cells[idx] = CellModel(attrib=dict(cell.attrib), value=value)
        rows.append(RowModel(attrib=dict(row.attrib), cells=cells))

    return members, sheet_path, sheet_root, rows


def get_value(row: RowModel, column: int) -> str:
    cell = row.cells.get(column)
    return "" if cell is None else cell.value


def set_value(row: RowModel, column: int, value: str) -> None:
    if column not in row.cells:
        row.cells[column] = CellModel(attrib={"r": f"{column_letter(column)}1"}, value="")
    row.cells[column].value = value


def normalize_rows(rows: list[RowModel]) -> tuple[list[RowModel], int, int]:
    kept: list[RowModel] = rows[:2]
    removed = 0
    remapped = 0

    for row in rows[2:]:
        if not any(get_value(row, column).strip() for column in range(1, 6)):
            continue

        pos = get_value(row, POS_COL).strip()
        word = get_value(row, WORD_COL).strip()

        if pos == "m":
            removed += 1
            continue

        if pos == "fw":
            mapped = FW_MAP.get(word)
            if mapped is None:
                raise KeyError(f"Unmapped fw word: {word!r}")
            if mapped != pos:
                remapped += 1
            set_value(row, POS_COL, mapped)
        elif pos == "K":
            mapped = K_MAP.get(word)
            if mapped is None:
                raise KeyError(f"Unmapped K word: {word!r}")
            remapped += 1
            set_value(row, POS_COL, mapped)

        kept.append(row)

    return kept, removed, remapped


def seed_known_translations(rows: list[RowModel]) -> tuple[dict[str, str], dict[str, str]]:
    ru: dict[str, str] = {}
    fr: dict[str, str] = {}
    for row in rows[2:]:
        word = get_value(row, WORD_COL).strip()
        if not word:
            continue
        word_ru = get_value(row, RU_COL).strip()
        word_fr = get_value(row, FR_COL).strip()
        if word_ru:
            ru.setdefault(word, word_ru)
        if word_fr:
            fr.setdefault(word, word_fr)
    return ru, fr


def fill_from_known(rows: list[RowModel], ru: dict[str, str], fr: dict[str, str]) -> int:
    copied = 0
    for row in rows[2:]:
        word = get_value(row, WORD_COL).strip()
        if not word:
            continue
        if not get_value(row, RU_COL).strip() and word in ru:
            set_value(row, RU_COL, ru[word])
            copied += 1
        if not get_value(row, FR_COL).strip() and word in fr:
            set_value(row, FR_COL, fr[word])
            copied += 1
    return copied


def missing_words(rows: list[RowModel]) -> list[str]:
    pending: list[str] = []
    seen: set[str] = set()
    for row in rows[2:]:
        word = get_value(row, WORD_COL).strip()
        if not word or word in seen:
            continue
        if not get_value(row, RU_COL).strip() or not get_value(row, FR_COL).strip():
            seen.add(word)
            pending.append(word)
    return pending


def translate_request(text: str, target: str) -> str:
    params = urllib.parse.urlencode(
        {
            "client": "gtx",
            "sl": "en",
            "tl": target,
            "dt": "t",
            "q": text,
        }
    )
    url = f"https://translate.googleapis.com/translate_a/single?{params}"
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8"))
    return "".join(part[0] for part in payload[0])


def translate_pairs(items: list[tuple[str, str]], target: str) -> dict[str, str]:
    if not items:
        return {}

    query = DELIMITER.join(query for _, query in items)
    for attempt in range(3):
        try:
            translated = translate_request(query, target)
            parts = [part.strip() for part in re.split(r"\s*<#>\s*", translated)]
            if len(parts) == len(items):
                return {
                    key: part
                    for (key, _), part in zip(items, parts, strict=True)
                }
            break
        except Exception:
            if attempt == 2:
                raise
            time.sleep(1 + attempt)

    result: dict[str, str] = {}
    for key, query in items:
        for attempt in range(3):
            try:
                result[key] = translate_request(query, target).strip()
                break
            except Exception:
                if attempt == 2:
                    raise
                time.sleep(1 + attempt)
    return result


def translate_words(words: list[str], target: str) -> dict[str, str]:
    return translate_pairs([(word, word) for word in words], target)


def apply_translations(
    rows: list[RowModel],
    ru_translations: dict[str, str],
    fr_translations: dict[str, str],
) -> int:
    updates = 0
    for row in rows[2:]:
        word = get_value(row, WORD_COL).strip()
        if not word:
            continue
        if not get_value(row, RU_COL).strip() and word in ru_translations:
            set_value(row, RU_COL, ru_translations[word])
            updates += 1
        if not get_value(row, FR_COL).strip() and word in fr_translations:
            set_value(row, FR_COL, fr_translations[word])
            updates += 1
    return updates


def unique_words_for_pos(rows: list[RowModel], part_of_speech: str) -> list[str]:
    words: list[str] = []
    seen: set[str] = set()
    for row in rows[2:]:
        if get_value(row, POS_COL).strip() != part_of_speech:
            continue
        word = get_value(row, WORD_COL).strip()
        if not word or word in seen:
            continue
        seen.add(word)
        words.append(word)
    return words


def apply_pos_translations(
    rows: list[RowModel],
    part_of_speech: str,
    ru_translations: dict[str, str],
    fr_translations: dict[str, str],
) -> int:
    updates = 0
    for row in rows[2:]:
        if get_value(row, POS_COL).strip() != part_of_speech:
            continue
        word = get_value(row, WORD_COL).strip()
        if not word:
            continue
        if word in ru_translations and get_value(row, RU_COL) != ru_translations[word]:
            set_value(row, RU_COL, ru_translations[word])
            updates += 1
        if word in fr_translations and get_value(row, FR_COL) != fr_translations[word]:
            set_value(row, FR_COL, fr_translations[word])
            updates += 1
    return updates


def update_merge_ranges(sheet_root: ET.Element, last_row: int) -> None:
    merge_root = sheet_root.find("a:mergeCells", NS)
    if merge_root is None:
        return

    kept: list[ET.Element] = []
    for merge_cell in merge_root.findall("a:mergeCell", NS):
        ref = merge_cell.attrib.get("ref", "")
        start, _, end = ref.partition(":")
        start_row = int(re.search(r"\d+$", start).group()) if re.search(r"\d+$", start) else 0
        end_row = int(re.search(r"\d+$", end).group()) if re.search(r"\d+$", end) else start_row
        if end_row <= last_row and start_row <= last_row:
            kept.append(merge_cell)

    for merge_cell in list(merge_root):
        merge_root.remove(merge_cell)
    for merge_cell in kept:
        merge_root.append(merge_cell)

    if kept:
        merge_root.attrib["count"] = str(len(kept))
    else:
        sheet_root.remove(merge_root)


def build_shared_strings(rows: list[RowModel]) -> tuple[ET.Element, dict[str, int]]:
    root = ET.Element(f"{{{MAIN_NS}}}sst")
    index: dict[str, int] = {}
    count = 0

    for row in rows:
        for column in sorted(row.cells):
            if column == FREQUENCY_COL:
                continue
            value = row.cells[column].value
            if value == "":
                continue
            count += 1
            if value in index:
                continue
            string_index = len(index)
            index[value] = string_index
            item = ET.SubElement(root, f"{{{MAIN_NS}}}si")
            text = ET.SubElement(item, f"{{{MAIN_NS}}}t")
            if value.strip() != value:
                text.attrib["{http://www.w3.org/XML/1998/namespace}space"] = "preserve"
            text.text = value

    root.attrib["count"] = str(count)
    root.attrib["uniqueCount"] = str(len(index))
    return root, index


def render_sheet(sheet_root: ET.Element, rows: list[RowModel], shared_string_index: dict[str, int]) -> None:
    sheet_data = sheet_root.find("a:sheetData", NS)
    if sheet_data is None:
        raise RuntimeError("Sheet does not contain sheetData.")

    for row in list(sheet_data):
        sheet_data.remove(row)

    for row_number, row_model in enumerate(rows, start=1):
        row_attrib = dict(row_model.attrib)
        row_attrib["r"] = str(row_number)
        row_element = ET.SubElement(sheet_data, f"{{{MAIN_NS}}}row", row_attrib)

        for column in sorted(row_model.cells):
            cell_model = row_model.cells[column]
            cell_attrib = dict(cell_model.attrib)
            cell_attrib["r"] = f"{column_letter(column)}{row_number}"

            value = cell_model.value
            if column == FREQUENCY_COL:
                cell_attrib.pop("t", None)
            elif value == "":
                cell_attrib.pop("t", None)
            else:
                cell_attrib["t"] = "s"

            cell_element = ET.SubElement(row_element, f"{{{MAIN_NS}}}c", cell_attrib)
            if column == FREQUENCY_COL and value != "":
                value_element = ET.SubElement(cell_element, f"{{{MAIN_NS}}}v")
                value_element.text = value
            elif value != "":
                value_element = ET.SubElement(cell_element, f"{{{MAIN_NS}}}v")
                value_element.text = str(shared_string_index[value])

    dimension = sheet_root.find("a:dimension", NS)
    if dimension is not None:
        dimension.attrib["ref"] = f"A1:E{len(rows)}"

    update_merge_ranges(sheet_root, len(rows))


def write_workbook(
    workbook_path: Path,
    members: dict[str, bytes],
    sheet_path: str,
    sheet_root: ET.Element,
    rows: list[RowModel],
) -> None:
    shared_strings_root, shared_string_index = build_shared_strings(rows)
    render_sheet(sheet_root, rows, shared_string_index)

    members["xl/sharedStrings.xml"] = ET.tostring(
        shared_strings_root,
        encoding="utf-8",
        xml_declaration=True,
    )
    members[sheet_path] = ET.tostring(
        sheet_root,
        encoding="utf-8",
        xml_declaration=True,
    )

    with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
        tmp_path = Path(tmp.name)

    try:
        with zipfile.ZipFile(tmp_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for name, content in members.items():
                archive.writestr(name, content)
        shutil.move(tmp_path, workbook_path)
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Normalize POS and fill translations in file.xlsx.")
    parser.add_argument("workbook", nargs="?", default="file.xlsx")
    parser.add_argument("--batch-size", type=int, default=100)
    parser.add_argument("--max-batches", type=int)
    parser.add_argument("--retranslate-verbs", action="store_true")
    parser.add_argument("--sleep", type=float, default=0.5)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    workbook_path = Path(args.workbook)

    members, sheet_path, sheet_root, rows = load_archive(workbook_path)
    rows, removed, remapped = normalize_rows(rows)
    ru_known, fr_known = seed_known_translations(rows)
    copied = fill_from_known(rows, ru_known, fr_known)
    pending = missing_words(rows)

    print(
        f"Loaded {workbook_path} with {len(rows) - 2} data rows after removing {removed} 'm' rows "
        f"and remapping {remapped} POS values."
    )
    if copied:
        print(f"Filled {copied} cells from translations already present in the workbook.")

    write_workbook(workbook_path, members, sheet_path, sheet_root, rows)
    print("Saved normalized workbook state.")

    if not pending:
        print("No translation work remains.")
    else:
        batches_run = 0
        while pending:
            if args.max_batches is not None and batches_run >= args.max_batches:
                break

            batch = pending[: args.batch_size]
            batch_number = batches_run + 1
            total_batches = (len(pending) + args.batch_size - 1) // args.batch_size
            print(
                f"Batch {batch_number}/{total_batches}: translating {len(batch)} words "
                f"({len(pending)} unique words still missing)."
            )

            ru_translations = translate_words(batch, "ru")
            fr_translations = translate_words(batch, "fr")
            updates = apply_translations(rows, ru_translations, fr_translations)
            write_workbook(workbook_path, members, sheet_path, sheet_root, rows)

            batches_run += 1
            pending = missing_words(rows)
            print(
                f"Saved batch {batch_number}: wrote {updates} cell updates. "
                f"{len(pending)} unique words still missing."
            )

            if pending and args.sleep:
                time.sleep(args.sleep)

        if pending:
            print(f"Stopped with {len(pending)} unique words still missing.")
        else:
            print("Translations complete.")

    if not args.retranslate_verbs:
        return

    verb_words = unique_words_for_pos(rows, "v")
    if not verb_words:
        print("No verb rows found for contextual retranslation.")
        return

    print(f"Retranslating {len(verb_words)} unique verbs using 'to <word>' context.")
    for index in range(0, len(verb_words), args.batch_size):
        batch_number = (index // args.batch_size) + 1
        batch = verb_words[index : index + args.batch_size]
        items = [(word, f"to {word}") for word in batch]
        print(
            f"Verb batch {batch_number}: translating {len(batch)} contextualized verb prompts."
        )
        ru_translations = translate_pairs(items, "ru")
        fr_translations = translate_pairs(items, "fr")
        updates = apply_pos_translations(rows, "v", ru_translations, fr_translations)
        write_workbook(workbook_path, members, sheet_path, sheet_root, rows)
        print(f"Saved verb batch {batch_number}: wrote {updates} cell updates.")
        if args.sleep and index + args.batch_size < len(verb_words):
            time.sleep(args.sleep)

    override_updates = apply_pos_translations(
        rows,
        "v",
        {word: ru for word, (ru, _) in VERB_OVERRIDES.items()},
        {word: fr for word, (_, fr) in VERB_OVERRIDES.items()},
    )
    if override_updates:
        write_workbook(workbook_path, members, sheet_path, sheet_root, rows)
        print(f"Saved verb overrides: wrote {override_updates} cell updates.")

    print("Verb retranslation complete.")


if __name__ == "__main__":
    main()
