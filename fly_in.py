#!/usr/bin/env python3
import sys
from hub import TypeConsoleColor as TCC
from network_zone import NetworkZone
from parser import Parser
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


def test_maps() -> None:
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
            map_data: NetworkZone = Parser(f'./maps/{path}.txt').parser()
            planner = RoutePlanner(map_data)
            ok: bool = all(drone.current_zone == map_data.end for drone in planner.drone_list)
            turns: int = max((max(drone.route.keys()) + 1) for drone in planner.drone_list)
            target: int = targets.get(path, 0)
            perf: str = f'{TCC.LIME}PASS{TCC.RESET}' if turns <= target else f'{TCC.RED}OVER{TCC.RESET}'
            if ok:
                passed += 1
                print(f'OK   {perf} | {path}: {len(planner.drone_list)} drones, {turns} turns (target: {target})')
            else:
                failed += 1
                print(f'FAIL      | {path}: {len(planner.drone_list)} drones, {turns} turns — not all drones reached the end')
        except Exception as e:
            failed += 1
            print(f'FAIL      | {path}: {type(e).__name__} — {e}')
    print(f'\n{passed}/{passed + failed} maps passed')


def print_options() -> None:
    print(TCC.CYAN)
    print('+----------Legend----------+')
    print(f'|  {TCC.GREEN}EASY {TCC.YELLOW}MEDIUM {TCC.RED}HARD {TCC.ORANGE}EXTRA  {TCC.CYAN}|')
    print('+----Select your option----+')
    print(f'| {TCC.PURPLE}1: {TCC.GREEN}linear_path           {TCC.CYAN}|')
    print(f'| {TCC.PURPLE}2: {TCC.GREEN}simple_fork           {TCC.CYAN}|')
    print(f'| {TCC.PURPLE}3: {TCC.GREEN}basic_capacity        {TCC.CYAN}|')
    print(f'| {TCC.PURPLE}4: {TCC.YELLOW}dead_end_trap         {TCC.CYAN}|')
    print(f'| {TCC.PURPLE}5: {TCC.YELLOW}circular_loop         {TCC.CYAN}|')
    print(f'| {TCC.PURPLE}6: {TCC.YELLOW}priority_puzzle       {TCC.CYAN}|')
    print(f'| {TCC.PURPLE}7: {TCC.RED}maze_nightmare        {TCC.CYAN}|')
    print(f'| {TCC.PURPLE}8: {TCC.RED}capacity_hell         {TCC.CYAN}|')
    print(f'| {TCC.PURPLE}9: {TCC.RED}ultimate_challenge    {TCC.CYAN}|')
    print(f'| {TCC.PURPLE}10: {TCC.ORANGE}the_impossible_dream {TCC.CYAN}|')
    print(f'| {TCC.GOLD}q: Exit                  {TCC.CYAN}|')
    print('+--------------------------+')
    print(TCC.RESET)


def run_interactive_menu() -> None:
    map_options: dict[str, TypeMap] = {str(i): map_enum for i, map_enum in enumerate(TypeMap, start=1)}

    while True:
        test_maps()
        print_options()
        map_select: str = input('Select map (1-10 or q): ').strip().lower()
        if map_select == 'q':
            break
        if map_select in map_options:
            selected_path = map_options[map_select]
            try:
                network_map: NetworkZone = Parser(f'./maps/{selected_path}.txt').parser()
                planner = RoutePlanner(network_map)
                print(f'\n--- Output para {selected_path} ---')
                print(planner.output())
            except Exception as e:
                print(f'{TCC.RED}Error processing the map: {e}{TCC.RESET}')
            input(f'\n{TCC.YELLOW}Press Enter to return to the menu...{TCC.RESET}')
        else:
            print(f'\n{TCC.RED}Invalid option. Please enter a number between 1 and {len(map_options)} or "q" to exit.{TCC.RESET}')
            input(f'{TCC.YELLOW}Press Enter to try again...{TCC.RESET}')


def run_single_map(map_path: str) -> None:
    network_map: NetworkZone = Parser(map_path).parser()
    planner = RoutePlanner(network_map)
    print(planner.output())


def main() -> None:
    if len(sys.argv) == 2 and sys.argv[1] != '--interactive':
        try:
            run_single_map(sys.argv[1])
        except Exception as e:
            print(f'Error: {e}', file=sys.stderr)
            sys.exit(1)
    else:
        run_interactive_menu()


if __name__ == '__main__':
    main()