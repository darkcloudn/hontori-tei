import urllib.request
import urllib.parse
import re
import os

BASE_URL = 'https://nentokyo.jp/'
TARGET_DIR = '/Users/ducviettong/Documents/Mizsoft/Landingpage-food/temp'

if not os.path.exists(TARGET_DIR):
    os.makedirs(TARGET_DIR)

print("Fetching index...")
req = urllib.request.Request(BASE_URL, headers={'User-Agent': 'Mozilla/5.0'})
try:
    with urllib.request.urlopen(req) as response:
        html = response.read()
except Exception as e:
    print(f"Error fetching base URL: {e}")
    exit(1)

html_str = html.decode('utf-8')

# Regex to find unescaped links like src="...", href="..."
pattern = re.compile(r'(src|href)=["\'](.*?)["\']', re.IGNORECASE)

assets = []
def replace_link(match):
    attr = match.group(1)
    link = match.group(2)
    
    # We mainly care about resources: images, css, js
    if link.startswith('data:') or link.startswith('#'):
        return match.group(0)
    
    if link.endswith('.css') or link.endswith('.js') or re.search(r'\.(jpg|jpeg|png|svg|webp|gif)', link, re.IGNORECASE):
        full_url = urllib.parse.urljoin(BASE_URL, link)
        # Handle protocol-relative
        if full_url.startswith('//'):
            full_url = 'https:' + full_url
            
        parsed = urllib.parse.urlparse(full_url)
        local_path = parsed.path.lstrip('/')
        if not local_path:
            local_path = 'index_asset'
            
        assets.append((full_url, local_path))
        return f'{attr}="{local_path}"'
        
    return match.group(0)

print("Parsing HTML and rewriting links...")
new_html = pattern.sub(replace_link, html_str)

# Now also let's look for background-image: url(...)
bg_pattern = re.compile(r'url\((["\']?)(.*?)\1\)', re.IGNORECASE)
def replace_bg(match):
    quote = match.group(1)
    link = match.group(2)
    if link.startswith('data:') or link.startswith('#'):
        return match.group(0)
        
    full_url = urllib.parse.urljoin(BASE_URL, link)
    if full_url.startswith('//'):
        full_url = 'https:' + full_url
        
    parsed = urllib.parse.urlparse(full_url)
    local_path = parsed.path.lstrip('/')
    assets.append((full_url, local_path))
    return f'url({quote}{local_path}{quote})'

new_html = bg_pattern.sub(replace_bg, new_html)

print(f"Found {len(set(assets))} assets to download.")

for url, local_path in set(assets):
    full_local = os.path.join(TARGET_DIR, local_path)
    os.makedirs(os.path.dirname(full_local), exist_ok=True)
    if not os.path.exists(full_local):
        print(f"Downloading {url} to {local_path}...")
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req) as resp, open(full_local, 'wb') as f:
                f.write(resp.read())
        except Exception as e:
            print(f"Failed to download {url}: {e}")

with open(os.path.join(TARGET_DIR, 'index.html'), 'w', encoding='utf-8') as f:
    f.write(new_html)

print("Done cloning into temp!")
