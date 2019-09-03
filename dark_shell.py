from dslib.ds_process import DSProcess, Stat
from dsobj.ds_bonfire import DSBonfire
from dsobj.ds_item import DSItem, DSInfusion, Upgrade, infuse
from dslib.ds_commands import DS_NEST
from prompt_toolkit.completion import NestedCompleter
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.shortcuts import prompt, set_title, radiolist_dialog, input_dialog
from collections import defaultdict
from time import sleep
from threading import Thread
from psutil import pid_exists
import ctypes
import winsound
import os
import inspect
import pywintypes
import win32process
import win32gui


class DarkShell(DSProcess):
    PROCESS_NAME = "DARK SOULS"

    def __init__(self):
        super(DarkShell, self).__init__()
        self.bonfires = defaultdict(DSBonfire)
        self.items = defaultdict(DSItem)
        self.infusions = defaultdict(DSInfusion)
        self.stats = defaultdict(int)
        self.history = InMemoryHistory()
        self.completer = NestedCompleter.from_nested_dict(DS_NEST)

    def has_exited(self):
        return not pid_exists(self.id)

    def check_alive(self):
        while True:
            if self.has_exited():
                winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
                ctypes.windll.user32.MessageBoxW(0, "DARK SOULS process is no longer running",
                                                 "DARKSOULS.exe has exited", 0)
                return
            sleep(10)

    def prompt(self):
        try:
            self.command_manager(prompt("~ ",
                                        completer=self.completer,
                                        history=self.history,
                                        enable_history_search=True))
        except KeyboardInterrupt:
            pass

    def command_manager(self, command: str):

        args = command.split()

        try:

            if args[0] == "start":

                self.start()

            elif args[0] == "exit" or args[0] == "quit":

                os._exit(0)

            elif args[0] == "clear":

                os.system("cls")

            elif args[0] == "set":

                if args[1] == "speed-game":

                    if self.set_game_speed(float(args[2])):
                        print("Game speed changed to %s" % args[2])

                elif args[1] == "speed-self":

                    # TODO self speed change implementation
                    pass

                if args[1] == "no-dead":
                    enable = bool(int(args[2]))
                    if self.set_no_dead(enable):
                        print("NO DEAD %s" % ("enabled" if enable else "disabled"))

                elif args[1] == "death-cam":

                    enable = bool(int(args[2]))
                    if self.death_cam(enable):
                        print("Death cam %s" % ("enabled" if enable else "disabled"))

                elif args[1] == "hum":

                    if self.set_humanity(int(args[2])):
                        print("Humanity set to %s" % args[2])

                elif args[1] == "sls":

                    if self.set_souls(int(args[2])):
                        print("Souls set to %s" % args[2])

                else:

                    for stat in self.stats.keys():
                        if stat.value != args[1]:
                            if stat.value != "slv":
                                self.stats[stat] = self.get_stat(stat)
                        else:
                            new_stat = int(args[2])
                            cur_stat = self.get_stat(stat)
                            soul_level = self.get_soul_level() + (new_stat - cur_stat)
                            self.stats[stat] = new_stat
                            self.stats[Stat.SLV] = soul_level
                            print("%s set to %d" % (stat.value.upper(), new_stat))
                    self.level_up(self.stats)

            elif args[0] == "get":

                if args[1] == "stats":
                    print("\n\tHP: %d/%d" % (self.get_hp(), self.get_hp_mod_max()))
                    print("\tStamina: %d\n" % self.get_stamina())
                    for stat in self.stats.keys():
                        print("\t%s: %d" % (stat.value, self.get_stat(stat)))
                    print("\n")

            elif args[0] == "game-restart":

                if self.game_restart():
                    print("Game restarted")

            elif args[0] == "unlock-all-gestures":

                if self.unlock_all_gestures():
                    print("All gestures unlocked")

            elif args[0] == "item-drop" or args[0] == "item-get":

                i_name = args[1]
                i_count = 1 if len(args) < 3 else int(args[2])
                func = self.item_drop if args[0] == "item-drop" else self.item_get
                if i_name in self.items.keys():
                    item = self.items[i_name]
                    i_id = item.get_id()
                    i_cat = item.get_category()
                    if func(i_cat, i_id, i_count):
                        print("Created new item, ID: %d" % i_id)
                        return
                    else:
                        print("Failed to create item")
                        return
                print("Wrong arguments: %s" % i_name)

            elif args[0] == args[0] == "item-get-upgrade":

                i_name = args[1]
                i_count = 1 if len(args) < 3 else int(args[2])
                i_id = 0
                i_category = 0
                if i_name in self.items.keys():
                    item = self.items[i_name]
                    i_category = item.get_category()
                    if item.get_upgrade_type() == Upgrade.NONE:
                        print("Cant upgrade this item!")
                        return
                    if item.get_upgrade_type() == Upgrade.INFUSABLE or \
                            item.get_upgrade_type() == Upgrade.INFUSABLE_RESTRICTED:
                        values = [
                            (self.infusions[key].get_name(), self.infusions[key].get_name())
                            for key in self.infusions.keys()
                        ]
                        infusion = radiolist_dialog(
                            title="Select infusion type",
                            text="How would you like this weapon to be upgraded?",
                            values=values
                        ).run()
                        if infusion is None:
                            return
                        upgrade = input_dialog(
                            title="Enter upgrade value"
                        ).run()
                        if upgrade is None:
                            return
                        i_id = infuse(item, self.infusions[infusion], int(upgrade))
                    if i_id > 0:
                        if self.item_get(i_category, i_id, i_count):
                            print("Upgrade successful")
                            return
                    print("Upgrade failed")
                    return

            elif args[0] == "warp":

                if args[1] == "bonfire":
                    if not self.bonfire_warp():
                        print("Failed to warp")
                else:
                    b_name = " ".join(args[1:])
                    if b_name in self.bonfires.keys():
                        b_id = self.bonfires[b_name].get_id()
                        self.set_bonfire(b_id)
                        if self.bonfire_warp():
                            print("Warped to location ID: %d" % b_id)
                            return
                        else:
                            print("Failed to warp")
                            return
                    print("Wrong arguments: %s" % b_name)

            else:

                print("Unrecognized command: %s" % args[0])

        except (AttributeError, TypeError, KeyError, IndexError) as e:

            print("%s: couldn't complete the command\n%s" % (type(e), e))

    @staticmethod
    def get_window_pid(title):
        hwnd = win32gui.FindWindow(None, title)
        threadid, pid = win32process.GetWindowThreadProcessId(hwnd)
        return pid

    def read_bonfires(self):
        bonfires = open("res/bonfires.txt", "r").readlines()
        for b in bonfires:
            bonfire = DSBonfire(b.strip())
            self.bonfires[bonfire.get_name()] = bonfire

    def read_items(self):
        item_dir = os.path.join(os.path.dirname(inspect.getfile(inspect.currentframe())), "res", "items")
        item_files = [f for f in os.listdir(item_dir) if os.path.isfile(os.path.join(item_dir, f))]
        for file in item_files:
            items = open("res/items/%s" % file, "r").readlines()
            for i in items[1:]:
                item = DSItem(i.strip(), int(items[0], 16))
                self.items[item.get_name()] = item

    def read_infusions(self):
        infusions = open("res/infusions.txt").readlines()
        for i in infusions:
            infusion = DSInfusion(i.strip())
            self.infusions[infusion.get_name()] = infusion

    def start(self):
        try:
            pid = self.get_window_pid(self.PROCESS_NAME)
            self.attach(pid)
            print("Successfully attached to the DARK SOULS process")
            Thread(target=self.check_alive).start()
        except (pywintypes.error, TypeError, RuntimeError) as e:
            print("%s: couldn't attach to the DARK SOULS process" % type(e))
        rbn = Thread(target=self.read_bonfires)
        rit = Thread(target=self.read_items)
        rin = Thread(target=self.read_infusions)
        rbn.start(), rit.start(), rin.start()
        for stat in vars(Stat).values():
            if type(stat) == Stat:
                self.stats[stat] = 0
        self.disable_fps_disconnect()
        rbn.join(), rit.join(), rin.join()


if __name__ == "__main__":
    set_title("Dark Shell")
    print("Welcome to Dark Shell")
    print("Type 'start' to find the DARK SOULS process")
    dark_shell = DarkShell()
    while True:
        dark_shell.prompt()
