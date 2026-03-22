"""Build README.md with latest repos and interests from GitHub API."""

import json
import os
import pathlib
import re
import urllib.request

ROOT = pathlib.Path(__file__).parent.resolve()
GITHUB_USER = "katanabe"
REPOS_LIMIT = 5
EXCLUDE_REPOS = {GITHUB_USER}  # exclude profile repo itself


def replace_chunk(content: str, marker: str, chunk: str) -> str:
    pattern = re.compile(
        rf"<!-- {marker} starts -->.*<!-- {marker} ends -->",
        re.DOTALL,
    )
    return pattern.sub(
        f"<!-- {marker} starts -->\n{chunk}\n<!-- {marker} ends -->",
        content,
    )


def fetch_repos() -> list[dict]:
    url = f"https://api.github.com/users/{GITHUB_USER}/repos?sort=updated&per_page=100"
    headers = {"Accept": "application/vnd.github+json"}
    token = os.environ.get("GH_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def build_now_section(repos: list[dict]) -> str:
    lines = []
    for repo in repos:
        if repo["fork"] or repo["name"] in EXCLUDE_REPOS:
            continue
        if len(lines) >= REPOS_LIMIT:
            break
        name = repo["name"]
        desc = repo["description"] or ""
        url = repo["html_url"]
        lines.append(f"- [{name}]({url}) — {desc}" if desc else f"- [{name}]({url})")
    return "\n".join(lines)


def build_interests_section(repos: list[dict]) -> str:
    topics: dict[str, int] = {}
    for repo in repos:
        if repo["fork"] or repo["name"] in EXCLUDE_REPOS:
            continue
        for topic in repo.get("topics", []):
            topics[topic] = topics.get(topic, 0) + 1

    if not topics:
        # fallback: collect languages
        langs: set[str] = set()
        for repo in repos:
            if repo["fork"] or repo["name"] in EXCLUDE_REPOS:
                continue
            lang = repo.get("language")
            if lang:
                langs.add(lang.lower())
        return " · ".join(sorted(langs))

    sorted_topics = sorted(topics.items(), key=lambda x: x[1], reverse=True)
    return " · ".join(t[0] for t in sorted_topics[:12])


def main():
    readme_path = ROOT / "README.md"
    content = readme_path.read_text()

    repos = fetch_repos()

    content = replace_chunk(content, "now", build_now_section(repos))
    content = replace_chunk(content, "interests", build_interests_section(repos))

    readme_path.write_text(content)
    print("README.md updated.")


if __name__ == "__main__":
    main()
