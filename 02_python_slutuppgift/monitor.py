import json
import os
from datetime import datetime

import psutil
from alarm import CPUAlarm, DiskAlarm, MemoryAlarm


class Monitor:
    # def __init__(
    #     self, cpu_usage: int = 0, memory_usage: int = 0, disk_usage: int = 0
    # ) -> None:
    #     self.alarms = {
    #         "cpu": set(),
    #         "memory": set(),
    #         "disk": set(),
    #     }
    #     self.interval = 60
    #     self.is_active = False

    #     if cpu_usage != 0:
    #         self.alarms["cpu"].add(cpu_usage)

    #     if memory_usage != 0:
    #         self.alarms["memory"].add(memory_usage)

    #     if disk_usage != 0:
    #         self.alarms["disk"].add(disk_usage)
    def __init__(self) -> None:
        self.alarms = set()
        self.is_active = False

        self.file = os.path.join(os.path.dirname(__file__), "config.json")

        if os.path.exists(self.file):
            print("Hittade filen")
            with open(self.file, "r") as fp:
                config = json.load(fp)

                for alarm in config:
                    print("försöker ladda alarm")
                    self.alarms.add(
                        {"disk": DiskAlarm, "memory": MemoryAlarm, "cpu": CPUAlarm}[
                            alarm["category"]
                        ](**alarm)
                    )

    def save_file(self):
        with open(self.file, "w") as fp:
            alarm_json = [alarm.to_json() for alarm in self.alarms]

            json.dump(alarm_json, fp)

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

    def add_alarm(self, alarm_dict: dict) -> None:
        new_alarm = {"disk": DiskAlarm, "memory": MemoryAlarm, "cpu": CPUAlarm}[
            alarm_dict["category"]
        ](**alarm_dict)

        self.alarms.add(new_alarm)

        self.save_file()

    def remove_alarm(self, alarm_dict: dict) -> None:
        al = {"disk": DiskAlarm, "memory": MemoryAlarm, "cpu": CPUAlarm}[
            alarm_dict["category"]
        ](**alarm_dict)

        self.alarms.discard(al)

        self.save_file()

    def check_alarms(self):
        # current_status = self.get_current_status()

        # timestamp = datetime.now()

        alerts = [alarm for alarm in self.alarms if alarm.triggered()]

        # for alarm in self.alarms:
        #     pass
        # for alarm_type, alarm_levels in self.alarms.items():
        #     if alarm_type == "cpu":
        #         cpu_alarms = [
        #             {
        #                 "alarm_level": al,
        #                 "current": current_status["cpu"],
        #                 "alarm_type": alarm_type,
        #                 "timestamp": timestamp,
        #             }
        #             for al in alarm_levels
        #             if current_status["cpu"] >= al
        #         ]

        #         alerts.extend(cpu_alarms)

        #     elif alarm_type == "disk":
        #         for disk in current_status[alarm_type]:
        #             disk_alarms = [
        #                 {
        #                     "alarm_level": al,
        #                     "current": disk["quota"],
        #                     "alarm_type": alarm_type,
        #                     "path": disk["path"],
        #                     "timestamp": timestamp,
        #                 }
        #                 for al in alarm_levels
        #                 if disk["quota"] >= al
        #             ]

        #             alerts.extend(disk_alarms)

        #     elif alarm_type == "memory":
        #         memory_alarms = [
        #             {
        #                 "alarm_level": al,
        #                 "current": current_status["memory"]["percentage"],
        #                 "alarm_type": alarm_type,
        #                 "timestamp": timestamp,
        #             }
        #             for al in alarm_levels
        #             if current_status["memory"]["percentage"] >= al
        #         ]

        #         alerts.extend(memory_alarms)

        return alerts


if __name__ == "__main__":
    mon = Monitor()

    mon.add_alarm({"category": "cpu", "level": 1})
    mon.add_alarm({"category": "disk", "level": 50, "mountpoint": "/"})
    mon.add_alarm({"category": "memory", "level": 25})

    print(f"config.json existerar{'' if os.path.exists('config.json') else ' ej'}")

    alerts = mon.check_alarms()

    print(len(alerts))
