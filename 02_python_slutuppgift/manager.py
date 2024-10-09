import socket
import sys
from time import sleep

import psutil
from monitor import Monitor


class Manager:
    def __init__(self) -> None:
        self.menu_options = {
            "main": [
                ("Starta övervakning", self.start_monitoring),
                ("Lista aktiv övervakning", None),  # list_current_monitoring
                ("Skapa larm", None),  # add_alarm
                ("Ta bort larm", None),  # show_alarm
                ("Starta övervakningsläge", None),  # show_monitoring
                ("Visa alarm", None),  # remove_alarm
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
        self.monitor = Monitor()

    def run(self) -> None:
        while True:
            self.show_menu("main")
            self.process_answer()

    def start_monitoring(self) -> None:
        print("Startar övervakning")
        self.monitor.activate()

    def list_current_status(self) -> None:
        if not self.monitor.is_active:
            print("Ingen övervakning körs just nu")
            return

        current_status = self.monitor.get_current_status()

        print(f"CPU användning: {current_status['cpu']}%")

        print(
            f"Minnesanvändning: {current_status['memory']['percentage']}"
            f"({round(current_status['memory']['used'] / 1024 ** 3, 1)} GB av "
            f"{round(current_status['memory']['total'] / 1024 ** 3)} GB används)"
        )

        print("Diskanvändning för:")
        for disk_partition in current_status["disk"]:
            print(
                f"\t{disk_partition['path']: <12}: {disk_partition['quota']}% "
                f"({round(disk_partition['used'] / 1024 ** 3)} GB av"
                f" {round(disk_partition['size'] / 1024 ** 3)} GB används)"
            )

    def add_alarm(self) -> None:
        while True:
            self.show_menu("add")

            first_choice = input("Välj en av ovanstående: ")

            if not first_choice.isnumeric():
                print("Ej giltigt värde, försök igen")
                continue

            if 0 < int(first_choice) < len(self.menu_options["add"]):
                what = ["cpu", "memory", "disk"][int(first_choice) - 1]

                while True:
                    alarm_value = input("Ställ in nivå för alarmet: ")

                    if not alarm_value.isnumeric():
                        print("Ej giltigt värde, försök igen")
                        continue

                    if 0 <= int(alarm_value) <= 100:
                        self.monitor.add_alarm(what, int(alarm_value))
                        break

            elif int(first_choice) == 4:
                break

    def remove_alarm(self) -> None:
        while True:
            self.show_menu("remove")

            first_choice = input("Välj en av ovanstående: ")

            if not first_choice.isnumeric():
                print("Ej giltigt värde, försök igen")
                continue

            if 0 < int(first_choice) < len(self.menu_options["add"]):
                what = ["cpu", "memory", "disk"][int(first_choice) - 1]

                while True:
                    values = list(self.monitor.alarms[what])

                    if len(values) == 0:
                        print("Det finns inga alarm att ta bort")
                        break

                    print("Dessa nivåer är tillgängliga")

                    for number, value in enumerate(values, 1):
                        print(f"{number}: {value}")

                    second_choice = input("Välj en av ovanstående: ")

                    if not second_choice.isnumeric():
                        print("Ej giltigt värde, försök igen")
                        continue

                    if 0 < int(second_choice) <= len(self.monitor.alarms[what]):
                        self.monitor.remove_alarm(what, values[int(second_choice) - 1])
                        break

            elif int(first_choice) == 4:
                break

    def show_alarms(self) -> None:
        monitor_types = [
            ("cpu", "CPU larm"),
            ("memory", "Minneslarm"),
            ("disk", "Disklarm"),
        ]

        print(self.monitor.alarms)

        for key, text in monitor_types:
            for value in self.monitor.alarms[key]:
                print(f"{text}: {value}%")

    def show_menu(self, which_menu) -> None:
        print(
            "\n".join(
                [
                    f"{number}: {menu_option[0]}"
                    for number, menu_option in enumerate(
                        self.menu_options[which_menu], 1
                    )
                ]
            )
        )

    def process_answer(self) -> None:
        answer = input("Välj en av ovanstående: ")

        answer = answer.strip()

        if answer.isnumeric() and "." not in answer:
            if int(answer) == 1:
                self.start_monitoring()
            elif int(answer) == 2:
                self.list_current_status()
            elif int(answer) == 3:
                self.add_alarm()
            elif int(answer) == 4:
                self.remove_alarm()
            elif int(answer) == 5:
                try:
                    while True:
                        alerts = self.monitor.check_alarms()

                        if len(alerts) == 0:
                            print("Inga värden överstiger larmnivåerna")
                        else:
                            for alert in alerts:
                                print(
                                    f"{alert['timestamp'].strftime('%Y-%m-%d %H:%m.%S')}"
                                    f" {alert['alarm_type']} {alert['current']} > {alert['alarm_level']}"
                                )
                        sleep(5)
                except KeyboardInterrupt:
                    pass
            elif int(answer) == 6:
                self.show_alarms()
            elif int(answer) == 7:
                sys.exit()
        else:
            print(f"{answer} är inte ett giltigt värde")


if __name__ == "__main__":
    man = Manager()

    man.run()
