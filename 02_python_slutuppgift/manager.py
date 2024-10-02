import socket
import sys

import psutil


class Manager:
    def __init__(self) -> None:
        self.menu_options = {
            "main": [
                ("Starta övervakning", self.start_monitoring),
                ("Lista aktiv övervakning", None),  # list_current_monitoring
                ("Skapa larm", None),  # add_alarm
                ("Visa larm", None),  # show_alarm
                ("Starta övervakningsläge", None),  # show_monitoring
                ("Ta bort alarm", None),  # remove_alarm
                ("Avsluta", exit),
            ],
            "add": [
                ("CPU användning", None),  # add_alarm, 'cpu'
                ("Minnesanvändning", None),  # add_alarm, 'memory'
                ("Diskanvändning", None),  # add_alarm, 'disk'
                ("Tillbaka till huvudmenyn", None),  # show_menu, main
            ],
            "remove": [
                ("CPU användning", None),  # remove_alarm, 'cpu'
                ("Minnesanvändning", None),  # remove_alarm, 'memory'
                ("Diskanvändning", None),  # remove_alarm, 'disk'
                ("Tillbaka till huvudmenyn", None),  # show_menu, main
            ],
        }
        self.current_menu = "main"
        self.alarms = {"cpu": set(), "disk": set(), "memory": set()}
        self.monotoring_active = False

    def run(self) -> None:
        while True:
            self.show_menu()
            self.process_answer()

    def start_monitoring(self) -> None:
        print("Startar övervakning")
        self.monotoring_active = True

    def list_current_status(self) -> None:
        if not self.monotoring_active:
            print("Ingen övervakning körs just nu")
            return

        print(f"CPU användning: {round(psutil.cpu_percent())}%")

        memory = psutil.virtual_memory()

        print(
            f"Minnesanvändning: {round(memory.used * 100 / memory.total)}% "
            f"({round(memory.used / 1024 ** 3, 1)} GB av {round(memory.total / 1024 ** 3)}"
            f" GB används)"
        )

        print("Diskanvändning för:")
        for disk_partition in psutil.disk_partitions():
            disk_usage = psutil.disk_usage(disk_partition.mountpoint)

            print(
                f"\t{disk_partition.mountpoint: <12}: {disk_usage.percent}% "
                f"({round(disk_usage.used / 1024 ** 3)} GB av {round(disk_usage.total / 1024 ** 3)}"
                f" GB används)"
            )

    def add_alarm(self) -> None:
        while True:
            for number, which in self.menu_options["add"]:
                print(f"{number}: {self.menu_options[which][0]}")

            first_choice = input("Välj en av ovanstående")

            if not first_choice.isnumeric():
                print("Ej giltigt värde, försök igen")
                continue

            if 0 < int(first_choice) < len(self.menu_options["add"]):
                what = ["cpu", "memory", "disk"][int(first_choice)]

                while True:
                    alarm_value = input("Ställ in nivå för alarmet")

                    if not alarm_value.isnumeric():
                        print("Ej giltigt värde, försök igen")
                        continue

                    if 0 <= int(alarm_value) <= 100:
                        self.alarms[what].add(alarm_value)

            elif int(first_choice) == 4:
                break

    def show_alarms(self) -> None:
        monitor_types = [
            ("cpu", "CPU larm"),
            ("memory", "Minneslarm"),
            ("disk", "Disklarm"),
        ]

        for key, text in monitor_types:
            for value in self.alarms[key]:
                print(f"{text}: {value}%")

    def show_menu(self) -> None:
        for number, menu_option in enumerate(self.menu_options[self.current_menu], 1):
            print(f"{number}: {menu_option[0]}")

    def process_answer(self) -> None:
        answer = input("Välj en av ovanstående: ")

        answer = answer.strip()

        if answer.isnumeric() and "." not in answer:
            if int(answer) == 1:
                self.start_monitoring()
            elif int(answer) == 2:
                self.list_current_status()
            elif int(answer) == 3:
                pass
            elif int(answer) == 4:
                pass
            elif int(answer) == 5:
                pass
            elif int(answer) == 6:
                pass
            elif int(answer) == 7:
                sys.exit()
        else:
            print(f"{answer} är inte ett giltigt värde")

    def set_alarm(self, what: str, value: int) -> None:
        self.alarms[what].add(value)

    def remove_alarm(self, what: str, value: int) -> None:
        self.alarms[what].remove(value)


if __name__ == "__main__":
    man = Manager()

    man.list_current_status()

    man.start_monitoring()

    man.list_current_status()

    man.show_alarms()
