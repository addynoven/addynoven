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

# Repositories to ignore
IGNORED_REPOS = {
    # "addynoven/addynoven",
}

if not GITHUB_TOKEN:
    raise ValueError("GITHUB_TOKEN environment variable is not set")

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
    response.raise_for_status()
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
                if response.status_code == 200:
                    lang_data = response.json()
                    for lang, bytes_count in lang_data.items():
                        languages[lang] += bytes_count // 1000  # Weight by KB
            except:
                pass
    
    return languages.most_common(6)

def get_recent_activity():
    """Get recent public activity."""
    # Fetch larger history to cover the last month
    url = f"https://api.github.com/users/{GITHUB_USER}/events?per_page=100"
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        events = response.json()
    except Exception as e:
        print(f"Error fetching events: {e}")
        return [], 0
    
    activities = []
    seen_repos = set()
    ignored_count = 0
    cutoff_date = datetime.now() - timedelta(days=30)
    
    for event in events:
        if not isinstance(event, dict):
            continue
            
        created_at_str = event.get("created_at")
        if created_at_str:
            try:
                created_at = datetime.strptime(created_at_str, "%Y-%m-%dT%H:%M:%SZ")
                if created_at < cutoff_date:
                    continue
            except ValueError:
                pass

        repo_name = event.get("repo", {}).get("name", "")
        if not repo_name:
            continue
            
        # Skip ignored repos
        if repo_name in IGNORED_REPOS:
            ignored_count += 1
            continue
            
        event_type = event.get("type")
        repo_url = f"https://github.com/{repo_name}"
        
        # Unique entry per repo for cleaner look
        if repo_name in seen_repos:
            continue
            
        item_text = ""
        if event_type == "PushEvent":
            commits = event.get("payload", {}).get("commits", [])
            if commits:
                msg = commits[-1].get("message", "").split("\n")[0]
                if len(msg) > 50:
                    msg = msg[:47] + "..."
                if not msg:
                    msg = "Updated code"
                item_text = f"🔨 Pushed to [{repo_name}]({repo_url}): {msg}"
            else:
                # Fallback if no specific commit info in payload
                count = event.get("payload", {}).get("size", 1)
                item_text = f"🔨 Pushed {count} commits to [{repo_name}]({repo_url})"
                
        elif event_type == "CreateEvent":
            ref_type = event.get("payload", {}).get("ref_type")
            if ref_type == "repository":
                item_text = f"✨ Created repository [{repo_name}]({repo_url})"
                
        elif event_type == "WatchEvent":
            item_text = f"⭐ Starred [{repo_name}]({repo_url})"
            
        elif event_type == "PullRequestEvent":
            action = event.get("payload", {}).get("action")
            if action == "opened":
                title = event.get("payload", {}).get("pull_request", {}).get("title", "")
                if len(title) > 50:
                    title = title[:47] + "..."
                item_text = f"🔌 Opened PR in [{repo_name}]({repo_url}): {title}"

        if item_text:
            # Prepend date for visibility
            date_str = created_at.strftime("%Y-%m-%d")
            activities.append(f"`{date_str}` {item_text}")
            seen_repos.add(repo_name)

        # Limit for README (keep it cleaner than local debug)
        if len(activities) >= 10:
            break
    
    return activities, ignored_count

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
        return "No recent public activity."
    
    return "\n".join(f"{i+1}. {a}<br>" for i, a in enumerate(activities))

def update_readme():
    """Update the README with dynamic content."""
    readme_path = "README.md"
    
    print("📊 Fetching recent repos...")
    try:
        repos = get_recent_repos()
        print(f"   Found {len(repos)} recent repos")
    except Exception as e:
        print(f"   Error fetching repos: {e}")
        repos = []
    
    print("🔍 Analyzing languages...")
    languages = get_repo_languages(repos)
    print(f"   Top languages: {[l[0] for l in languages]}")
    
    print("📝 Fetching recent activity...")
    try:
        activities, ignored_count = get_recent_activity()
        print(f"   Found {len(activities)} activities (and filtered {ignored_count} from ignored repos)")
    except Exception as e:
        print(f"   Error fetching activity: {e}")
        activities = []
    
    # Generate sections
    stack_content = generate_stack_section(languages)
    activity_content = generate_activity_section(activities)

    print("\n⚡ Recent Activity:")
    print(activity_content)
    print("\n")
    
    # Get current date
    updated_date = datetime.now().strftime("%B %d, %Y")

    
    # Read current README
    if not os.path.exists(readme_path):
        print(f"❌ {readme_path} not found!")
        return

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
        r"(<!--RECENT_ACTIVITY:start-->).*?(<!--RECENT_ACTIVITY:end-->)",
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
