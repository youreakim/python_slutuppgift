import json
import os
import socket
from datetime import datetime

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

        if cpu_usage != 0:
            self.alarms["cpu"].add(cpu_usage)

        if memory_usage != 0:
            self.alarms["memory"].add(memory_usage)

        if disk_usage != 0:
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

        print(self.alarms)

    def remove_alarm(self, what: str, value: int) -> None:
        self.alarms[what].remove(value)

        print(self.alarms)

    def check_alarms(self):
        current_status = self.get_current_status()

        timestamp = datetime.now()

        alerts = []

        for alarm_type, alarm_levels in self.alarms.items():
            if alarm_type == "cpu":
                cpu_alarms = [
                    {
                        "alarm_level": al,
                        "current": current_status["cpu"],
                        "alarm_type": alarm_type,
                        "timestamp": timestamp,
                    }
                    for al in alarm_levels
                    if current_status["cpu"] >= al
                ]

                alerts.extend(cpu_alarms)

            elif alarm_type == "disk":
                for disk in current_status[alarm_type]:
                    disk_alarms = [
                        {
                            "alarm_level": al,
                            "current": disk["quota"],
                            "alarm_type": alarm_type,
                            "path": disk["path"],
                            "timestamp": timestamp,
                        }
                        for al in alarm_levels
                        if disk["quota"] >= al
                    ]

                    alerts.extend(disk_alarms)

            elif alarm_type == "memory":
                memory_alarms = [
                    {
                        "alarm_level": al,
                        "current": current_status["memory"]["percentage"],
                        "alarm_type": alarm_type,
                        "timestamp": timestamp,
                    }
                    for al in alarm_levels
                    if current_status["memory"]["percentage"] >= al
                ]

                alerts.extend(memory_alarms)

        return alerts


if __name__ == "__main__":
    mon = Monitor()

    print(f"{'activated' if mon.is_active else 'not active'}")

    mon.activate()

    print(f"{'activated' if mon.is_active else 'not active'}")

    print(mon.get_current_status())
