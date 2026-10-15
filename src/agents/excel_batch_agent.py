import os
import re
import csv
from pathlib import Path
from typing import List, Dict, Optional
from loguru import logger
import openpyxl


class ExcelBatchAgent:
    """
    Dedicated agent for ingesting custom job lists from Excel (.xlsx, .xls) and CSV files.
    Extracts direct application links, company names, and job titles,
    supporting standard URLs, embedded cell hyperlinks, and Excel =HYPERLINK() formulas.
    """

    URL_COLUMN_ALIASES = [
        "direct apply link", "apply link", "apply_link", "job link",
        "job_link", "url", "job url", "job_url", "link", "website",
        "direct link", "direct_link", "application url", "application_link", "career link"
    ]

    COMPANY_COLUMN_ALIASES = [
        "company", "company name", "company_name", "employer",
        "organization", "hiring company", "firm"
    ]

    TITLE_COLUMN_ALIASES = [
        "job title", "job_title", "title", "role", "position",
        "job role", "job_role", "designation"
    ]

    LOCATION_COLUMN_ALIASES = [
        "location", "city", "country", "remote", "location & work mode", "job location", "workplace"
    ]

    def __init__(self, file_path: Optional[str] = None):
        self.file_path = file_path

    def locate_sheet(self, search_dir: str = "data_folder") -> Optional[str]:
        """
        Auto-discovers any Excel or CSV file in data_folder, Downloads, or workspace root.
        """
        if self.file_path and os.path.exists(self.file_path):
            return os.path.abspath(self.file_path)

        candidates = [
            Path(search_dir) / "jobs.xlsx",
            Path(search_dir) / "jobs.csv",
            Path("jobs.xlsx"),
            Path("jobs.csv")
        ]

        # Scan data_folder for any .xlsx or .csv
        search_path = Path(search_dir)
        if search_path.exists():
            for f in search_path.iterdir():
                if f.suffix.lower() in [".xlsx", ".xls", ".csv"] and not f.name.endswith(".template"):
                    return str(f.resolve())

        # Scan Downloads for recent job tracker spreadsheets
        downloads_dir = Path.home() / "Downloads"
        if downloads_dir.exists():
            for f in downloads_dir.iterdir():
                if f.suffix.lower() in [".xlsx", ".xls", ".csv"] and ("job" in f.name.lower() or "tracker" in f.name.lower()):
                    return str(f.resolve())

        # Scan root dir
        for f in Path(".").iterdir():
            if f.suffix.lower() in [".xlsx", ".xls", ".csv"] and not f.name.endswith(".template"):
                return str(f.resolve())

        for c in candidates:
            if c.exists():
                return str(c.resolve())

        return None

    def parse_jobs(self, target_file: Optional[str] = None) -> List[Dict[str, str]]:
        file_to_parse = target_file or self.file_path or self.locate_sheet()
        if not file_to_parse or not os.path.exists(file_to_parse):
            logger.warning(f"[ExcelBatchAgent] No valid job spreadsheet found at: {file_to_parse}")
            return []

        logger.info(f"[ExcelBatchAgent] Ingesting jobs from spreadsheet: {file_to_parse}")
        ext = Path(file_to_parse).suffix.lower()

        if ext in [".xlsx", ".xls"]:
            return self._parse_excel(file_to_parse)
        elif ext == ".csv":
            return self._parse_csv(file_to_parse)
        else:
            logger.error(f"[ExcelBatchAgent] Unsupported file extension '{ext}'. Use .xlsx or .csv")
            return []

    def _parse_excel(self, file_path: str) -> List[Dict[str, str]]:
        jobs = []
        try:
            wb = openpyxl.load_workbook(file_path, data_only=False)
            
            # Select target sheet
            target_sheet = wb.active
            for name in wb.sheetnames:
                if any(k in name.lower() for k in ["job", "role", "tracker", "openings"]):
                    target_sheet = wb[name]
                    break

            logger.info(f"[ExcelBatchAgent] Scanning sheet: '{target_sheet.title}'")

            # Scan rows to locate the header row
            header_row_idx = None
            col_map = {}
            all_rows = list(target_sheet.iter_rows())

            for r_idx, row in enumerate(all_rows[:25], start=1):
                row_vals = [str(c.value).strip().lower() if c.value is not None else "" for c in row]
                mapping = self._map_columns(row_vals)
                if "url" in mapping:
                    header_row_idx = r_idx
                    col_map = mapping
                    logger.info(f"[ExcelBatchAgent] Detected table header at row {r_idx}: {mapping}")
                    break

            if header_row_idx and "url" in col_map:
                for r_idx, row in enumerate(all_rows[header_row_idx:], start=header_row_idx + 1):
                    # Check cell values
                    url_cell = row[col_map["url"]] if col_map["url"] < len(row) else None
                    if not url_cell:
                        continue

                    # Try to extract URL from cell value, formula, or hyperlink
                    clean_url = self._extract_url_from_cell(url_cell)
                    if not clean_url:
                        continue

                    title_cell = row[col_map.get("title")] if "title" in col_map and col_map["title"] < len(row) else None
                    company_cell = row[col_map.get("company")] if "company" in col_map and col_map["company"] < len(row) else None
                    location_cell = row[col_map.get("location")] if "location" in col_map and col_map["location"] < len(row) else None

                    title_val = self._clean_text(title_cell.value if title_cell else "") or f"Position (Row {r_idx})"
                    company_val = self._clean_text(company_cell.value if company_cell else "") or "Tech Employer"
                    loc_val = self._clean_text(location_cell.value if location_cell else "") or "Remote"

                    jobs.append({
                        "title": title_val,
                        "company": company_val,
                        "location": loc_val,
                        "url": clean_url,
                        "platform": "Excel Batch Import"
                    })
            else:
                # Deep scan for any cell containing http/https or =HYPERLINK
                logger.info("[ExcelBatchAgent] No standard column headers detected; performing deep URL pattern scan...")
                for r_idx, row in enumerate(all_rows, start=1):
                    for cell in row:
                        found_url = self._extract_url_from_cell(cell)
                        if found_url:
                            jobs.append({
                                "title": f"Position (Row {r_idx})",
                                "company": "Tech Employer",
                                "location": "Remote",
                                "url": found_url,
                                "platform": "Excel Batch Import"
                            })
                            break

        except Exception as e:
            logger.error(f"[ExcelBatchAgent] Failed to parse Excel sheet '{file_path}': {e}")

        logger.info(f"[ExcelBatchAgent] Successfully parsed {len(jobs)} verified jobs from Excel.")
        return jobs

    def _parse_csv(self, file_path: str) -> List[Dict[str, str]]:
        jobs = []
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                reader = csv.reader(f)
                rows = list(reader)
                if not rows:
                    return []

                # Find header row
                header_row_idx = None
                col_map = {}
                for idx, row in enumerate(rows[:20]):
                    row_vals = [c.strip().lower() for c in row]
                    mapping = self._map_columns(row_vals)
                    if "url" in mapping:
                        header_row_idx = idx
                        col_map = mapping
                        break

                if header_row_idx is not None and "url" in col_map:
                    for row_idx, row in enumerate(rows[header_row_idx + 1:], start=header_row_idx + 2):
                        if not row or all(not v.strip() for v in row):
                            continue
                        url_val = self._get_cell(row, col_map.get("url"))
                        clean_url = self._extract_url(url_val)
                        if clean_url:
                            jobs.append({
                                "title": self._get_cell(row, col_map.get("title")) or f"Position (Row {row_idx})",
                                "company": self._get_cell(row, col_map.get("company")) or "Tech Employer",
                                "location": self._get_cell(row, col_map.get("location")) or "Remote",
                                "url": clean_url,
                                "platform": "CSV Batch Import"
                            })
                else:
                    for row_idx, row in enumerate(rows, start=1):
                        for cell_val in row:
                            found_url = self._extract_url(cell_val)
                            if found_url:
                                jobs.append({
                                    "title": f"Position (Row {row_idx})",
                                    "company": "Tech Employer",
                                    "location": "Remote",
                                    "url": found_url,
                                    "platform": "CSV Batch Import"
                                })
                                break

        except Exception as e:
            logger.error(f"[ExcelBatchAgent] Failed to parse CSV file '{file_path}': {e}")

        logger.info(f"[ExcelBatchAgent] Successfully parsed {len(jobs)} jobs from CSV.")
        return jobs

    def _map_columns(self, header_row: List[str]) -> Dict[str, int]:
        col_map = {}
        for idx, col in enumerate(header_row):
            clean_col = col.strip().lower()
            if not clean_col:
                continue

            if any(alias in clean_col for alias in self.URL_COLUMN_ALIASES) and "url" not in col_map:
                col_map["url"] = idx
            elif any(alias in clean_col for alias in self.COMPANY_COLUMN_ALIASES) and "company" not in col_map:
                col_map["company"] = idx
            elif any(alias in clean_col for alias in self.TITLE_COLUMN_ALIASES) and "title" not in col_map:
                col_map["title"] = idx
            elif any(alias in clean_col for alias in self.LOCATION_COLUMN_ALIASES) and "location" not in col_map:
                col_map["location"] = idx

        return col_map

    @classmethod
    def _extract_url_from_cell(cls, cell) -> Optional[str]:
        if not cell:
            return None

        # 1. Hyperlink attribute
        if hasattr(cell, "hyperlink") and cell.hyperlink and cell.hyperlink.target:
            return cell.hyperlink.target.strip()

        # 2. String value or formula
        val = str(cell.value) if cell.value is not None else ""
        return cls._extract_url(val)

    @staticmethod
    def _extract_url(text: str) -> Optional[str]:
        if not text:
            return None
        text = text.strip()
        # Direct URL
        if text.startswith("http://") or text.startswith("https://"):
            return text.split()[0]
        # Regex search for URLs inside =HYPERLINK("...", ...) or free text
        match = re.search(r"https?://[^\s,\"'\)\>\<\;]+", text)
        return match.group(0).rstrip(".,;") if match else None

    @staticmethod
    def _clean_text(val) -> str:
        if val is None:
            return ""
        return str(val).strip()

    @staticmethod
    def _get_cell(row, idx: Optional[int]) -> str:
        if idx is not None and 0 <= idx < len(row):
            val = row[idx]
            return str(val).strip() if val is not None else ""
        return ""
