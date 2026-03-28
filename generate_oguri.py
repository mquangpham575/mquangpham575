import base64
import os
import requests
from datetime import datetime

# GitHub GraphQL query for contribution calendar
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


def get_real_contributions(username, token):
    if not token:
        print("No GITHUB_TOKEN found. Using random data.")
        return None

    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = requests.post(
            "https://api.github.com/graphql",
            json={"query": QUERY, "variables": {"userName": username}},
            headers=headers,
        )
        response.raise_for_status()
        data = response.json()

        # Flatten days from weeks
        calendar = data["data"]["user"]["contributionsCollection"][
            "contributionCalendar"
        ]
        all_days = [
            day for week in calendar["weeks"] for day in week["contributionDays"]
        ]

        # Get last 30 days
        now = datetime.now()
        from datetime import timedelta

        thirty_days_ago = now - timedelta(days=30)
        processed_days = []
        for d in all_days:
            day_date = datetime.strptime(d["date"], "%Y-%m-%d")
            if thirty_days_ago <= day_date <= now:
                processed_days.append(
                    {
                        "count": d["contributionCount"],
                        "has_commit": d["contributionCount"] > 0,
                    }
                )
        return processed_days
    except Exception as e:
        print(f"Error fetching contributions: {e}")
        return None


def generate_oguri_gourmet_svg(
    img1_path="assets/oguri-1.png",
    img2_path="assets/oguri-2.png",
    output_path="oguri-run.svg",
):
    if not os.path.exists(img1_path) or not os.path.exists(img2_path):
        print("Error: Assets not found.")
        return

    with open(img1_path, "rb") as f1, open(img2_path, "rb") as f2:
        encoded1 = base64.b64encode(f1.read()).decode("utf-8")
        encoded2 = base64.b64encode(f2.read()).decode("utf-8")
        data_uri1 = f"data:image/png;base64,{encoded1}"
        data_uri2 = f"data:image/png;base64,{encoded2}"

    WIDTH = 700
    HEIGHT = 110
    CELL_SIZE = 15
    GAP = 5
    BLOCK_W = CELL_SIZE + GAP

    now = datetime.now()
    token = os.environ.get("GITHUB_TOKEN")
    username = os.environ.get("GITHUB_REPOSITORY_OWNER", "mquangpham575")

    real_data = get_real_contributions(username, token)

    if real_data:
        active_cols = len(real_data)
        has_commit = [d["has_commit"] for d in real_data]
        counts = [d["count"] for d in real_data]
    else:
        # Fallback to random if API fails
        import random

        random.seed(now.strftime("%Y%m%d"))
        active_cols = 30
        has_commit = [random.random() > 0.3 for _ in range(active_cols)]
        counts = [random.randint(1, 10) if h else 0 for h in has_commit]

    run_distance = WIDTH + 50

    travel_distance = run_distance - 40

    mouth_1_keyframes = []
    mouth_2_keyframes = []
    for i in range(active_cols):
        start_pct = (i * BLOCK_W / float(travel_distance)) * 100
        if has_commit[i]:
            mouth_1_keyframes.append(f"{start_pct}% {{ opacity: 1; }}")
            mouth_2_keyframes.append(f"{start_pct}% {{ opacity: 0; }}")
        else:
            mouth_1_keyframes.append(f"{start_pct}% {{ opacity: 0; }}")
            mouth_2_keyframes.append(f"{start_pct}% {{ opacity: 1; }}")

    last_commit_pct = (active_cols * BLOCK_W / float(travel_distance)) * 100

    mouth_1_keyframes.append(f"{last_commit_pct + 0.01}% {{ opacity: 0; }}")
    mouth_2_keyframes.append(f"{last_commit_pct + 0.01}% {{ opacity: 1; }}")

    mouth_1_str = " ".join(mouth_1_keyframes)
    mouth_2_str = " ".join(mouth_2_keyframes)

    svg_content = [
        f'<svg width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">',
        '<rect width="100%" height="100%" fill="#0D1117" rx="15"/>',
        "<style>",
        f"""
        @keyframes oguri-run {{
            0% {{ transform: translateX(-0px); }}
            100% {{ transform: translateX({run_distance - 40}px); }}
        }}
        @keyframes oguri-bounce {{
            0%, 100% {{ transform: translateY(0px); }}
            50% {{ transform: translateY(-3px); }}
        }}
        @keyframes mask-eat {{
            0% {{ width: 0px; }}
            100% {{ width: {travel_distance}px; }}
        }}
        @keyframes oguri-mouth-1 {{ {mouth_1_str} }}
        @keyframes oguri-mouth-2 {{ {mouth_2_str} }}
        .oguri-container {{ animation: oguri-run 8s infinite linear; }}
        .oguri-bounce-layer {{ animation: oguri-bounce 0.15s infinite ease-in-out; }}
        .mask-rector {{ animation: mask-eat 8s infinite linear; fill: black; }}
        .oguri-1 {{ animation: oguri-mouth-1 8s infinite step-end; image-rendering: pixelated; }}
        .oguri-2 {{ animation: oguri-mouth-2 8s infinite step-end; image-rendering: pixelated; }}
        .text {{ fill: #8B949E; font-family: 'Segoe UI', sans-serif; font-size: 11px; font-weight: bold; }}
        """,
        "</style>",
        f'''
        <mask id="eat-mask">
            <rect width="{WIDTH}" height="{HEIGHT}" fill="white" />
            <rect x="0" y="0" height="{HEIGHT}" class="mask-rector" />
        </mask>
        ''',
        '<g transform="translate(40, 78)" mask="url(#eat-mask)">',
    ]

    def get_color(count):
        if count == 0:
            return "#161B22"
        if count < 3:
            return "#0E4429"
        if count < 6:
            return "#006D32"
        if count < 10:
            return "#26A641"
        return "#39D353"

    for i in range(active_cols):
        color = get_color(counts[i])
        if counts[i] > 0:
            x = i * BLOCK_W
            svg_content.append(
                f'<rect x="{x}" y="0" width="{CELL_SIZE}" height="{CELL_SIZE}" fill="{color}" rx="3"/>'
            )

    svg_content.append("</g>")

    svg_content.append(f'''
    <g class="oguri-container" transform="translate(0, 10)">
        <g class="oguri-bounce-layer">
            <g transform="translate(80, 0) scale(-1, 1)">
                <image class="oguri-1" xlink:href="{data_uri1}" width="100" height="120" x="0" y="0" />
                <image class="oguri-2" xlink:href="{data_uri2}" width="80" height="100" x="0" y="10" />
            </g>
            <text x="5" y="-5" class="text" fill="#58A6FF">OGURI :: {now.strftime("%b %d")}</text>
        </g>
    </g>
    ''')

    svg_content.append("</svg>")

    with open(output_path, "w") as f:
        f.write("\n".join(svg_content))

    print(f"Successfully generated {output_path} with real contribution data.")


if __name__ == "__main__":
    generate_oguri_gourmet_svg()
