#!/usr/bin/env python3
"""Module for rendering network route animations into interactive HTML pages.

Parses network configuration files, computes drone flight routes, and builds
a standalone HTML/CSS/JS web application to visualize drone navigation, hub
occupancy, and custom node styling.
"""
import sys
import json
import os
from collections import Counter
from parser import Parser
from route_planner import RoutePlanner
from hub import Hub, TypeMetadata as TMHub, TypeZone
from connection import TypeMetadata as TMConnection
from network_zone import NetworkZone
from drone import Drone

COLOR_MAP: dict[str, str] = {
    'black': '#333', 'white': '#eee', 'red': '#e74c3c',
    'blue': '#3498db', 'green': '#2ecc71', 'yellow': '#f1c40f',
    'magenta': '#e91e63', 'cyan': '#00bcd4', 'orange': '#ff9800',
    'purple': '#9b59b6', 'brown': '#795548', 'maroon': '#800000',
    'gold': '#ffd700', 'lime': '#cddc39', 'crimson': '#dc143c',
    'violet': '#7c4dff', 'darkred': '#b71c1c',
    'rainbow': (
        '''linear-gradient(
            135deg, #ff0000, #ff7f00,
            #ffff00, #00ff00, #0000ff,
            #4b0082, #8b00ff
        )'''
    ),
}


DRONE_COLORS: list[str] = [
    '#ff6b6b', '#4ecdc4', '#45b7d1', '#f9ca24', '#6c5ce7',
    '#fd79a8', '#00cec9', '#e17055', '#0984e3', '#d63031',
    '#a29bfe', '#55efc4', '#fdcb6e', '#e84393', '#00b894',
    '#fab1a0', '#74b9ff', '#ff7675', '#b2bec3', '#636e72',
    '#ffeaa7', '#dfe6e9', '#81ecec', '#ff9ff3', '#feca57',
]


def _isConnection(name: str) -> bool:
    """Checks whether a given location string represents a connection path.

    Args:
      name (str): The node or connection identifier.

    Returns:
      bool: True if the name contains a hyphen indicating a connection,
        False otherwise.
    """
    if '-' in name:
        return True
    else:
        return False


def _get_connection_hubs(name: str) -> tuple[str, str] | None:
    """Extracts endpoint hub names from a connection string identifier.

    Args:
      name (str): Formatted connection string (e.g., 'hubA-hubB').

    Returns:
      tuple[str, str] | None:
        A tuple of (init_hub, final_hub) if valid, otherwise None.
    """
    if _isConnection(name):
        parts = name.split('-')
        if len(parts) == 2:
            return parts[0], parts[1]
    return None


def _connection_coords(
        hub_a: str,
        hub_b: str,
        hub_positions: dict[str, tuple[int, int]]
) -> tuple[int, int]:
    """Calculates midpoint coordinates between two connected hubs.

    Args:
      hub_a (str): Name of the first hub.
      hub_b (str): Name of the second hub.
      hub_positions (dict[str, tuple[int, int]]):
        Screen coordinates mapping for hubs.

    Returns:
      tuple[int, int]: Midpoint pixel coordinates (X, Y).
    """
    x1, y1 = hub_positions[hub_a]
    x2, y2 = hub_positions[hub_b]
    return (x1 + x2) // 2, (y1 + y2) // 2


def create_svg_connections(
    network_zone: NetworkZone,
    hub_positions: dict[str, tuple[int, int]]
) -> list[str]:
    """Generates SVG line elements representing
    connection pathways between hubs.

    Args:
        network_zone (NetworkZone):
            Network graph model containing connection definitions.
        hub_positions (dict[str, tuple[int, int]]):
            Pixel positions of all hubs.

    Returns:
        list[str]: SVG markup strings for connection lines and capacity labels.
    """
    connections_svg: list[str] = []
    for connection in network_zone.connections:
        init_conn_x, init_conn_y = hub_positions[connection.init_hub.name]
        final_conn_x, final_conn_y = hub_positions[connection.final_hub.name]
        capacity_link: int = int(
            connection.metadata.get(TMConnection.MAX_LINK_CAPACITY, 1)
        )
        capacity_label: str = (
            f' [{capacity_link}]' if capacity_link > 1 else ''
        )
        connections_svg.append(
            f'''<line x1="{init_conn_x}" y1="{init_conn_y}"
                x2="{final_conn_x}" y2="{final_conn_y}"
                stroke="#555" stroke-width="2" stroke-dasharray="6,4"/>'''
        )
        mid_x = (init_conn_x + final_conn_x) // 2
        mid_y = (init_conn_y + final_conn_y) // 2
        if capacity_label:
            connections_svg.append(
                f'''<text x="{mid_x}" y="{mid_y - 6}"
                fill="#888" font-size="10" text-anchor="middle">
                  {capacity_label.strip()}
                </text>'''
            )
    return connections_svg


def create_html_hubs(
    all_hubs: list[Hub],
    network_zone: NetworkZone,
    hub_positions: dict[str, tuple[int, int]]
) -> list[str]:
    """Generates styled HTML div elements representing hubs
    on the visualization map.

    Args:
        all_hubs (list[Hub]): Collection of all hubs to render.
        network_zone (NetworkZone):
            Network topology containing start and end hubs.
        hub_positions (dict[str, tuple[int, int]]):
            Pixel placement map for each hub.

    Returns:
        list[str]: Formatted HTML div strings for hub elements.
    """
    hubs_html: list[str] = []
    for hub in all_hubs:
        x, y = hub_positions[hub.name]
        color_raw: str = str(hub.metadata.get(TMHub.COLOR, 'white')).lower()
        color: str | None = COLOR_MAP.get(color_raw)
        is_rainbow_cls: str = ' rainbow-hub' if color_raw == 'rainbow' else ''
        zone_hub: str = hub.metadata.get(TMHub.ZONE, TypeZone.NORMAL)
        if hub == network_zone.start:
            border: str = '3px solid #2ecc71'
        elif hub == network_zone.end:
            border = '3px solid #e74c3c'
        elif zone_hub == TypeZone.RESTRICTED:
            border = '3px dashed #fff'
        elif zone_hub == TypeZone.PRIORITY:
            border = '3px solid #fff'
        else:
            border = '3px solid #555'
        max_drones: int = int(hub.metadata.get(TMHub.MAX_DRONES, 1))
        hubs_html.append(
            f'''<div class="hub{is_rainbow_cls}"
                    style="left:{x}px; top:{y}px; background:{color};
                    border:{border};" data-max="{max_drones}">
                <span>{hub.name}</span>
                <span class="hub-occupancy" id="occupancy-{hub.name}">
                    0/{max_drones}
                </span>
            </div>'''
        )
    return hubs_html


def generate_keyframes(
    drone: Drone,
    network_zone: NetworkZone,
    hub_positions: dict[str, tuple[int, int]],
    total_turns: int
) -> str:
    """Generates CSS keyframe animations representing
    step-by-step drone movement.

    Args:
        drone (Drone):
            Drone instance whose path will be translated into keyframes.
        network_zone (NetworkZone):
            Topology model containing origin and destination info.
        hub_positions (dict[str, tuple[int, int]]):
            Pixel coordinates mapping for hubs.
        total_turns (int):
            Total simulation turns used to normalize animation timing.

    Returns:
        str: CSS @keyframes string defining movement timeline for the drone.
    """
    positions: list[str] = []
    current_hub_name: str = network_zone.start.name
    hub_restricted_positions: dict[int, tuple[int, int]] = {}
    for turn in range(total_turns):
        if turn in drone.route:
            position_name = drone.route[turn]
            connection_hubs = _get_connection_hubs(position_name)
            if connection_hubs:
                init_hub, final_hub = connection_hubs
                hub_restricted_positions[turn] = _connection_coords(
                    init_hub, final_hub, hub_positions
                )
            else:
                current_hub_name = position_name
        positions.append(current_hub_name)
    drone_animations: list[str] = [f'@keyframes drone{drone.id} {{']
    start_coord_x, start_coord_y = hub_positions[network_zone.start.name]
    drone_animations.append(
        f'  0% {{ left: {start_coord_x}px; top: {start_coord_y}px; }}'
    )
    for turn, hub_name in enumerate(positions):
        move_percent = ((turn + 0.5) / total_turns) * 100
        hold_percent = ((turn + 1) / total_turns) * 100
        if turn in hub_restricted_positions:
            x, y = hub_restricted_positions[turn]
        else:
            x, y = hub_positions[hub_name]
        drone_animations.append(
            f'  {move_percent:.2f}% {{ left: {x}px; top: {y}px; }}'
        )
        drone_animations.append(
            f'  {hold_percent:.2f}% {{ left: {x}px; top: {y}px; }}'
        )
        if hub_name == network_zone.end.name:
            drone_animations.append(f'  100% {{ left: {x}px; top: {y}px; }}')
            break
    drone_animations.append('}')
    return '\n'.join(drone_animations)


def build_drone_positions(
    planner: RoutePlanner,
    hub_positions: dict[str, tuple[int, int]],
    total_turns: int
) -> dict[int, list[dict[str, int]]]:
    """Builds a turn-by-turn map of pixel coordinates
    for all drones in manual step mode.

    Args:
        planner (RoutePlanner): Route planner containing executed drone paths.
        hub_positions (dict[str, tuple[int, int]]):
            Pixel placement map for hubs.
        total_turns (int): Total simulation turns.

    Returns:
        dict[int, list[dict[str, int]]]:
            Dict mapping drone IDs to lists of coordinate dicts
            ({'x': x, 'y': y}).
    """
    start_hub_name: str = planner.network_zone.start.name
    start_coord_x, start_coord_y = hub_positions[start_hub_name]
    result: dict[int, list[dict[str, int]]] = {}

    for drone in planner.drone_list:
        drone_positions: list[dict[str, int]] = [
            {'x': start_coord_x, 'y': start_coord_y}
        ]
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


def build_hub_occupancy(
    planner: RoutePlanner,
    total_turns: int
) -> dict[int, dict[str, int]]:
    """Calculates drone occupancy counts per hub for each turn step.

    Args:
        planner (RoutePlanner): Route planner containing drone flight data.
        total_turns (int): Total simulation turns.

    Returns:
        dict[int, dict[str, int]]:
            Mapping of turn index to hub occupancy counts.
    """
    end_hub_name: str = planner.network_zone.end.name
    total_drones: int = len(planner.drone_list)

    def get_hub(drone: Drone, turn: int) -> str | None:
        if turn == 0:
            return planner.network_zone.start.name
        action: str | None = drone.route.get(turn - 1)
        return action if action and not _isConnection(action) else None

    result: dict[int, dict[str, int]] = {}

    for turn in range(total_turns + 1):
        counts = Counter(
            hub for drone in planner.drone_list
            if (hub := get_hub(drone, turn)) is not None
        )
        counts[end_hub_name] += total_drones - sum(counts.values())
        result[turn] = dict(counts)

    return result


def calculate_hub_screen_positions(
    all_hubs: list[Hub],
    min_x: int,
    min_y: int,
    node_distance_px: int,
    padding_px: int
) -> dict[str, tuple[int, int]]:
    """Maps relative grid coordinates of hubs
    into absolute screen pixel coordinates.

    Args:
        all_hubs (list[Hub]): List of hubs to scale and position.
        min_x (int): Minimum X grid coordinate across all hubs.
        min_y (int): Minimum Y grid coordinate across all hubs.
        node_distance_px (int): Pixel distance multiplier per grid unit.
        padding_px (int): Canvas edge padding in pixels.

    Returns:
        dict[str, tuple[int, int]]:
            Dictionary mapping hub names to (X, Y) pixel pairs.
    """
    screen_positions: dict[str, tuple[int, int]] = {}
    for hub in all_hubs:
        px: int = (hub.coord_x - min_x) * node_distance_px + padding_px
        py: int = (hub.coord_y - min_y) * node_distance_px + padding_px
        screen_positions[hub.name] = (px, py)
    return screen_positions


def generate_html(planner: RoutePlanner) -> str:
    """Assembles full HTML, CSS, and JS components into
    an interactive visualizer web page.

    Args:
        planner (RoutePlanner): Route planner containing simulation state.

    Returns:
        str: Fully rendered standalone HTML document content.
    """
    network_zone: NetworkZone = planner.network_zone
    all_hubs: list[Hub] = network_zone.all_hubs()

    min_coord_x: int = min(hub.coord_x for hub in all_hubs)
    max_coord_x: int = max(hub.coord_x for hub in all_hubs)
    min_coord_y: int = min(hub.coord_y for hub in all_hubs)
    max_coord_y: int = max(hub.coord_y for hub in all_hubs)

    node_distance_px: int = 100
    padding_px: int = 40
    map_w: int = (
        (max_coord_x - min_coord_x) *
        node_distance_px + padding_px * 2
    )
    map_h: int = (
        (max_coord_y - min_coord_y) *
        node_distance_px + padding_px * 2
    )

    hub_positions: dict[str, tuple[int, int]] = calculate_hub_screen_positions(
        all_hubs, min_coord_x, min_coord_y, node_distance_px, padding_px
    )

    total_turns: int = max(
        (max(drone.route.keys()) + 1)
        for drone
        in planner.drone_list
    ) if planner.drone_list else 1
    turn_duration: int = 1
    anim_duration: int = total_turns * turn_duration

    drone_positions: dict[int, list[dict[str, int]]] = build_drone_positions(
        planner, hub_positions, total_turns
    )
    drone_positions_json: str = json.dumps(drone_positions)

    hub_occupancy: dict[int, dict[str, int]] = build_hub_occupancy(
        planner, total_turns
    )
    hub_occupancy_json: str = json.dumps(hub_occupancy)

    keyframes_css: list[str] = []
    for drone in planner.drone_list:
        keyframes_css.append(generate_keyframes(
            drone, network_zone, hub_positions, total_turns
        ))

    hubs_html: list[str] = create_html_hubs(
        all_hubs, network_zone, hub_positions
    )
    connections_svg: list[str] = create_svg_connections(
        network_zone, hub_positions
    )

    drones_html: list[str] = []
    drone_anim_css: list[str] = []
    for drone in planner.drone_list:
        dron_color: str = DRONE_COLORS[drone.id % len(DRONE_COLORS)]
        start_coord_x, start_coord_y = hub_positions[network_zone.start.name]
        drones_html.append(
            f'''<div class="drone" id="drone{drone.id}"
                style="left:{start_coord_x}px;
                    top:{start_coord_y}px;
                    background:{dron_color};">
                D{drone.id}
            </div>'''
        )
        drone_anim_css.append(
            f'''#drone{drone.id} {{
                animation: drone{drone.id} {anim_duration}s linear infinite;
            }}'''
        )

    keyframes_str = '\n'.join(keyframes_css)
    drone_anim_str = '\n'.join(drone_anim_css)
    hubs_str = '\n'.join(hubs_html)
    conns_str = '\n'.join(connections_svg)
    drones_str = '\n'.join(drones_html)

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
  .hub-occupancy {{
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
    <div class="controls">
        <button id="modeBtn">Manual</button>
        <button class="arrow" id="prevBtn" disabled>&#9664;</button>
        <span class="turn-display" id="turnDisplay">Auto</span>
        <button class="arrow" id="nextBtn" disabled>&#9654;</button>
    </div>
    <div class="map">
        <svg class="connections">
            {conns_str}
        </svg>
        {hubs_str}
        {drones_str}
    </div>
<script>
const Mode = Object.freeze({{
    AUTO: 'Auto',
    MANUAL: 'Manual'
}});

const prevBtn = document.getElementById('prevBtn')
const nextBtn = document.getElementById('nextBtn')
const modeBtn = document.getElementById('modeBtn')
const turnDisplay = document.getElementById('turnDisplay')

const dronePositions = {drone_positions_json};
const hubOccupancy = {hub_occupancy_json};
const totalTurns = {total_turns};
const moveTime = 500;
const animCSS = {
    json.dumps(
        {
            f'drone{d.id}':
            f'drone{d.id} {anim_duration}s linear infinite'
            for d
            in planner.drone_list
        }
    )
};

let autoMode = true;
let currentTurn = 0;
let moving = false;

let animStart = performance.now();
let occupancyInterval = null;

const prevTurn = () => {{
    if (!autoMode && !moving) setTurn(currentTurn - 1, true);
}};
const nextTurn = () => {{
    if (!autoMode && !moving) setTurn(currentTurn + 1, true);
}};

prevBtn.addEventListener('click', prevTurn);
nextBtn.addEventListener('click', nextTurn);
modeBtn.addEventListener('click', toggleMode);

document.addEventListener('keydown', (event) => {{
    if (!autoMode) {{
        if (event.key === 'ArrowLeft') {{
            event.preventDefault(); prevTurn();
        }}
        if (event.key === 'ArrowRight') {{
            event.preventDefault(); nextTurn();
        }}
    }}
}});

if (autoMode) StopOccupancyTimer(false);

function toggleMode() {{
    autoMode = !autoMode;
    const drones = document.querySelectorAll('.drone');

    if (autoMode) {{
        modeBtn.textContent = Mode.MANUAL;
        modeBtn.classList.remove('active');
        turnDisplay.textContent = Mode.AUTO;

        drones.forEach(drone => {{
            drone.style.transition = 'none';
            drone.style.removeProperty('left');
            drone.style.removeProperty('top');
            drone.style.animation = 'none';
            drone.offsetHeight;
            drone.style.animation = animCSS[drone.id];
            drone.style.animationDelay = -(currentTurn * 1000) + 'ms';
        }});

        animStart = performance.now() - (currentTurn * 1000);
        prevBtn.disabled = true;
        nextBtn.disabled = true;
        StopOccupancyTimer(false);

    }} else {{
        modeBtn.textContent = Mode.AUTO;
        modeBtn.classList.add('active');
        StopOccupancyTimer(true);

        currentTurn = updateCurrentTurn();

        drones.forEach(d => {{
            d.style.animation = 'none';
            d.style.transition = `left ${{moveTime}}ms ease,
                top ${{moveTime}}ms ease`;
        }});

        setTurn(currentTurn, false);
    }}
}}

function StopOccupancyTimer(isStoped) {{
    if (occupancyInterval) clearInterval(occupancyInterval);
    if (isStoped) occupancyInterval = null;
    else occupancyInterval = setInterval(
        () => {{updateHubOccupancy(updateCurrentTurn())}}
        ,200
    );
}}

function updateCurrentTurn() {{
    const time_elapsed = performance.now() - animStart;
    return Math.floor((time_elapsed + 500) / 1000) % totalTurns;
}}

function setTurn(turn, animate) {{
    currentTurn = Math.max(0, Math.min(turn, totalTurns));
    applyTurn(currentTurn, animate);
    turnDisplay.textContent = `Turn ${{currentTurn}}/${{totalTurns}}`;
    updateButtons();
}}

function applyTurn(turn, animate) {{
    if (animate && !autoMode) {{
        moving = true;
        prevBtn.disabled = true;
        nextBtn.disabled = true;
        setTimeout(() => {{ moving = false; updateButtons(); }}, moveTime);
    }}

    for (const [id, positions] of Object.entries(dronePositions)) {{
        const drone = document.getElementById('drone' + id);
        if (drone) {{
            const index = Math.min(turn, positions.length - 1);
            const position = positions[index];
            drone.style.left = position.x + 'px';
            drone.style.top = position.y + 'px';
        }}
    }}
    updateHubOccupancy(turn);
}}

function updateButtons() {{
    if (!autoMode) {{
        prevBtn.disabled = moving || currentTurn <= 0;
        nextBtn.disabled = moving || currentTurn >= totalTurns;
    }}
}}

function updateHubOccupancy(turn) {{
    const occupancy = hubOccupancy[turn] || {{}};
    document.querySelectorAll('.hub-occupancy').forEach(hub_occupancy => {{
        const max_drones = hub_occupancy.parentElement.dataset.max;
        const drones_in_hub = (
            occupancy[hub_occupancy.id.replace('occupancy-', '')]
            || 0
        );
        hub_occupancy.textContent = `${{drones_in_hub}}/${{max_drones}}`;
    }});
}}
</script>
</body>
</html>'''


def main() -> None:
    """Main CLI entry point for visualizer execution.

    Parses command-line arguments, loads network layout configuration,
    executes route planning, and writes rendered visualization HTML
    to the requested file path.
    """
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print('Usage: python visualizer.py <map_file> [output_file]')
        print(
            'Example: python visualizer.py maps/easy/01_linear_path.txt '
            'output.html'
        )
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
