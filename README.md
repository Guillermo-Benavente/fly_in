*This project has been created as part of the 42 curriculum by gbenaven.*

# Fly-In — Drone Network Route Planner & Visualizer

## Description

**Fly-In** is an algorithmic and visual solution designed to simulate, plan, and optimize the traffic of a fleet of drones across a restricted connectivity network. 

The main objective is to move $N$ drones from a starting point (start hub) to a destination point (end hub) in the **fewest number of turns possible**, while respecting all physical and operational network constraints:
* **Maximum Hub Capacity (`max_drones`):** Simultaneous limit of drones allowed to occupy a node.
* **Maximum Link Capacity (`max_link_capacity`):** Limit of drones that can cross a connection within the same turn.
* **Special Zones:** Restricted zones (non-traversable) and priority zones (preferred routes).

The project consists of a Python core responsible for graph modeling and traffic conflict resolution, accompanied by an interactive web visualization tool to audit drone behaviors turn by turn.

---

## Technical Choices & Algorithm Strategy

To solve the massive drone traffic routing problem without incurring collisions or bottlenecks, the software architecture is split into three distinct stages:

### 1. Mapping and Distance Calculation (`Mapper`)
Instead of blindly calculating individual paths for each drone, the system constructs a **distance vector field** over the graph topology:
* **Reverse BFS from Destination:** Starting from the target node, a Breadth-First Search (BFS) is executed backwards. This assigns each node a `remaining_cost` value representing the exact number of turns required to reach the destination via the shortest path available.
* **Route Prioritization:** An additional pass accounts for how many `PRIORITY` zones are traversed along optimal paths (`priority_count`), breaking ties between alternative paths with equal turn costs.

### 2. Route Planning and Traffic Control (`RoutePlanner`)
The planning engine simulates the system deterministically turn by turn:
* **Dynamic Dispatch:** Each turn, active drones navigate toward adjacent nodes with the lowest `remaining_cost`.
* **Congestion Resolution:** When optimal routes become saturated due to hub or link limits, the `RoutePlanner` reroutes excess drones toward alternative paths with the next best `remaining_cost`, or holds a drone in place for one turn if waiting is more efficient than taking a long detour.

---

## Visual Representation & User Experience

The `visualizer.py` script transforms textual simulation logs into a self-contained, interactive **HTML/CSS/JS web dashboard**, enhancing debugging and presentation:

* **Smooth Interpolation (CSS Animations):** Translates discrete turn movements into fluid animations using dynamically generated `@keyframes` based on scheduled drone trajectories.
* **Dual Execution Modes (Auto vs. Manual):**
  * **Automatic Mode:** Plays back the complete fleet movement at constant speed in a visual loop.
  * **Manual Mode:** Enables step-by-step navigation (via UI buttons or keyboard arrow keys `←` and `→`), inspecting node occupancies and link usage in real time.
* **Enhanced Visual Feedback:**
  * Color-coded hub categories (Restricted, Priority, Start, and End).
  * Dynamic occupancy indicators `[occupancy / max_drones]` rendered beneath each node.
  * SVG link renders displaying maximum link capacities.

---

## Instructions

### Prerequisites
* Python 3.10+ with a virtual environment configured with compatibility dependencies (handling `StrEnum`).
* GNU Make.

### Compilation and Environment Setup
Build the virtual environment and ensure all dependencies are met:

```bash
make
```

### 1. Running the Main Simulation
To calculate paths and output the drone traffic turn-by-turn to standard output:

```bash
# Run with a specific map file
make run MAP=maps/easy/01_linear_path.txt
```

### 2. Generating the Graphical Visualization
To render the interactive HTML visualization file:

```bash
# Generate visual output (defaults to output.html)
make visualize MAP=maps/easy/01_linear_path.txt
```

### 3. Cleanup Rules

```bash
# Clean temporary files and cached outputs
make clean

# Remove virtual environment and generated artifacts
make fclean

# Rebuild project environment
make re
```

---

---

## Example Input and Output

### Example Map File (`map.txt`)
```text
# Map configuration
nb_drones: 2

start_hub: start 0 0 [color=green]
hub: waypoint1 1 0 [color=blue]
hub: waypoint2 2 0 [color=blue]
end_hub: goal 3 0 [color=red]

connection: start-waypoint1
connection: waypoint1-waypoint2
connection: waypoint2-goal
```

### Example Console Output (`fly_in.py`)
```text
D0-waypoint1
D0-waypoint2 D1-waypoint1
D0-goal D1-waypoint2
D1-goal
```

---

## Resources

### Traditional References
* **Breadth-First Search (BFS):** [GeeksforGeeks - BFS for a Graph](https://www.geeksforgeeks.org/breadth-first-search-or-bfs-for-a-graph/)
* **CSS Animations & Keyframe Specification:** [MDN Web Docs - @keyframes](https://developer.mozilla.org/en-US/docs/Web/CSS/@keyframes)

### AI Usage Statement
In compliance with academic guidelines, the use of AI tools during project development is detailed below:
* **Use Cases:**
  * **Code Documentation:** Generation and standardization of Google/PEP 257 docstrings across all project modules (`Mapper`, `RoutePlanner`, `visualizer.py`, etc.).
  * **Refactoring & Code Quality:** Reviewing variable naming conventions, static typing annotations, and screen coordinate resolution logic for HTML visualization rendering.
  * **README Authoring:** Structuring technical descriptions, architectural explanations, and Markdown layout.
* **Manually Developed Components:** The core routing algorithm logic, graph data structures, and overall software architecture were designed and implemented manually by the author.