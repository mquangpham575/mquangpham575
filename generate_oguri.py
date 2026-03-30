import requests
import base64
import os
from datetime import datetime, timedelta

# Dimensions & Layout
WIDTH, HEIGHT = 800, 100
SQUARE_SIZE = 15
GAP = 3

# Sprite Configuration
SPRITE_NORMAL_SIZE = 80
SPRITE_EAT_SIZE = 100
MOUTH_RATIO = 0.8  # Mouth position as ratio of sprite width
MOUTH_OFFSET = -20  # Fine-tuning adjustment for mouth sync
ANIMATION_DURATION = "10s"

# GitHub Dark Mode Palette
BG_COLOR = "#0d1117"  # Page background
SQUARE_BG = "#161b22" # Level 0 square background
COLORS = [SQUARE_BG, "#0e4429", "#006d32", "#26a641", "#39d353"]

def get_base64_image(path):
    # Convert PNG asset to base64 for embedding
    # Adjustment: Error handling for missing assets
    if not os.path.exists(path):
        return ""
    with open(path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def get_contributions():
    # Fetch user's contribution data from GitHub API
    # Adjustment: Added support for GITHUB_TOKEN environment variable for workflows
    token = os.environ.get("GITHUB_TOKEN")
    if not token and os.path.exists("github_PAT.md"):
        with open("github_PAT.md", "r") as f:
            token = f.read().strip()
    
    if not token:
        print("Warning: No GITHUB_TOKEN found. Using placeholder data.")
        return [0, 1, 2, 3, 4, 1, 2, 3, 4, 0] * 3

    headers = {"Authorization": f"Bearer {token}"}
    to_date = datetime.now()
    from_date = to_date - timedelta(days=29)
    
    query = """
    query($from: DateTime!, $to: DateTime!) {
      user(login: "mquangpham575") {
        contributionsCollection(from: $from, to: $to) {
          contributionCalendar {
            weeks {
              contributionDays {
                contributionLevel
              }
            }
          }
        }
      }
    }
    """
    variables = {"from": from_date.isoformat(), "to": to_date.isoformat()}
    try:
        resp = requests.post("https://api.github.com/graphql", json={"query": query, "variables": variables}, headers=headers)
        data = resp.json()
        
        if 'errors' in data:
            print(f"GitHub API Error: {data['errors']}")
            return [0] * 30
            
        days = []
        weeks = data['data']['user']['contributionsCollection']['contributionCalendar']['weeks']
        level_map = {"NONE": 0, "FIRST_QUARTILE": 1, "SECOND_QUARTILE": 2, "THIRD_QUARTILE": 3, "FOURTH_QUARTILE": 4}
        
        for week in weeks:
            for day in week['contributionDays']:
                days.append(level_map[day['contributionLevel']])
        return days[-30:]
    except Exception as e:
        print(f"Error fetching contributions: {e}")
        return [0] * 30

def create_oguri_svg():
    # Main logic to generate the animated SVG
    days = get_contributions()
    normal_b64 = get_base64_image("assets/oguri-normal.png")
    eat_b64 = get_base64_image("assets/oguri-eat.png")
    
    # Calculate centering
    total_content_width = (len(days) * SQUARE_SIZE) + ((len(days) - 1) * GAP)
    x_offset = (WIDTH - total_content_width) // 2
    # Position squares lower than center, plus 10px top margin
    squares_y = (HEIGHT - SQUARE_SIZE) // 2 + 20 + 10
    
    # Calculate Sprite Vertical Centering, pushed down 10px for top margin
    y_normal = (HEIGHT - SPRITE_NORMAL_SIZE) // 2 + 10
    y_eat = (HEIGHT - SPRITE_EAT_SIZE) // 2 + 10
    
    # Reveal Animation Calculation (tracking mouth_x)
    m_start = -SPRITE_NORMAL_SIZE + (SPRITE_NORMAL_SIZE * MOUTH_RATIO + MOUTH_OFFSET)
    m_end = WIDTH + (SPRITE_NORMAL_SIZE * MOUTH_RATIO + MOUTH_OFFSET)
    rev_start = m_start - WIDTH
    rev_end = m_end - WIDTH
    
    svg_header = f'''<svg width="{WIDTH}" height="{HEIGHT}" xmlns="http://www.w3.org/2000/svg">
<style>
  @keyframes moveOguri {{
    0% {{ transform: translateX(-{SPRITE_NORMAL_SIZE}px); }}
    100% {{ transform: translateX({WIDTH}px); }}
  }}
  @keyframes reveal {{
    0% {{ transform: translateX({rev_start}px); }}
    100% {{ transform: translateX({rev_end}px); }}
  }}
  .oguri-group {{
    animation: moveOguri {ANIMATION_DURATION} linear infinite;
  }}
  .black-layer {{
    animation: reveal {ANIMATION_DURATION} linear infinite;
  }}
  @keyframes switchSprite {{
    {_generate_keyframes(days, x_offset)}
  }}
  @keyframes switchSpriteNormal {{
    {_generate_keyframes(days, x_offset, inverse=True)}
  }}
  @keyframes oguri-bounce {{
    0%, 100% {{ transform: translateY(0px); }}
    50% {{ transform: translateY(-3px); }}
  }}
  .oguri-eat {{ animation: switchSprite {ANIMATION_DURATION} linear infinite; }}
  .oguri-normal {{ animation: switchSpriteNormal {ANIMATION_DURATION} linear infinite; }}
  .oguri-bounce {{ animation: oguri-bounce 0.15s infinite ease-in-out; }}
</style>
'''
    
    svg_body = f'  <rect width="{WIDTH}" height="{HEIGHT}" fill="{BG_COLOR}" />\n'
    # Render contribution squares
    for i, level in enumerate(days):
        x = x_offset + i * (SQUARE_SIZE + GAP)
        svg_body += f'  <rect x="{x}" y="{squares_y}" width="{SQUARE_SIZE}" height="{SQUARE_SIZE}" rx="2" ry="2" fill="{COLORS[level]}" />\n'
    
    # Reveal layer (matches background to "erase" squares as mouth passes)
    svg_body += f'  <rect class="black-layer" x="0" y="0" width="{WIDTH}" height="{HEIGHT}" fill="{BG_COLOR}" />\n'
    
    # Render Sprite Group
    svg_body += f'''
  <g class="oguri-group">
    <g class="oguri-bounce">
      <image class="oguri-normal" href="data:image/png;base64,{normal_b64}" x="0" y="{y_normal}" width="{SPRITE_NORMAL_SIZE}" height="{SPRITE_NORMAL_SIZE}" />
      <image class="oguri-eat" href="data:image/png;base64,{eat_b64}" x="0" y="{y_eat}" width="{SPRITE_EAT_SIZE}" height="{SPRITE_EAT_SIZE}" opacity="0" />
    </g>
    <!-- Debug Mouth Point: <circle cx="{SPRITE_NORMAL_SIZE * MOUTH_RATIO + MOUTH_OFFSET}" cy="{y_normal + SPRITE_NORMAL_SIZE // 2}" r="3" fill="red" /> -->
  </g>
'''
    
    # Adjustment: Using oguri-run.svg to match existing workflow and README
    with open("oguri-run.svg", "w") as f:
        f.write(svg_header + svg_body + "</svg>")

def _generate_keyframes(days, start_x, inverse=False):
    # Generates many keyframes for smooth opacity switching
    keyframes = []
    num_steps = 400
    for step in range(num_steps + 1):
        p = step / (num_steps / 100)
        curr_x = -SPRITE_NORMAL_SIZE + (WIDTH + SPRITE_NORMAL_SIZE) * (p / 100)
        mouth_x = curr_x + SPRITE_NORMAL_SIZE * MOUTH_RATIO + MOUTH_OFFSET
        
        is_eating = False
        for i, level in enumerate(days):
            sq_x = start_x + i * (SQUARE_SIZE + GAP)
            if sq_x <= mouth_x + 5 and mouth_x - 5 <= sq_x + SQUARE_SIZE and COLORS[level] != SQUARE_BG:
                is_eating = True
                break
        
        opacity = (0 if is_eating else 1) if inverse else (1 if is_eating else 0)
        keyframes.append(f"{p:.2f}% {{ opacity: {opacity}; }}")
    return "\n    ".join(keyframes)

if __name__ == "__main__":
    create_oguri_svg()
