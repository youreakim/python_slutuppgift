import json
import os
import socket

import psutil


class Supervisor:
    def __init__(
        self, cpu_usage: int = 0, memory_usage: int = 0, disk_usage: int = 0
    ) -> None:
        self.usage = {
            "cpu": [cpu_usage],
            "memory": [memory_usage],
            "disk": [disk_usage],
        }
        self.interval = 60
