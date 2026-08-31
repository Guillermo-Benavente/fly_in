#!/usr/bin/env python3
import sys
import json
import os
from collections import Counter
from parser import Parser
from route_planner import RoutePlanner
from hub import Hub
from network_zone import NetworkZone
from drone import Drone

COLOR_MAP: dict[str, str] = {
    'black': '#333', 'white': '#eee', 'red': '#e74c3c',
    'blue': '#3498db', 'green': '#2ecc71', 'yellow': '#f1c40f',
    'magenta': '#e91e63', 'cyan': '#00bcd4', 'orange': '#ff9800',
    'purple': '#9b59b6', 'brown': '#795548', 'maroon': '#800000',
    'gold': '#ffd700', 'lime': '#cddc39', 'crimson': '#dc143c',
    'violet': '#7c4dff', 'darkred': '#b71c1c',
    'rainbow': 'linear-gradient(135deg, #ff0000, #ff7f00, #ffff00, #00ff00, #0000ff, #4b0082, #8b00ff)',
}


DRONE_COLORS: list[str] = [
    '#ff6b6b', '#4ecdc4', '#45b7d1', '#f9ca24', '#6c5ce7',
    '#fd79a8', '#00cec9', '#e17055', '#0984e3', '#d63031',
    '#a29bfe', '#55efc4', '#fdcb6e', '#e84393', '#00b894',
    '#fab1a0', '#74b9ff', '#ff7675', '#b2bec3', '#636e72',
    '#ffeaa7', '#dfe6e9', '#81ecec', '#ff9ff3', '#feca57',
]


def _parse_transit(value: str) -> tuple[str, str] | None:
    if '-' in value:
        parts = value.split('-')
        if len(parts) == 2:
            return parts[0], parts[1]
    return None

def _isConnection(value: str) -> bool:
    if '-' in value:
        return True
    else:
        return False

def _connection_coords(hub_a: str, hub_b: str, hub_positions: dict[str, tuple[int, int]]) -> tuple[int, int]:
    x1, y1 = hub_positions[hub_a]
    x2, y2 = hub_positions[hub_b]
    return (x1 + x2) // 2, (y1 + y2) // 2


def generate_keyframes(
    drone_id: int, 
    route: dict[int, str], 
    start_hub_name: str, 
    hub_positions: dict[str, tuple[int, int]], 
    total_turns: int
) -> str:
    positions: list[str] = []
    current = start_hub_name
    transit_mid: dict[int, tuple[int, int]] = {}
    for turn in range(total_turns):
        if turn in route:
            val = route[turn]
            parsed = _parse_transit(val)
            if parsed:
                transit_mid[turn] = _connection_coords(parsed[0], parsed[1], hub_positions)
            else:
                current = val
        positions.append(current)
    lines: list[str] = [f'@keyframes drone{drone_id} {{']
    sx, sy = hub_positions[start_hub_name]
    lines.append(f'  0% {{ left: {sx}px; top: {sy}px; }}')
    for i, hub_name in enumerate(positions):
        turn_num = i
        move_pct = ((i + 0.5) / total_turns) * 100
        hold_pct = ((i + 1) / total_turns) * 100
        if turn_num in transit_mid:
            x, y = transit_mid[turn_num]
        else:
            x, y = hub_positions[hub_name]
        lines.append(f'  {move_pct:.2f}% {{ left: {x}px; top: {y}px; }}')
        lines.append(f'  {hold_pct:.2f}% {{ left: {x}px; top: {y}px; }}')
    lines.append('}')
    return '\n'.join(lines)


def build_drone_positions(
    planner: RoutePlanner, 
    hub_positions: dict[str, tuple[int, int]], 
    total_turns: int
) -> dict[int, list[dict[str, int]]]:
    start_hub_name: str = planner.network_zone.start.name
    start_coord_x, start_coord_y = hub_positions[start_hub_name]
    result: dict[int, list[dict[str, int]]] = {}

    for drone in planner.drone_list:
        drone_positions: list[dict[str, int]] = [{'x': start_coord_x, 'y': start_coord_y}]
        current_hub_name: str = start_hub_name

        for turn in range(total_turns):
            turn_position_name: str = drone.route.get(turn, '')

            if turn_position_name and _isConnection(turn_position_name):
                from_hub, to_hub = turn_position_name.split('-')
                x, y = _connection_coords(from_hub, to_hub, hub_positions)
            else:
                if turn_position_name:
                    current_hub_name = turn_position_name
                x, y = hub_positions[current_hub_name]

            drone_positions.append({'x': x, 'y': y})

        result[drone.id] = drone_positions

    return result

def build_hub_occupancy(planner: RoutePlanner, total_turns: int) -> dict[int, dict[str, int]]:
    def get_hub(drone: Drone, turn: int) -> str | None:
        if turn == 0:
            return planner.network_zone.start.name
        action: str | None = drone.route.get(turn - 1)
        return action if action and not _isConnection(action) else None

    return {
        turn: dict(Counter(
            hub for drone in planner.drone_list 
            if (hub := get_hub(drone, turn)) is not None
        ))
        for turn in range(total_turns + 1)
    }
  
def calculate_hub_screen_positions(
    all_hubs: list[Hub],
    min_x: int,
    min_y: int,
    node_distance_px: int,
    padding_px: int
) -> dict[str, tuple[int, int]]:
    screen_positions: dict[str, tuple[int, int]] = {}
    for hub in all_hubs:
        px: int = (hub.coord_x - min_x) * node_distance_px + padding_px
        py: int = (hub.coord_y - min_y) * node_distance_px + padding_px
        screen_positions[hub.name] = (px, py)
    return screen_positions

def generate_html(planner: RoutePlanner) -> str:
    network_zone: NetworkZone = planner.network_zone
    all_hubs: list[Hub] = network_zone.all_hubs()

    min_coord_x: int = min(h.coord_x for h in all_hubs)
    max_coord_x: int = max(h.coord_x for h in all_hubs)
    min_coord_y: int = min(h.coord_y for h in all_hubs)
    max_coord_y: int = max(h.coord_y for h in all_hubs)

    node_distance_px: int = 100
    padding_px: int = 40
    map_w: int = (max_coord_x - min_coord_x) * node_distance_px + padding_px * 2
    map_h: int = (max_coord_y - min_coord_y) * node_distance_px + padding_px * 2

    hub_positions: dict[str, tuple[int, int]] = calculate_hub_screen_positions(
        all_hubs, min_coord_x, min_coord_y, node_distance_px, padding_px
    )

    total_turns: int = max((max(d.route.keys()) + 1) for d in planner.drone_list) if planner.drone_list else 1
    turn_duration: int = 1
    anim_duration: int = total_turns * turn_duration

    drone_positions: dict[int, list[dict[str, int]]] = build_drone_positions(planner, hub_positions, total_turns)
    drone_positions_json: str = json.dumps(drone_positions)

    hub_occupancy: dict[int, dict[str, int]] = build_hub_occupancy(planner, total_turns)
    hub_occupancy_json: str = json.dumps(hub_occupancy)
    # TODO
    keyframes_css: list[str] = []
    for drone in planner.drone_list:
        keyframes_css.append(generate_keyframes(drone.id, drone.route, network_zone.start.name, hub_positions, total_turns))

    hub_max: dict[str, int] = {}
    for hub in all_hubs:
        hub_max[hub.name] = int(hub.metadata.get('max_drones', 1))

    hubs_html: list[str] = []
    for hub in all_hubs:
        x, y = hub_positions[hub.name]
        color_raw = str(hub.metadata.get('color', 'white')).lower()
        color = COLOR_MAP.get(color_raw, '#eee')
        is_rainbow_cls = ' rainbow-hub' if color_raw == 'rainbow' else ''
        zone = hub.metadata.get('zone', 'normal')
        if zone == 'restricted':
            border = '3px dashed #fff'
        elif zone == 'priority':
            border = '3px solid #fff'
        else:
            border = '3px solid #555'
        if hub == network_zone.start:
            border = '3px solid #2ecc71'
        elif hub == network_zone.end:
            border = '3px solid #e74c3c'
        max_d = hub_max[hub.name]
        hubs_html.append(
            f'<div class="hub{is_rainbow_cls}" style="left:{x}px; top:{y}px; background:{color}; border:{border};" data-max="{max_d}">'
            f'<span>{hub.name}</span>'
            f'<span class="hub-occ" id="occ-{hub.name}">0/{max_d}</span></div>'
        )

    conns_html: list[str] = []
    for conn in network_zone.connections:
        x1, y1 = hub_positions[conn.init_hub.name]
        x2, y2 = hub_positions[conn.final_hub.name]
        cap = conn.metadata.get('max_link_capacity', '')
        cap_label = f' [{cap}]' if cap else ''
        conns_html.append(
            f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
            f'stroke="#555" stroke-width="2" stroke-dasharray="6,4"/>'
        )
        mid_x = (x1 + x2) // 2
        mid_y = (y1 + y2) // 2
        if cap_label:
            conns_html.append(
                f'<text x="{mid_x}" y="{mid_y - 6}" fill="#888" font-size="10" text-anchor="middle">{cap_label.strip()}</text>'
            )

    drones_html: list[str] = []
    drone_anim_css: list[str] = []
    for drone in planner.drone_list:
        dc = DRONE_COLORS[drone.id % len(DRONE_COLORS)]
        sx, sy = hub_positions[network_zone.start.name]
        drones_html.append(
            f'<div class="drone" id="drone{drone.id}" '
            f'style="left:{sx}px; top:{sy}px; background:{dc};">'
            f'D{drone.id}</div>'
        )
        drone_anim_css.append(
            f'#drone{drone.id} {{ animation: drone{drone.id} {anim_duration}s linear infinite; }}'
        )

    keyframes_str = '\n'.join(keyframes_css)
    drone_anim_str = '\n'.join(drone_anim_css)
    hubs_str = '\n    '.join(hubs_html)
    conns_str = '\n    '.join(conns_html)
    drones_str = '\n    '.join(drones_html)

    route_lines: list[str] = []
    for drone in planner.drone_list:
        route_str = ' -> '.join(drone.route[t] for t in sorted(drone.route.keys()))
        route_lines.append(f'D{drone.id}: {route_str}')
    routes_text = '\n'.join(route_lines)

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Fly-In Visualization</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    background: #1a1a2e;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: 100vh;
    font-family: 'Segoe UI', monospace;
    color: #eee;
  }}
  h1 {{
    margin: 20px 0 10px;
    font-size: 24px;
    color: #eee;
  }}
  .info {{
    margin-bottom: 15px;
    color: #aaa;
    font-size: 14px;
  }}
  .controls {{
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 15px;
    background: #16213e;
    border: 1px solid #0f3460;
    border-radius: 8px;
    padding: 10px 20px;
  }}
  .controls button {{
    background: #0f3460;
    color: #eee;
    border: 1px solid #3498db;
    border-radius: 6px;
    padding: 6px 16px;
    font-size: 14px;
    cursor: pointer;
    font-family: inherit;
  }}
  .controls button:hover {{
    background: #3498db;
  }}
  .controls button.active {{
    background: #2ecc71;
    border-color: #2ecc71;
    color: #000;
  }}
  .controls .turn-display {{
    font-size: 14px;
    color: #aaa;
    min-width: 120px;
    text-align: center;
  }}
  .controls .arrow {{
    font-size: 18px;
    padding: 4px 12px;
  }}
  .map {{
    position: relative;
    width: {map_w}px;
    height: {map_h}px;
    background: #16213e;
    border: 2px solid #0f3460;
    border-radius: 12px;
    overflow: hidden;
  }}
  .connections {{
    position: absolute;
    top: 0; left: 0;
    width: 100%; height: 100%;
  }}
  .hub {{
    position: absolute;
    width: 40px; height: 40px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 2;
    box-shadow: 0 0 8px rgba(0,0,0,0.5);
    transform: translate(-50%, -50%);
  }}
  .hub span {{
    font-size: 8px;
    color: #fff;
    text-shadow: 0 0 3px #000;
    text-align: center;
    line-height: 1.1;
    max-width: 38px;
    overflow: hidden;
    word-break: break-all;
  }}
  .hub-occ {{
    position: absolute;
    top: 100%;
    left: 50%;
    transform: translateX(-50%);
    font-size: 9px;
    color: #fff;
    background: rgba(0,0,0,0.7);
    padding: 1px 5px;
    border-radius: 4px;
    white-space: nowrap;
    margin-top: 2px;
  }}
  .drone {{
    position: absolute;
    width: 22px; height: 22px;
    border-radius: 50%;
    border: 2px solid #fff;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 8px;
    font-weight: bold;
    color: #000;
    z-index: 3;
    box-shadow: 0 0 10px rgba(255,255,255,0.4);
    transform: translate(-50%, -50%);
  }}
  {keyframes_str}
  {drone_anim_str}
  .routes {{
    margin-top: 15px;
    background: #16213e;
    border: 1px solid #0f3460;
    border-radius: 8px;
    padding: 15px 20px;
    font-family: monospace;
    font-size: 12px;
    white-space: pre;
    max-width: {map_w}px;
    overflow-x: auto;
    color: #aaa;
  }}
  .rainbow-hub {{
    background-size: 200% 200% !important;
    animation: rainbowGlow 3s ease infinite;
  }}
  @keyframes rainbowGlow {{
    0% {{ background-position: 0% 50%; }}
    50% {{ background-position: 100% 50%; }}
    100% {{ background-position: 0% 50%; }}
  }}
</style>
</head>
<body>
  <h1>Fly-In Visualization</h1>
  <div class="info">Drones: {len(planner.drone_list)} | Turns: {total_turns}</div>
  <div class="controls">
    <button id="modeBtn" onclick="toggleMode()">Manual</button>
    <button class="arrow" id="prevBtn" onclick="prevTurn()" disabled>&#9664;</button>
    <span class="turn-display" id="turnDisplay">Auto</span>
    <button class="arrow" id="nextBtn" onclick="nextTurn()" disabled>&#9654;</button>
  </div>
  <div class="map">
    <svg class="connections">
      {conns_str}
    </svg>
    {hubs_str}
    {drones_str}
  </div>
  <div class="routes">{routes_text}</div>
<script>
const dronePositions = {drone_positions_json};
const totalTurns = {total_turns};
const moveTime = 500;
let autoMode = true;
let currentTurn = 0;
let animStart = performance.now();
let moving = false;
let occInterval = null;

const animCSS = {json.dumps({f'drone{d.id}': f'drone{d.id} {anim_duration}s linear infinite' for d in planner.drone_list})};
const hubOccupancy = {hub_occupancy_json};

function updateHubOccupancy(turn) {{
  const occ = hubOccupancy[turn] || {{}};
  document.querySelectorAll('.hub-occ').forEach(el => {{
    const max = el.parentElement.dataset.max;
    const count = occ[el.id.replace('occ-', '')] || 0;
    el.textContent = count + '/' + max;
  }});
}}

function applyTurn(turn, animate) {{
  if (animate && !autoMode) {{
    moving = true;
    document.getElementById('prevBtn').disabled = true;
    document.getElementById('nextBtn').disabled = true;
    setTimeout(() => {{ moving = false; updateButtons(); }}, moveTime);
  }}
  for (const [id, positions] of Object.entries(dronePositions)) {{
    const el = document.getElementById('drone' + id);
    if (!el) continue;
    const idx = Math.min(turn, positions.length - 1);
    const pos = positions[idx];
    el.style.left = pos.x + 'px';
    el.style.top = pos.y + 'px';
  }}
  updateHubOccupancy(turn);
}}

function setTurn(turn, animate) {{
  currentTurn = Math.max(0, Math.min(turn, totalTurns));
  applyTurn(currentTurn, animate);
  document.getElementById('turnDisplay').textContent = 'Turn ' + currentTurn + '/' + totalTurns;
  updateButtons();
}}

function updateButtons() {{
  if (autoMode) return;
  document.getElementById('prevBtn').disabled = moving || currentTurn <= 0;
  document.getElementById('nextBtn').disabled = moving || currentTurn >= totalTurns;
}}

function toggleMode() {{
  autoMode = !autoMode;
  const btn = document.getElementById('modeBtn');
  const drones = document.querySelectorAll('.drone');
  if (autoMode) {{
    btn.textContent = 'Manual';
    btn.classList.remove('active');
    document.getElementById('turnDisplay').textContent = 'Auto';
    drones.forEach(d => {{
      d.style.transition = 'none';
      d.style.removeProperty('left');
      d.style.removeProperty('top');
      d.style.animation = 'none';
      d.offsetHeight;
      d.style.animation = animCSS[d.id];
      d.style.animationDelay = -(currentTurn * 1000) + 'ms';
    }});
    animStart = performance.now() - (currentTurn * 1000);
    document.getElementById('prevBtn').disabled = true;
    document.getElementById('nextBtn').disabled = true;
    if (occInterval) clearInterval(occInterval);
    occInterval = setInterval(() => {{
      const elapsed = performance.now() - animStart;
      const t = Math.floor((elapsed + 500) / 1000) % totalTurns;
      updateHubOccupancy(t);
    }}, 200);
  }} else {{
    btn.textContent = 'Auto';
    btn.classList.add('active');
    if (occInterval) {{
      clearInterval(occInterval);
      occInterval = null;
    }}
    const elapsed = performance.now() - animStart;
    currentTurn = Math.floor((elapsed + 500) / 1000) % totalTurns;
    drones.forEach(d => {{
      d.style.animation = 'none';
      d.style.transition = 'left ' + moveTime + 'ms ease, top ' + moveTime + 'ms ease';
    }});
    setTurn(currentTurn, false);
  }}
}}

function prevTurn() {{
  if (!autoMode && !moving) setTurn(currentTurn - 1, true);
}}

function nextTurn() {{
  if (!autoMode && !moving) setTurn(currentTurn + 1, true);
}}

document.addEventListener('keydown', (e) => {{
  if (autoMode) return;
  if (e.key === 'ArrowLeft') {{ e.preventDefault(); prevTurn(); }}
  if (e.key === 'ArrowRight') {{ e.preventDefault(); nextTurn(); }}
}});

if (autoMode) {{
  occInterval = setInterval(() => {{
    const elapsed = performance.now() - animStart;
    const t = Math.floor((elapsed + 500) / 1000) % totalTurns;
    updateHubOccupancy(t);
  }}, 200);
}}
</script>
</body>
</html>'''


def main():
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print('Usage: python visualizer.py <map_file> [output_file]')
        print('Example: python visualizer.py maps/easy/01_linear_path.txt output.html')
        sys.exit(1)

    map_file = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) == 3 else 'output.html'
    network_zone = Parser(map_file).parser()
    planner = RoutePlanner(network_zone)

    html = generate_html(planner)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        f.write(html)
    print(f'Generated {output_path}')


if __name__ == '__main__':
    main()
