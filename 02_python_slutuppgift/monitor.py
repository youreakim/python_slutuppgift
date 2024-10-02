import json
import os
import socket

import psutil


class Monitor:
    def __init__(
        self, cpu_usage: int = 0, memory_usage: int = 0, disk_usage: int = 0
    ) -> None:
        self.alarms = {
            "cpu": set(),
            "memory": set(),
            "disk": set(),
        }
        self.interval = 60
        self.is_active = False

        self.alarms["cpu"].add(cpu_usage)
        self.alarms["memory"].add(memory_usage)
        self.alarms["disk"].add(disk_usage)

    def activate(self) -> None:
        self.is_active = True

    def get_current_status(self) -> dict:
        cpu_load = psutil.cpu_percent()

        memory_percentage = psutil.virtual_memory().percent
        memory_used = psutil.virtual_memory().used
        memory_total = psutil.virtual_memory().total

        disk_info = []

        for disk in psutil.disk_partitions():
            disk_usage = psutil.disk_usage(disk.mountpoint)

            disk_info.append(
                {
                    "path": disk.mountpoint,
                    "size": disk_usage.total,
                    "used": disk_usage.used,
                    "quota": disk_usage.percent,
                }
            )

        return {
            "cpu": cpu_load,
            "memory": {
                "percentage": memory_percentage,
                "total": memory_total,
                "used": memory_used,
            },
            "disk": disk_info,
        }

    def add_alarm(self, what: str, value: int) -> None:
        self.alarms[what].add(value)

    def remove_alarm(self, what: str, value: int) -> None:
        self.alarms[what].remove(value)

    def check_alarms(self):
        current_status = self.get_current_status()

        cpu_alarms, disk_alarms, memory_alarms = [], [], []

        for alarm in self.alarms:
            if alarm == "cpu":
                cpu_alarms = [
                    {"alarm": al, "current": current_status["cpu"]}
                    for al in self.alarms[alarm]
                    if current_status["cpu"] >= al
                ]

            elif alarm == "disk":
                pass

            elif alarm == "memory":
                memory_alarms = [
                    {"alarm": al, "current": current_status["memory"]["percentage"]}
                    for al in self.alarms[alarm]
                    if current_status["memory"]["percentage"] >= al
                ]

        return {"cpu": cpu_alarms, "disk": disk_alarms, "memory": memory_alarms}


if __name__ == "__main__":
    mon = Monitor()

    print(f"{'activated' if mon.is_active else 'not active'}")

    mon.activate()

    print(f"{'activated' if mon.is_active else 'not active'}")

    print(mon.get_current_status())
