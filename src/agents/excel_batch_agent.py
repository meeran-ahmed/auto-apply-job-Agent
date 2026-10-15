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
    normalizing them for autonomous background submission by ATSAgent.
    """

    URL_COLUMN_ALIASES = [
        "url", "job url", "job_url", "link", "job link", "job_link",
        "apply link", "apply_link", "website", "direct link",
        "direct_link", "application url", "application_link", "career link"
    ]

    COMPANY_COLUMN_ALIASES = [
        "company", "company name", "company_name", "employer",
        "organization", "hiring company", "firm"
    ]

    TITLE_COLUMN_ALIASES = [
        "title", "job title", "job_title", "role", "position",
        "job role", "job_role", "designation"
    ]

    LOCATION_COLUMN_ALIASES = [
        "location", "city", "country", "remote", "job location", "workplace"
    ]

    def __init__(self, file_path: Optional[str] = None):
        self.file_path = file_path

    def locate_sheet(self, search_dir: str = "data_folder") -> Optional[str]:
        """
        Auto-discovers any Excel or CSV file in the given directory or root.
        """
        if self.file_path and os.path.exists(self.file_path):
            return os.path.abspath(self.file_path)

        candidates = [
            Path(search_dir) / "jobs.xlsx",
            Path(search_dir) / "jobs.csv",
            Path("jobs.xlsx"),
            Path("jobs.csv")
        ]

        # Scan search_dir for any .xlsx or .csv
        search_path = Path(search_dir)
        if search_path.exists():
            for f in search_path.iterdir():
                if f.suffix.lower() in [".xlsx", ".xls", ".csv"] and not f.name.endswith(".template"):
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
            wb = openpyxl.load_workbook(file_path, data_only=True)
            sheet = wb.active
            rows = list(sheet.iter_rows(values_only=True))
            if not rows:
                return []

            header_row = [str(cell).strip().lower() if cell is not None else "" for cell in rows[0]]
            col_map = self._map_columns(header_row)

            # If headers were detected
            if "url" in col_map:
                for row_idx, row in enumerate(rows[1:], start=2):
                    if not row or all(v is None for v in row):
                        continue
                    url_val = self._get_cell(row, col_map.get("url"))
                    if not url_val:
                        continue
                    clean_url = self._extract_url(url_val)
                    if clean_url:
                        jobs.append({
                            "title": self._get_cell(row, col_map.get("title")) or "Engineering Position",
                            "company": self._get_cell(row, col_map.get("company")) or "Tech Employer",
                            "location": self._get_cell(row, col_map.get("location")) or "Remote",
                            "url": clean_url,
                            "platform": "Excel Batch Import"
                        })
            else:
                # Raw row-by-row fallback scanning for any cell matching http:// or https://
                logger.info("[ExcelBatchAgent] No standard column headers detected; performing deep URL pattern scan...")
                for row_idx, row in enumerate(rows, start=1):
                    for cell_val in row:
                        if cell_val:
                            found_url = self._extract_url(str(cell_val))
                            if found_url:
                                jobs.append({
                                    "title": f"Position (Row {row_idx})",
                                    "company": "Tech Employer",
                                    "location": "Remote",
                                    "url": found_url,
                                    "platform": "Excel Batch Import"
                                })
                                break

        except Exception as e:
            logger.error(f"[ExcelBatchAgent] Failed to parse Excel sheet '{file_path}': {e}")

        logger.info(f"[ExcelBatchAgent] Successfully parsed {len(jobs)} jobs from Excel.")
        return jobs

    def _parse_csv(self, file_path: str) -> List[Dict[str, str]]:
        jobs = []
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                reader = csv.reader(f)
                rows = list(reader)
                if not rows:
                    return []

                header_row = [c.strip().lower() for c in rows[0]]
                col_map = self._map_columns(header_row)

                if "url" in col_map:
                    for row_idx, row in enumerate(rows[1:], start=2):
                        if not row or all(not v.strip() for v in row):
                            continue
                        url_val = self._get_cell(row, col_map.get("url"))
                        clean_url = self._extract_url(url_val)
                        if clean_url:
                            jobs.append({
                                "title": self._get_cell(row, col_map.get("title")) or "Engineering Position",
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

    @staticmethod
    def _get_cell(row, idx: Optional[int]) -> str:
        if idx is not None and 0 <= idx < len(row):
            val = row[idx]
            return str(val).strip() if val is not None else ""
        return ""

    @staticmethod
    def _extract_url(text: str) -> Optional[str]:
        if not text:
            return None
        text = text.strip()
        if text.startswith("http://") or text.startswith("https://"):
            return text.split()[0]
        # Regex search
        match = re.search(r"https?://[^\s,;\"']+", text)
        return match.group(0) if match else None
