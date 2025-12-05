import requests
import re
import os

# CONFIG
GITHUB_USERNAME = "addynoven"
README_PATH = "README.md"

# Language to status mapping - customize these!
LANGUAGE_STATUS_MAP = {
    "python": "Training AI Models;Crunching Data with Python",
    "jupyter notebook": "Training AI Models;Data Science Mode",
    "dart": "Building Mobile Apps;Flutter Development",
    "javascript": "Building Web Apps;Full-Stack Engineering",
    "typescript": "Building Web Apps;TypeScript Development",
    "html": "Crafting Web Interfaces;Frontend Development",
    "css": "Styling the Web;CSS Magic",
    "c#": "Game Dev with Unity;Scripting Logic",
    "c++": "Systems Programming;Low-Level Wizardry",
    "c": "Systems Programming;Bare Metal Coding",
    "go": "Building Microservices;Go Development",
    "rust": "Memory Safe Programming;Rust Development",
    "java": "Enterprise Development;Java Engineering",
    "kotlin": "Android Development;Kotlin Mode",
    "swift": "iOS Development;Swift Coding",
    "ruby": "Web Development;Ruby on Rails",
    "php": "Backend Development;PHP Scripting",
    "shell": "Automating Everything;Shell Scripting",
    "dockerfile": "Containerizing Apps;DevOps Mode",
    "yaml": "Configuring Infrastructure;DevOps Mode",
}

# Default fallback messages when language is None/Unknown
DEFAULT_STATUSES = [
    "Full-Stack Developer;Building apps & breaking things",
    "Coding Something Awesome;Always Learning",
]

def get_latest_activity():
    """Fetch the latest public activity and determine current status."""
    url = f"https://api.github.com/users/{GITHUB_USERNAME}/events/public"
    
    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            return DEFAULT_STATUSES[0]
        
        events = response.json()
        
        for event in events:
            if event["type"] == "PushEvent":
                repo_name = event["repo"]["name"]
                # Fetch repo language
                repo_url = f"https://api.github.com/repos/{repo_name}"
                repo_response = requests.get(repo_url, timeout=10)
                
                if repo_response.status_code == 200:
                    repo_data = repo_response.json()
                    language = repo_data.get("language")
                    
                    # Only use language if it's valid (not None or empty)
                    if language:
                        return map_language_to_status(language)
        
        # No valid language found in recent activity
        return DEFAULT_STATUSES[0]
        
    except Exception as e:
        print(f"Error fetching activity: {e}")
        return DEFAULT_STATUSES[0]

def map_language_to_status(language):
    """Map a programming language to a status message."""
    if not language:
        return DEFAULT_STATUSES[0]
    
    lang_lower = language.lower().strip()
    
    # Check for exact match first
    if lang_lower in LANGUAGE_STATUS_MAP:
        return LANGUAGE_STATUS_MAP[lang_lower]
    
    # Check for partial matches
    for key, status in LANGUAGE_STATUS_MAP.items():
        if key in lang_lower or lang_lower in key:
            return status
    
    # Fallback: use the language name naturally
    return f"Working with {language};Coding Mode"

def format_for_url(text):
    """Format text for URL (replace spaces with +)."""
    return text.replace(" ", "+").replace("&", "%26")

def update_readme(status_line):
    """Update the README with the new typing animation."""
    base_url = "https://readme-typing-svg.demolab.com?font=Fira+Code&pause=1000&color=70A5FD&center=true&vCenter=true&width=495"
    
    # Format the status for URL
    formatted_status = format_for_url(status_line)
    new_url = f"{base_url}&lines={formatted_status}"
    
    new_img_tag = f'<img src="{new_url}" alt="Typing SVG" />'
    
    with open(README_PATH, "r", encoding="utf-8") as file:
        content = file.read()
        
    # Regex to replace content between the markers
    pattern = r"(<!-- TYPING:START -->)([\s\S]*?)(<!-- TYPING:END -->)"
    replacement = f"\\1\n{new_img_tag}\n\\3"
    
    new_content = re.sub(pattern, replacement, content)
    
    with open(README_PATH, "w", encoding="utf-8") as file:
        file.write(new_content)
    
    print(f"README updated with: {status_line}")

if __name__ == "__main__":
    status = get_latest_activity()
    print(f"Detected status: {status}")
    update_readme(status)
