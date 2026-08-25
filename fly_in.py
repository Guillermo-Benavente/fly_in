#!/usr/bin/env python3
from parser import Parser
from network_zone import NetworkZone
from route_planner import RoutePlanner
from strenum import StrEnum


class TypeMap(StrEnum):
    EASY_01 = 'easy/01_linear_path'
    EASY_02 = 'easy/02_simple_fork'
    EASY_03 = 'easy/03_basic_capacity'
    MEDIUM_01 = 'medium/01_dead_end_trap'
    MEDIUM_02 = 'medium/02_circular_loop'
    MEDIUM_03 = 'medium/03_priority_puzzle'
    HARD_01 = 'hard/01_maze_nightmare'
    HARD_02 = 'hard/02_capacity_hell'
    HARD_03 = 'hard/03_ultimate_challenge'
    CHALLENGER = 'challenger/01_the_impossible_dream'


def test_maps():
    targets: dict[str, int] = {
        TypeMap.EASY_01: 6,
        TypeMap.EASY_02: 8,
        TypeMap.EASY_03: 6,
        TypeMap.MEDIUM_01: 12,
        TypeMap.MEDIUM_02: 15,
        TypeMap.MEDIUM_03: 12,
        TypeMap.HARD_01: 30,
        TypeMap.HARD_02: 35,
        TypeMap.HARD_03: 45,
        TypeMap.CHALLENGER: 45,
    }
    passed: int = 0
    failed: int = 0
    for path in [map for map in TypeMap]:
        try:
            map: NetworkZone = Parser(f'./maps/{path}.txt').parser()
            planner = RoutePlanner(map)
            ok: bool = all(drone.current_zone == map.end for drone in planner.drone_list)
            turns: int = max((max(drone.route.keys()) + 1) for drone in planner.drone_list)
            target: int = targets.get(path, 0)
            perf: str = 'PASS' if turns <= target else 'OVER'
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
    print('\033[32m')
    print('+----Select your option----+')
    print('| 1: linear_path           |')
    print('| 2: simple_fork           |')
    print('| 3: basic_capacity        |')
    print('| 4: dead_end_trap         |')
    print('| 5: circular_loop         |')
    print('| 6: priority_puzzle       |')
    print('| 7: maze_nightmare        |')
    print('| 8: capacity_hell         |')
    print('| 9: ultimate_challenge    |')
    print('| 10: the_impossible_dream |')
    print('+--------------------------+')
    print('\033[0m')
    input('Select map: ')


if __name__ == "__main__":
    main()