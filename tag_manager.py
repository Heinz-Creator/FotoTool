print(">>> TAG_MANAGER GELADEN <<<")


import os
import json
import re

class TagManager:

    def __init__(self, app_dir):
        self.data_file = os.path.join(app_dir, "tags.json")
        self.data = {}
        self._load()

    def _load(self):
        if os.path.isfile(self.data_file):
            try:
                with open(self.data_file, "r", encoding="utf-8") as f:
                    self.data = json.load(f)
            except Exception:
                self.data = {}

    def _save(self):
        with open(self.data_file, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2)

    def _file_key(self, path):
        try:
            size = os.path.getsize(path)
        except Exception:
            size = 0
        return f"{os.path.basename(path)}|{size}"

    def scan_archive(self, archiv_root):
        print("SCAN ARCHIV:", archiv_root)

        learned = 0
        self.data = {}

        for root, _, files in os.walk(archiv_root):
            print("CHECK ROOT:", root)
            for f in files:
                fullpath = os.path.join(root, f)

                rel = os.path.relpath(root, archiv_root)
                if rel == ".":
                    continue

                parts = rel.split(os.sep)

                year = None
                event_name = None

                for part in parts:
                    # Jahr suchen
                    m = re.search(r"(19\d{2}|20\d{2})", part)
                    if m:
                        year = m.group(1)
                        cleaned = part.replace(year, "").strip()
                        cleaned = cleaned.replace("_", " ").replace("-", " ").strip()
                        if cleaned:
                            event_name = cleaned
                    else:
                        # Wenn kein Jahr drin, kompletten Ordnernamen als Event nehmen
                        cleaned = part.replace("_", " ").replace("-", " ").strip()
                        if cleaned and not event_name:
                            event_name = cleaned

                key = self._file_key(fullpath)

                tags = []
                if event_name:
                    tags.append(event_name)

                self.data[key] = {
                    "tags": tags,
                    "year": year,
                    "month": None
                }

                learned += 1

        self._save()
        return learned

    def scan_import_structure(self, import_root):
        """
        Liest Ordnerstruktur des Import-Ordners
        und speichert Ordnernamen als Tags.
        """
        learned = 0
        self.data = {}

        for root, _, files in os.walk(import_root):
            rel = os.path.relpath(root, import_root)
            if rel == ".":
                continue

            parts = rel.split(os.sep)

            # Alle Ordnernamen als Tags nehmen
            tags = []
            for part in parts:
                cleaned = part.replace("_", " ").replace("-", " ").strip()
                if cleaned:
                    tags.append(cleaned)

            for f in files:
                fullpath = os.path.join(root, f)
                key = self._file_key(fullpath)

                self.data[key] = {
                    "tags": tags,
                    "year": None,
                    "month": None
                }

                learned += 1

        self._save()
        return learned



    def tags_for_file(self, filepath):
        key = self._file_key(filepath)
        entry = self.data.get(key)
        if not entry:
            return []
        return entry.get("tags", [])

    def learned_date_for_file(self, filepath):
        key = self._file_key(filepath)
        entry = self.data.get(key)
        if not entry:
            return None, None
        return entry.get("year"), entry.get("month")
