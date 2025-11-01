import re
def remove_html_tags(text: str) -> str:
    """remove html brackets from description text"""

    if not text:
        return text
    clean_text = re.sub(r'<[^>]+>', '', text)
    return clean_text
