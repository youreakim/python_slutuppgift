"""Contains class to monitor system resources and alert if certain alarms are triggered."""

import json
import os
import queue
from datetime import datetime
from time import sleep

import psutil

from alarm import Alarm, CPUAlarm, DiskAlarm, MemoryAlarm


class Monitor:
    """Maintains a list of alarms and checks if any of them are triggered at regular intervals."""

    def __init__(self) -> None:
        self.alarms = set()
        self.is_active = False
        self.send_to_queue = False
        self.config_file = os.path.join(os.path.dirname(__file__), "config.json")
        self.queue = queue.Queue()
        self.log_file_name = f"log_{datetime.now().strftime('%Y_%m_%d_%H_%M')}.txt"

        if os.path.exists(self.config_file):
            with open(self.config_file, "r") as fp:
                config = json.load(fp)

                partitions = [x.mountpoint for x in psutil.disk_partitions()]

                print("Laddar tidigare konfigurerade alarm")

                for alarm in config:
                    # check to see that the mountpoint exists, if not skip that alarm
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
        """Starts the monitoring, checks the alarms every five seconds and writes alerts to a log
        file, and if sent to the queue if that is set to True"""
        self.is_active = True

        with open(self.log_file_name, "a") as log_file:
            print(f"{datetime.now().isoformat()} Startar övervakning", file=log_file)

        while True:
            alerts = self.check_alarms()

            with open(self.log_file_name, "a") as log_file:
                for alert in alerts:
                    log_text = (
                        f"{alert['timestamp']} {alert['alarm'].category} larm aktiverat, "
                        f"nuvarande nivå {alert['current_level']}% överstiger "
                        f"konfigurerad nivå {alert['alarm'].level}%"
                        f"{' för partition ' + alert['alarm'].mountpoint if alert['alarm'].category == 'disk' else ''}"
                    )

                    print(log_text, file=log_file)

                    if self.send_to_queue:
                        self.queue.put(alert)

            sleep(5)

    def save_config_file(self) -> None:
        """Saves currently configured alarms to a file."""
        with open(self.config_file, "w") as fp:
            alarm_json = [dict(alarm) for alarm in self.alarms]

            json.dump(alarm_json, fp)

    def get_current_status(self) -> dict:
        """Returns the current system load for CPU, memory and disk partitions."""
        cpu_load = psutil.cpu_percent()

        mem = psutil.virtual_memory()

        disk_info = []

        for disk in psutil.disk_partitions():
            disk_usage = psutil.disk_usage(disk.mountpoint)

            disk_info.append(
                {
                    "path": disk.mountpoint,
                    "size": disk_usage.total,
                    "used": disk_usage.used,
                    "percent": disk_usage.percent,
                }
            )

        return {
            "cpu": cpu_load,
            "memory": {"percent": mem.percent, "total": mem.total, "used": mem.used},
            "disk": disk_info,
        }

    def add_alarm(self, alarm_dict: dict) -> Alarm:
        new_alarm = {"disk": DiskAlarm, "memory": MemoryAlarm, "cpu": CPUAlarm}[
            alarm_dict["category"]
        ](**alarm_dict)

        self.alarms.add(new_alarm)

        self.save_config_file()

        with open(self.log_file_name, "a") as log_file:
            print(
                f"{datetime.now().isoformat()} Nytt alarm skapat: {new_alarm}",
                file=log_file,
            )

        return new_alarm

    def remove_alarm(self, al: Alarm) -> None:
        self.alarms.discard(al)

        self.save_config_file()

        with open(self.log_file_name, "a") as log_file:
            print(f"{datetime.now().isoformat()} Alarm borttaget: {al}", file=log_file)

    def check_alarms(self) -> list:
        """Checks all configured alarms and returns just the highest triggered for each
        category."""
        alerts = [alarm.check_alarm() for alarm in self.alarms]

        max_alerts = []
        cpu_alerts = [
            alert
            for alert in alerts
            if alert is not None and isinstance(alert["alarm"], CPUAlarm)
        ]
        if len(cpu_alerts) > 0:
            max_alerts.append(max(cpu_alerts, key=lambda alert: alert["alarm"]))

        memory_alerts = [
            alert
            for alert in alerts
            if alert is not None and isinstance(alert["alarm"], MemoryAlarm)
        ]
        if len(memory_alerts) > 0:
            max_alerts.append(max(memory_alerts, key=lambda alert: alert["alarm"]))

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
                    if alert["alarm"].mountpoint == partition
                ]

                if len(partition_alerts) > 0:
                    max_alerts.append(
                        max(partition_alerts, key=lambda alert: alert["alarm"])
                    )

        return max_alerts
