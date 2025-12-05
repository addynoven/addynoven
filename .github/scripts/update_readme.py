#!/usr/bin/env python3
"""
Auto-update README with recent GitHub activity.
Analyzes recent repos and commits to show current tech stack.
"""

import os
import re
import requests
from datetime import datetime, timedelta
from collections import Counter

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
GITHUB_USER = os.environ.get("GITHUB_USER", "addynoven")

HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

# Map GitHub languages to friendly names/categories
LANGUAGE_ICONS = {
    "Dart": "🎯 Flutter/Dart",
    "JavaScript": "⚡ JavaScript",
    "TypeScript": "💙 TypeScript",
    "Python": "🐍 Python",
    "Java": "☕ Java",
    "Kotlin": "🟣 Kotlin",
    "Swift": "🍎 Swift",
    "C++": "⚙️ C++",
    "C": "🔧 C",
    "Go": "🐹 Go",
    "Rust": "🦀 Rust",
    "Ruby": "💎 Ruby",
    "PHP": "🐘 PHP",
    "HTML": "🌐 HTML/CSS",
    "CSS": "🎨 CSS",
    "Shell": "🐚 Shell",
    "Vue": "💚 Vue.js",
}

def get_recent_repos():
    """Get repos updated in the last 90 days."""
    url = f"https://api.github.com/users/{GITHUB_USER}/repos?sort=updated&per_page=100"
    response = requests.get(url, headers=HEADERS)
    repos = response.json()
    
    cutoff = datetime.now() - timedelta(days=365)
    recent = []
    
    for repo in repos:
        if isinstance(repo, dict) and repo.get("pushed_at"):
            pushed = datetime.strptime(repo["pushed_at"], "%Y-%m-%dT%H:%M:%SZ")
            if pushed > cutoff and not repo.get("fork"):
                recent.append(repo)
    
    return recent[:10]  # Top 10 recent repos

def get_repo_languages(repos):
    """Get languages used in recent repos."""
    languages = Counter()
    
    for repo in repos:
        lang = repo.get("language")
        if lang:
            languages[lang] += 1
        
        # Also fetch detailed language breakdown
        lang_url = repo.get("languages_url")
        if lang_url:
            try:
                response = requests.get(lang_url, headers=HEADERS)
                lang_data = response.json()
                for lang, bytes_count in lang_data.items():
                    languages[lang] += bytes_count // 1000  # Weight by KB
            except:
                pass
    
    return languages.most_common(6)

def get_recent_activity():
    """Get recent public activity."""
    url = f"https://api.github.com/users/{GITHUB_USER}/events/public?per_page=10"
    response = requests.get(url, headers=HEADERS)
    events = response.json()
    
    activities = []
    seen_repos = set()
    
    for event in events:
        if not isinstance(event, dict):
            continue
            
        repo_name = event.get("repo", {}).get("name", "").split("/")[-1]
        event_type = event.get("type")
        
        if repo_name in seen_repos:
            continue
        seen_repos.add(repo_name)
        
        if event_type == "PushEvent":
            commits = event.get("payload", {}).get("commits", [])
            if commits:
                msg = commits[0].get("message", "").split("\n")[0][:50]
                activities.append(f"🔨 Pushed to **{repo_name}**: {msg}")
        elif event_type == "CreateEvent":
            ref_type = event.get("payload", {}).get("ref_type")
            if ref_type == "repository":
                activities.append(f"✨ Created **{repo_name}**")
        elif event_type == "WatchEvent":
            activities.append(f"⭐ Starred **{repo_name}**")
        
        if len(activities) >= 5:
            break
    
    return activities

def generate_stack_section(languages):
    """Generate the tech stack section."""
    if not languages:
        return "Currently exploring new technologies..."
    
    lines = []
    for lang, _ in languages:
        icon = LANGUAGE_ICONS.get(lang, f"📦 {lang}")
        lines.append(f"  {icon}")
    
    return "\n".join(lines)

def generate_activity_section(activities):
    """Generate recent activity section."""
    if not activities:
        return "- 🔭 Working on something awesome..."
    
    return "\n".join(f"- {a}" for a in activities)

def update_readme():
    """Update the README with dynamic content."""
    readme_path = "README.md"
    
    print("📊 Fetching recent repos...")
    repos = get_recent_repos()
    print(f"   Found {len(repos)} recent repos")
    
    print("🔍 Analyzing languages...")
    languages = get_repo_languages(repos)
    print(f"   Top languages: {[l[0] for l in languages]}")
    
    print("📝 Fetching recent activity...")
    activities = get_recent_activity()
    print(f"   Found {len(activities)} activities")
    
    # Generate sections
    stack_content = generate_stack_section(languages)
    activity_content = generate_activity_section(activities)
    
    # Get current date
    updated_date = datetime.now().strftime("%B %d, %Y")
    
    # Read current README
    with open(readme_path, "r") as f:
        content = f.read()
    
    # Replace dynamic sections using markers
    content = re.sub(
        r"(<!-- STACK:START -->).*?(<!-- STACK:END -->)",
        f"\\1\n{stack_content}\n\\2",
        content,
        flags=re.DOTALL
    )
    
    content = re.sub(
        r"(<!-- ACTIVITY:START -->).*?(<!-- ACTIVITY:END -->)",
        f"\\1\n{activity_content}\n\\2",
        content,
        flags=re.DOTALL
    )
    
    content = re.sub(
        r"(<!-- UPDATED:START -->).*?(<!-- UPDATED:END -->)",
        f"\\1 *Last updated: {updated_date}* \\2",
        content,
        flags=re.DOTALL
    )
    
    # Write updated README
    with open(readme_path, "w") as f:
        f.write(content)
    
    print("✅ README updated successfully!")

if __name__ == "__main__":
    update_readme()
