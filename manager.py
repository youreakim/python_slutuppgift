import sys
import threading

import psutil

from monitor import Monitor

if psutil.LINUX:
    import termios
    import tty

    def keyboard_reaction(monitor):
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
            monitor.toggle_stdout_logging()

elif psutil.WINDOWS:
    import msvcrt

    def keyboard_reaction(monitor):
        while True:
            if msvcrt.kbhit():
                msvcrt.getch()
                break

        monitor.toggle_stdout_logging()


class Manager:
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
        self.current_menu = "main"
        self.monitor = Monitor()

    def run(self) -> None:
        while True:
            self.show_menu(self.menu_options["main"])
            self.process_answer()

    def start_monitoring(self) -> None:
        print("Startar övervakning")

        threading.Thread(target=self.monitor.run, daemon=True).start()

    def list_current_status(self) -> None:
        if not self.monitor.is_active:
            print("Ingen övervakning är aktiv, välj starta övervakning i huvudmenyn")
            return

        current_status = self.monitor.get_current_status()

        print(f"CPU användning: {current_status['cpu']}%")

        print(
            f"Minnesanvändning: {current_status['memory']['percent']}% "
            f"({current_status['memory']['used']} av "
            f"{current_status['memory']['total']} används)"
        )

        print("Diskanvändning för:")
        for disk_partition in current_status["disk"]:
            print(
                f"\t{disk_partition['path']: <12}: {disk_partition['percent']}% "
                f"({disk_partition['used']} av"
                f" {disk_partition['size']} används)"
            )

        print("Tryck på valfri tangent för att återgå till huvudmenyn")
        t = threading.Thread(target=keyboard_reaction)
        t.start()
        t.join()

    def add_alarm(self) -> None:
        alarm = {}

        self.show_menu(self.menu_options["add"])

        while True:
            answer = input("Välj en av ovanstående: ")

            if not answer.isnumeric() or (
                1 > int(answer) >= len(self.menu_options["add"])
            ):
                print("Ej giltigt värde, försök igen")
                continue

            alarm["category"] = ["cpu", "memory", "disk"][int(answer) - 1]
            break

        if alarm["category"] == "disk":
            partitions = psutil.disk_partitions()

            self.show_menu([partition.mountpoint for partition in partitions])

            while True:
                answer = input("Välj en av de ovanstående: ")

                if not answer.isnumeric() or (1 > int(answer) >= len(partitions)):
                    print("Ej giltigt värde, försök igen")
                    continue

                alarm["mountpoint"] = partitions[int(answer) - 1].mountpoint
                break

        while True:
            answer = input("Välj den nivå där det ska larmas: ")

            if not answer.isnumeric() or (0 > int(answer) > 100):
                print("Ej giltigt värde, försök igen")
                continue

            alarm["level"] = int(answer)
            break

        al = self.monitor.add_alarm(alarm)

        print(f"Nytt alarm skapat: {al}")

    def remove_alarm(self) -> None:
        if len(self.monitor.alarms) == 0:
            print("Det finns inga alarm att ta bort")
            return None

        while True:
            alarm_list = list(self.monitor.alarms)

            for count, alarm in enumerate(alarm_list, 1):
                print(f"{count}. {alarm}")

            print("Tryck 0 för att avbryta")

            answer = input("Välj en av ovanstående: ")

            if not answer.isnumeric() or 1 > int(answer) <= len(alarm_list):
                print("Ej giltigt värde, försök igen")
                continue

            if answer.strip() == "0":
                break

            self.monitor.remove_alarm(alarm_list[int(answer) - 1])
            break

        return None

    def show_alarms(self) -> None:
        if self.monitor is None:
            print("Ingen övervakning körs just nu.")

        elif len(self.monitor.alarms) == 0:
            print("Det finns inga alarm konfigurerade.")

        else:
            for alarm in self.monitor.alarms:
                print(alarm)

    def show_menu(self, which_menu) -> None:
        print(
            "\n".join(
                [
                    f"{number}: {menu_option}"
                    for number, menu_option in enumerate(which_menu, 1)
                ]
            )
        )

    def show_current_monitoring(self) -> None:
        self.monitor.toggle_stdout_logging()
        t = threading.Thread(target=keyboard_reaction, args=(self.monitor,))
        t.start()
        while self.monitor.log_to_stdout:
            if not self.monitor.queue.empty():
                alert = self.monitor.queue.get()
                print(
                    f"{alert['timestamp']} {alert['category']} "
                    f"{alert['current_level']} > {alert['level']}"
                )
        t.join()

    def process_answer(self) -> None:
        answer = input("Välj en av ovanstående: ")

        answer = answer.strip()

        if answer.isnumeric() and "." not in answer:
            [
                self.start_monitoring,
                self.list_current_status,
                self.add_alarm,
                self.remove_alarm,
                self.show_current_monitoring,
                self.show_alarms,
                sys.exit,
            ][int(answer) - 1]()
        else:
            print(f"{answer} är inte ett giltigt värde")


if __name__ == "__main__":
    man = Manager()

    man.run()
