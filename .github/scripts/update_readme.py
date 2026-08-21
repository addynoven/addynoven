#!/usr/bin/env python3
"""
Auto-update README with recent GitHub activity.
Generates a borderless SVG card for recent activity and updates telemetry sections.
"""

import os
import re
import html
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
    """Get repos updated in the last 365 days."""
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


def get_recent_activity(max_items=20):
    """Get recent public activity as structured data.

    Returns:
        tuple: (list of activity dicts, ignored_count)
        Each dict has: date, short_date, type, repo, repo_url, detail, count
    """
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
        created_at = None
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

        date_str = created_at.strftime("%Y-%m-%d") if created_at else "unknown"
        short_date = date_str[5:] if len(date_str) >= 10 else date_str

        activity = None

        if event_type == "PushEvent":
            commits = event.get("payload", {}).get("commits", [])
            if commits:
                msg = commits[-1].get("message", "").split("\n")[0]
                if len(msg) > 50:
                    msg = msg[:47] + "..."
                if not msg:
                    msg = "Updated code"
                count = len(commits)
            else:
                count = event.get("payload", {}).get("size", 1)
                msg = "Updated code"

            activity = {
                "date": date_str, "short_date": short_date,
                "type": "PUSH", "repo": repo_name,
                "repo_url": repo_url, "detail": msg, "count": count,
            }

        elif event_type == "CreateEvent":
            ref_type = event.get("payload", {}).get("ref_type")
            if ref_type == "repository":
                activity = {
                    "date": date_str, "short_date": short_date,
                    "type": "NEW", "repo": repo_name,
                    "repo_url": repo_url, "detail": "Created repository",
                    "count": 0,
                }

        elif event_type == "WatchEvent":
            activity = {
                "date": date_str, "short_date": short_date,
                "type": "STAR", "repo": repo_name,
                "repo_url": repo_url, "detail": "Starred", "count": 0,
            }

        elif event_type == "PullRequestEvent":
            action = event.get("payload", {}).get("action")
            if action == "opened":
                title = event.get("payload", {}).get("pull_request", {}).get("title", "")
                if len(title) > 50:
                    title = title[:47] + "..."
                activity = {
                    "date": date_str, "short_date": short_date,
                    "type": "PR", "repo": repo_name,
                    "repo_url": repo_url, "detail": title, "count": 0,
                }

        if activity:
            activities.append(activity)
            seen_repos.add(repo_name)

        if len(activities) >= max_items:
            break

    return activities, ignored_count


def generate_activity_section(activities):
    """Generate recent activity section as markdown (console output)."""
    if not activities:
        return "No recent public activity."

    emoji_map = {"PUSH": "🔨", "STAR": "⭐", "NEW": "✨", "PR": "🔌"}
    lines = []

    for i, a in enumerate(activities[:10]):
        emoji = emoji_map.get(a["type"], "📌")

        if a["type"] == "PUSH":
            text = f"{emoji} Pushed {a['count']} commits to [{a['repo']}]({a['repo_url']})"
        elif a["type"] == "STAR":
            text = f"{emoji} Starred [{a['repo']}]({a['repo_url']})"
        elif a["type"] == "NEW":
            text = f"{emoji} Created repository [{a['repo']}]({a['repo_url']})"
        elif a["type"] == "PR":
            text = f"{emoji} Opened PR in [{a['repo']}]({a['repo_url']}): {a['detail']}"
        else:
            text = f"📌 [{a['repo']}]({a['repo_url']})"

        lines.append(f"{i+1}. `{a['date']}` {text}<br>")

    return "\n".join(lines)


def generate_activity_svg(activities, output_path="recent_activity.svg"):
    """Generate a borderless dark-themed SVG card for recent activity.

    Two-column layout, single-line items with ellipsis truncation.
    Styled to match the terminal metrics card.
    """

    ITEMS_PER_COL = 10
    LINE_HEIGHT = 22
    HEADER_Y = 28
    FIRST_ITEM_Y = 58
    COL1_X = 25
    COL2_X = 505
    WIDTH = 985
    MAX_REPO_LEN = 32

    # Absolute x offsets from column start
    NUM_OFF = 0
    DATE_OFF = 35
    ACTION_OFF = 90
    REPO_OFF = 140

    ACTION_COLORS = {
        "PUSH": "#3fb950",
        "STAR": "#e3b341",
        "NEW": "#58a6ff",
        "PR": "#bc8cff",
    }

    items = activities[:ITEMS_PER_COL * 2]
    num_rows = min(ITEMS_PER_COL, max(len(items), 1))
    height = FIRST_ITEM_Y + num_rows * LINE_HEIGHT + 18

    def esc(text):
        """Escape text for XML."""
        return html.escape(str(text))

    def truncate(text, max_len):
        if len(text) > max_len:
            return text[:max_len - 3] + "..."
        return text

    svg = []
    svg.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{height}"'
        f' font-family="ConsolasFallback,Consolas,Monaco,monospace" font-size="14px">'
    )
    svg.append('<style>')
    svg.append("@font-face {")
    svg.append("  src: local('Consolas'), local('Consolas Bold'), local('Monaco');")
    svg.append("  font-family: 'ConsolasFallback';")
    svg.append("  font-display: swap;")
    svg.append("}")
    svg.append("text, tspan { white-space: pre; }")
    svg.append('</style>')
    svg.append(f'<rect width="{WIDTH}" height="{height}" fill="#161b22" rx="15"/>')
    svg.append('')

    # Header: recent-activity@neon ─────────...
    dashes = "\u2500" * 77
    svg.append(
        f'<text x="{COL1_X}" y="{HEADER_Y}" fill="#c9d1d9" font-size="14px">'
        f'recent-activity'
        f'<tspan fill="#616e7f">@</tspan>'
        f'<tspan fill="#ffa657">neon</tspan>'
        f'<tspan fill="#30363d"> {dashes}</tspan>'
        f'</text>'
    )
    svg.append('')

    for i, item in enumerate(items):
        col_x = COL1_X if i < ITEMS_PER_COL else COL2_X
        row = i if i < ITEMS_PER_COL else i - ITEMS_PER_COL
        y = FIRST_ITEM_Y + row * LINE_HEIGHT

        num = f"{i + 1:2d}."
        date = esc(item["short_date"])
        action = item["type"]
        color = ACTION_COLORS.get(action, "#c9d1d9")

        # Own repos: show just repo name. Others: show user/repo.
        repo = item["repo"]
        if action in ("PUSH", "NEW") and "/" in repo:
            owner, repo_name = repo.split("/", 1)
            if owner.lower() == GITHUB_USER.lower():
                repo_display = repo_name
            else:
                repo_display = repo
        else:
            repo_display = repo

        repo_display = esc(truncate(repo_display, MAX_REPO_LEN))

        nx = col_x + NUM_OFF
        dx = col_x + DATE_OFF
        ax = col_x + ACTION_OFF
        rx = col_x + REPO_OFF

        svg.append(
            f'<text y="{y}">'
            f'<tspan x="{nx}" fill="#484f58">{num}</tspan>'
            f'<tspan x="{dx}" fill="#616e7f">{date}</tspan>'
            f'<tspan x="{ax}" fill="{color}">{action:4s}</tspan>'
            f'<tspan x="{rx}" fill="#a5d6ff">{repo_display}</tspan>'
            f'</text>'
        )

    svg.append('</svg>')

    with open(output_path, "w") as f:
        f.write("\n".join(svg))

    print(f"✅ Activity SVG written to {output_path}")


def generate_stack_section(languages):
    """Generate the tech stack section."""
    if not languages:
        return "Currently exploring new technologies..."

    lines = []
    for lang, _ in languages:
        icon = LANGUAGE_ICONS.get(lang, f"📦 {lang}")
        lines.append(f"  {icon}")

    return "\n".join(lines)


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
        activities, ignored_count = get_recent_activity(max_items=20)
        print(f"   Found {len(activities)} activities (and filtered {ignored_count} from ignored repos)")
    except Exception as e:
        print(f"   Error fetching activity: {e}")
        activities = []

    # Generate activity SVG card (borderless, two-column)
    print("🎨 Generating activity SVG...")
    generate_activity_svg(activities)

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

    # Replace dynamic sections using markers (no-op if markers don't exist)
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
