import socket


class Manager:
    def __init__(self) -> None:
        self.menu_options = [
            "Starta övervakning",
            "Lista aktiv övervakning",
            "Skapa larm",
            "Visa larm",
            "Starta övervakningsläge",
            "Ta bort alarm",
            "Avsluta",
        ]
        self.alarms = {"cpu": [], "disk": [], "memory": []}

    def run(self):
        pass

    def show_menu(self, choose_wisely: bool = True):
        while choose_wisely:
            for number, menu_option in enumerate(self.menu_options, 1):
                print(f"{number}: {menu_option}")

            answer = input("Välj en av ovanstående")

            answer = answer.strip()

            if answer.isnumeric() and "." not in answer:
                pass
            else:
                print(f"{answer} är inte ett giltigt värde")

    def add_alarm(self, what: str, value: int):
        if what in self.alarms and 0 <= value <= 100:
            self.alarms[what].append(value)

            self.alarms[what].sort()

            return True

        return False

    def remove_alarm(self, what: str, value: int):
        self.alarms[what].pop(self.alarms[what].index(value))
