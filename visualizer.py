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

    <div id="startDroneVisual" class="start-drone-visual">
        <div
            id="startDroneNode"
            class="drone"
            style="background-color: {DRONE_COLORS[0]};
                   position: relative; left: 0; top: 0;"
        >D0</div>
    </div>

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

const resetButton = document.getElementById('resetBtn');
const playButton = document.getElementById('playBtn');
const previousButton = document.getElementById('prevBtn');
const nextButton = document.getElementById('nextBtn');
const turnDisplay = document.getElementById('turnDisplay');
const dronesContainer = document.getElementById('dronesContainer');
const startDroneVisual = document.getElementById('startDroneVisual');
const errorBanner = document.getElementById('errorBanner');

const currentHtmlFileName =
    window.location.pathname.split('/').pop();

const expectedMapFileName =
    currentHtmlFileName.replace(/\\.html?$/i, '.txt');

let startDroneNode =
    document.getElementById('startDroneNode');

let currentTurn = parseInt(
    localStorage.getItem('flyin_current_turn') || '0',
    10
);

const autoResumePlay =
    localStorage.getItem('flyin_is_playing') === 'true';

let isPlaying = false;
let playInterval = null;
let isStepping = false;

const turnLinesCache = new Map();

let droneStatesHistory = [
    {{ activeDrones: new Map(), startedCount: 0, arrivedCount: 0 }}
];


function showError(message) {{
    errorBanner.textContent = `⚠️ ${{message}}`;
    errorBanner.style.display = 'block';
}}


function configureDroneNode(droneNode, droneId) {{
    const numericDroneId = parseInt(droneId, 10);

    droneNode.id = `drone_${{droneId}}`;
    droneNode.className = 'drone';
    droneNode.textContent = `D${{droneId}}`;
    droneNode.style.backgroundColor =
        DRONE_COLORS[Math.abs(numericDroneId) % DRONE_COLORS.length];
    droneNode.style.zIndex =
        String(3 + Math.max(0, numericDroneId));

    return droneNode;
}}


function createDroneNode(droneId) {{
    return configureDroneNode(
        document.createElement('div'),
        droneId
    );
}}


function moveDroneToPosition(
    droneNode,
    targetX,
    targetY,
    animate = true
) {{
    if (animate) {{
        void droneNode.offsetWidth;
        droneNode.classList.add('is-moving');
    }} else droneNode.classList.remove('is-moving');

    droneNode.style.left = `${{targetX}}px`;
    droneNode.style.top = `${{targetY}}px`;
}}


function spawnDroneAtPosition(
    droneId,
    positionX,
    positionY
) {{
    const droneNode = createDroneNode(droneId);
    moveDroneToPosition(
        droneNode,
        positionX,
        positionY,
        false
    );
    dronesContainer.appendChild(droneNode);
    return droneNode;
}}


function createStartDronePlaceholder(droneId) {{
    const placeholderNode = document.createElement('div');

    placeholderNode.id = 'startDroneNode';
    placeholderNode.className = 'drone';
    placeholderNode.textContent = `D${{droneId}}`;
    placeholderNode.style.position = 'relative';
    placeholderNode.style.left = '0';
    placeholderNode.style.top = '0';
    placeholderNode.style.zIndex = '4';
    placeholderNode.style.backgroundColor =
        DRONE_COLORS[
            Math.abs(parseInt(droneId, 10))
            % DRONE_COLORS.length
        ];

    return placeholderNode;
}}


function spawnDroneFromStart(
    droneId,
    targetX,
    targetY
) {{
    const startCoordinates = HUB_POSITIONS[START_HUB];

    if (!startCoordinates || !startDroneNode) return null;

    const departingDroneNode =
        configureDroneNode(startDroneNode, droneId);

    departingDroneNode.style.position = 'absolute';
    departingDroneNode.style.left =
        `${{startCoordinates.x}}px`;
    departingDroneNode.style.top =
        `${{startCoordinates.y}}px`;
    departingDroneNode.style.transform =
        'translate(-50%, -50%)';

    dronesContainer.appendChild(departingDroneNode);

    const nextDroneId =
        parseInt(droneId, 10) + 1;

    if (nextDroneId < TOTAL_DRONES) {{
        const nextStartDroneNode =
            createStartDronePlaceholder(nextDroneId);

        startDroneVisual.appendChild(
            nextStartDroneNode
        );

        startDroneNode =
            nextStartDroneNode;
    }} else {{
        startDroneVisual.style.display =
            'none';
    }}

    moveDroneToPosition(
        departingDroneNode,
        targetX,
        targetY
    );

    return departingDroneNode;
}}


function moveDroneBackToStart(
    returningDroneNode,
    returningDroneId,
    targetTurn
) {{
    const startCoordinates =
        HUB_POSITIONS[START_HUB];

    if (!startCoordinates || !returningDroneNode) {{
        return Promise.resolve();
    }}

    return new Promise(resolve => {{
        const mapContainer =
            dronesContainer.parentElement;

        let animationFinished = false;

        returningDroneNode.style.position =
            'absolute';

        returningDroneNode.style.zIndex = '10';

        mapContainer.appendChild(
            returningDroneNode
        );

        const handleReturnAnimationEnd = event => {{
            if (
                animationFinished ||
                event.propertyName !== 'left'
            ) return;

            animationFinished = true;

            returningDroneNode.removeEventListener(
                'transitionend',
                handleReturnAnimationEnd
            );

            if (currentTurn !== targetTurn) {{
                resolve();
                return;
            }}

            startDroneNode?.remove();

            returningDroneNode.id =
                'startDroneNode';

            returningDroneNode.className =
                'drone';

            returningDroneNode.style.position =
                'relative';

            returningDroneNode.style.left = '0';
            returningDroneNode.style.top = '0';

            returningDroneNode.style.transform =
                'translate(-50%, -50%)';

            returningDroneNode.style.zIndex = '4';

            returningDroneNode.style.backgroundColor =
                DRONE_COLORS[
                    Math.abs(
                        parseInt(
                            returningDroneId,
                            10
                        )
                    ) % DRONE_COLORS.length
                ];

            returningDroneNode.classList.remove(
                'is-moving'
            );

            returningDroneNode.textContent =
                `D${{returningDroneId}}`;

            startDroneVisual.appendChild(
                returningDroneNode
            );

            startDroneNode =
                returningDroneNode;

            startDroneVisual.style.display =
                'block';

            resolve();
        }};

        returningDroneNode.addEventListener(
            'transitionend',
            handleReturnAnimationEnd
        );

        void returningDroneNode.offsetWidth;

        returningDroneNode.classList.add(
            'is-moving'
        );

        returningDroneNode.style.left =
            `${{startCoordinates.x}}px`;

        returningDroneNode.style.top =
            `${{startCoordinates.y}}px`;
    }});
}}


function resetStartDroneVisual() {{
    startDroneVisual.innerHTML = '';

    if (TOTAL_DRONES <= 0) {{
        startDroneVisual.style.display = 'none';
        startDroneNode = null;
        return;
    }}

    startDroneNode =
        createStartDronePlaceholder(0);

    startDroneVisual.appendChild(
        startDroneNode
    );

    startDroneVisual.style.display =
        'block';
}}


function resetStateToZero() {{
    dronesContainer.innerHTML = '';

    droneStatesHistory = [
        {{ activeDrones: new Map(), startedCount: 0, arrivedCount: 0 }}
    ];

    currentTurn = 0;

    localStorage.setItem(
        'flyin_current_turn',
        '0'
    );

    resetStartDroneVisual();
}}


async function loadChunkForTurn(turnNumber) {{
    const chunkIndex =
        Math.floor((turnNumber - 1) / CHUNK_SIZE);

    const chunkFileName =
        `chunk_${{chunkIndex}}.txt`;

    try {{
        const response = await fetch(
            `${{CHUNKS_DIR}}/${{chunkFileName}}`
        );

        if (!response.ok) {{
            showError(
                `No se ha podido cargar ${{chunkFileName}}`
            );
            return false;
        }}

        const chunkText = await response.text();
        const chunkLines = chunkText
            .split('\\n')
            .map(line => line.trim())
            .filter(Boolean);

        if (!chunkLines.length) {{
            showError(
                `${{chunkFileName}} está vacío`
            );
            return false;
        }}

        const headerLine = chunkLines[0];
        const headerMatch = headerLine.match(
            /^#\\s*map=(\\S+)\\s+chunk=(\\d+)\\s+start_turn=(\\d+)$/
        );

        if (!headerMatch) {{
            showError(
                `${{chunkFileName}} no tiene una cabecera válida`
            );
            return false;
        }}

        const chunkMapPath = headerMatch[1];
        const declaredChunkIndex =
            parseInt(headerMatch[2], 10);

        const chunkMapFileName =
            chunkMapPath.split('/').pop();

        if (chunkMapFileName !== expectedMapFileName) {{
            showError(
                `El chunk ${{chunkFileName}} pertenece a ` +
                `"${{chunkMapFileName}}" y no a ` +
                `"${{expectedMapFileName}}"`
            );
            return false;
        }}

        if (declaredChunkIndex !== chunkIndex) {{
            showError(
                `El archivo ${{chunkFileName}} declara ` +
                `chunk=${{declaredChunkIndex}}`
            );
            return false;
        }}

        /*
         * La línea 0 es la cabecera.
         * Solo las líneas restantes son turnos.
         */
        chunkLines.slice(1).forEach((turnLine, lineIndex) => {{
            const absoluteTurn =
                chunkIndex * CHUNK_SIZE + lineIndex + 1;

            turnLinesCache.set(
                absoluteTurn,
                turnLine
            );
        }});

        errorBanner.style.display = 'none';

        return turnLinesCache.has(turnNumber);
    }} catch (error) {{
        showError(
            `Error leyendo ${{chunkFileName}}: ${{error.message}}`
        );
        return false;
    }}
}}


function getCoordinates(locationName) {{
    if (!locationName) return null;

    const directPosition =
        HUB_POSITIONS[locationName];

    if (directPosition) return directPosition;

    const [initialHubName, finalHubName] =
        locationName.split('-');

    const initialHubPosition =
        HUB_POSITIONS[initialHubName];

    const finalHubPosition =
        HUB_POSITIONS[finalHubName];

    if (
        !initialHubPosition ||
        !finalHubPosition
    ) {{
        return null;
    }}

    return {{
        x: Math.floor(
            (initialHubPosition.x +
                finalHubPosition.x) / 2
        ),
        y: Math.floor(
            (initialHubPosition.y +
                finalHubPosition.y) / 2
        )
    }};
}}


async function processUpToTurn(targetTurn) {{
    while (droneStatesHistory.length <= targetTurn) {{
        const turnNumber =
            droneStatesHistory.length;

        if (!turnLinesCache.has(turnNumber)) {{
            if (!await loadChunkForTurn(turnNumber)) {{
                return false;
            }}
        }}

        const turnLine =
            turnLinesCache.get(turnNumber);

        const previousState =
            droneStatesHistory[turnNumber - 1];

        const activeDrones =
            new Map(previousState.activeDrones);

        let startedDroneCount =
            previousState.startedCount;

        let arrivedDroneCount =
            previousState.arrivedCount;

        if (turnLine) {{
            for (
                const movementToken
                of turnLine.split(/\\s+/)
            ) {{
                if (!movementToken.startsWith('D')) continue;

                const separatorIndex =
                    movementToken.indexOf('-');

                if (separatorIndex === -1) continue;

                const droneId =
                    movementToken.substring(
                        1,
                        separatorIndex
                    );

                const targetLocation =
                    movementToken.substring(
                        separatorIndex + 1
                    );

                const numericDroneId =
                    parseInt(droneId, 10);

                if (
                    !previousState.activeDrones.has(droneId) &&
                    numericDroneId >= previousState.startedCount
                ) {{
                    startedDroneCount = Math.max(
                        startedDroneCount,
                        numericDroneId + 1
                    );
                }}

                const previousLocation =
                    previousState.activeDrones.get(
                        droneId
                    );

                if (
                    targetLocation === GOAL_HUB &&
                    previousLocation !== GOAL_HUB
                ) {{
                    arrivedDroneCount++;
                }}

                activeDrones.set(
                    droneId,
                    targetLocation
                );
            }}
        }}

        droneStatesHistory.push({{
            activeDrones,
            startedCount: startedDroneCount,
            arrivedCount: arrivedDroneCount,
        }});
    }}

    return true;
}}


function updateStartDroneVisual(
    turnState,
    movingBackward = false
) {{
    const remainingDrones = Math.max(
        0,
        TOTAL_DRONES - turnState.startedCount
    );

    if (movingBackward) {{
        if (remainingDrones <= 0) {{
            startDroneVisual.style.display =
                'none';
        }}
        return;
    }}

    if (
        remainingDrones <= 0 ||
        !startDroneNode
    ) {{
        startDroneVisual.style.display =
            'none';
        return;
    }}

    const nextDroneId =
        String(turnState.startedCount);

    startDroneVisual.style.display =
        'block';

    startDroneNode.textContent =
        `D${{nextDroneId}}`;

    startDroneNode.style.backgroundColor =
        DRONE_COLORS[
            Math.abs(
                parseInt(nextDroneId, 10)
            ) % DRONE_COLORS.length
        ];
}}


async function renderDrones(
    turnState,
    previousState,
    movingBackward
) {{
    const activeDrones =
        turnState.activeDrones;

    let returningDroneId = null;

    if (
        movingBackward &&
        previousState.startedCount >
            turnState.startedCount
    ) {{
        returningDroneId =
            String(
                previousState.startedCount - 1
            );
    }}

    const dronesAtGoal = [...activeDrones]
        .filter(
            ([, location]) =>
                location === GOAL_HUB
        )
        .map(
            ([droneId]) =>
                String(droneId)
        )
        .sort(
            (firstId, secondId) =>
                parseInt(firstId, 10) -
                parseInt(secondId, 10)
        );

    const newestGoalDroneId =
        dronesAtGoal.at(-1) ?? null;

    const previousDronesAtGoal =
        [...previousState.activeDrones]
            .filter(
                ([, location]) =>
                    location === GOAL_HUB
            )
            .map(
                ([droneId]) =>
                    String(droneId)
            )
            .sort(
                (firstId, secondId) =>
                    parseInt(firstId, 10) -
                    parseInt(secondId, 10)
            );

    const previousNewestGoalDroneId =
        previousDronesAtGoal.at(-1) ?? null;

    const newDroneReachedGoal =
        !movingBackward &&
        newestGoalDroneId !== null &&
        previousState.activeDrones.get(
            newestGoalDroneId
        ) !== GOAL_HUB;

    for (
        const [droneId, locationName]
        of activeDrones
    ) {{
        const droneIdString =
            String(droneId);

        if (
            movingBackward &&
            droneIdString === returningDroneId
        ) {{
            continue;
        }}

        const targetCoordinates =
            getCoordinates(locationName);

        if (!targetCoordinates) continue;

        const keepPreviousGoalDrone =
            newDroneReachedGoal &&
            droneIdString === previousNewestGoalDroneId;

        if (
            locationName === GOAL_HUB &&
            droneIdString !== newestGoalDroneId &&
            !keepPreviousGoalDrone
        ) {{
            continue;
        }}

        let droneNode =
            document.getElementById(
                `drone_${{droneIdString}}`
            );

        if (!droneNode) {{
            if (movingBackward) {{
                const previousLocation =
                    previousState.activeDrones.get(
                        droneIdString
                    );

                const previousCoordinates =
                    getCoordinates(previousLocation);

                if (previousCoordinates) {{
                    droneNode =
                        spawnDroneAtPosition(
                            droneIdString,
                            previousCoordinates.x,
                            previousCoordinates.y
                        );
                }}
            }} else if (
                !previousState.activeDrones.has(
                    droneIdString
                )
            ) {{
                droneNode =
                    spawnDroneFromStart(
                        droneIdString,
                        targetCoordinates.x,
                        targetCoordinates.y
                    );
            }} else {{
                const previousLocation =
                    previousState.activeDrones.get(
                        droneIdString
                    );

                const previousCoordinates =
                    getCoordinates(previousLocation) ||
                    targetCoordinates;

                droneNode =
                    spawnDroneAtPosition(
                        droneIdString,
                        previousCoordinates.x,
                        previousCoordinates.y
                    );
            }}
        }}

        if (!droneNode) continue;

        if (
            previousState.activeDrones.has(
                droneIdString
            )
        ) {{
            moveDroneToPosition(
                droneNode,
                targetCoordinates.x,
                targetCoordinates.y
            );
        }}
    }}

    if (
        newDroneReachedGoal &&
        previousNewestGoalDroneId !== null
    ) {{
        const arrivingDroneNode =
            document.getElementById(
                `drone_${{newestGoalDroneId}}`
            );

        const previousGoalDroneNode =
            document.getElementById(
                `drone_${{previousNewestGoalDroneId}}`
            );

        if (
            arrivingDroneNode &&
            previousGoalDroneNode
        ) {{
            const handleGoalArrival = event => {{
                if (event.propertyName !== 'left') return;

                arrivingDroneNode.removeEventListener(
                    'transitionend',
                    handleGoalArrival
                );

                previousGoalDroneNode.remove();
            }};

            arrivingDroneNode.addEventListener(
                'transitionend',
                handleGoalArrival
            );
        }}
    }}

    if (returningDroneId !== null) {{
        const returningDroneNode =
            document.getElementById(
                `drone_${{returningDroneId}}`
            );

        if (returningDroneNode) {{
            await moveDroneBackToStart(
                returningDroneNode,
                returningDroneId,
                currentTurn
            );
        }}
    }}

    for (
        const droneNode
        of document.querySelectorAll(
            '#dronesContainer .drone'
        )
    ) {{
        const droneId =
            droneNode.id.replace(
                'drone_',
                ''
            );

        if (!activeDrones.has(droneId)) {{
            droneNode.remove();
        }}
    }}
}}


function updateHubOccupancy(turnState) {{
    const hubOccupancy = {{}};

    for (
        const [, locationName]
        of turnState.activeDrones
    ) {{
        if (
            locationName !== GOAL_HUB &&
            !locationName.includes('-')
        ) {{
            hubOccupancy[locationName] =
                (hubOccupancy[locationName] || 0) + 1;
        }}
    }}

    const remainingDrones =
        TOTAL_DRONES -
        turnState.startedCount;

    hubOccupancy[START_HUB] =
        (hubOccupancy[START_HUB] || 0) +
        remainingDrones;

    hubOccupancy[GOAL_HUB] =
        turnState.arrivedCount;

    document
        .querySelectorAll('.hub-occupancy')
        .forEach(occupancyElement => {{
            const hubName =
                occupancyElement.id.replace(
                    'occupancy-',
                    ''
                );

            const maximumDrones =
                occupancyElement
                    .parentElement
                    .dataset
                    .max;

            occupancyElement.textContent =
                `${{
                    hubOccupancy[hubName] || 0
                }}/${{maximumDrones}}`;
        }});
}}


async function renderTurn(
    targetTurn,
    forceReset = false
) {{
    const previousTurn = currentTurn;
    const movingBackward =
        targetTurn < previousTurn;

    if (targetTurn === 0 && forceReset) {{
        resetStateToZero();

        turnDisplay.textContent =
            'Turn 0';

        updateHubOccupancy(
            droneStatesHistory[0]
        );

        updateButtons();

        return true;
    }}

    if (targetTurn === 0) {{
        const previousState =
            droneStatesHistory[previousTurn];

        const targetState =
            droneStatesHistory[0];

        currentTurn = 0;

        localStorage.setItem(
            'flyin_current_turn',
            '0'
        );

        turnDisplay.textContent =
            'Turn 0';

        updateStartDroneVisual(
            targetState,
            true
        );

        await renderDrones(
            targetState,
            previousState,
            true
        );

        updateHubOccupancy(
            targetState
        );

        updateButtons();

        return true;
    }}

    if (!await processUpToTurn(targetTurn)) {{
        return false;
    }}

    const previousState =
        droneStatesHistory[previousTurn];

    const targetState =
        droneStatesHistory[targetTurn];

    currentTurn =
        targetTurn;

    localStorage.setItem(
        'flyin_current_turn',
        String(targetTurn)
    );

    turnDisplay.textContent =
        `Turn ${{targetTurn}}`;

    updateStartDroneVisual(
        targetState,
        movingBackward
    );

    await renderDrones(
        targetState,
        previousState,
        movingBackward
    );

    updateHubOccupancy(
        targetState
    );

    updateButtons();

    return true;
}}


function updateButtons() {{
    previousButton.disabled =
        isStepping ||
        currentTurn <= 0;

    nextButton.disabled =
        isStepping;
}}


async function stepNext() {{
    if (isStepping) return;

    isStepping = true;

    try {{
        const nextTurn =
            currentTurn + 1;

        if (!await processUpToTurn(nextTurn)) {{
            if (isPlaying) togglePlay();
            return;
        }}

        await renderTurn(nextTurn);
    }} finally {{
        isStepping = false;
        updateButtons();
    }}
}}


async function stepPrevious() {{
    if (isStepping || currentTurn <= 0) return;

    isStepping = true;

    try {{
        await renderTurn(
            currentTurn - 1
        );
    }} finally {{
        isStepping = false;
        updateButtons();
    }}
}}


function togglePlay() {{
    if (isPlaying) {{
        isPlaying = false;

        localStorage.setItem(
            'flyin_is_playing',
            'false'
        );

        playButton.textContent =
            '▶ Play';

        playButton.classList.remove(
            'active'
        );

        if (playInterval) {{
            clearInterval(playInterval);
            playInterval = null;
        }}

        return;
    }}

    isPlaying = true;

    localStorage.setItem(
        'flyin_is_playing',
        'true'
    );

    playButton.textContent =
        '❚❚ Pause';

    playButton.classList.add(
        'active'
    );

    playInterval = setInterval(
        () => stepNext(),
        600
    );
}}


resetButton.addEventListener(
    'click',
    async () => {{
        if (isPlaying) togglePlay();
        await renderTurn(0, true);
    }}
);

playButton.addEventListener(
    'click',
    togglePlay
);

nextButton.addEventListener(
    'click',
    () => {{
        if (!isPlaying) stepNext();
    }}
);

previousButton.addEventListener(
    'click',
    () => {{
        if (!isPlaying) stepPrevious();
    }}
);

document.addEventListener(
    'keydown',
    event => {{
        if (
            event.key === 'ArrowRight' &&
            !isPlaying
        ) {{
            stepNext();
        }}

        if (
            event.key === 'ArrowLeft' &&
            !isPlaying
        ) {{
            stepPrevious();
        }}

        if (event.key === ' ') {{
            event.preventDefault();
            togglePlay();
        }}
    }}
);


(async () => {{
    await renderTurn(currentTurn);

    if (autoResumePlay) {{
        togglePlay();
    }}
}})();
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
