import os
import json
from pathlib import Path

CONFIG_FILE = Path(__file__).parent / ".config.json"

DEFAULT_TAGS = {
    "primary": ["#人工智能", "#量子科技", "#高等数学", "#操作系统", "#计算机网络", "#专业英语", "#课程学习", "#课题研究"],
    "secondary": ["#实验报告", "#学术论文", "#项目文档", "#复习备考", "#期末考试", "#常用参考"],
    "status": ["#待处理", "#进行中", "#已完成", "#非常重要"]
}


def normalize_tag(tag):
    tag = str(tag or "").strip()
    if not tag:
        return ""
    tag = tag.lstrip("#").strip()
    return f"#{tag}" if tag else ""


def display_tag(tag):
    tag = str(tag or "").strip()
    if tag.startswith("#"):
        return tag[1:].strip()
    return tag


def normalize_tags(tags):
    normalized = []
    seen = set()
    for tag in tags or []:
        value = normalize_tag(tag)
        if value and value not in seen:
            normalized.append(value)
            seen.add(value)
    return normalized

STANDARD_DIRS_EN = [
    "00Inbox", "01Study", "02Research", "03Projects", "04Code", 
    "05Papers", "06Notes", "07Resources", "08PPT", "09Resume", 
    "10Archive", "99Temp"
]

STANDARD_DIRS_CN = [
    "00收集箱", "01课程学习", "02课题研究", "03项目管理", "04代码仓库", 
    "05学术论文", "06知识笔记", "07常用资源", "08演示汇报", "09个人简历", 
    "10归档区", "99临时缓冲"
]

NAME_PRESET_BASES = [
    {
        "key": "regular",
        "label": "常规模版",
        "prefix": "01",
        "default_format": "{date}_{topic}_{version}_{status}"
    },
    {
        "key": "paper",
        "label": "学术论文",
        "prefix": "05",
        "default_format": "{date}_{topic}_{version}"
    },
    {
        "key": "exp",
        "label": "实验报告",
        "prefix": "01",
        "default_format": "{date}_{topic}_{version}"
    },
    {
        "key": "slides",
        "label": "幻灯片",
        "prefix": "08",
        "default_format": "{date}_{topic}_{version}"
    },
    {
        "key": "image",
        "label": "实验图片",
        "prefix": "07",
        "default_format": "{date}_{topic}_{version}"
    },
    {
        "key": "meeting",
        "label": "会议纪要",
        "prefix": "06",
        "default_format": "{date}_{topic}_{version}"
    },
    {
        "key": "report",
        "label": "项目报告",
        "prefix": "03",
        "default_format": "{date}_{topic}_{version}"
    },
    {
        "key": "note",
        "label": "学习笔记",
        "prefix": "06",
        "default_format": "{date}_{topic}"
    },
    {
        "key": "data",
        "label": "数据表格",
        "prefix": "04",
        "default_format": "{date}_{topic}_{version}"
    },
    {
        "key": "contract",
        "label": "合同文档",
        "prefix": "03",
        "default_format": "{date}_{topic}_{version}"
    },
    {
        "key": "daily",
        "label": "日常记录",
        "prefix": "06",
        "default_format": "{date}_{topic}"
    },
    {
        "key": "keep",
        "label": "保持原名",
        "prefix": "00",
        "default_format": "{stem}"
    },
]

class AppConfig:
    def __init__(self):
        self.workspace_dir = ""
        self.downloads_dir = str(Path.home() / "Downloads")
        self.backup_disk_dir = ""
        self.backup_cloud_dir = ""
        self.theme = "dark"  # "dark", "light", or "zhongguose"
        self.monitored_downloads = True
        self.auto_rule_enabled = False
        self.tags = DEFAULT_TAGS.copy()
        self.workspace_lang = "en"  # "en" or "cn"
        self.use_custom_dirs = False
        self.custom_standard_dirs = []
        self.auto_rules = [
            {"name": "论文文档", "keywords": ["paper", "论文", "arxiv"], "extensions": [".pdf"], "target_prefix": "05"},
            {"name": "演示文稿", "keywords": ["ppt", "presentation", "汇报"], "extensions": [".ppt", ".pptx"], "target_prefix": "08"},
            {"name": "代码文件", "keywords": ["code", "script"], "extensions": [".py", ".js", ".ts", ".cpp", ".java"], "target_prefix": "04"},
            {"name": "图片素材", "keywords": ["image", "photo", "截图"], "extensions": [".png", ".jpg", ".jpeg"], "target_prefix": "07"},
        ]
        self.custom_name_templates = []
        
        # Default workspace setup in the same folder if not set
        default_ws = Path(__file__).parent / "Workspace"
        self.workspace_dir = str(default_ws.resolve())
        
        self.load()

    def get_standard_dirs(self):
        if self.use_custom_dirs and self.custom_standard_dirs:
            return self.custom_standard_dirs
        return STANDARD_DIRS_CN if self.workspace_lang == "cn" else STANDARD_DIRS_EN

    def get_inbox_name(self):
        if self.use_custom_dirs and self.custom_standard_dirs:
            for d in self.custom_standard_dirs:
                if "inbox" in d.lower() or "收集" in d:
                    return d
            return self.custom_standard_dirs[0]
        return "00收集箱" if self.workspace_lang == "cn" else "00Inbox"

    def load(self):
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.workspace_dir = data.get("workspace_dir", self.workspace_dir)
                    self.downloads_dir = data.get("downloads_dir", self.downloads_dir)
                    self.backup_disk_dir = data.get("backup_disk_dir", self.backup_disk_dir)
                    self.backup_cloud_dir = data.get("backup_cloud_dir", self.backup_cloud_dir)
                    self.theme = data.get("theme", self.theme)
                    self.monitored_downloads = data.get("monitored_downloads", self.monitored_downloads)
                    loaded_tags = data.get("tags", self.tags)
                    self.tags = {
                        "primary": normalize_tags(loaded_tags.get("primary", DEFAULT_TAGS["primary"])),
                        "secondary": normalize_tags(loaded_tags.get("secondary", DEFAULT_TAGS["secondary"])),
                        "status": normalize_tags(loaded_tags.get("status", DEFAULT_TAGS["status"]))
                    }
                    self.workspace_lang = data.get("workspace_lang", self.workspace_lang)
                    self.use_custom_dirs = data.get("use_custom_dirs", self.use_custom_dirs)
                    self.custom_standard_dirs = data.get("custom_standard_dirs", self.custom_standard_dirs)
                    self.auto_rule_enabled = data.get("auto_rule_enabled", self.auto_rule_enabled)
                    self.auto_rules = data.get("auto_rules", self.auto_rules)
                    self.custom_name_templates = data.get("custom_name_templates", self.custom_name_templates)
                    # Migration: if tags are the old English defaults, upgrade to Chinese
                    if self.tags.get("primary") == ["#AI", "#Quantum", "#Math", "#OS", "#Network", "#English"]:
                        self.tags = DEFAULT_TAGS.copy()
                        self.save()
            except Exception as e:
                print(f"Error loading config: {e}")

    def save(self):
        try:
            data = {
                "workspace_dir": self.workspace_dir,
                "downloads_dir": self.downloads_dir,
                "backup_disk_dir": self.backup_disk_dir,
                "backup_cloud_dir": self.backup_cloud_dir,
                "theme": self.theme,
                "monitored_downloads": self.monitored_downloads,
                "tags": self.tags,
                "workspace_lang": self.workspace_lang,
                "use_custom_dirs": self.use_custom_dirs,
                "custom_standard_dirs": self.custom_standard_dirs,
                "auto_rule_enabled": self.auto_rule_enabled,
                "auto_rules": self.auto_rules,
                "custom_name_templates": self.custom_name_templates
            }
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Error saving config: {e}")

# Global configuration instance
config = AppConfig()
