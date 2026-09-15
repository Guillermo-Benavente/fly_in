#!/usr/bin/env python3

import json
import os
import sys

from parser import Parser
from hub import Hub, TypeMetadata as TMHub, TypeZone
from connection import TypeMetadata as TMConnection
from network_zone import NetworkZone


COLOR_MAP: dict[str, str] = {
    'black': '#333', 'white': '#eee', 'red': '#e74c3c',
    'blue': '#3498db', 'green': '#2ecc71', 'yellow': '#f1c40f',
    'magenta': '#e91e63', 'cyan': '#00bcd4', 'orange': '#ff9800',
    'purple': '#9b59b6', 'brown': '#795548', 'maroon': '#800000',
    'gold': '#ffd700', 'lime': '#cddc39', 'crimson': '#dc143c',
    'violet': '#7c4dff', 'darkred': '#b71c1c',
    'rainbow': (
        'linear-gradient(135deg, #ff0000, #ff7f00, #ffff00, '
        '#00ff00, #0000ff, #4b0082, #8b00ff)'
    ),
}

DRONE_COLORS: list[str] = [
    '#ff6b6b', '#4ecdc4', '#45b7d1', '#f9ca24', '#6c5ce7',
    '#fd79a8', '#00cec9', '#e17055', '#0984e3', '#d63031',
    '#a29bfe', '#55efc4', '#fdcb6e', '#e84393', '#00b894',
    '#fab1a0', '#74b9ff', '#ff7675', '#b2bec3', '#636e72',
    '#ffeaa7', '#dfe6e9', '#81ecec', '#ff9ff3', '#feca57',
]


def create_svg_connections(
    network_zone: NetworkZone,
    hub_positions: dict[str, tuple[int, int]],
) -> list[str]:
    """Generate SVG elements representing network connections.

    Args:
        network_zone: Network zone containing the connections to render.
        hub_positions: Mapping of hub names to their pixel coordinates.

    Returns:
        A list of SVG elements representing the connections and, when
        applicable, their link capacities.
    """
    connections_svg: list[str] = []

    for connection in network_zone.connections:
        initial_x, initial_y = hub_positions[connection.init_hub.name]
        final_x, final_y = hub_positions[connection.final_hub.name]

        connections_svg.append(
            f'<line x1="{initial_x}" y1="{initial_y}" '
            f'x2="{final_x}" y2="{final_y}" '
            'stroke="#555" stroke-width="2" stroke-dasharray="6,4"/>'
        )

        link_capacity = int(
            connection.metadata.get(
                TMConnection.MAX_LINK_CAPACITY, 1
            )
        )

        if link_capacity > 1:
            middle_x = (initial_x + final_x) // 2
            middle_y = (initial_y + final_y) // 2

            connections_svg.append(
                f'<text x="{middle_x}" y="{middle_y - 6}" '
                'fill="#888" font-size="10" text-anchor="middle">'
                f'[{link_capacity}]</text>'
            )

    return connections_svg


def create_html_hubs(
    hubs: list[Hub],
    network_zone: NetworkZone,
    hub_positions: dict[str, tuple[int, int]],
) -> list[str]:
    """Generate HTML elements representing network hubs.

    Args:
        hubs: Hubs to render in the visualization.
        network_zone: Network zone used to identify the start and end hubs
            and determine special hub styles.
        hub_positions: Mapping of hub names to their pixel coordinates.

    Returns:
        A list of HTML elements representing the hubs, including their
        colors, borders, and maximum drone occupancy.
    """
    hubs_html: list[str] = []

    for hub in hubs:
        position_x, position_y = hub_positions[hub.name]
        raw_color = str(
            hub.metadata.get(TMHub.COLOR, 'white')
        ).lower()

        hub_color = COLOR_MAP.get(raw_color, raw_color)
        rainbow_class = (
            ' rainbow-hub' if raw_color == 'rainbow' else ''
        )
        hub_zone = hub.metadata.get(TMHub.ZONE, TypeZone.NORMAL)

        if hub == network_zone.start:
            border_style = '3px solid #2ecc71'
        elif hub == network_zone.end:
            border_style = '3px solid #e74c3c'
        elif hub_zone == TypeZone.RESTRICTED:
            border_style = '3px dashed #fff'
        elif hub_zone == TypeZone.PRIORITY:
            border_style = '3px solid #fff'
        else:
            border_style = '3px solid #555'

        maximum_drones = int(
            hub.metadata.get(TMHub.MAX_DRONES, 1)
        )

        hubs_html.append(
            f'''<div class="hub{rainbow_class}"
    style="left:{position_x}px; top:{position_y}px;
           background:{hub_color}; border:{border_style};"
    data-max="{maximum_drones}">
    <span>{hub.name}</span>
    <span class="hub-occupancy" id="occupancy-{hub.name}">
        0/{maximum_drones}
    </span>
</div>'''
        )

    return hubs_html


def generate_html(network_zone: NetworkZone) -> str:
    """Generate an interactive HTML visualization of a network zone.

    The generated document contains the network hubs and connections,
    together with JavaScript controls for navigating and animating drone
    movements.

    Args:
        network_zone: Network zone to visualize.

    Returns:
        A complete HTML document containing the network visualization.
    """
    all_hubs: list[Hub] = network_zone.all_hubs()

    minimum_x = min(hub.coord_x for hub in all_hubs)
    maximum_x = max(hub.coord_x for hub in all_hubs)
    minimum_y = min(hub.coord_y for hub in all_hubs)
    maximum_y = max(hub.coord_y for hub in all_hubs)

    node_distance_pixels = 100
    map_padding_pixels = 40

    map_width = (
        (maximum_x - minimum_x) * node_distance_pixels
        + map_padding_pixels * 2
    )
    map_height = (
        (maximum_y - minimum_y) * node_distance_pixels
        + map_padding_pixels * 2
    )

    hub_positions: dict[str, tuple[int, int]] = {
        hub.name: (
            (hub.coord_x - minimum_x) * node_distance_pixels
            + map_padding_pixels,
            (hub.coord_y - minimum_y) * node_distance_pixels
            + map_padding_pixels,
        )
        for hub in all_hubs
    }

    hubs_html = '\n'.join(
        create_html_hubs(
            all_hubs,
            network_zone,
            hub_positions,
        )
    )

    connections_svg = '\n'.join(
        create_svg_connections(
            network_zone,
            hub_positions,
        )
    )

    total_drones = network_zone.drones
    start_hub_name = network_zone.start.name
    goal_hub_name = network_zone.end.name
    start_position_x, start_position_y = hub_positions[start_hub_name]

    hub_positions_json = json.dumps({
        name: {
            'x': position[0],
            'y': position[1],
        }
        for name, position in hub_positions.items()
    })

    drone_colors_json = json.dumps(DRONE_COLORS)

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Fly-In Visualizer</title>

<style>
* {{
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}}

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
}}

.controls {{
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 15px;
    padding: 10px 20px;
    background: #16213e;
    border: 1px solid #0f3460;
    border-radius: 8px;
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

.turn-display {{
    min-width: 140px;
    text-align: center;
    font-size: 14px;
    color: #aaa;
}}

.arrow {{
    font-size: 18px;
    padding: 4px 12px;
}}

.map {{
    position: relative;
    width: {map_width}px;
    height: {map_height}px;
    background: #16213e;
    border: 2px solid #0f3460;
    border-radius: 12px;
    overflow: hidden;
}}

.connections {{
    position: absolute;
    inset: 0;
    width: 100%;
    height: 100%;
}}

.hub {{
    position: absolute;
    width: 40px;
    height: 40px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 2;
    box-shadow: 0 0 8px rgba(0, 0, 0, 0.5);
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
    background: rgba(0, 0, 0, 0.7);
    padding: 1px 5px;
    border-radius: 4px;
    white-space: nowrap;
    margin-top: 2px;
}}

.drone {{
    position: absolute;
    width: 22px;
    height: 22px;
    border-radius: 50%;
    border: 2px solid #fff;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 8px;
    font-weight: bold;
    color: #000;
    z-index: 3;
    box-shadow: 0 0 10px rgba(255, 255, 255, 0.4);
    transform: translate(-50%, -50%);
}}

.drone.is-moving {{
    transition: left 400ms ease, top 400ms ease;
}}

.start-drone-visual {{
    position: absolute;
    left: {start_position_x}px;
    top: {start_position_y}px;
    z-index: 4;
    pointer-events: none;
}}

.error-banner {{
    color: #e74c3c;
    font-size: 12px;
    margin: 8px;
    display: none;
}}
</style>
</head>

<body>
<h1>Fly-In Visualization</h1>

<div class="controls">
    <button id="resetBtn">&#9100; Reset</button>
    <button id="playBtn">&#9654; Play</button>
    <button class="arrow" id="prevBtn" disabled>&#9664;</button>
    <span class="turn-display" id="turnDisplay">Turn 0</span>
    <button class="arrow" id="nextBtn">&#9654;</button>
</div>

<div id="errorBanner" class="error-banner"></div>

<div class="map">
    <svg class="connections">
        {connections_svg}
    </svg>

    {hubs_html}

    <div id="dronesContainer"></div>
</div>

<script>
const HUB_POSITIONS = {hub_positions_json};
const DRONE_COLORS = {drone_colors_json};
const TOTAL_DRONES = {total_drones};
const START_HUB = '{start_hub_name}';
const GOAL_HUB = '{goal_hub_name}';
const CHUNK_SIZE = 50;
const CHUNKS_DIR = './chunks';

let movements = [];
let currentChunk = 0;
let currentTurn = 0;
let turn = 0;
let previousMovement = '';
let boundaryMovement = '';
let droneAtGoal = null;
let droneAtStart = 'D0';
let isPlaying = false;
let playTimeout = null;
let navigationQueue = Promise.resolve();

const resetButton = document.getElementById('resetBtn');
const playButton = document.getElementById('playBtn');
const previousButton = document.getElementById('prevBtn');
const nextButton = document.getElementById('nextBtn');
const turnDisplay = document.getElementById('turnDisplay');
const dronesContainer = document.getElementById('dronesContainer');
const errorBanner = document.getElementById('errorBanner');

function queueNextTurn() {{
    navigationQueue = navigationQueue
        .then(() => nextTurn())
        .catch(error => {{
            errorBanner.textContent = error.message;
            errorBanner.style.display = 'block';
        }});
    return navigationQueue;
}}

function queuePreviousTurn() {{
    navigationQueue = navigationQueue
        .then(() => previousTurn())
        .catch(error => {{
            errorBanner.textContent = error.message;
            errorBanner.style.display = 'block';
        }});
    return navigationQueue;
}}

function saveState() {{
    const drones = Array
        .from(dronesContainer.querySelectorAll('.drone'))
        .filter(drone => {{
        if (drone.dataset.hub === GOAL_HUB && drone.id !== droneAtGoal)
            return false;
        if (drone.dataset.hub === START_HUB && drone.id !== droneAtStart)
            return false;
        return true;
    }}).map(drone => ({{
        name: drone.id,
        hub: drone.dataset.hub,
        left: drone.style.left,
        top: drone.style.top
    }}));
    const occupancy = {{}};
    document.querySelectorAll('.hub-occupancy').forEach(element => {{
        occupancy[element.id] = element.textContent;
    }});
    localStorage.setItem('flyInVisualizerState', JSON.stringify({{
        isPlaying,
        turn,
        drones,
        droneAtGoal,
        droneAtStart,
        previousMovement,
        occupancy
    }}));
}}

function loadState() {{
    const savedState = localStorage.getItem('flyInVisualizerState');
    if (!savedState) return null;
    try {{
        return JSON.parse(savedState);
    }} catch {{
        return null;
    }}
}}

function togglePlay() {{
    isPlaying = !isPlaying;
    if (isPlaying) {{
        playButton.textContent = '❚❚ Pause';
        playButton.classList.add('active');
        clearTimeout(playTimeout);
        playTimeout = setTimeout(playNext, 450);
    }} else {{
        playButton.textContent = '▶ Play';
        playButton.classList.remove('active');
        clearTimeout(playTimeout);
        playTimeout = null;
    }}
    saveState();
}}

async function playNext() {{
    if (!isPlaying) return;
    await queueNextTurn();
    if (isPlaying) playTimeout = setTimeout(playNext, 450);
}}

function updateOccupancy(hub, change) {{
    const occupancy = document.getElementById(`occupancy-${{hub}}`);
    if (!occupancy) return;
    const current = parseInt(occupancy.textContent.split('/')[0]);
    occupancy.textContent = `${{current + change}}/1`;
}}

function createDrone(hub, name) {{
    const numDron = parseInt(name.replace('D', ''));
    const newDron = document.createElement('div');
    newDron.id = name;
    newDron.textContent = name;
    newDron.dataset.hub = hub;
    newDron.style.left = `${{HUB_POSITIONS[hub].x}}px`;
    newDron.style.top = `${{HUB_POSITIONS[hub].y}}px`;
    newDron.style.backgroundColor = DRONE_COLORS[numDron % 25];
    newDron.classList.add('drone');
    dronesContainer.appendChild(newDron);
}}

function removeDron(name) {{
    const drone = document.getElementById(name);
    if (drone) drone.remove();
}}

function getPreviousMovement(turnIndex) {{
    if (turnIndex > 0) return movements[turnIndex - 1];
    return previousMovement;
}}

function getPreviousHub(name, turnIndex) {{
    if (name === 'D0' && turnIndex === 0) return START_HUB;
    const previousTurn = getPreviousMovement(turnIndex);
    if (!previousTurn) return START_HUB;
    const movement = previousTurn
        .split(' ')
        .find(movement => movement.startsWith(`${{name}}-`));
    if (!movement) return START_HUB;
    if (turnIndex === 0 && !movements.some((turnMovement, index) => {{
        if (index >= turnIndex)
            return false;
        return turnMovement
            .split(' ')
            .some(movement => movement.startsWith(`${{name}}-`));
    }}))
        return START_HUB;
    return movement.split('-')[1];
}}

function getPreviousGoalDrone(turnIndex) {{
    if (turnIndex > 0) {{
        for (let i = turnIndex - 1; i >= 0; i--) {{
            const previousGoalMovement = movements[i]
                .split(' ')
                .find(movement => movement.endsWith(`-${{GOAL_HUB}}`));
            if (previousGoalMovement)
                return previousGoalMovement.split('-')[0];
        }}
    }}

    if (previousMovement) {{
        const previousGoalMovement = previousMovement
            .split(' ')
            .find(movement => movement.endsWith(`-${{GOAL_HUB}}`));
        if (previousGoalMovement)
            return previousGoalMovement.split('-')[0];
    }}
    return null;
}}

function prepareStart(drone, numDron, origin, destination, isReverse) {{
    if (!isReverse && origin === START_HUB) {{
        const nextDrone = `D${{numDron + 1}}`;
        createDrone(START_HUB, nextDrone);
        droneAtStart = nextDrone;
    }}
    if (isReverse && destination === START_HUB) {{
        const oldDrone = droneAtStart;
        const newDrone = drone;
        if (oldDrone && oldDrone !== newDrone.id) {{
            newDrone.addEventListener('transitionend', event => {{
                if (event.propertyName === 'left')
                    removeDron(oldDrone);
            }}, {{ once: true }});
        }}
        droneAtStart = newDrone.id;
    }}
}}

function prepareGoal(name, origin, destination, isReverse, turnIndex) {{
    if (!isReverse && destination === GOAL_HUB) {{
        const oldDrone = droneAtGoal;
        const newDrone = document.getElementById(name);
        if (oldDrone && newDrone) {{
            newDrone.addEventListener('transitionend', event => {{
                if (event.propertyName === 'left')
                    removeDron(oldDrone);
            }}, {{ once: true }});
        }}
        droneAtGoal = name;
    }}
    if (isReverse && origin === GOAL_HUB) {{
        const previousName = getPreviousGoalDrone(turnIndex);
        if (previousName && !document.getElementById(previousName))
            createDrone(GOAL_HUB, previousName);
        droneAtGoal = previousName || null;
    }}
}}

function move(turnMovements, isReverse = false, turnIndex = 0) {{
    turnMovements.split(' ').forEach(movement => {{
        const [name, movementDestination] = movement.split('-');
        let drone = document.getElementById(name);
        let origin;
        let destination;
        if (isReverse) {{
            origin = movementDestination;
            destination = getPreviousHub(name, turnIndex);
            if (!drone) createDrone(origin, name);
            drone = document.getElementById(name);
        }} else {{
            origin = drone.dataset.hub;
            destination = movementDestination;
        }}
        prepareStart(
            drone,
            parseInt(name.replace('D', '')),
            origin,
            destination,
            isReverse
        );
        prepareGoal(
            name,
            origin,
            destination,
            isReverse,
            turnIndex
        );
        updateOccupancy(origin, -1);
        updateOccupancy(destination, 1);
        drone.classList.add('is-moving');
        drone.style.left = `${{HUB_POSITIONS[destination].x}}px`;
        drone.style.top = `${{HUB_POSITIONS[destination].y}}px`;
        drone.dataset.hub = destination;
    }});
}}

async function getLastMovement(chunk) {{
    if (chunk < 0)
        return '';
    const response = await fetch(`${{CHUNKS_DIR}}/chunk_${{chunk}}.txt`);
    if (!response.ok)
        return '';
    const text = await response.text();
    return text
        .split('\\n')
        .map(line => line.trim())
        .filter(line => line !== '')
        .at(-1);
}}

async function loadChunk(chunk) {{
    const response = await fetch(`${{CHUNKS_DIR}}/chunk_${{chunk}}.txt`);
    if (!response.ok)
        throw new Error(`No se pudo leer el chunk ${{chunk}}`);
    const text = await response.text();
    const lines = text.split('\\n');
    const header = lines[0].trim();
    const mapMatch = header.match(/map=([^\\s]+)/);
    if (!mapMatch)
        throw new Error('La cabecera del chunk no contiene el mapa');
    const mapPath = mapMatch[1];
    const mapFile = mapPath.split('/').pop();
    const currentFile = window.location.pathname
        .split('/')
        .pop()
        .replace(/\\.[^/.]+$/, '');
    if (mapFile.replace(/\\.[^/.]+$/, '') !== currentFile)
        throw new Error(`Estos ficheros no son para el mapa ${{currentFile}}`);
    movements = lines
        .slice(1)
        .map(line => line.trim())
        .filter(line => line !== '');
    currentChunk = chunk;
    currentTurn = 0;
}}

async function nextTurn() {{
    if (currentTurn >= movements.length) {{
        try {{
            previousMovement = movements[movements.length - 1];
            await loadChunk(currentChunk + 1);
        }} catch (error) {{
            return false;
        }}
    }}
    const movement = movements[currentTurn];
    move(movement, false, currentTurn);
    if (currentTurn > 0)
        previousMovement = movement;
    currentTurn++;
    turn++;
    turnDisplay.textContent = `Turn ${{turn}}`;
    saveState();
    return true;
}}

async function previousTurn() {{
    if (currentTurn <= 0) {{
        if (currentChunk <= 0)
            return false;
        const movement = movements[0];
        await loadChunk(currentChunk - 1);
        previousMovement = movements[movements.length - 1];
        currentTurn = movements.length - 1;
        move(movement, true, 0);
        turn--;
        turnDisplay.textContent = `Turn ${{turn}}`;
        saveState();
        return true;
    }}
    currentTurn--;
    const movement = movements[currentTurn];
    move(movement, true, currentTurn);
    if (currentTurn > 0)
        previousMovement = movements[currentTurn - 1];
    turn--;
    turnDisplay.textContent = `Turn ${{turn}}`;
    saveState();
    return true;
}}

resetButton.addEventListener('click', () => {{
    clearTimeout(playTimeout);
    dronesContainer.replaceChildren();
    currentChunk = 0;
    currentTurn = 0;
    turn = 0;
    previousMovement = '';
    boundaryMovement = '';
    droneAtGoal = null;
    droneAtStart = 'D0';
    isPlaying = false;
    playTimeout = null;
    navigationQueue = Promise.resolve();
    document
        .querySelectorAll('.hub-occupancy')
        .forEach(element => {{
            element.textContent = '0/1';
        }});
    document
        .getElementById(`occupancy-${{START_HUB}}`)
        .textContent = `${{TOTAL_DRONES}}/1`;
    document
        .getElementById(`occupancy-${{GOAL_HUB}}`)
        .textContent = '0/1';
    playButton.textContent = '▶ Play';
    playButton.classList.remove('active');
    createDrone(START_HUB, droneAtStart);
    turnDisplay.textContent = 'Turn 0';
    saveState();
}});

nextButton.addEventListener('click', queueNextTurn);
previousButton.addEventListener('click', queuePreviousTurn);
playButton.addEventListener('click', togglePlay);

document.addEventListener('keydown', event => {{
    if (event.repeat) return;
    if (event.key === 'ArrowRight') nextTurn();
    if (event.key === 'ArrowLeft') previousTurn();
    if (event.key === ' ') {{
        event.preventDefault();
        togglePlay();
    }}
}});

document.addEventListener('DOMContentLoaded', async () => {{
    try {{
        const savedState = loadState();
        if (!savedState) {{
            await loadChunk(0);
            createDrone(START_HUB, droneAtStart);
            document
                .getElementById(`occupancy-${{START_HUB}}`)
                .textContent = `${{TOTAL_DRONES}}/1`;
            document
                .getElementById(`occupancy-${{GOAL_HUB}}`)
                .textContent = '0/1';
            return;
        }}
        turn = savedState.turn || 0;
        currentChunk = Math.floor(turn / CHUNK_SIZE);
        await loadChunk(currentChunk);
        currentTurn = turn % CHUNK_SIZE;
        previousMovement = savedState.previousMovement || '';
        droneAtGoal = savedState.droneAtGoal || null;
        droneAtStart = savedState.droneAtStart || 'D0';
        dronesContainer.replaceChildren();
        if (savedState.drones && savedState.drones.length) {{
            savedState.drones.forEach(drone => {{
                createDrone(drone.hub, drone.name);
                const element = document.getElementById(drone.name);
                if (element) {{
                    element.style.left = drone.left;
                    element.style.top = drone.top;
                }}
            }});
        }} else createDrone(START_HUB, droneAtStart);
        if (savedState.occupancy) {{
            Object.entries(savedState.occupancy).forEach(([id, value]) => {{
                const element = document.getElementById(id);
                if (element)
                    element.textContent = value;
            }});
        }}
        turnDisplay.textContent = `Turn ${{turn}}`;
        isPlaying = !!savedState.isPlaying;
        if (isPlaying) {{
            playButton.textContent = '❚❚ Pause';
            playButton.classList.add('active');
            playTimeout = setTimeout(playNext, 450);
        }}
    }} catch (error) {{
        errorBanner.textContent = error.message;
        errorBanner.style.display = 'block';
    }}
}});
</script>
</body>
</html>'''


def main() -> None:
    """Parse command-line arguments and generate the visualization.

    The first argument specifies the map file to parse. An optional second
    argument specifies the output HTML file; if omitted, ``output.html``
    is used.

    Raises:
        SystemExit: If the number of command-line arguments is invalid.
    """
    if not 2 <= len(sys.argv) <= 3:
        print(
            'Usage: python visualizer.py '
            '<map_file> [output_file]'
        )
        sys.exit(1)

    map_file = sys.argv[1]
    output_path = (
        sys.argv[2]
        if len(sys.argv) == 3
        else 'output.html'
    )

    network_zone = Parser(map_file).parser()
    generated_html = generate_html(network_zone)

    os.makedirs(
        os.path.dirname(output_path) or '.',
        exist_ok=True,
    )

    with open(
        output_path,
        'w',
        encoding='utf-8',
    ) as output_file:
        output_file.write(generated_html)

    print(
        f'Generated visual layout HTML at {output_path}'
    )


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('\n[Simulation interrupted by user]', file=sys.stderr)
        sys.exit(130)
    except Exception as error:
        print(
            f'Error: {error}',
            file=sys.stderr,
        )
