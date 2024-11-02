"""Contains a class to manage and display alarms and system information."""

import sys
import threading
import time

import psutil

from monitor import Monitor

if psutil.LINUX:
    import termios
    import tty

    def keyboard_reaction(monitor):
        """Listens for keyboard input, and stops the monitor sending triggered
        alerts to the queue."""
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
            monitor.send_to_queue = False

elif psutil.WINDOWS:
    import msvcrt

    def keyboard_reaction(monitor):
        while True:
            if msvcrt.kbhit():
                msvcrt.getch()
                break

        monitor.send_to_queue = False


def bytes_to_readable(num_bytes: int) -> tuple[float, str]:
    """Converts a number of bytes to a float and a unit."""
    units = ["B", "KB", "MB", "GB", "TB", "PB"]
    d = 1
    count = 0

    while num_bytes >= d * 1024:
        d *= 1024
        count += 1

    return round(num_bytes / d, 1), units[count]


class Manager:
    """A class to manage and display system alarms using an interactive menu."""

    def __init__(self) -> None:
        self.menu_options = {
            "main": [
                "Starta övervakning",
                "Lista aktiv övervakning",
                "Skapa larm",
                "Ta bort larm",
                "Starta övervakningsläge",
                "Visa alarm",
                "Avsluta",
            ],
            "add": [
                "CPU användning",
                "Minnesanvändning",
                "Diskanvändning",
                "Tillbaka till huvudmenyn",
            ],
        }
        self.monitor = Monitor()

    def main(self) -> None:
        """Main menu loop"""
        while True:
            self.show_menu(self.menu_options["main"])
            self.process_answer()

    def process_answer(self) -> None:
        """Handles input from the main menu, validates it and calls
        the corresponding method or ends the program."""
        answer = input("Välj en av ovanstående: ")

        answer = answer.strip()

        next_step = [
            self.start_monitoring,
            self.list_current_status,
            self.add_alarm,
            self.remove_alarm,
            self.show_current_monitoring,
            self.show_alarms,
            sys.exit,
        ]

        if (
            answer.isnumeric()
            and "." not in answer
            and 0 < int(answer) <= len(next_step)
        ):
            next_step[int(answer) - 1]()
        else:
            print(f"{answer} är inte ett giltigt värde")

    def start_monitoring(self) -> None:
        """Starts the monitor in a separate thread."""
        print("\nStartar övervakning\n")

        threading.Thread(target=self.monitor.run, daemon=True).start()

    def list_current_status(self) -> None:
        """Lists the current system resources used for cpu, memory and partitions."""
        if not self.monitor.is_active:
            print(
                "\nIngen övervakning är aktiv, välj starta övervakning i huvudmenyn\n"
            )
            return

        current_status = self.monitor.get_current_status()

        print(f"\nCPU användning: {current_status['cpu']}%")

        mem_used, mem_used_unit = bytes_to_readable(current_status["memory"]["used"])
        mem_total, mem_total_unit = bytes_to_readable(current_status["memory"]["total"])

        print(
            f"Minnesanvändning: {current_status['memory']['percent']}% "
            f"({mem_used} {mem_used_unit} av "
            f"{mem_total} {mem_total_unit} används)"
        )

        print("Diskanvändning för:")
        for disk_partition in current_status["disk"]:
            disk_used, disk_used_unit = bytes_to_readable(disk_partition["used"])
            disk_total, disk_total_unit = bytes_to_readable(disk_partition["size"])

            print(
                f"\t{disk_partition['path']: <12}: {disk_partition['percent']}% "
                f"({disk_used} {disk_used_unit} av"
                f" {disk_total} {disk_total_unit} används)"
            )

        print("\nTryck på valfri tangent för att återgå till huvudmenyn\n")
        t = threading.Thread(target=keyboard_reaction, args=(self.monitor,))
        t.start()
        t.join()

    def add_alarm(self) -> None:
        alarm = {}

        self.show_menu(self.menu_options["add"])

        while True:
            answer = input("Välj en av ovanstående: ")

            if answer == "4":
                return

            if (
                answer.isnumeric()
                and "." not in answer
                and 0 < int(answer) <= len(self.menu_options["add"])
            ):
                alarm["category"] = ["cpu", "memory", "disk"][int(answer) - 1]
                break

            print("Ej giltigt värde, försök igen")

        if alarm["category"] == "disk":
            partitions = psutil.disk_partitions()

            self.show_menu([partition.mountpoint for partition in partitions])

            while True:
                answer = input("Välj en av de ovanstående: ")

                if (
                    answer.isnumeric()
                    and "." not in answer
                    and 0 < int(answer) <= len(partitions)
                ):
                    alarm["mountpoint"] = partitions[int(answer) - 1].mountpoint
                    break

                print("Ej giltigt värde, försök igen")

        while True:
            answer = input("Välj den nivå där det ska larmas: ")

            if not answer.isnumeric() or (0 > int(answer) > 100):
                print("Ej giltigt värde, försök igen")
                continue

            alarm["level"] = int(answer)
            break

        al = self.monitor.add_alarm(alarm)

        print(f"\nNytt alarm skapat: {al}\n")

    def remove_alarm(self) -> None:
        if len(self.monitor.alarms) == 0:
            print("\nDet finns inga alarm att ta bort\n")
            return None

        while True:
            alarm_list = list(self.monitor.alarms)

            for count, alarm in enumerate(alarm_list, 1):
                print(f"{count}. {alarm}")

            print("Tryck 0 för att avbryta")

            answer = input("Välj en av ovanstående: ")

            if not answer.isnumeric() or 0 < int(answer) > len(alarm_list):
                print("Ej giltigt värde, försök igen")
                continue

            if answer.strip() == "0":
                break

            self.monitor.remove_alarm(alarm_list[int(answer) - 1])
            break

        return None

    def show_alarms(self) -> None:
        if len(self.monitor.alarms) == 0:
            print("\nDet finns inga alarm konfigurerade.\n")

        else:
            print(f"\nDet finns {len(self.monitor.alarms)} alarm konfigurerade:")
            for alarm in self.monitor.alarms:
                print(alarm)
            print("")

    def show_menu(self, which_menu: list[str]) -> None:
        print(
            "\n".join(
                [
                    f"{number}: {menu_option}"
                    for number, menu_option in enumerate(which_menu, 1)
                ]
            )
        )

    def show_current_monitoring(self) -> None:
        """Checks the monitor queue and prints any alarm triggered to the screen"""
        if not self.monitor.is_active:
            print(
                "\nIngen övervakning är aktiv, välj starta övervakning i huvudmenyn\n"
            )
            return
        elif len(self.monitor.alarms) == 0:
            print("\nInga alarm konfigurerade, återgår till huvudmenyn.\n")
            return

        print(
            "Övervakning aktiverad, tryck valfri tangent för att återgå till huvudmenyn."
        )
        self.monitor.send_to_queue = True
        t = threading.Thread(target=keyboard_reaction, args=(self.monitor,))
        t.start()
        while self.monitor.send_to_queue:
            if not self.monitor.queue.empty():
                alert = self.monitor.queue.get()
                # Due to the thread end needs to be set this way to align output to the left
                print(
                    f"{alert['timestamp']} *** VARNING {alert['alarm'].category} larm aktiverat, "
                    f"nuvarande nivå {alert['current_level']}% överstiger "
                    f"konfigurerad nivå {alert['alarm'].level}%"
                    f"{' för partition ' + alert['alarm'].mountpoint if alert['alarm'].category == 'disk' else ''}"
                    f" ***",
                    end="\n\r",
                )
            time.sleep(0.1)
        t.join()


if __name__ == "__main__":
    Manager().main()
