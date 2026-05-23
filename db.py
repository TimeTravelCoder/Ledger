import sqlite3
from pathlib import Path
from config import config

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
            self._conn = sqlite3.connect(self._db_path)
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
        """Advanced composite search by name/tags/status."""
        conn = self.get_conn()
        cursor = conn.cursor()
        
        sql = "SELECT * FROM files WHERE 1=1"
        params = []
        
        if query:
            sql += " AND (filename LIKE ? OR filepath LIKE ? OR description LIKE ?)"
            q = f"%{query}%"
            params.extend([q, q, q])
            
        if selected_tags:
            # We want to match all selected tags
            for tag in selected_tags:
                sql += " AND tags LIKE ?"
                params.append(f"%{tag}%")

        if file_status:
            # e.g., matching a status tag like #TODO, #Doing, #Done
            sql += " AND tags LIKE ?"
            params.append(f"%{file_status}%")

        sql += " ORDER BY filepath ASC"
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

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
