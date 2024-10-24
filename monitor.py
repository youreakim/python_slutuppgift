import json
import os
from time import sleep

import psutil
from alarm import Alarm, CPUAlarm, DiskAlarm, MemoryAlarm


def bytes_to_readable(mem):
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
        # self.is_active = False
        self.log_to_stdout = False
        self.config_file = os.path.join(os.path.dirname(__file__), "config.json")

        if os.path.exists(self.config_file):
            with open(self.config_file, "r") as fp:
                config = json.load(fp)

                for alarm in config:
                    self.alarms.add(
                        {"disk": DiskAlarm, "memory": MemoryAlarm, "cpu": CPUAlarm}[
                            alarm["category"]
                        ](**alarm)
                    )

    def run(self) -> None:
        while True:
            alerts = self.check_alarms()

            with open("log.txt", "a") as log_file:
                for alert in alerts:
                    log_text = (
                        f"{alert['timestamp']} {alert['category']} alarm triggered, "
                        f"{alert['current_level']} > {alert['level']}"
                    )

                    print(log_text, file=log_file)

                    if self.log_to_stdout:
                        print(log_text)

            sleep(5)

    def save_config_file(self) -> None:
        with open(self.config_file, "w") as fp:
            alarm_json = [dict(alarm) for alarm in self.alarms]

            json.dump(alarm_json, fp)

    def toggle_stdout_logging(self) -> None:
        self.log_to_stdout = not self.log_to_stdout

    def get_current_status(self) -> dict:
        cpu_load = psutil.cpu_percent()

        memory_percentage = psutil.virtual_memory().percent
        memory_used, memory_used_unit = bytes_to_readable(psutil.virtual_memory().used)
        memory_total, memory_total_unit = bytes_to_readable(
            psutil.virtual_memory().total
        )

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
                "percent": memory_percentage,
                "total": f"{memory_total} {memory_total_unit}",
                "used": f"{memory_used} {memory_used_unit}",
            },
            "disk": disk_info,
        }

    def add_alarm(self, alarm_dict: dict) -> None:
        new_alarm = {"disk": DiskAlarm, "memory": MemoryAlarm, "cpu": CPUAlarm}[
            alarm_dict["category"]
        ](**alarm_dict)

        self.alarms.add(new_alarm)

        self.save_config_file()

    def remove_alarm(self, al: Alarm) -> None:
        self.alarms.discard(al)

        self.save_config_file()

    def check_alarms(self) -> list:
        alerts = [alarm.triggered() for alarm in self.alarms]

        return [alert for alert in alerts if alert is not None]


if __name__ == "__main__":
    print(bytes_to_readable(psutil.virtual_memory().total))
    print(bytes_to_readable(psutil.disk_usage("/home").total))
    # mon = Monitor()

    # th = threading.Thread(target=mon.run, daemon=True)
    # th.start()

    # sleep(20)

    # mon.toggle_stdout_logging()

    # sleep(20)
