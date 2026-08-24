#!/usr/bin/env python3
from parser import Parser
from network_zone import NetworkZone
from route_planner import RoutePlanner

TARGETS: dict[str, int] = {
    'easy/01_linear_path': 6,
    'easy/02_simple_fork': 8,
    'easy/03_basic_capacity': 6,
    'medium/01_dead_end_trap': 12,
    'medium/02_circular_loop': 15,
    'medium/03_priority_puzzle': 12,
    'hard/01_maze_nightmare': 30,
    'hard/02_capacity_hell': 35,
    'hard/03_ultimate_challenge': 45,
    'challenger/01_the_impossible_dream': 45,
}


def test_maps():
    maps: list[str] = [
        'easy/01_linear_path',
        'easy/02_simple_fork',
        'easy/03_basic_capacity',
        'medium/01_dead_end_trap',
        'medium/02_circular_loop',
        'medium/03_priority_puzzle',
        'hard/01_maze_nightmare',
        'hard/02_capacity_hell',
        'hard/03_ultimate_challenge',
        'challenger/01_the_impossible_dream',
    ]
    passed: int = 0
    failed: int = 0
    for path in maps:
        try:
            map: NetworkZone = Parser(f'./maps/{path}.txt').parser()
            planner = RoutePlanner(map)
            ok: bool = all(drone.current_zone == map.end for drone in planner.drone_list)
            turns: int = max((max(drone.route.keys()) + 1) for drone in planner.drone_list)
            target: int = TARGETS.get(path, 0)
            perf: str = 'PASS' if turns < target else 'OVER'
            if ok:
                passed += 1
                print(f'OK   {path}: {len(planner.drone_list)} drones, {turns} turns (target: {target}) {perf}')
            else:
                failed += 1
                print(f'FAIL {path}: {len(planner.drone_list)} drones, {turns} turns — not all drones reached the end')
        except Exception as e:
            failed += 1
            print(f'FAIL {path}: {type(e).__name__} — {e}')
    print(f'\n{passed}/{passed + failed} maps passed')


def main():
    test_maps()


if __name__ == "__main__":
    main()