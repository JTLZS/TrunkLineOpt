import pandas as pd

def clean_skills(skill_str):
    """
    辅助函数：清理技能字符串 (去除空格、空项)
    例如: "cold; express " -> ["cold", "express"]
    """
    if pd.isna(skill_str) or str(skill_str).strip() == "":
        return []
    parts = str(skill_str).split(';')
    cleaned = [p.strip() for p in parts if p.strip()]
    return cleaned