import json
import os
import queue
from datetime import datetime
from time import sleep

import psutil

from alarm import Alarm, CPUAlarm, DiskAlarm, MemoryAlarm


def bytes_to_readable(mem: int) -> tuple[float, str]:
    units = ["B", "KB", "MB", "GB", "TB", "PB"]
    d = 1
    count = 0

    while mem >= d * 1024:
        d *= 1024
        count += 1

    return round(mem / d, 1), units[count]


class Monitor:
    def __init__(self) -> None:
        self.alarms = set()
        self.is_active = False
        self.log_to_stdout = False
        self.config_file = os.path.join(os.path.dirname(__file__), "config.json")
        self.queue = queue.Queue()
        self.log_file_name = f"log_{datetime.now().strftime('%Y_%m_%d_%H_%M')}.txt"

        if os.path.exists(self.config_file):
            with open(self.config_file, "r") as fp:
                config = json.load(fp)

                partitions = [x.mountpoint for x in psutil.disk_partitions()]

                print("Laddar tidigare konfigurerade alarm")

                for alarm in config:
                    if (
                        alarm["category"] == "disk"
                        and alarm["mountpoint"] not in partitions
                    ):
                        continue

                    self.alarms.add(
                        {"disk": DiskAlarm, "memory": MemoryAlarm, "cpu": CPUAlarm}[
                            alarm["category"]
                        ](**alarm)
                    )

    def run(self) -> None:
        self.is_active = True

        with open(self.log_file_name, "a") as log_file:
            print(f"{datetime.now().isoformat()} Startar övervakning", file=log_file)

        while True:
            alerts = self.check_alarms()

            with open(self.log_file_name, "a") as log_file:
                for alert in alerts:
                    log_text = (
                        f"{alert['timestamp']} {alert['alarm'].category} alarm triggered, "
                        f"{alert['current_level']} > {alert['alarm'].level}"
                    )

                    print(log_text, file=log_file)

                    if self.log_to_stdout:
                        self.queue.put(alert)

            sleep(5)

    def save_config_file(self) -> None:
        with open(self.config_file, "w") as fp:
            alarm_json = [dict(alarm) for alarm in self.alarms]

            json.dump(alarm_json, fp)

    def toggle_stdout_logging(self) -> None:
        self.log_to_stdout = not self.log_to_stdout

    def get_current_status(self) -> dict:
        cpu_load = psutil.cpu_percent()

        mem = psutil.virtual_memory()

        memory_used, memory_used_unit = bytes_to_readable(mem.used)
        memory_total, memory_total_unit = bytes_to_readable(mem.total)

        disk_info = []

        for disk in psutil.disk_partitions():
            disk_usage = psutil.disk_usage(disk.mountpoint)

            usage_total, usage_total_unit = bytes_to_readable(disk_usage.total)
            usage_used, usage_used_unit = bytes_to_readable(disk_usage.used)

            disk_info.append(
                {
                    "path": disk.mountpoint,
                    "size": f"{usage_total} {usage_total_unit}",
                    "used": f"{usage_used} {usage_used_unit}",
                    "percent": disk_usage.percent,
                }
            )

        return {
            "cpu": cpu_load,
            "memory": {
                "percent": mem.percent,
                "total": f"{memory_total} {memory_total_unit}",
                "used": f"{memory_used} {memory_used_unit}",
            },
            "disk": disk_info,
        }

    def add_alarm(self, alarm_dict: dict) -> Alarm:
        new_alarm = {"disk": DiskAlarm, "memory": MemoryAlarm, "cpu": CPUAlarm}[
            alarm_dict["category"]
        ](**alarm_dict)

        with open(self.log_file_name, "a") as log_file:
            print(
                f"{datetime.now().isoformat()} Nytt alarm skapat: {new_alarm}",
                file=log_file,
            )

        self.alarms.add(new_alarm)

        self.save_config_file()

        return new_alarm

    def remove_alarm(self, al: Alarm) -> None:
        with open(self.log_file_name, "a") as log_file:
            print(f"{datetime.now().isoformat()} Alarm borttaget: {al}", file=log_file)

        self.alarms.discard(al)

        self.save_config_file()

    def check_alarms(self) -> list:
        alerts = [alarm.triggered() for alarm in self.alarms]

        max_alerts = []
        cpu_alerts = [
            alert
            for alert in alerts
            if alert is not None and isinstance(alert["alarm"], CPUAlarm)
        ]
        if len(cpu_alerts) > 0:
            max_alerts.append(max(cpu_alerts, key=lambda alert: alert["alarm"].level))

        memory_alerts = [
            alert
            for alert in alerts
            if alert is not None and isinstance(alert["alarm"], MemoryAlarm)
        ]
        if len(memory_alerts) > 0:
            max_alerts.append(
                max(memory_alerts, key=lambda alert: alert["alarm"].level)
            )

        disk_alerts = [
            alert
            for alert in alerts
            if alert is not None and isinstance(alert["alarm"], DiskAlarm)
        ]
        if len(disk_alerts) > 0:
            partitions = [
                partition.mountpoint for partition in psutil.disk_partitions()
            ]

            for partition in partitions:
                partition_alerts = [
                    alert
                    for alert in disk_alerts
                    if alert["alarm"].partition == partition
                ]

                if len(partition_alerts) > 0:
                    max_alerts.append(
                        max(partition_alerts, key=lambda alert: alert["alarm"].level)
                    )

        return max_alerts


if __name__ == "__main__":
    print(bytes_to_readable(psutil.virtual_memory().total))
    print(bytes_to_readable(psutil.disk_usage("/home").total))
    # mon = Monitor()

    # th = threading.Thread(target=mon.run, daemon=True)
    # th.start()

    # sleep(20)

    # mon.toggle_stdout_logging()

    # sleep(20)
