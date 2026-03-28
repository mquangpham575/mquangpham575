import base64
import os
import random
from datetime import datetime

def generate_oguri_gourmet_svg(img1_path="assets/oguri-1.png", img2_path="assets/oguri-2.png", output_path="oguri-run.svg"):
    if not os.path.exists(img1_path) or not os.path.exists(img2_path):
        print("Error: Assets not found.")
        return

    with open(img1_path, "rb") as f1, open(img2_path, "rb") as f2:
        encoded1 = base64.b64encode(f1.read()).decode('utf-8')
        encoded2 = base64.b64encode(f2.read()).decode('utf-8')
        data_uri1 = f"data:image/png;base64,{encoded1}"
        data_uri2 = f"data:image/png;base64,{encoded2}"

    WIDTH = 800
    HEIGHT = 160
    CELL_SIZE = 15
    GAP = 5
    BLOCK_W = CELL_SIZE + GAP 
    
    now = datetime.now()
    day_of_month = now.day
    random.seed(now.strftime("%Y%m%d"))
    
    active_cols = day_of_month
    run_distance = active_cols * BLOCK_W
    
    has_commit = [random.random() > 0.3 for _ in range(active_cols)]

    mouth_1, mouth_2 = [], []
    for i in range(active_cols):
        start_pct = (i * BLOCK_W / float(run_distance)) * 100
        mid_pct = start_pct + (100.0 / active_cols) * 0.5
        
        if has_commit[i]:
            mouth_1.append(f"{start_pct}% {{ opacity: 1; }} {mid_pct}% {{ opacity: 0; }}")
            mouth_2.append(f"{start_pct}% {{ opacity: 0; }} {mid_pct}% {{ opacity: 1; }}")
        else:
            mouth_1.append(f"{start_pct}% {{ opacity: 1; }}")
            mouth_2.append(f"{start_pct}% {{ opacity: 0; }}")
    
    mouth_1.append("100% { opacity: 1; }")
    mouth_2.append("100% { opacity: 0; }")

    svg_content = [
        f'<svg width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">',
        f'<rect width="100%" height="100%" fill="#0D1117" rx="15"/>',
        '<style>',
        f'''
        @keyframes oguri-run {{
            0% {{ transform: translateX(0px); }}
            100% {{ transform: translateX({run_distance}px); }}
        }}
        @keyframes oguri-bounce {{
            0%, 100% {{ transform: translateY(0px); }}
            50% {{ transform: translateY(-5px); }}
        }}
        @keyframes oguri-eat {{ {" ".join(mouth_1)} }}
        @keyframes oguri-eat-alt {{ {" ".join(mouth_2)} }}
        @keyframes mask-eat {{
            0% {{ width: 0px; }}
            100% {{ width: {run_distance + 45}px; }}
        }}
        .oguri-container {{ animation: oguri-run 5s infinite linear; }}
        .oguri-bounce-layer {{ animation: oguri-bounce 0.18s infinite ease-in-out; }}
        .oguri-1 {{ animation: oguri-eat 5s infinite step-end; image-rendering: pixelated; }}
        .oguri-2 {{ animation: oguri-eat-alt 5s infinite step-end; image-rendering: pixelated; }}
        .mask-rector {{ animation: mask-eat 5s infinite linear; fill: black; }}
        .text {{ fill: #8B949E; font-family: "Segoe UI", sans-serif; font-size: 11px; font-weight: bold; }}
        ''',
        '</style>',
        f'''
        <mask id="eat-mask">
            <rect width="{WIDTH}" height="{HEIGHT}" fill="white" />
            <rect x="0" y="0" height="{HEIGHT}" class="mask-rector" />
        </mask>
        ''',
        # Grid Brought UP to Y=78 to hit mouth area
        '<g transform="translate(40, 78)" mask="url(#eat-mask)">'
    ]
    
    COLORS = ["#0E4429", "#006D32", "#26A641", "#39D353"]
    for i in range(active_cols):
        if has_commit[i]:
            x = i * BLOCK_W
            svg_content.append(f'<rect x="{x}" y="0" width="{CELL_SIZE}" height="{CELL_SIZE}" fill="{random.choice(COLORS)}" rx="3"/>')
    
    svg_content.append('</g>')
    
    # Character moved to Y=10 to match grid alignment
    svg_content.append(f'''
    <g class="oguri-container" transform="translate(0, 10)">
        <g class="oguri-bounce-layer">
            <g transform="translate(80, 0) scale(-1, 1)">
                <image class="oguri-1" xlink:href="{data_uri1}" width="80" height="100" x="0" y="0" />
                <image class="oguri-2" xlink:href="{data_uri2}" width="80" height="100" x="0" y="0" />
            </g>
            <text x="5" y="-5" class="text" fill="#58A6FF">OGURI :: {now.strftime("%b %d")}</text>
        </g>
    </g>
    ''')
    
    svg_content.append('</svg>')
    
    with open(output_path, "w") as f:
        f.write("\n".join(svg_content))
    
    print(f"Successfully generated {output_path} with final coordinate fixes.")

if __name__ == "__main__":
    generate_oguri_gourmet_svg()
