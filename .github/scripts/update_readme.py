import os
import sys
import json
import urllib.request
import datetime

branch = os.environ.get("BRANCH_NAME", "").strip()
if not branch or not branch.isdigit():
    print(f"Branch '{branch}' is not a numeric AppID. Skipping.")
    sys.exit(0)

print(f"[+] Processing AppID: {branch}")

# 1. Fetch game name from Steam Store API (using urllib standard library, zero dependencies)
game_name = f"Game {branch}"
try:
    req = urllib.request.Request(
        f"https://store.steampowered.com/api/appdetails?appids={branch}",
        headers={"User-Agent": "Mozilla/5.0"}
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        if data and str(branch) in data and data[str(branch)].get("success"):
            game_name = data[str(branch)]["data"]["name"]
except Exception as e:
    print(f"Steam API query warning: {e}")

print(f"[+] Game Name: {game_name}")

# 2. Update README.md
readme_path = "README.md"
if not os.path.exists(readme_path):
    print("README.md not found.")
    sys.exit(0)

with open(readme_path, "r", encoding="utf-8") as f:
    content = f.read()

start_tag = "<!-- RECENT_GAMES_START -->"
end_tag = "<!-- RECENT_GAMES_END -->"

if start_tag not in content or end_tag not in content:
    print("Tags not found in README.md.")
    sys.exit(0)

repo_name = os.environ.get("GITHUB_REPOSITORY", "DrxmReal/WhoziaoHub")
today_str = datetime.datetime.now().strftime("%Y-%m-%d")
new_row = f"| {today_str} | [`{branch}`](https://github.com/{repo_name}/tree/{branch}) | **{game_name}** | Tải mới | `✅ Sẵn sàng` |"

before = content.split(start_tag)[0] + start_tag + "\n"
middle_and_after = content.split(start_tag)[1]
table_part, after = middle_and_after.split(end_tag)

lines = [line.strip() for line in table_part.strip().split("\n") if line.strip()]
header_lines = lines[:2]
existing_rows = lines[2:]

# Avoid duplicate row
existing_rows = [row for row in existing_rows if f"`{branch}`" not in row]
updated_rows = [new_row] + existing_rows[:14]

new_table = "\n".join(header_lines + updated_rows) + "\n"
updated_readme = before + new_table + end_tag + after

with open(readme_path, "w", encoding="utf-8") as f:
    f.write(updated_readme)

print(f"[+] Successfully updated README.md with {game_name} ({branch})")
