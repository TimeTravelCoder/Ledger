use pyo3::prelude::*;
use std::collections::HashSet;
use std::collections::HashMap;

// Predefined semantic synonyms for standard tags
fn get_semantic_synonyms() -> HashMap<&'static str, Vec<&'static str>> {
    let mut map = HashMap::new();
    map.insert("财务报表", vec!["发票", "财务", "报表", "账单", "费用", "报销", "支出", "收入", "税", "流水", "资产", "invoice", "receipt", "finance", "billing", "tax"]);
    map.insert("发票收据", vec!["发票", "收据", "小票", "账单", "费用", "报销", "receipt", "invoice", "billing"]);
    map.insert("代码项目", vec!["代码", "程序", "软件", "系统", "开发", "技术", "源码", "工程", "编译", "github", "programming", "code", "develop", "software", "api"]);
    map.insert("技术文档", vec!["技术", "设计说明", "架构", "设计", "文档", "规范", "接口", "api", "doc", "spec", "markdown"]);
    map.insert("合同协议", vec!["合同", "协议", "合作", "签约", "租赁", "采购", "劳动", "保密", "contract", "agreement", "cooperate"]);
    map.insert("设计稿件", vec!["图片", "照片", "设计", "图纸", "稿件", "插图", "海报", "素材", "ui", "psd", "figma", "sketch", "design", "image", "drawing"]);
    map.insert("论文文献", vec!["论文", "文献", "期刊", "报告", "研究", "毕业设计", "毕设", "查重", "thesis", "paper", "research", "report", "journal"]);
    map.insert("个人证件", vec!["身份证", "护照", "驾照", "证件", "证书", "简历", "体检", "passport", "id", "license", "certificate", "resume"]);
    map.insert("会议纪要", vec!["会议", "纪要", "记录", "周报", "汇报", "日常", "沟通", "meeting", "minutes", "record", "weekly", "report"]);
    map.insert("学习资料", vec!["学习", "教程", "课件", "笔记", "书籍", "视频", "讲义", "study", "tutorial", "note", "book", "course"]);
    map
}

/// Extract English words and individual Chinese characters
fn extract_terms(text: &str) -> HashSet<String> {
    let mut terms = HashSet::new();
    let text = text.to_lowercase();
    
    let mut current_eng_word = String::new();
    
    for c in text.chars() {
        if c.is_ascii_alphanumeric() {
            current_eng_word.push(c);
        } else {
            if !current_eng_word.is_empty() {
                terms.insert(current_eng_word.clone());
                current_eng_word.clear();
            }
            if c >= '\u{4e00}' && c <= '\u{9fa5}' {
                terms.insert(c.to_string());
            }
        }
    }
    
    if !current_eng_word.is_empty() {
        terms.insert(current_eng_word);
    }
    
    terms
}

fn calculate_similarity(terms_a: &HashSet<String>, terms_b: &HashSet<String>) -> f64 {
    if terms_a.is_empty() || terms_b.is_empty() {
        return 0.0;
    }
    let intersection: HashSet<_> = terms_a.intersection(terms_b).collect();
    let union: HashSet<_> = terms_a.union(terms_b).collect();
    intersection.len() as f64 / union.len() as f64
}

#[pyfunction]
#[pyo3(signature = (filename, remark, db_tags, top_k))]
pub fn recommend_tags(
    filename: Option<&str>, 
    remark: Option<&str>, 
    db_tags: Vec<String>, 
    top_k: usize
) -> PyResult<Vec<String>> {
    let filename_clean = filename.unwrap_or("");
    let remark_clean = remark.unwrap_or("");
    let combined_text = format!("{} {}", filename_clean, remark_clean).to_lowercase();
    
    let combined_terms = extract_terms(&combined_text);
    let synonyms_map = get_semantic_synonyms();
    
    let mut suggestions: Vec<(String, f64)> = Vec::new();
    
    for tag in &db_tags {
        let tag_plain = tag.trim_start_matches('#');
        let mut score = 0.0;
        
        // Category 1: Exact tag name substring match (Weight 5.0)
        if combined_text.contains(tag_plain) {
            score += 5.0;
        }
        
        // Category 2: Synonym keyword matches (Weight 2.5 per match)
        if let Some(synonyms) = synonyms_map.get(tag_plain) {
            for &syn in synonyms {
                if combined_text.contains(syn) {
                    score += 2.5;
                }
            }
        }
        
        // Category 3: Term-level Jaccard similarity (Weight 1.0)
        let tag_terms = extract_terms(tag_plain);
        let jaccard = calculate_similarity(&combined_terms, &tag_terms);
        score += jaccard * 1.5;
        
        if score > 0.1 {
            suggestions.push((tag.clone(), score));
        }
    }
    
    // Sort descending by score
    suggestions.sort_by(|a, b| b.1.partial_cmp(&a.1).unwrap_or(std::cmp::Ordering::Equal));
    
    let mut recommended: Vec<String> = suggestions.into_iter().take(top_k).map(|(tag, _)| tag).collect();
    
    // Fallback to standard generic tags if no suggestions score high enough
    if recommended.len() < top_k {
        for tag in &db_tags {
            if !recommended.contains(tag) {
                recommended.push(tag.clone());
            }
            if recommended.len() >= top_k {
                break;
            }
        }
    }
    
    Ok(recommended.into_iter().take(top_k).collect())
}
