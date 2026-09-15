*This project has been created as part of the 42 curriculum by gbenaven.*

# Fly-In — Drone Network Route Planner & Visualizer

## Description

**Fly-In** is a Python-based route planning and simulation system for managing a fleet of drones travelling through a constrained network of hubs and connections.

The main objective is to move all drones from a starting hub to a destination hub while minimizing the number of simulation turns and respecting the constraints defined by the network.

The network can include:

* **Hub capacity:** the maximum number of drones that can occupy a hub at the same time, controlled by `max_drones`.
* **Connection capacity:** the maximum number of drones that can use a connection during the same turn, controlled by `max_link_capacity`.
* **Zone types:**

  * `normal`: standard traversal cost.
  * `priority`: standard traversal cost with priority when selecting between equivalent routes.
  * `restricted`: requires additional traversal time.
  * `blocked`: cannot be traversed.
* **Multiple possible routes:** drones dynamically select routes according to the current network state and available capacity.

The project is divided into several components responsible for parsing the input map, modelling the network as a graph, calculating route costs, simulating drone movements, and generating an interactive visualization.

---

## Algorithm & Implementation Strategy

The routing system uses a graph-based representation of the network.

### 1. Network Parsing

The input map is parsed by `Parser`, which converts the configuration file into a `NetworkZone` containing:

* the number of drones;
* the start hub;
* the destination hub;
* intermediate hubs;
* network connections;
* hub and connection metadata.

The parser also validates the input and rejects invalid configurations such as duplicated hubs, duplicated coordinates, invalid metadata, invalid connections, or missing required elements.

### 2. Graph Construction

`Mapper` converts the network topology into a graph of `MapNode` objects.

Each node stores information about:

* its associated hub;
* neighbouring nodes;
* the minimum remaining traversal cost;
* the maximum number of drones allowed;
* the number of priority zones associated with an optimal path.

Connections are stored independently with their corresponding capacity limits.

### 3. Remaining-Cost Calculation

Instead of calculating an independent route for every drone, the mapper calculates the minimum remaining traversal cost from every reachable hub to the destination.

The calculation starts from the destination and propagates costs backwards through the graph using a queue-based cost relaxation process.

Each zone contributes a traversal cost:

| Zone       |            Cost |
| ---------- | --------------: |
| Normal     |               1 |
| Priority   |               1 |
| Restricted |               2 |
| Blocked    | Not traversable |

This creates a cost field that allows drones to make local routing decisions while still progressing towards a globally optimal destination.

### 4. Priority Path Selection

When multiple paths have the same traversal cost, the mapper calculates a `priority_count` for nodes belonging to optimal paths.

This value is later used by the route planner to prefer paths containing priority zones when the estimated remaining cost is equivalent.

### 5. Turn-Based Drone Simulation

`RoutePlanner` performs the simulation one turn at a time.

For every active drone, the planner:

1. Identifies its available neighbouring nodes.
2. Removes blocked or capacity-limited destinations.
3. Checks the capacity of the corresponding connection.
4. Selects the best remaining candidate according to the routing heuristics.
5. Updates hub occupancy and connection usage.
6. Records the resulting movement.

The selection process considers:

* remaining traversal cost;
* priority path count;
* hub occupancy;
* connection capacity;
* the drone's position in the current turn.

If no valid movement is available, the drone remains in its current position until a valid movement becomes possible.

A safety limit is also used to detect situations where drones become stuck in an infinite routing loop.

---

## Project Structure

```text
.
├── connection.py       # Connection model and validation
├── drone.py            # Drone model
├── hub.py              # Hub model and zone definitions
├── mapper.py           # Graph construction and route cost calculation
├── network_zone.py     # Network topology container
├── parser.py           # Input map parser and validation
├── route_planner.py    # Drone routing and simulation
├── fly_in.py           # Main CLI entry point
└── Makefile            # Build and execution commands
```

---

## Instructions

### Prerequisites

* Python 3.10 or later.
* GNU Make.
* Python dependencies listed by the project environment.

### Installation

Create the project environment and install the required dependencies with:

```bash
make
```

### Run the Simulation

To run a map and display the drone movements in the terminal:

```bash
make run MAP=maps/easy/01_linear_path.txt
```

The program outputs the movements turn by turn.

### Cleanup

Remove temporary files and generated outputs:

```bash
make clean
```

Remove the virtual environment and generated artifacts:

```bash
make fclean
```

Rebuild the project environment:

```bash
make re
```

---

## Input Format

A map is described using configuration directives.

### Example

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

The main directives are:

| Directive    | Purpose                            |
| ------------ | ---------------------------------- |
| `nb_drones`  | Number of drones in the simulation |
| `start_hub`  | Starting hub                       |
| `end_hub`    | Destination hub                    |
| `hub`        | Intermediate hub                   |
| `connection` | Connection between two hubs        |

Optional metadata can be used to configure hub and connection behaviour, including zone type, colour, hub capacity, and connection capacity.

---

## Example Input and Output

Given the following map:

```text
nb_drones: 2
start_hub: start 0 0
hub: waypoint1 1 0
hub: waypoint2 2 0
end_hub: goal 3 0

connection: start-waypoint1
connection: waypoint1-waypoint2
connection: waypoint2-goal
```

The simulation may produce:

```text
D0-waypoint1
D0-waypoint2 D1-waypoint1
D0-goal D1-waypoint2
D1-goal
```

Each line represents one simulation turn.

For example:

```text
D0-waypoint2 D1-waypoint1
```

means that during that turn:

* Drone `D0` moves to `waypoint2`.
* Drone `D1` moves to `waypoint1`.

The output therefore provides a compact representation of the complete simulation timeline.

---

## Resources

### Traditional References

* **Graph traversal and shortest-path algorithms:** Breadth-first search and graph traversal concepts were used as references when designing the network cost calculation.

### AI Usage

AI tools were used as development assistance for specific tasks during the project:

* **Code documentation:** reviewing and standardizing Python docstrings according to PEP 257 and Google-style conventions.
* **Code quality:** reviewing naming, typing, and general code organization.
* **Visualization:** reviewing parts of the HTML/SVG visualization implementation and suggesting improvements.
* **README:** assisting with the structure, wording, and technical documentation of this file.

The core routing algorithm, graph structures, simulation logic, and overall project architecture were designed and implemented by the author.
