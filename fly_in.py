#!/usr/bin/env python3
from parser import Parser
from network_zone import NetworkZone
from route_planner import RoutePlanner


def main():
    map: NetworkZone = Parser('./maps/easy/01_linear_path.txt').paser()
    RoutePlanner(map)

if __name__ == "__main__":
    main()