import requests
import re
import os

# CONFIG
GITHUB_USERNAME = "addynoven"
README_PATH = "README.md"

def get_latest_activity():
    url = f"https://api.github.com/users/{GITHUB_USERNAME}/events/public"
    response = requests.get(url)
    if response.status_code != 200:
        return "Coding something cool..."
    
    events = response.json()
    
    for event in events:
        if event["type"] == "PushEvent":
            repo_name = event["repo"]["name"]
            # Fetch repo language
            repo_url = f"https://api.github.com/repos/{repo_name}"
            repo_data = requests.get(repo_url).json()
            language = repo_data.get("language", "Unknown")
            
            return map_language_to_status(language)
            
    return "Exploring new tech..."

def map_language_to_status(language):
    # DYNAMIC LOGIC: This is where the magic happens
    lang = str(language).lower()
    
    if "python" in lang or "jupyter" in lang:
        return "Training+AI+Models;Crunching+Data+with+Python"
    elif "dart" in lang:
        return "Building+Mobile+Apps;Flutter+Development"
    elif "javascript" in lang or "typescript" in lang or "html" in lang:
        return "Building+Web+Apps;Full-Stack+Engineering"
    elif "c#" in lang:
        return "Game+Dev+with+Unity;Scripting+Logic"
    else:
        return f"Working+with+{language};Writing+Code"

def update_readme(status_line):
    # The base URL for the typing SVG service
    base_url = "https://readme-typing-svg.demolab.com?font=Fira+Code&pause=1000&color=70A5FD&center=true&vCenter=true&width=435"
    # Always keep "I am Aditya" as the first line, append the dynamic status
    new_lines = f"I+am+Aditya;{status_line}"
    new_url = f"{base_url}&lines={new_lines}"
    
    new_img_tag = f'<img src="{new_url}" alt="Typing SVG" />'
    
    with open(README_PATH, "r", encoding="utf-8") as file:
        content = file.read()
        
    # Regex to replace content between the markers
    pattern = r"(<!-- TYPING:START -->)([\s\S]*?)(<!-- TYPING:END -->)"
    replacement = f"\\1\n{new_img_tag}\n\\3"
    
    new_content = re.sub(pattern, replacement, content)
    
    with open(README_PATH, "w", encoding="utf-8") as file:
        file.write(new_content)

if __name__ == "__main__":
    status = get_latest_activity()
    print(f"Detected status: {status}")
    update_readme(status)
