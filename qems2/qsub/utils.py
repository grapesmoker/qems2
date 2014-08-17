from bs4 import BeautifulSoup

DEFAULT_ALLOWED_TAGS = ['b', 'i', 'u', 'strong', 'emph']

def sanitize_html(html, allowed_tags=DEFAULT_ALLOWED_TAGS):
    soup = BeautifulSoup(html)
    for tag in soup.find_all(True):
        if tag.name not in allowed_tags:
            tag.hidden = True

    return soup.renderContents()