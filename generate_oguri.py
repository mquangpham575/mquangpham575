import base64
import os
import random
from datetime import date, datetime, timedelta

import requests

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

GITHUB_API_URL = "https://api.github.com/graphql"
LOOKBACK_DAYS = 30
ANIM_DURATION = "8s"

WIDTH, HEIGHT = 800, 110
CELL_SIZE, GAP = 15, 5
BLOCK_W = CELL_SIZE + GAP
TRAVEL_DISTANCE = WIDTH + 10  # how far the character runs / the mask expands

# (max_count_inclusive, color) — ordered from lowest to highest
CONTRIBUTION_COLORS = [
    (0, "#161B22"),
    (2, "#0E4429"),
    (5, "#006D32"),
    (9, "#26A641"),
]
CONTRIBUTION_COLOR_MAX = "#39D353"

QUERY = """
query($userName:String!) {
  user(login: $userName){
    contributionsCollection {
      contributionCalendar {
        weeks {
          contributionDays {
            contributionCount
            date
          }
        }
      }
    }
  }
}
"""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def encode_image(path: str) -> str:
    """Read an image file and return a base64 data URI."""
    with open(path, "rb") as f:
        return f"data:image/png;base64,{base64.b64encode(f.read()).decode()}"


def get_color(count: int) -> str:
    """Map a contribution count to a GitHub-style green heatmap color."""
    for threshold, color in CONTRIBUTION_COLORS:
        if count <= threshold:
            return color
    return CONTRIBUTION_COLOR_MAX


# ---------------------------------------------------------------------------
# Data layer
# ---------------------------------------------------------------------------

def fetch_contributions(username: str, token: str) -> list[dict] | None:
    """Fetch the last LOOKBACK_DAYS of contribution counts from GitHub."""
    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = requests.post(
            GITHUB_API_URL,
            json={"query": QUERY, "variables": {"userName": username}},
            headers=headers,
        )
        response.raise_for_status()
        calendar = (
            response.json()["data"]["user"]
            ["contributionsCollection"]["contributionCalendar"]
        )
        all_days = [
            day for week in calendar["weeks"] for day in week["contributionDays"]
        ]
        cutoff = datetime.now().date() - timedelta(days=LOOKBACK_DAYS)
        return [
            {"count": d["contributionCount"]}
            for d in all_days
            if date.fromisoformat(d["date"]) >= cutoff
        ]
    except Exception as e:
        print(f"Error fetching contributions: {e}")
        return None


def fallback_contributions() -> list[dict]:
    """Generate deterministic pseudo-random contribution data for today."""
    random.seed(date.today().toordinal())
    return [
        {"count": random.randint(1, 10) if random.random() > 0.3 else 0}
        for _ in range(LOOKBACK_DAYS)
    ]


def get_contributions(username: str, token: str) -> list[dict]:
    if not token:
        print("No GITHUB_TOKEN found. Using random data.")
        return fallback_contributions()
    return fetch_contributions(username, token) or fallback_contributions()


# ---------------------------------------------------------------------------
# SVG building
# ---------------------------------------------------------------------------

def build_mouth_keyframes(days: list[dict]) -> tuple[str, str]:
    """Return (mouth_1_css, mouth_2_css) keyframe strings.

    mouth-1 is open (opacity 1) on days with commits; mouth-2 is open otherwise.
    The +0.01 nudge on the final keyframe ensures the mouth closes the instant
    the character passes the last contribution block.
    """
    scale = 100.0 / TRAVEL_DISTANCE
    mouth_1, mouth_2 = [], []

    for i, day in enumerate(days):
        pct = i * BLOCK_W * scale
        has = day["count"] > 0
        mouth_1.append(f"{pct:.4f}% {{ opacity: {'1' if has else '0'}; }}")
        mouth_2.append(f"{pct:.4f}% {{ opacity: {'0' if has else '1'}; }}")

    end_pct = len(days) * BLOCK_W * scale + 0.01
    mouth_1.append(f"{end_pct:.4f}% {{ opacity: 0; }}")
    mouth_2.append(f"{end_pct:.4f}% {{ opacity: 1; }}")

    return " ".join(mouth_1), " ".join(mouth_2)


def generate_svg(
    img1_path: str = "assets/oguri-1.png",
    img2_path: str = "assets/oguri-2.png",
    output_path: str = "oguri-run.svg",
    username: str = "mquangpham575",
    token: str = "",
) -> None:
    try:
        data_uri1 = encode_image(img1_path)
        data_uri2 = encode_image(img2_path)
    except FileNotFoundError as e:
        print(f"Error: Asset not found — {e}")
        return

    now = datetime.now()
    days = get_contributions(username, token)
    mouth_1_str, mouth_2_str = build_mouth_keyframes(days)

    contribution_rects = "\n    ".join(
        f'<rect x="{i * BLOCK_W}" y="0" width="{CELL_SIZE}" height="{CELL_SIZE}"'
        f' fill="{get_color(day["count"])}" rx="3"/>'
        for i, day in enumerate(days)
        if day["count"] > 0
    )

    svg = f"""\
<svg width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}"
     xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
<rect width="100%" height="100%" fill="#0D1117" rx="15"/>
<style>
  @keyframes oguri-run {{
      0%   {{ transform: translateX(0px); }}
      100% {{ transform: translateX({TRAVEL_DISTANCE}px); }}
  }}
  @keyframes oguri-bounce {{
      0%, 100% {{ transform: translateY(0px); }}
      50%       {{ transform: translateY(-3px); }}
  }}
  @keyframes mask-eat {{
      0%   {{ width: 0px; }}
      100% {{ width: {TRAVEL_DISTANCE}px; }}
  }}
  @keyframes oguri-mouth-1 {{ {mouth_1_str} }}
  @keyframes oguri-mouth-2 {{ {mouth_2_str} }}
  .oguri-container  {{ animation: oguri-run    {ANIM_DURATION} infinite linear; }}
  .oguri-bounce-layer {{ animation: oguri-bounce 0.15s           infinite ease-in-out; }}
  .mask-rector      {{ animation: mask-eat     {ANIM_DURATION} infinite linear; fill: black; }}
  .oguri-1 {{ animation: oguri-mouth-1 {ANIM_DURATION} infinite step-end; image-rendering: pixelated; }}
  .oguri-2 {{ animation: oguri-mouth-2 {ANIM_DURATION} infinite step-end; image-rendering: pixelated; }}
  .text    {{ fill: #8B949E; font-family: 'Segoe UI', sans-serif; font-size: 11px; font-weight: bold; }}
</style>
<mask id="eat-mask">
  <rect width="{WIDTH}" height="{HEIGHT}" fill="white"/>
  <rect x="0" y="0" height="{HEIGHT}" class="mask-rector"/>
</mask>
<g transform="translate(40, 78)" mask="url(#eat-mask)">
    {contribution_rects}
</g>
<g class="oguri-container" transform="translate(0, 10)">
  <g class="oguri-bounce-layer">
    <g transform="translate(80, 0) scale(-1, 1)">
      <image class="oguri-1" xlink:href="{data_uri1}" width="100" height="120" x="0" y="0"/>
      <image class="oguri-2" xlink:href="{data_uri2}" width="80"  height="100" x="0" y="10"/>
    </g>
    <text x="5" y="-5" class="text" fill="#58A6FF">OGURI :: {now.strftime("%b %d")}</text>
  </g>
</g>
</svg>"""

    with open(output_path, "w") as f:
        f.write(svg)

    print(f"Successfully generated {output_path}.")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    generate_svg(
        token=os.environ.get("GITHUB_TOKEN", ""),
        username=os.environ.get("GITHUB_REPOSITORY_OWNER", "mquangpham575"),
    )
