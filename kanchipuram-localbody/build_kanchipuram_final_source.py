#!/usr/bin/env python3
"""
Kanchipuram Local Body Source Workbook Builder
-----------------------------------------------

Purpose:
    Merge the two source workbooks used for the Kanchipuram local-body
    hierarchy project and create one final, sorted source workbook.

Important source/data rules:
    1. Preserve original source data.
    2. Assembly Polling Station / Part is NOT the same as Local Body Ward.
    3. Do NOT redistribute Assembly votes into Local Body Wards.
    4. Estimated values must remain explicitly marked as estimated.
    5. Tamil source names are retained; English columns are readable
       transliterations/labels, not claimed official spellings.
    6. Unresolved source relationships are retained rather than guessed.

Input files:
    - KANCHIPURAM_LOCALBODY_HIERARCHY_ORIGINAL_CORRECTED.xlsx
    - KANCHIPURAM_LOCALBODY_HIERARCHY_TAMIL_ENGLISH.xlsx

Output:
    - KANCHIPURAM_FINAL_SOURCE_MERGED_SORTED.xlsx

Usage:
    python build_kanchipuram_final_source.py

Optional:
    python build_kanchipuram_final_source.py \
        --original path/to/original.xlsx \
        --english path/to/tamil_english.xlsx \
        --output path/to/final.xlsx
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable

import pandas as pd
from openpyxl import load_workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter


DEFAULT_ORIGINAL = "KANCHIPURAM_LOCALBODY_HIERARCHY_ORIGINAL_CORRECTED.xlsx"
DEFAULT_ENGLISH = "KANCHIPURAM_LOCALBODY_HIERARCHY_TAMIL_ENGLISH.xlsx"
DEFAULT_OUTPUT = "KANCHIPURAM_FINAL_SOURCE_MERGED_SORTED.xlsx"


def find_column(df: pd.DataFrame, candidates: Iterable[str]) -> str | None:
    """Return the first matching column name from candidates."""
    normalized = {str(c).strip().lower(): c for c in df.columns}
    for candidate in candidates:
        key = candidate.strip().lower()
        if key in normalized:
            return normalized[key]
    return None


def read_excel_all_sheets(path: Path) -> dict[str, pd.DataFrame]:
    """Read every worksheet while preserving worksheet names."""
    return pd.read_excel(path, sheet_name=None, dtype=object)


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Trim column labels and string cell whitespace without altering values."""
    out = df.copy()
    out.columns = [str(c).strip() for c in out.columns]

    for col in out.columns:
        if out[col].dtype == object:
            out[col] = out[col].map(
                lambda x: x.strip() if isinstance(x, str) else x
            )
    return out


def merge_hierarchy(
    original_sheets: dict[str, pd.DataFrame],
    english_sheets: dict[str, pd.DataFrame],
) -> pd.DataFrame:
    """
    Merge the hierarchy tables by source row identity.

    The preferred table is FINAL_SOURCE_HIERARCHY if it already exists.
    Otherwise, locate the largest hierarchy-like worksheet and merge the
    English columns using the row order/index because the bilingual workbook
    was generated from the corrected hierarchy source.
    """
    preferred_names = [
        "FINAL_SOURCE_HIERARCHY",
        "HIERARCHY",
        "LOCALBODY_HIERARCHY",
    ]

    source_name = next(
        (n for n in preferred_names if n in original_sheets), None
    )

    if source_name is None:
        candidates = []
        for name, df in original_sheets.items():
            cols = {str(c).strip().lower() for c in df.columns}
            score = sum(
                term in " ".join(cols)
                for term in [
                    "district",
                    "local body",
                    "ward",
                    "representative",
                ]
            )
            if score >= 2:
                candidates.append((len(df), name))
        if not candidates:
            raise ValueError(
                "Could not identify the hierarchy sheet in the original workbook."
            )
        source_name = max(candidates)[1]

    base = normalize_columns(original_sheets[source_name])
    eng_source_name = next(
        (n for n in preferred_names if n in english_sheets), None
    )

    if eng_source_name is None:
        candidates = []
        for name, df in english_sheets.items():
            cols = {str(c).strip().lower() for c in df.columns}
            score = sum(
                term in " ".join(cols)
                for term in [
                    "district",
                    "local body",
                    "ward",
                    "english",
                ]
            )
            if score >= 2:
                candidates.append((len(df), name))
        if not candidates:
            raise ValueError(
                "Could not identify the bilingual hierarchy sheet."
            )
        eng_source_name = max(candidates)[1]

    eng = normalize_columns(english_sheets[eng_source_name])

    # If the English workbook already contains the Tamil/source columns,
    # use only its explicit English columns to avoid duplicate data.
    english_cols = [
        c for c in eng.columns
        if "(English)" in str(c) or str(c).lower().endswith(" english")
    ]

    if not english_cols:
        # Fall back to columns containing English in their labels.
        english_cols = [
            c for c in eng.columns if "english" in str(c).lower()
        ]

    if not english_cols:
        raise ValueError(
            "No English columns were found in the bilingual workbook."
        )

    # The bilingual workbook was generated row-for-row from the corrected
    # hierarchy. Prefer a row-order merge; it preserves source hierarchy
    # exactly and avoids fuzzy/guessed parent matching.
    if len(base) != len(eng):
        raise ValueError(
            "Hierarchy row counts differ: "
            f"original={len(base)}, bilingual={len(eng)}. "
            "Do not silently align mismatched rows."
        )

    merged = base.reset_index(drop=True).copy()

    for col in english_cols:
        new_col = str(col).strip()
        if new_col in merged.columns:
            # Keep the source column and avoid overwriting it.
            continue
        merged[new_col] = eng[col].reset_index(drop=True)

    return merged


def add_serial_number(df: pd.DataFrame) -> pd.DataFrame:
    """Add a stable S.No column as the first column."""
    out = df.copy()
    if "S.No" in out.columns:
        out = out.drop(columns=["S.No"])
    out.insert(0, "S.No", range(1, len(out) + 1))
    return out


def sort_hierarchy(df: pd.DataFrame) -> pd.DataFrame:
    """
    Sort using the requested hierarchy:
        District
        -> Local Body Category
        -> Parent Administrative Unit
        -> Local Body
        -> Local Body Ward
        -> Representative
        -> Election Year

    Missing columns are skipped rather than fabricated.
    """
    out = df.copy()

    possible = [
        "District",
        "Local Body Category",
        "Parent Administrative Unit",
        "Local Body",
        "Local Body Ward",
        "Representative",
        "Election Year",
    ]

    sort_cols = [c for c in possible if c in out.columns]

    if not sort_cols:
        # Safe fallback: retain source order.
        return add_serial_number(out)

    # Stable mergesort preserves original order among equivalent source rows.
    return add_serial_number(
        out.sort_values(
            by=sort_cols,
            kind="mergesort",
            na_position="last",
        ).reset_index(drop=True)
    )


def build_readme() -> pd.DataFrame:
    """Create the final workbook README."""
    rows = [
        ("Purpose", "Final source workbook for Kanchipuram local-body hierarchy."),
        ("Source", "Kanchipuram Tamil Nadu State Election Commission local-body source data and the supplied bilingual hierarchy workbook."),
        ("Hierarchy", "District → Assembly Constituency → Assembly Polling Station / Part → Village / Habitation → Local Body → Local Body Ward → Representative."),
        ("Rural", "District → Panchayat Union → Village Panchayat → Village Panchayat Ward → Ward Member. Village Panchayat President is a separate representative/master entry."),
        ("Urban", "District → Town Panchayat / Municipality / Corporation → Ward → Councillor."),
        ("Critical rule", "Assembly Polling Station / Part ≠ Local Body Ward."),
        ("Vote rule", "Assembly votes are not redistributed or estimated into local-body wards."),
        ("Estimate rule", "Any estimated material must remain explicitly marked as ESTIMATED and must not be represented as official local-body results."),
        ("Language rule", "Tamil source values are retained. English values are separate readable transliterations/labels and are not claimed to be official spellings unless supplied as such by the source."),
        ("Data integrity", "Unresolved source relationships are retained/marked rather than guessed."),
        ("Sorting", "District → Local Body Category → Parent Administrative Unit → Local Body → Local Body Ward → Representative → Election Year."),
    ]
    return pd.DataFrame(rows, columns=["Field", "Value"])


def style_workbook(path: Path) -> None:
    """Apply readable formatting without changing cell contents."""
    wb = load_workbook(path)

    header_fill = PatternFill(fill_type="solid", fgColor="1F4E78")
    header_font = Font(color="FFFFFF", bold=True)
    title_font = Font(bold=True, size=12)

    for ws in wb.worksheets:
        ws.freeze_panes = "A2"
        ws.auto_filter.ref = ws.dimensions

        for cell in ws[1]:
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(
                horizontal="center",
                vertical="center",
                wrap_text=True,
            )

        ws.row_dimensions[1].height = 30

        # Reasonable widths, capped so huge text does not create unusable sheets.
        for col_idx, column_cells in enumerate(
            ws.iter_cols(min_row=1, max_row=min(ws.max_row, 500)),
            start=1,
        ):
            max_len = 0
            for cell in column_cells:
                value = "" if cell.value is None else str(cell.value)
                max_len = max(max_len, len(value))
            width = min(max(max_len + 2, 10), 45)
            ws.column_dimensions[get_column_letter(col_idx)].width = width

        if ws.title == "FINAL_SOURCE_README":
            ws.column_dimensions["A"].width = 24
            ws.column_dimensions["B"].width = 110
            for row in ws.iter_rows():
                for cell in row:
                    cell.alignment = Alignment(
                        vertical="top",
                        wrap_text=True,
                    )

    # Highlight the final hierarchy sheet title/header only.
    if "FINAL_SOURCE_HIERARCHY" in wb.sheetnames:
        ws = wb["FINAL_SOURCE_HIERARCHY"]
        ws.freeze_panes = "A2"

    wb.save(path)


def copy_original_sheets(
    writer: pd.ExcelWriter,
    sheets: dict[str, pd.DataFrame],
    skip: set[str],
) -> None:
    """Copy original worksheets unchanged at the dataframe level."""
    for name, df in sheets.items():
        if name in skip:
            continue
        safe_name = name[:31]
        normalize_columns(df).to_excel(
            writer,
            sheet_name=safe_name,
            index=False,
        )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build the final sorted Kanchipuram source workbook."
    )
    parser.add_argument("--original", default=DEFAULT_ORIGINAL)
    parser.add_argument("--english", default=DEFAULT_ENGLISH)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    original_path = Path(args.original).expanduser().resolve()
    english_path = Path(args.english).expanduser().resolve()
    output_path = Path(args.output).expanduser().resolve()

    if not original_path.exists():
        raise FileNotFoundError(f"Original workbook not found: {original_path}")
    if not english_path.exists():
        raise FileNotFoundError(f"Bilingual workbook not found: {english_path}")

    print(f"Reading original workbook: {original_path}")
    original_sheets = read_excel_all_sheets(original_path)

    print(f"Reading bilingual workbook: {english_path}")
    english_sheets = read_excel_all_sheets(english_path)

    print("Building final hierarchy...")
    hierarchy = merge_hierarchy(original_sheets, english_sheets)
    hierarchy = sort_hierarchy(hierarchy)

    readme = build_readme()

    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Retain the original source sheets and add the final source layer.
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        readme.to_excel(writer, sheet_name="FINAL_SOURCE_README", index=False)
        hierarchy.to_excel(
            writer,
            sheet_name="FINAL_SOURCE_HIERARCHY",
            index=False,
        )

        # Preserve all original sheets from the corrected workbook.
        copy_original_sheets(
            writer,
            original_sheets,
            skip={
                "FINAL_SOURCE_README",
                "FINAL_SOURCE_HIERARCHY",
            },
        )

    style_workbook(output_path)

    print()
    print("SUCCESS")
    print(f"Output: {output_path}")
    print(f"Final hierarchy rows: {len(hierarchy):,}")
    print(f"Workbook sheets: {len(load_workbook(output_path, read_only=True).sheetnames)}")


if __name__ == "__main__":
    main()