"""Generate profile.svg with GitHub data."""

import html
import json
import os
import pathlib
import urllib.request

ROOT = pathlib.Path(__file__).parent.resolve()
GITHUB_USER = "katanabe"
REPOS_LIMIT = 3


def _headers() -> dict:
    headers = {"Accept": "application/vnd.github+json"}
    token = os.environ.get("GH_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def fetch_repos() -> list[dict]:
    url = f"https://api.github.com/users/{GITHUB_USER}/repos?sort=updated&per_page=100"
    req = urllib.request.Request(url, headers=_headers())
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def fetch_stats(repos: list[dict]) -> dict:
    stars = sum(r.get("stargazers_count", 0) for r in repos if not r["fork"] and r["name"] != GITHUB_USER)
    repo_count = sum(1 for r in repos if not r["fork"] and r["name"] != GITHUB_USER)
    base = {"commits": None, "stars": stars, "prs": None, "repos": repo_count}

    if not os.environ.get("GH_TOKEN"):
        return base

    query = """{ user(login: "%s") {
      contributionsCollection { totalCommitContributions }
      pullRequests { totalCount }
    }}""" % GITHUB_USER
    payload = json.dumps({"query": query}).encode()
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=payload,
        headers={**_headers(), "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read())
        u = data["data"]["user"]
        base["commits"] = u["contributionsCollection"]["totalCommitContributions"]
        base["prs"] = u["pullRequests"]["totalCount"]
    except Exception:
        pass
    return base


def format_number(n: int) -> str:
    if n >= 1000:
        return f"{n / 1000:.1f}k"
    return str(n)


def build_now_lines(repos: list[dict]) -> list[str]:
    lines = []
    for repo in repos:
        if repo["fork"] or repo["name"] == GITHUB_USER:
            continue
        lines.append(repo["name"])
        if len(lines) >= REPOS_LIMIT:
            break
    return lines


def build_interests_string(repos: list[dict]) -> str:
    topics: dict[str, int] = {}
    for repo in repos:
        if repo["fork"] or repo["name"] == GITHUB_USER:
            continue
        for topic in repo.get("topics", []):
            topics[topic] = topics.get(topic, 0) + 1
    if not topics:
        langs: set[str] = set()
        for repo in repos:
            if repo["fork"] or repo["name"] == GITHUB_USER:
                continue
            lang = repo.get("language")
            if lang:
                langs.add(lang.lower())
        return " · ".join(sorted(langs))
    sorted_topics = sorted(topics.items(), key=lambda x: x[1], reverse=True)
    return " · ".join(t[0] for t in sorted_topics[:10])


def render_svg(now: list[str], interests: str, stats: dict) -> str:
    now_padded = (now + ["", "", ""])[:3]
    n = [html.escape(f"› {x}") if x else "" for x in now_padded]
    c = html.escape(format_number(stats["commits"]) if stats["commits"] is not None else "-")
    s = html.escape(format_number(stats["stars"]))
    p = html.escape(format_number(stats["prs"]) if stats["prs"] is not None else "-")
    r = html.escape(format_number(stats["repos"]))
    i = html.escape(interests)

    return f"""<svg width="780" height="392" viewBox="0 0 780 392" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <clipPath id="clip">
      <rect width="780" height="392" rx="10"/>
    </clipPath>
  </defs>
  <g clip-path="url(#clip)">
    <rect width="780" height="392" fill="#2E3440"/>
    <rect width="780" height="4" fill="#88C0D0"/>
    <rect x="1" y="1" width="778" height="390" rx="9" fill="none" stroke="#3B4252" stroke-width="1"/>

    <text x="40" y="46" font-family="'Courier New',Courier,monospace" font-size="26" font-weight="bold" fill="#D8DEE9">katanabe</text>
    <text x="40" y="68" font-family="'Courier New',Courier,monospace" font-size="12" fill="#4C566A">Software Engineer @ ttti llc.  ·  Tokyo, JP</text>
    <rect x="40" y="76" width="160" height="2" rx="1" fill="#88C0D0"/>
    <rect x="40" y="88" width="700" height="1" fill="#3B4252"/>

    <text x="40" y="108" font-family="'Courier New',Courier,monospace" font-size="10" fill="#88C0D0" letter-spacing="3">NOW</text>
    <text x="410" y="108" font-family="'Courier New',Courier,monospace" font-size="10" fill="#88C0D0" letter-spacing="3">STACK</text>

    <text x="40" y="128" font-family="'Courier New',Courier,monospace" font-size="13" fill="#D8DEE9">{n[0]}</text>
    <text x="40" y="148" font-family="'Courier New',Courier,monospace" font-size="13" fill="#D8DEE9">{n[1]}</text>
    <text x="40" y="168" font-family="'Courier New',Courier,monospace" font-size="13" fill="#D8DEE9">{n[2]}</text>

    <text x="410" y="128" font-family="'Courier New',Courier,monospace" font-size="13" fill="#D8DEE9">TypeScript · Vue · Python</text>
    <text x="410" y="148" font-family="'Courier New',Courier,monospace" font-size="13" fill="#4C566A">css · glsl · go template</text>
    <text x="410" y="168" font-family="'Courier New',Courier,monospace" font-size="13" fill="#4C566A">ruby · dockerfile</text>

    <rect x="40" y="184" width="700" height="1" fill="#3B4252"/>

    <text x="40" y="203" font-family="'Courier New',Courier,monospace" font-size="10" fill="#88C0D0" letter-spacing="3">STATS</text>

    <text x="125" y="228" text-anchor="middle" font-family="'Courier New',Courier,monospace" font-size="20" font-weight="bold" fill="#D8DEE9">{c}</text>
    <text x="125" y="246" text-anchor="middle" font-family="'Courier New',Courier,monospace" font-size="11" fill="#4C566A">commits</text>
    <rect x="210" y="210" width="1" height="42" fill="#3B4252"/>
    <text x="295" y="228" text-anchor="middle" font-family="'Courier New',Courier,monospace" font-size="20" font-weight="bold" fill="#D8DEE9">{s}</text>
    <text x="295" y="246" text-anchor="middle" font-family="'Courier New',Courier,monospace" font-size="11" fill="#4C566A">stars</text>
    <rect x="380" y="210" width="1" height="42" fill="#3B4252"/>
    <text x="465" y="228" text-anchor="middle" font-family="'Courier New',Courier,monospace" font-size="20" font-weight="bold" fill="#D8DEE9">{p}</text>
    <text x="465" y="246" text-anchor="middle" font-family="'Courier New',Courier,monospace" font-size="11" fill="#4C566A">PRs</text>
    <rect x="550" y="210" width="1" height="42" fill="#3B4252"/>
    <text x="635" y="228" text-anchor="middle" font-family="'Courier New',Courier,monospace" font-size="20" font-weight="bold" fill="#D8DEE9">{r}</text>
    <text x="635" y="246" text-anchor="middle" font-family="'Courier New',Courier,monospace" font-size="11" fill="#4C566A">repos</text>

    <rect x="40" y="262" width="700" height="1" fill="#3B4252"/>

    <text x="40" y="281" font-family="'Courier New',Courier,monospace" font-size="10" fill="#88C0D0" letter-spacing="3">INTERESTS</text>
    <text x="40" y="300" font-family="'Courier New',Courier,monospace" font-size="12" fill="#D8DEE9">{i}</text>

    <rect x="40" y="316" width="700" height="1" fill="#3B4252"/>

    <text x="40" y="335" font-family="'Courier New',Courier,monospace" font-size="10" fill="#88C0D0" letter-spacing="3">LINKS</text>
    <text x="40" y="356" font-family="'Courier New',Courier,monospace" font-size="12" fill="#81A1C1">github.com/katanabe</text>
    <text x="252" y="356" font-family="'Courier New',Courier,monospace" font-size="12" fill="#3B4252">·</text>
    <text x="265" y="356" font-family="'Courier New',Courier,monospace" font-size="12" fill="#81A1C1">ttti.jp</text>

    <rect x="553" y="344" width="14" height="14" rx="2" fill="#3B4252"/>
    <rect x="573" y="344" width="14" height="14" rx="2" fill="#88C0D0"/>
    <rect x="593" y="344" width="14" height="14" rx="2" fill="#81A1C1"/>
    <rect x="613" y="344" width="14" height="14" rx="2" fill="#A3BE8C"/>
    <rect x="633" y="344" width="14" height="14" rx="2" fill="#EBCB8B"/>
    <rect x="653" y="344" width="14" height="14" rx="2" fill="#BF616A"/>
    <rect x="673" y="344" width="14" height="14" rx="2" fill="#B48EAD"/>

    <rect x="40" y="372" width="700" height="1" fill="#3B4252"/>
    <text x="40" y="387" font-family="'Courier New',Courier,monospace" font-size="10" fill="#3B4252">Building since 2015</text>
    <text x="740" y="387" text-anchor="end" font-family="'Courier New',Courier,monospace" font-size="10" fill="#3B4252">github.com/katanabe/katanabe</text>
  </g>
</svg>"""


def main():
    repos = fetch_repos()
    stats = fetch_stats(repos)
    now = build_now_lines(repos)
    interests = build_interests_string(repos)
    svg = render_svg(now, interests, stats)
    (ROOT / "profile.svg").write_text(svg)
    print("profile.svg updated.")


if __name__ == "__main__":
    main()
