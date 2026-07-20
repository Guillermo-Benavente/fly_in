#!/usr/bin/env python3
from parser import Parser
from network_zone import NetworkZone
from route_planner import RoutePlanner


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
            map: NetworkZone = Parser(f'./maps/{path}.txt').paser()
            planner = RoutePlanner(map)
            ok: bool = all(drone.current_zone == map.end for drone in planner.drone_list)
            if ok:
                passed += 1
                print(f'OK  {path}: {len(planner.drone_list)} drones reached the end')
            else:
                failed += 1
                print(f'FAIL {path}: not all drones reached the end')
        except Exception as e:
            failed += 1
            print(f'FAIL {path}: {type(e).__name__} — {e}')
    print(f'\n{passed}/{passed + failed} maps passed')


def main():
    test_maps()


if __name__ == "__main__":
    main()