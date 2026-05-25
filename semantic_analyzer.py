import re
from db import db

# Predefined high-value semantic synonyms for standard tags to boost precision
SEMANTIC_SYNONYMS = {
    "财务报表": ["发票", "财务", "报表", "账单", "费用", "报销", "支出", "收入", "税", "流水", "资产", "invoice", "receipt", "finance", "billing", "tax"],
    "发票收据": ["发票", "收据", "小票", "账单", "费用", "报销", "receipt", "invoice", "billing"],
    "代码项目": ["代码", "程序", "软件", "系统", "开发", "技术", "源码", "工程", "编译", "github", "programming", "code", "develop", "software", "api"],
    "技术文档": ["技术", "设计说明", "架构", "设计", "文档", "规范", "接口", "api", "doc", "spec", "markdown"],
    "合同协议": ["合同", "协议", "合作", "签约", "租赁", "采购", "劳动", "保密", "contract", "agreement", "cooperate"],
    "设计稿件": ["图片", "照片", "设计", "图纸", "稿件", "插图", "海报", "素材", "ui", "psd", "figma", "sketch", "design", "image", "drawing"],
    "论文文献": ["论文", "文献", "期刊", "报告", "研究", "毕业设计", "毕设", "查重", "thesis", "paper", "research", "report", "journal"],
    "个人证件": ["身份证", "护照", "驾照", "证件", "证书", "简历", "体检", "passport", "id", "license", "certificate", "resume"],
    "会议纪要": ["会议", "纪要", "记录", "周报", "汇报", "日常", "沟通", "meeting", "minutes", "record", "weekly", "report"],
    "学习资料": ["学习", "教程", "课件", "笔记", "书籍", "视频", "讲义", "study", "tutorial", "note", "book", "course"]
}

class SemanticAnalyzer:
    """
    Zero-dependency lightweight Semantic keyword classifier and recommender.
    Combines Jaccard character-level overlap, dictionary synonym mapping,
    and exact tag-name substring scanning for rapid Chinese tag suggestions.
    """
    @staticmethod
    def extract_terms(text):
        """
        Extract clean character sets and English terms from text.
        """
        if not text:
            return set()
        # Convert to lowercase
        text = text.lower()
        # Extract English words
        en_words = set(re.findall(r'[a-z0-9]+', text))
        # Extract Chinese characters
        cn_chars = set(re.findall(r'[\u4e00-\u9fa5]', text))
        return en_words.union(cn_chars)

    @staticmethod
    def calculate_similarity(terms_a, terms_b):
        """
        Standard Jaccard similarity score.
        """
        if not terms_a or not terms_b:
            return 0.0
        intersection = terms_a.intersection(terms_b)
        union = terms_a.union(terms_b)
        return len(intersection) / float(len(union))

    @classmethod
    def recommend_tags(cls, filename, remark="", top_k=3):
        """
        Analyze a filename and description to suggest the top_k most relevant tags.
        """
        # Clean input text
        filename_clean = filename or ""
        remark_clean = remark or ""
        combined_text = f"{filename_clean} {remark_clean}".lower()
        combined_terms = cls.extract_terms(combined_text)

        # 1. Fetch active tags from config to ensure synchronization with user's customized tags
        db_tags = []
        try:
            from config import config
            for cat in ["primary", "secondary", "status"]:
                if cat in config.tags:
                    db_tags.extend(config.tags[cat])
        except Exception:
            pass

        # Default tags if config tags load failed
        if not db_tags:
            db_tags = ["#财务报表", "#代码项目", "#合同协议", "#设计稿件", "#论文文献", "#个人证件", "#会议纪要", "#学习资料"]

        suggestions = []
        for tag in db_tags:
            # Strip hash prefix for analysis
            tag_plain = tag.lstrip("#")
            score = 0.0

            # Category 1: Exact tag name substring match (Weight 5.0)
            if tag_plain in combined_text:
                score += 5.0

            # Category 2: Synonym keyword matches (Weight 2.5 per match)
            synonyms = SEMANTIC_SYNONYMS.get(tag_plain, [])
            for syn in synonyms:
                if syn in combined_text:
                    score += 2.5

            # Category 3: Term-level Jaccard similarity (Weight 1.0)
            tag_terms = cls.extract_terms(tag_plain)
            jaccard = cls.calculate_similarity(combined_terms, tag_terms)
            score += jaccard * 1.5

            if score > 0.1:
                suggestions.append((tag, score))

        # Sort by score descending
        suggestions.sort(key=lambda x: x[1], reverse=True)

        # Format top K suggestions
        recommended = [tag for tag, _ in suggestions[:top_k]]

        # Fallback to standard generic tags if no suggestions score high enough
        if len(recommended) < top_k:
            for tag in db_tags:
                if tag not in recommended:
                    recommended.append(tag)
                if len(recommended) >= top_k:
                    break

        return recommended[:top_k]
