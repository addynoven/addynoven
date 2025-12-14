#!/usr/bin/env python3
"""
Local script to ONLY print recent GitHub activity to the shell.
Does NOT update README.md.
"""

import os
import requests
from datetime import datetime, timedelta

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

def get_recent_activity():
    """Get recent public activity."""
    # Fetch larger history to cover the last month
    url = f"https://api.github.com/users/{GITHUB_USER}/events?per_page=100"
    print(f"   Querying: {url}")
    
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    events = response.json()
    
    activities = []
    seen_repos = set()
    ignored_count = 0
    cutoff_date = datetime.now() - timedelta(days=30)
    
    # Debug: stats on event types
    event_types = {}
    
    print(f"   Found {len(events)} raw events")
    
    for event in events:
        if not isinstance(event, dict):
            continue
            
        etype = event.get("type", "Unknown")
        event_types[etype] = event_types.get(etype, 0) + 1
            
        created_at_str = event.get("created_at")
        if created_at_str:
            # Parse 2023-01-01T00:00:00Z
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
        
        # Unique entry per repo check to show ALL history
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
                # Debug: Print payload to understand why commits are missing
                if len(activities) < 3: # Only print for first few to avoid spam
                     print(f"   [Debug] Payload for {repo_name}: {event.get('payload')}")
                
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
                    item_text = f"🔌 Opened PR in [{repo_name}]({repo_url}): {title}"

        if item_text:
            # Prepend date for visibility
            date_str = created_at.strftime("%Y-%m-%d")
            activities.append(f"`{date_str}` {item_text}")
            seen_repos.add(repo_name)

        # Show more items for local debug
        if len(activities) >= 100:
            break
    
    print(f"   Event Types Found: {event_types}")
    return activities, ignored_count

def generate_activity_section(activities):
    """Generate recent activity section."""
    if not activities:
        return "No recent public activity."
    
    return "\n".join(f"{i+1}. {a}" for i, a in enumerate(activities))

if __name__ == "__main__":
    print("📝 Fetching recent activity...")
    try:
        activities, ignored_count = get_recent_activity()
        print(f"   Found {len(activities)} activities (and filtered {ignored_count} from ignored repos)")
        
        print("\n⚡ Recent Activity:")
        print(generate_activity_section(activities))
        print("\n")
        
    except Exception as e:
        print(f"   Error fetching activity: {e}")
