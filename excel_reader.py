# -*- coding: utf-8 -*-
# SPDX-License-Identifier: GPL-3.0-or-later
"""Simple Excel/CSV reader for the ETFAR QGIS plugin.
Supports:
- .xlsx without external dependencies through an internal XML parser
- .xlsx using openpyxl when available
- .xls using xlrd when available
- .csv using Python built-in csv
"""

import os
import csv
import zipfile
# XLSX XML is bounded and screened for DTD/entity declarations before parsing.
import xml.etree.ElementTree as ET  # nosec B405
from collections import OrderedDict


def _norm(v):
    if v is None:
        return ""
    return str(v).strip()


def _unique_headers(headers):
    result = []
    used = {}
    for i, h in enumerate(headers):
        name = _norm(h) or "FIELD_%s" % (i + 1)
        # Shapefile will truncate field names on export; keep full names in the UI.
        base = name
        n = 2
        while name in used:
            name = "%s_%s" % (base, n)
            n += 1
        used[name] = True
        result.append(name)
    return result


def list_sheets(path):
    ext = os.path.splitext(path)[1].lower()
    if ext == ".csv":
        return ["CSV"]
    if ext == ".xlsx":
        try:
            import openpyxl
            wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
            names = list(wb.sheetnames)
            wb.close()
            return names
        except Exception:
            return _xlsx_list_sheets_xml(path)
    if ext == ".xls":
        try:
            import xlrd
            book = xlrd.open_workbook(path, on_demand=True)
            names = book.sheet_names()
            book.release_resources()
            return names
        except Exception:
            return []
    return []


def read_table(path, sheet_name=None):
    ext = os.path.splitext(path)[1].lower()
    if ext == ".csv":
        return _read_csv(path)
    if ext == ".xlsx":
        try:
            return _read_xlsx_openpyxl(path, sheet_name)
        except Exception:
            return _read_xlsx_xml(path, sheet_name)
    if ext == ".xls":
        try:
            return _read_xls_xlrd(path, sheet_name)
        except Exception as e:
            raise RuntimeError(
                "The .xls format requires the xlrd module in QGIS Python. Save the file as .xlsx or .csv. Detail: %s" %
                e)
    raise RuntimeError("Unsupported format. Use .xlsx, .xls, or .csv.")


def _read_csv(path):
    # Coba utf-8 lalu latin-1.
    last_err = None
    for enc in ("utf-8-sig", "utf-8", "latin-1"):
        try:
            with open(path, newline="", encoding=enc) as f:
                sample = f.read(4096)
                f.seek(0)
                try:
                    dialect = csv.Sniffer().sniff(sample)
                except Exception:
                    dialect = csv.excel
                rows = list(csv.reader(f, dialect))
            return _rows_to_table(rows)
        except Exception as e:
            last_err = e
    raise RuntimeError("Failed to read CSV: %s" % last_err)


def _read_xlsx_openpyxl(path, sheet_name=None):
    import openpyxl
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    try:
        ws = wb[sheet_name] if sheet_name and sheet_name in wb.sheetnames else wb[wb.sheetnames[0]]
        rows = []
        for row in ws.iter_rows(values_only=True):
            rows.append(list(row))
        return _rows_to_table(rows)
    finally:
        wb.close()


def _read_xls_xlrd(path, sheet_name=None):
    import xlrd
    book = xlrd.open_workbook(path, on_demand=True)
    try:
        if sheet_name and sheet_name in book.sheet_names():
            sh = book.sheet_by_name(sheet_name)
        else:
            sh = book.sheet_by_index(0)
        rows = []
        for r in range(sh.nrows):
            rows.append([sh.cell_value(r, c) for c in range(sh.ncols)])
        return _rows_to_table(rows)
    finally:
        book.release_resources()


def _rows_to_table(rows):
    # Find the first non-empty header row.
    header_idx = None
    for i, row in enumerate(rows):
        if any(_norm(v) for v in row):
            header_idx = i
            break
    if header_idx is None:
        return [], []
    headers = _unique_headers(rows[header_idx])
    records = []
    for row in rows[header_idx + 1:]:
        if not any(_norm(v) for v in row):
            continue
        rec = OrderedDict()
        for i, h in enumerate(headers):
            rec[h] = row[i] if i < len(row) else ""
        records.append(rec)
    return headers, records


# ==========================================================
# Parser XLSX XML fallback
# ==========================================================

_NS_MAIN = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
_NS_REL = "{http://schemas.openxmlformats.org/package/2006/relationships}"
_NS_DOCREL = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
MAX_XML_MEMBER_BYTES = 25 * 1024 * 1024


def _safe_xml_from_zip(archive, member_name):
    """Parse a bounded XLSX XML member after rejecting DTD/entity payloads."""
    info = archive.getinfo(member_name)
    if info.file_size > MAX_XML_MEMBER_BYTES:
        raise RuntimeError(
            "The XLSX XML member is too large to process safely.")
    raw = archive.read(member_name)
    lowered = raw[:4096].lower()
    if b"<!doctype" in lowered or b"<!entity" in lowered:
        raise RuntimeError(
            "Unsafe XML declarations are not allowed in XLSX files.")
    # ElementTree is safe here because entity declarations were rejected and
    # the uncompressed member size was bounded before parsing.
    return ET.fromstring(raw)  # nosec B314


def _xlsx_list_sheets_xml(path):
    try:
        with zipfile.ZipFile(path) as z:
            workbook = _safe_xml_from_zip(z, "xl/workbook.xml")
            sheets = workbook.find(_NS_MAIN + "sheets")
            names = []
            if sheets is not None:
                for sh in sheets:
                    names.append(sh.attrib.get("name", "Sheet"))
            return names
    except Exception:
        return []


def _col_index(cell_ref):
    letters = ""
    for ch in cell_ref:
        if ch.isalpha():
            letters += ch.upper()
        else:
            break
    n = 0
    for ch in letters:
        n = n * 26 + (ord(ch) - 64)
    return max(0, n - 1)


def _shared_strings(z):
    try:
        root = _safe_xml_from_zip(z, "xl/sharedStrings.xml")
    except Exception:
        return []
    strings = []
    for si in root.findall(_NS_MAIN + "si"):
        texts = []
        t = si.find(_NS_MAIN + "t")
        if t is not None and t.text is not None:
            texts.append(t.text)
        for r in si.findall(_NS_MAIN + "r"):
            rt = r.find(_NS_MAIN + "t")
            if rt is not None and rt.text is not None:
                texts.append(rt.text)
        strings.append("".join(texts))
    return strings


def _sheet_map(z):
    workbook = _safe_xml_from_zip(z, "xl/workbook.xml")
    rels = _safe_xml_from_zip(z, "xl/_rels/workbook.xml.rels")
    rid_to_target = {}
    for rel in rels:
        rid = rel.attrib.get("Id")
        target = rel.attrib.get("Target", "")
        if rid and target:
            if not target.startswith("/"):
                target = "xl/" + target
            else:
                target = target.lstrip("/")
            rid_to_target[rid] = target
    result = OrderedDict()
    sheets = workbook.find(_NS_MAIN + "sheets")
    if sheets is not None:
        for sh in sheets:
            name = sh.attrib.get("name", "Sheet")
            rid = sh.attrib.get(_NS_DOCREL + "id")
            result[name] = rid_to_target.get(rid, "")
    return result


def _cell_value(cell, shared):
    typ = cell.attrib.get("t")
    v = cell.find(_NS_MAIN + "v")
    if typ == "inlineStr":
        is_el = cell.find(_NS_MAIN + "is")
        if is_el is not None:
            t = is_el.find(_NS_MAIN + "t")
            return t.text if t is not None and t.text is not None else ""
        return ""
    if v is None or v.text is None:
        return ""
    text = v.text
    if typ == "s":
        try:
            return shared[int(text)]
        except Exception:
            return text
    return text


def _read_xlsx_xml(path, sheet_name=None):
    with zipfile.ZipFile(path) as z:
        smap = _sheet_map(z)
        if not smap:
            raise RuntimeError("Sheet tidak ditemukan pada file XLSX.")
        if sheet_name and sheet_name in smap:
            sheet_path = smap[sheet_name]
        else:
            sheet_path = list(smap.values())[0]
        shared = _shared_strings(z)
        root = _safe_xml_from_zip(z, sheet_path)
        sheet_data = root.find(_NS_MAIN + "sheetData")
        rows = []
        max_col = 0
        if sheet_data is None:
            return [], []
        for row_el in sheet_data.findall(_NS_MAIN + "row"):
            row = []
            for c in row_el.findall(_NS_MAIN + "c"):
                ref = c.attrib.get("r", "A1")
                idx = _col_index(ref)
                while len(row) <= idx:
                    row.append("")
                row[idx] = _cell_value(c, shared)
            max_col = max(max_col, len(row))
            rows.append(row)
        # Normalize row length.
        for row in rows:
            while len(row) < max_col:
                row.append("")
        return _rows_to_table(rows)
