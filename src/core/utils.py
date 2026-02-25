import markdown
from bs4 import BeautifulSoup

def strip_markdown(markdown_text: str) -> str:
    """
    Converts markdown to plain text using a combination of markdown and 
    BeautifulSoup libraries.
    """
    if not markdown_text:
        return ""
        
    # Convert markdown to HTML
    html = markdown.markdown(markdown_text)

    # Parse the HTML and extract the plain text
    soup = BeautifulSoup(html, features="html.parser")
    plain_text = soup.get_text()

    # Aggressively strip whitespace from EACH line
    lines = [line.strip() for line in plain_text.splitlines()]
    
    # Rejoin lines, ensuring we don't end up with more than 2 consecutive newlines for aesthetics
    result = "\n\n".join(lines)
    
    # Final cleanup of leading/trailing block whitespace
    return result.strip()
