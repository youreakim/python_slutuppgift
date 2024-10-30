from abc import ABC, abstractmethod
from datetime import datetime

import psutil


class Alarm(ABC):
    @abstractmethod
    def triggered(self) -> dict | None:
        pass


class MemoryAlarm(Alarm):
    def __init__(self, category, level) -> None:
        self.category = category
        self.level = level

    def __eq__(self, other):
        return isinstance(other, type(self)) and self.level == other.level

    def __gt__(self, other):
        return self.category == other.category and self.level > other.level

    def __lt__(self, other):
        return other.__gt__(self)

    def __hash__(self):
        return hash((self.category, self.level))

    def __str__(self):
        return f"{self.category.capitalize()} larm: {self.level}%"

    def __iter__(self):
        for key in self.__dict__:
            yield key, getattr(self, key)

    def triggered(self):
        current_level = psutil.virtual_memory().percent
        if current_level >= self.level:
            alert = {
                "alarm": self,
                "timestamp": datetime.now().isoformat(),
                "current_level": current_level,
            }

            return alert

        return None


class CPUAlarm(Alarm):
    def __init__(self, category, level):
        self.category = category
        self.level = level

    def __eq__(self, other):
        return isinstance(other, type(self)) and self.level == other.level

    def __gt__(self, other):
        return self.category == other.category and self.level > other.level

    def __lt__(self, other):
        return other.__gt__(self)

    def __hash__(self):
        return hash((self.category, self.level))

    def __str__(self):
        return f"{self.category.capitalize()} larm: {self.level}%"

    def __iter__(self):
        for key in self.__dict__:
            yield key, getattr(self, key)

    def triggered(self):
        current_level = psutil.cpu_percent()
        if current_level >= self.level:
            alert = {
                "alarm": self,
                "timestamp": datetime.now().isoformat(),
                "current_level": current_level,
            }

            return alert

        return None


class DiskAlarm(Alarm):
    def __init__(self, category, level, mountpoint):
        self.category = category
        self.level = level
        self.mountpoint = mountpoint

    def __eq__(self, other):
        return (
            isinstance(other, type(self))
            and self.mountpoint == other.mountpoint
            and self.level == other.level
        )

    def __gt__(self, other):
        return (
            self.category == other.category
            and self.mountpoint == other.mountpoint
            and self.level > other.level
        )

    def __lt__(self, other):
        return other.__gt__(self)

    def __hash__(self):
        return hash((self.level, self.mountpoint))

    def __str__(self):
        return f"Disk larm för partition {self.mountpoint}: {self.level}%"

    def __iter__(self):
        for key in self.__dict__:
            yield key, getattr(self, key)

    def triggered(self):
        current_level = psutil.disk_usage(self.mountpoint).percent
        if current_level >= self.level:
            alert = {
                "alarm": self,
                "timestamp": datetime.now().isoformat(),
                "current_level": current_level,
            }

            return alert

        return None


if __name__ == "__main__":
    a = CPUAlarm("cpu", 1)
    b = MemoryAlarm("memory", 10)
    c = DiskAlarm("disk", 40, "/")
    d = MemoryAlarm("memory", 5)

    alerts = [b.triggered(), d.triggered()]

    highest = max(alerts, key=lambda alert: alert["alarm"])

    print(highest["alarm"])

    print(f"Current cpu usage: {psutil.cpu_percent()}%")
    print(a.triggered())

    print(f"Current memory usage: {psutil.virtual_memory().percent}%")
    print(b.triggered())

    print(
        f"Current disk usage for partition {c.mountpoint}: {psutil.disk_usage(c.mountpoint).percent}%"
    )
    print(c.triggered())
