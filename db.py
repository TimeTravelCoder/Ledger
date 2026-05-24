import sqlite3
import datetime
from pathlib import Path
from config import config

def get_pinyin_char(char):
    if not '\u4e00' <= char <= '\u9fa5':
        return char.lower()
    
    try:
        gb_bytes = char.encode('gb2312')
        if len(gb_bytes) == 2:
            code = gb_bytes[0] * 256 + gb_bytes[1]
            if 45217 <= code <= 45252: return 'a'
            if 45253 <= code <= 45760: return 'b'
            if 45761 <= code <= 46317: return 'c'
            if 46318 <= code <= 46825: return 'd'
            if 46826 <= code <= 47009: return 'e'
            if 47010 <= code <= 47296: return 'f'
            if 47297 <= code <= 47613: return 'g'
            if 47614 <= code <= 48118: return 'h'
            if 48119 <= code <= 49061: return 'j'
            if 49062 <= code <= 49323: return 'k'
            if 49324 <= code <= 49895: return 'l'
            if 49896 <= code <= 50370: return 'm'
            if 50371 <= code <= 50613: return 'n'
            if 50614 <= code <= 50621: return 'o'
            if 50622 <= code <= 50905: return 'p'
            if 50906 <= code <= 51386: return 'q'
            if 51387 <= code <= 51445: return 'r'
            if 51446 <= code <= 52217: return 's'
            if 52218 <= code <= 52697: return 't'
            if 52698 <= code <= 52979: return 'w'
            if 52980 <= code <= 53688: return 'x'
            if 53689 <= code <= 54480: return 'y'
            if 54481 <= code <= 55289: return 'z'
    except Exception:
        pass
    return char.lower()

def get_pinyin_initials(text):
    if not text:
        return ""
    return "".join(get_pinyin_char(c) for c in text)


class DatabaseManager:
    def __init__(self):
        self._conn = None
        self._db_path = None

    def get_conn(self):
        # Dynamically connect to the database in the current workspace directory
        db_dir = Path(config.workspace_dir)
        try:
            db_dir.mkdir(parents=True, exist_ok=True)
        except Exception:
            # Fallback if workspace_dir is invalid
            db_dir = Path(__file__).parent / "Workspace"
            db_dir.mkdir(parents=True, exist_ok=True)

        current_db_path = db_dir / ".docman.db"
        
        # If database path changed, close old connection
        if self._conn is not None and self._db_path != current_db_path:
            self.close()

        if self._conn is None:
            self._db_path = current_db_path
            self._conn = sqlite3.connect(self._db_path, timeout=20.0)
            self._conn.row_factory = sqlite3.Row
            self._init_db()

        return self._conn

    def _init_db(self):
        conn = self._conn
        cursor = conn.cursor()
        
        # Files table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filepath TEXT UNIQUE, -- Relative path from workspace root
            filename TEXT,
            file_size INTEGER,
            modified_time REAL,
            tags TEXT,           -- Comma separated tags, e.g. "#AI,#Paper,#TODO"
            description TEXT,
            backup_disk_status INTEGER DEFAULT 0,
            backup_cloud_status INTEGER DEFAULT 0,
            last_backup_time TEXT
        )
        """)
        
        # Backup history table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS backup_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
            backup_type TEXT, -- 'disk' or 'cloud'
            files_copied INTEGER,
            bytes_copied INTEGER,
            status TEXT
        )
        """)
        
        conn.commit()

    def sync_file_metadata(self, rel_path, filename, size, mtime):
        """Update or insert file metadata if it changed or is new."""
        conn = self.get_conn()
        cursor = conn.cursor()
        
        # Check if file already exists in db
        cursor.execute("SELECT id, file_size, modified_time FROM files WHERE filepath = ?", (rel_path,))
        row = cursor.fetchone()
        
        if row:
            # File exists, update if changed
            if row["file_size"] != size or abs(row["modified_time"] - mtime) > 0.01:
                cursor.execute("""
                UPDATE files 
                SET file_size = ?, modified_time = ?, backup_disk_status = 0, backup_cloud_status = 0 
                WHERE id = ?
                """, (size, mtime, row["id"]))
                conn.commit()
        else:
            # File is new, insert it
            cursor.execute("""
            INSERT INTO files (filepath, filename, file_size, modified_time, tags, description)
            VALUES (?, ?, ?, ?, '', '')
            """, (rel_path, filename, size, mtime))
            conn.commit()

    def update_file_tags(self, rel_path, tags_list):
        """Update the tags of a file."""
        conn = self.get_conn()
        cursor = conn.cursor()
        tags_str = ",".join(tags_list)
        cursor.execute("UPDATE files SET tags = ? WHERE filepath = ?", (tags_str, rel_path))
        conn.commit()

    def update_file_description(self, rel_path, description):
        """Update the description/notes of a file."""
        conn = self.get_conn()
        cursor = conn.cursor()
        cursor.execute("UPDATE files SET description = ? WHERE filepath = ?", (description, rel_path))
        conn.commit()

    def delete_file_record(self, rel_path):
        """Delete a file record from db (e.g. if deleted on disk)."""
        conn = self.get_conn()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM files WHERE filepath = ?", (rel_path,))
        conn.commit()

    def rename_file_record(self, old_rel_path, new_rel_path, new_filename):
        """Update record when file is renamed or moved."""
        conn = self.get_conn()
        cursor = conn.cursor()
        cursor.execute("""
        UPDATE files 
        SET filepath = ?, filename = ?, backup_disk_status = 0, backup_cloud_status = 0
        WHERE filepath = ?
        """, (new_rel_path, new_filename, old_rel_path))
        conn.commit()

    def get_file_info(self, rel_path):
        """Get database record for a file."""
        conn = self.get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM files WHERE filepath = ?", (rel_path,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def search_files(self, query=None, selected_tags=None, file_status=None):
        """Advanced composite search by name/tags/status with relevance ranking and SQLite pre-filtering."""
        conn = self.get_conn()
        cursor = conn.cursor()
        
        # Build dynamic SQL pre-filtering query to avoid loading all rows in large workspaces
        sql = "SELECT * FROM files"
        params = []
        conditions = []
        
        if selected_tags:
            for tag in selected_tags:
                tag_cleaned = tag.strip()
                if tag_cleaned:
                    conditions.append("tags LIKE ?")
                    params.append(f"%{tag_cleaned}%")
                    
        if file_status:
            status_cleaned = file_status.strip()
            if status_cleaned:
                conditions.append("tags LIKE ?")
                params.append(f"%{status_cleaned}%")
                
        if conditions:
            sql += " WHERE " + " AND ".join(conditions)
            
        cursor.execute(sql, tuple(params))
        rows = cursor.fetchall()
        records = [dict(row) for row in rows]
        
        # 1. Precise Tag Filtering (exact match, no substring clashes) on the reduced record set
        if selected_tags:
            normalized_selected = {t.strip().lower().lstrip("#") for t in selected_tags if t.strip()}
            filtered = []
            for r in records:
                r_tags = r.get("tags") or ""
                file_tags = {t.strip().lower().lstrip("#") for t in r_tags.split(",") if t.strip()}
                if normalized_selected.issubset(file_tags):
                    filtered.append(r)
            records = filtered
            
        # 2. Precise Status Filtering (exact match, no substring clashes) on the reduced record set
        if file_status:
            normalized_status = file_status.strip().lower().lstrip("#")
            filtered = []
            for r in records:
                r_tags = r.get("tags") or ""
                file_tags = {t.strip().lower().lstrip("#") for t in r_tags.split(",") if t.strip()}
                if normalized_status in file_tags:
                    filtered.append(r)
            records = filtered
            
        # 3. Multi-keyword and Pinyin text search
        if query:
            keywords = query.lower().split()
            if not keywords:
                # If query was just spaces, return sorted by filepath
                records.sort(key=lambda x: x["filepath"])
                return records
                
            matched_records = []
            for r in records:
                filename = (r.get("filename") or "").lower()
                filepath = (r.get("filepath") or "").lower()
                description = (r.get("description") or "").lower()
                r_tags = (r.get("tags") or "").lower()
                
                filename_initials = get_pinyin_initials(filename)
                
                # Check if all keywords match this record
                record_matches_all = True
                total_relevance = 0
                
                for kw in keywords:
                    kw_matches = False
                    kw_relevance = 0
                    
                    # Match filename (case-insensitive substring)
                    if kw in filename:
                        kw_matches = True
                        if filename == kw:
                            kw_relevance = max(kw_relevance, 100)
                        elif filename.startswith(kw):
                            kw_relevance = max(kw_relevance, 80)
                        else:
                            kw_relevance = max(kw_relevance, 50)
                            
                    # Match filename (pinyin initials)
                    if filename_initials and kw in filename_initials:
                        kw_matches = True
                        if filename_initials == kw:
                            kw_relevance = max(kw_relevance, 45)
                        elif filename_initials.startswith(kw):
                            kw_relevance = max(kw_relevance, 42)
                        else:
                            kw_relevance = max(kw_relevance, 40)
                            
                    # Match filepath
                    if kw in filepath:
                        kw_matches = True
                        kw_relevance = max(kw_relevance, 30)
                        
                    # Match description
                    if kw in description:
                        kw_matches = True
                        kw_relevance = max(kw_relevance, 20)
                        
                    # Match tags
                    if kw in r_tags:
                        kw_matches = True
                        kw_relevance = max(kw_relevance, 15)
                        
                    if not kw_matches:
                        record_matches_all = False
                        break
                    else:
                        total_relevance += kw_relevance
                        
                if record_matches_all:
                    r["relevance_score"] = total_relevance
                    matched_records.append(r)
                    
            # Sort by relevance score descending, then by filepath ascending
            matched_records.sort(key=lambda x: (-x.get("relevance_score", 0), x["filepath"]))
            return matched_records
            
        else:
            # If no text query, sort purely by filepath alphabetically
            records.sort(key=lambda x: x["filepath"])
            return records


    def get_recent_files(self, days=7):
        """Return files modified within the recent N days."""
        conn = self.get_conn()
        cursor = conn.cursor()
        cutoff = datetime.datetime.now().timestamp() - days * 24 * 60 * 60
        cursor.execute(
            "SELECT * FROM files WHERE modified_time >= ? ORDER BY modified_time DESC",
            (cutoff,)
        )
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def get_tag_distribution(self):
        """Return tag counts as a dict."""
        counts = {}
        for record in self.search_files():
            tags = record.get("tags", "")
            for tag in tags.split(","):
                tag = tag.strip()
                if not tag:
                    continue
                counts[tag] = counts.get(tag, 0) + 1
        return counts

    def mark_as_backed_up(self, rel_paths, backup_type):
        """Mark specific files as backed up in the db."""
        conn = self.get_conn()
        cursor = conn.cursor()
        
        import datetime
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        field = "backup_disk_status" if backup_type == "disk" else "backup_cloud_status"
        
        for path in rel_paths:
            cursor.execute(f"""
            UPDATE files 
            SET {field} = 1, last_backup_time = ? 
            WHERE filepath = ?
            """, (now_str, path))
            
        conn.commit()

    def add_backup_history(self, backup_type, files_count, bytes_count, status="success"):
        """Record backup events."""
        conn = self.get_conn()
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO backup_history (backup_type, files_copied, bytes_copied, status)
        VALUES (?, ?, ?, ?)
        """, (backup_type, files_count, bytes_count, status))
        conn.commit()

    def get_backup_history(self, limit=10):
        conn = self.get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM backup_history ORDER BY timestamp DESC LIMIT ?", (limit,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def close(self):
        if self._conn:
            try:
                self._conn.close()
            except Exception:
                pass
            self._conn = None
            self._db_path = None

# Global database manager instance
db = DatabaseManager()
