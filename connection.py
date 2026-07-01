from hub import Hub


class Connection():
    init_hub: Hub
    final_hub: Hub
    metadata: dict[str,str]