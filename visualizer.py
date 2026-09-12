#!/usr/bin/env python3
"""Module for rendering network visualizer layout into standalone HTML pages.

Parses network configuration files to build the static HTML/CSS/JS map layout.
Handles dynamic DOM lifecycle with performance optimization for high drone counts.
"""
import sys
import json
import os
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


def create_svg_connections(
    network_zone: NetworkZone,
    hub_positions: dict[str, tuple[int, int]]
) -> list[str]:
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


def generate_html(network_zone: NetworkZone) -> str:
    all_hubs: list[Hub] = network_zone.all_hubs()

    min_coord_x: int = min(hub.coord_x for hub in all_hubs)
    max_coord_x: int = max(hub.coord_x for hub in all_hubs)
    min_coord_y: int = min(hub.coord_y for hub in all_hubs)
    max_coord_y: int = max(hub.coord_y for hub in all_hubs)

    node_distance_px: int = 100
    padding_px: int = 40
    map_w: int = (max_coord_x - min_coord_x) * node_distance_px + padding_px * 2
    map_h: int = (max_coord_y - min_coord_y) * node_distance_px + padding_px * 2

    hub_positions: dict[str, tuple[int, int]] = calculate_hub_screen_positions(
        all_hubs, min_coord_x, min_coord_y, node_distance_px, padding_px
    )

    hubs_html: list[str] = create_html_hubs(
        all_hubs, network_zone, hub_positions
    )
    connections_svg: list[str] = create_svg_connections(
        network_zone, hub_positions
    )

    hubs_str = '\n'.join(hubs_html)
    conns_str = '\n'.join(connections_svg)

    total_drones: int = getattr(
        network_zone, 'drones', getattr(network_zone, 'nb_drones', getattr(network_zone, 'drones_count', 0))
    )
    start_hub_name = network_zone.start.name
    goal_hub_name = network_zone.end.name
    start_pos = hub_positions[start_hub_name]

    hub_pos_js = json.dumps({
        name: {'x': pos[0], 'y': pos[1]}
        for name, pos in hub_positions.items()
    })
    drone_colors_js = json.dumps(DRONE_COLORS)

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Fly-In Visualizer</title>
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
  h1 {{ margin: 20px 0 10px; font-size: 24px; color: #eee; }}
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
  .controls button:hover {{ background: #3498db; }}
  .controls button.active {{
    background: #2ecc71;
    border-color: #2ecc71;
    color: #000;
  }}
  .controls .turn-display {{
    font-size: 14px;
    color: #aaa;
    min-width: 140px;
    text-align: center;
  }}
  .controls .arrow {{ font-size: 18px; padding: 4px 12px; }}
  .map {{
    position: relative;
    width: {map_w}px;
    height: {map_h}px;
    background: #16213e;
    border: 2px solid #0f3460;
    border-radius: 12px;
    overflow: hidden;
  }}
  .connections {{ position: absolute; top: 0; left: 0; width: 100%; height: 100%; }}
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
  .drone.is-moving {{
    transition: left 400ms ease, top 400ms ease;
  }}
  .start-drone-visual {{
    position: absolute;
    left: {start_pos[0]}px;
    top: {start_pos[1]}px;
    z-index: 4;
    pointer-events: none;
  }}
  .error-banner {{
    color: #e74c3c;
    font-size: 12px;
    margin-top: 8px;
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
    <div id="errorBanner" class="error-banner">
        ⚠️ No se han podido cargar los archivos de chunks desde ./chunks/
    </div>
    <div class="map">
        <svg class="connections">
            {conns_str}
        </svg>
        {hubs_str}
        <div id="startDroneVisual" class="start-drone-visual">
            <div id="startDroneNode" class="drone" style="background-color: {DRONE_COLORS[0]}; position: relative; left: 0; top: 0; transform: translate(-50%, -50%);">
                <span id="startDroneLabel">D0</span>
            </div>
        </div>
        <div id="dronesContainer"></div>
    </div>
<script>
const HUB_POSITIONS = {hub_pos_js};
const DRONE_COLORS = {drone_colors_js};
const TOTAL_DRONES = {total_drones};
const START_HUB = '{start_hub_name}';
const GOAL_HUB = '{goal_hub_name}';
const CHUNK_SIZE = 50;
const CHUNKS_DIR = './chunks';

const resetBtn = document.getElementById('resetBtn');
const playBtn = document.getElementById('playBtn');
const prevBtn = document.getElementById('prevBtn');
const nextBtn = document.getElementById('nextBtn');
const turnDisplay = document.getElementById('turnDisplay');
const dronesContainer = document.getElementById('dronesContainer');
const startDroneVisual = document.getElementById('startDroneVisual');
let startDroneNode = document.getElementById('startDroneNode');
let startDroneLabel = document.getElementById('startDroneLabel');
const errorBanner = document.getElementById('errorBanner');

let currentTurn = parseInt(localStorage.getItem('flyin_current_turn') || '0', 10);
let autoResumePlay = localStorage.getItem('flyin_is_playing') === 'true';

let isPlaying = false;
let playInterval = null;
let isStepping = false;

const turnLinesCache = new Map();
let droneStatesHistory = [
    {{ activeDrones: new Map(), startedCount: 0, arrivedCount: 0 }}
];

function resetStateToZero() {{
    dronesContainer.innerHTML = '';
    droneStatesHistory = [
        {{ activeDrones: new Map(), startedCount: 0, arrivedCount: 0 }}
    ];
    currentTurn = 0;
    localStorage.setItem('flyin_current_turn', '0');
}}

async function loadChunkForTurn(turn) {{
    const chunkIndex = Math.floor((turn - 1) / CHUNK_SIZE);
    const chunkFileName = `chunk_${{chunkIndex}}.txt`;
    
    try {{
        const response = await fetch(`${{CHUNKS_DIR}}/${{chunkFileName}}`);
        if (!response.ok) {{
            return false;
        }}
        errorBanner.style.display = 'none';
        const text = await response.text();
        const lines = text.split('\\n').map(l => l.trim()).filter(l => l.length > 0);
        
        lines.forEach((line, idx) => {{
            const turnNum = (chunkIndex * CHUNK_SIZE) + idx + 1;
            turnLinesCache.set(turnNum, line);
        }});
        return turnLinesCache.has(turn);
    }} catch (err) {{
        return false;
    }}
}}

function getCoordinates(locName) {{
    if (!locName) return null;
    if (HUB_POSITIONS[locName]) {{
        return HUB_POSITIONS[locName];
    }}
    const dashIdx = locName.indexOf('-');
    if (dashIdx !== -1) {{
        const hA = locName.substring(0, dashIdx);
        const hB = locName.substring(dashIdx + 1);
        if (HUB_POSITIONS[hA] && HUB_POSITIONS[hB]) {{
            return {{
                x: Math.floor((HUB_POSITIONS[hA].x + HUB_POSITIONS[hB].x) / 2),
                y: Math.floor((HUB_POSITIONS[hA].y + HUB_POSITIONS[hB].y) / 2)
            }};
        }}
    }}
    return null;
}}

async function processUpToTurn(targetTurn) {{
    if (targetTurn === 0) return true;

    while (droneStatesHistory.length <= targetTurn) {{
        const turnToProcess = droneStatesHistory.length;
        if (!turnLinesCache.has(turnToProcess)) {{
            const loaded = await loadChunkForTurn(turnToProcess);
            if (!loaded) return false;
        }}

        const line = turnLinesCache.get(turnToProcess);
        const prevTurnState = droneStatesHistory[turnToProcess - 1];
        
        const nextActiveDrones = new Map(prevTurnState.activeDrones);
        let nextStartedCount = prevTurnState.startedCount;
        let nextArrivedCount = prevTurnState.arrivedCount;

        if (line) {{
            const tokens = line.split(/\\s+/);
            tokens.forEach(token => {{
                if (token.startsWith('D')) {{
                    const firstDash = token.indexOf('-');
                    if (firstDash !== -1) {{
                        const dId = token.substring(1, firstDash);
                        const target = token.substring(firstDash + 1);
                        
                        const dIdNum = parseInt(dId, 10);
                        if (!prevTurnState.activeDrones.has(dId) && dIdNum >= prevTurnState.startedCount) {{
                            nextStartedCount = Math.max(nextStartedCount, dIdNum + 1);
                        }}

                        const prevLoc = prevTurnState.activeDrones.get(dId);
                        if (target === GOAL_HUB && prevLoc !== GOAL_HUB) {{
                            nextArrivedCount++;
                        }}
                        
                        nextActiveDrones.set(dId, target);
                    }}
                }}
            }});
        }}

        droneStatesHistory.push({{
            activeDrones: nextActiveDrones,
            startedCount: nextStartedCount,
            arrivedCount: nextArrivedCount
        }});
    }}
    return true;
}}

function setDronePosition(el, x, y, animate = true) {{
    if (animate) {{
        el.classList.add('is-moving');
    }} else {{
        el.classList.remove('is-moving');
    }}
    el.style.left = `${{x}}px`;
    el.style.top = `${{y}}px`;
}}

function createDroneElement(droneId) {{
    const el = document.createElement('div');
    el.id = `drone_${{droneId}}`;
    el.className = 'drone';
    el.textContent = `D${{droneId}}`;
    const colorIdx = Math.abs(parseInt(droneId, 10)) % DRONE_COLORS.length;
    el.style.backgroundColor = DRONE_COLORS[colorIdx];
    // Los drones más recientes quedan por encima de los anteriores en GOAL.
    el.style.zIndex = String(3 + Math.max(0, parseInt(droneId, 10)));
    return el;
}}

function spawnDroneFromStart(droneId, targetX, targetY) {{
    const startCoords = HUB_POSITIONS[START_HUB];
    const el = startDroneNode;

    // El propio elemento que estaba dibujando el drone de START pasa a ser
    // el drone real que sale. No creamos otro elemento encima.
    el.id = `drone_${{droneId}}`;
    el.textContent = `D${{droneId}}`;
    el.className = 'drone';
    el.style.position = 'absolute';
    el.style.left = `${{startCoords.x}}px`;
    el.style.top = `${{startCoords.y}}px`;
    el.style.transform = 'translate(-50%, -50%)';
    el.style.zIndex = String(3 + Math.max(0, parseInt(droneId, 10)));

    const colorIdx = Math.abs(parseInt(droneId, 10)) % DRONE_COLORS.length;
    el.style.backgroundColor = DRONE_COLORS[colorIdx];
    el.classList.remove('is-moving');
    dronesContainer.appendChild(el);

    // El siguiente drone de la cola aparece INMEDIATAMENTE en START;
    // no esperamos a que termine el movimiento del drone que acaba de salir.
    const nextId = parseInt(droneId, 10) + 1;
    const remainingAfterSpawn = Math.max(0, TOTAL_DRONES - nextId);
    const placeholder = document.createElement('div');
    placeholder.id = 'startDroneNode';
    placeholder.className = 'drone';
    placeholder.style.position = 'relative';
    placeholder.style.left = '0';
    placeholder.style.top = '0';
    placeholder.style.transform = 'translate(-50%, -50%)';
    placeholder.style.backgroundColor = DRONE_COLORS[nextId % DRONE_COLORS.length];
    placeholder.innerHTML = `<span id="startDroneLabel">D${{nextId}}</span>`;

    if (remainingAfterSpawn > 0) {{
        startDroneVisual.appendChild(placeholder);
        startDroneNode = placeholder;
        startDroneLabel = placeholder.querySelector('#startDroneLabel');
    }} else {{
        startDroneVisual.style.display = 'none';
        startDroneNode = placeholder;
        startDroneLabel = placeholder.querySelector('#startDroneLabel');
    }}

    void el.offsetWidth;
    setDronePosition(el, targetX, targetY, true);
    return el;
}}

function spawnDroneAtPosition(droneId, x, y) {{
    const el = createDroneElement(droneId);
    el.classList.remove('is-moving');
    el.style.left = `${{x}}px`;
    el.style.top = `${{y}}px`;
    dronesContainer.appendChild(el);
    return el;
}}

function moveDrone(el, targetX, targetY) {{
    // El navegador necesita haber pintado la posición actual antes de aplicar la transición.
    void el.offsetWidth;
    setDronePosition(el, targetX, targetY, true);
}}

function moveDroneBackToStart(el, droneId, turn) {{
    const startCoords = HUB_POSITIONS[START_HUB];
    if (!startCoords || !el) return;

    let done = false;
    const finish = (event) => {{
        if (done || event.propertyName !== 'left') return;
        done = true;
        el.removeEventListener('transitionend', finish);

        if (currentTurn !== turn) return;

        // El drone que estaba esperando en START es el que desaparece al ser
        // tapado. El drone que vuelve es el que debe quedarse allí.
        const startPlaceholder = startDroneNode;
        if (startPlaceholder && startPlaceholder !== el) startPlaceholder.remove();

        el.id = 'startDroneNode';
        el.className = 'drone';
        el.style.position = 'relative';
        el.style.left = '0';
        el.style.top = '0';
        el.style.transform = 'translate(-50%, -50%)';
        el.style.zIndex = '4';
        el.classList.remove('is-moving');

        startDroneVisual.appendChild(el);
        startDroneNode = el;
        startDroneLabel = el;
        startDroneVisual.style.display = 'block';
        el.textContent = `D${{droneId}}`;
    }};

    el.addEventListener('transitionend', finish);
    moveDrone(el, startCoords.x, startCoords.y);
}}

function removeDrone(droneId) {{
    const el = document.getElementById(`drone_${{droneId}}`);
    if (el) {{
        el.remove();
    }}
}}

async function renderTurn(turn) {{
    const sourceTurn = currentTurn;
    const movingBackward = turn < sourceTurn;

    if (turn === 0) {{
        if (!movingBackward) {{
            resetStateToZero();
            updateButtons();
            return true;
        }}
    }} else {{
        const ok = await processUpToTurn(turn);
        if (!ok) return false;
    }}

    const sourceState = droneStatesHistory[sourceTurn] || droneStatesHistory[0];
    const turnState = droneStatesHistory[turn] || droneStatesHistory[0];
    const activeDrones = turnState.activeDrones;
    const startCoords = HUB_POSITIONS[START_HUB];

    // Drones que desaparecen al retroceder: deben volver visualmente desde su
    // posición actual hasta START antes de eliminarse.
    currentTurn = turn;
    localStorage.setItem('flyin_current_turn', String(turn));
    turnDisplay.textContent = `Turn ${{turn}}`;

    const remainingInStart = Math.max(0, TOTAL_DRONES - turnState.startedCount);
    const hasNewStart = !movingBackward && turnState.startedCount > sourceState.startedCount;

    if (movingBackward) {{
        if (remainingInStart > 0) {{
            startDroneVisual.style.display = 'block';
            const nextDroneId = String(turnState.startedCount);
            startDroneLabel.textContent = `D${{nextDroneId}}`;
            const colorIdx = Math.abs(parseInt(nextDroneId, 10)) % DRONE_COLORS.length;
            startDroneNode.style.backgroundColor = DRONE_COLORS[colorIdx];
        }} else {{
            startDroneVisual.style.display = 'none';
        }}
    }} else if (hasNewStart) {{
        // spawnDroneFromStart reutiliza el elemento de START como el drone real
        // y crea el placeholder siguiente inmediatamente.
    }} else {{
        if (remainingInStart > 0) {{
            startDroneVisual.style.display = 'block';
            const nextDroneId = String(turnState.startedCount);
            startDroneLabel.textContent = `D${{nextDroneId}}`;
            const colorIdx = Math.abs(parseInt(nextDroneId, 10)) % DRONE_COLORS.length;
            startDroneNode.style.backgroundColor = DRONE_COLORS[colorIdx];
        }} else {{
            startDroneVisual.style.display = 'none';
        }}
    }}

    // GOAL: el drone anterior permanece visible hasta que el nuevo llega y lo tapa.
    const goalDrones = [];
    activeDrones.forEach((locName, dId) => {{
        if (locName === GOAL_HUB) goalDrones.push(String(dId));
    }});
    goalDrones.sort((a, b) => parseInt(a, 10) - parseInt(b, 10));

    const latestGoalDroneId = goalDrones.length
        ? goalDrones[goalDrones.length - 1]
        : null;

    const previousGoalDrones = Array.from(sourceState.activeDrones.entries())
        .filter(([, loc]) => loc === GOAL_HUB)
        .map(([id]) => String(id))
        .sort((a, b) => parseInt(a, 10) - parseInt(b, 10));

    const previousLatestGoalDroneId = previousGoalDrones.length
        ? previousGoalDrones[previousGoalDrones.length - 1]
        : null;

    const newGoalArrival = !movingBackward && latestGoalDroneId !== null &&
        sourceState.activeDrones.get(latestGoalDroneId) !== GOAL_HUB &&
        activeDrones.get(latestGoalDroneId) === GOAL_HUB;

    const hubOccupancy = {{}};

    // ID del único drone cuyo spawn estamos deshaciendo en esta transición.
    let reverseSpawnId = null;
    if (movingBackward) {{
        const startedIds = Array.from(sourceState.activeDrones.keys())
            .filter(id => !activeDrones.has(id));
        reverseSpawnId = startedIds.length ? startedIds[startedIds.length - 1] : null;
    }}

    activeDrones.forEach((locName, dId) => {{
        const id = String(dId);
        const coords = getCoordinates(locName);
        if (!coords) return;

        // Los drones antiguos de GOAL permanecen ocultos. El único antiguo que
        // conservamos es el que estaba visible justo antes de la llegada actual.
        const preserveOldGoal = newGoalArrival && id === previousLatestGoalDroneId;
        const hiddenGoalDrone = locName === GOAL_HUB && id !== latestGoalDroneId && !preserveOldGoal;
        if (hiddenGoalDrone) return;

        let el = document.getElementById(`drone_${{id}}`);

        if (!el) {{
            if (movingBackward) {{
                // Al retroceder solo recuperamos el drone de ESTA transición,
                // nunca todos los drones ocultos del historial.
                const sourceLoc = sourceState.activeDrones.get(id);
                const sourceCoords = getCoordinates(sourceLoc);
                if (sourceCoords) el = spawnDroneAtPosition(id, sourceCoords.x, sourceCoords.y);
            }} else if (!sourceState.activeDrones.has(id)) {{
                el = spawnDroneFromStart(id, coords.x, coords.y);
            }} else {{
                const sourceLoc = sourceState.activeDrones.get(id);
                const sourceCoords = getCoordinates(sourceLoc);
                const fallback = sourceCoords || coords;
                el = spawnDroneAtPosition(id, fallback.x, fallback.y);
            }}
        }}

        if (!el) return;

        // El drone que acaba de nacer ya sale de START inmediatamente.
        // Los demás se mueven desde su posición actual.
        if (sourceState.activeDrones.has(id) && !(movingBackward && id === reverseSpawnId)) {{
            moveDrone(el, coords.x, coords.y);
        }}

        if (locName !== GOAL_HUB && !locName.includes('-')) {{
            hubOccupancy[locName] = (hubOccupancy[locName] || 0) + 1;
        }}
    }});

    // El anterior de GOAL se elimina únicamente cuando el recién llegado
    // termina SU transición. transitionend funciona incluso si se pulsa Next
    // muy rápido, a diferencia de un timeout fijo de 410ms.
    if (newGoalArrival && previousLatestGoalDroneId !== null) {{
        const arrivingEl = document.getElementById(`drone_${{latestGoalDroneId}}`);
        const coveredEl = document.getElementById(`drone_${{previousLatestGoalDroneId}}`);

        if (arrivingEl && coveredEl) {{
            const onArrival = (event) => {{
                if (event.propertyName !== 'left') return;
                arrivingEl.removeEventListener('transitionend', onArrival);
                if (coveredEl.isConnected) coveredEl.remove();
            }};
            arrivingEl.addEventListener('transitionend', onArrival);
        }}
    }}

    // Al retroceder solo deshacemos el spawn que pertenece a este turno.
    // El drone vuelve a START y, al solapar el placeholder, éste desaparece.
    if (reverseSpawnId !== null) {{
        const el = document.getElementById(`drone_${{reverseSpawnId}}`);
        if (el) moveDroneBackToStart(el, reverseSpawnId, turn);
    }}

    // Limpieza SOLO de elementos que no pertenecen al estado objetivo y que no
    // están haciendo una reversión animada hacia START.
    document.querySelectorAll('#dronesContainer .drone').forEach(el => {{
        const id = el.id.replace('drone_', '');
        if (!activeDrones.has(id) && id !== reverseSpawnId) {{
            removeDrone(id);
        }}
    }});

    hubOccupancy[START_HUB] = (hubOccupancy[START_HUB] || 0) + remainingInStart;

    document.querySelectorAll('.hub-occupancy').forEach(hubEl => {{
        const hubName = hubEl.id.replace('occupancy-', '');
        const maxDrones = hubEl.parentElement.dataset.max;
        const count = hubOccupancy[hubName] || 0;
        hubEl.textContent = `${{count}}/${{maxDrones}}`;
    }});

    updateButtons();
    return true;
}}

function updateButtons() {{
    prevBtn.disabled = isStepping || currentTurn <= 0;
    nextBtn.disabled = isStepping;
}}

async function stepNext() {{
    if (isStepping) return;
    isStepping = true;
    try {{
        const nextTurn = currentTurn + 1;
        const ok = await processUpToTurn(nextTurn);
        if (!ok) {{
            if (isPlaying) togglePlay();
            return;
        }}
        await renderTurn(nextTurn);
    }} finally {{
        isStepping = false;
        updateButtons();
    }}
}}

async function stepPrev() {{
    if (isStepping || currentTurn <= 0) return;
    isStepping = true;
    try {{
        await renderTurn(currentTurn - 1);
    }} finally {{
        isStepping = false;
        updateButtons();
    }}
}}

function togglePlay() {{
    if (isPlaying) {{
        isPlaying = false;
        localStorage.setItem('flyin_is_playing', 'false');
        playBtn.textContent = '▶ Play';
        playBtn.classList.remove('active');
        if (playInterval) clearInterval(playInterval);
    }} else {{
        isPlaying = true;
        localStorage.setItem('flyin_is_playing', 'true');
        playBtn.textContent = '❚❚ Pause';
        playBtn.classList.add('active');
        playInterval = setInterval(async () => {{
            // stepNext() gestiona su propio bloqueo; no lo bloqueemos aquí
            // antes de llamarlo, porque entonces stepNext() retorna sin hacer nada.
            await stepNext();
        }}, 600);
    }}
}}

resetBtn.addEventListener('click', async () => {{
    if (isPlaying) togglePlay();
    resetStateToZero();
    await renderTurn(0);
}});

playBtn.addEventListener('click', togglePlay);
nextBtn.addEventListener('click', () => {{ if (!isPlaying) stepNext(); }});
prevBtn.addEventListener('click', () => {{ if (!isPlaying) stepPrev(); }});

document.addEventListener('keydown', (e) => {{
    if (e.key === 'ArrowRight' && !isPlaying) stepNext();
    if (e.key === 'ArrowLeft' && !isPlaying) stepPrev();
    if (e.key === ' ') {{ e.preventDefault(); togglePlay(); }}
}});

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
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print('Usage: python visualizer.py <map_file> [output_file]')
        sys.exit(1)

    map_file = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) == 3 else 'output.html'

    network_zone = Parser(map_file).parser()

    html = generate_html(network_zone)
    os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
    with open(output_path, 'w') as f:
        f.write(html)
    print(f'Generated visual layout HTML at {output_path}')


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
    except Exception as e:
        print(f'Error: {e}', file=sys.stderr)