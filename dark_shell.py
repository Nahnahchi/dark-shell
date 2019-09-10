from dslib.ds_process import DSProcess, Stat
from dsobj.ds_bonfire import DSBonfire
from dsobj.ds_item import DSItem, DSInfusion, Upgrade, infuse
from dsres.ds_commands import DS_NEST
from prompt_toolkit.completion import NestedCompleter
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.shortcuts import prompt, set_title, radiolist_dialog, input_dialog
from collections import defaultdict
from time import sleep
from threading import Thread
from psutil import pid_exists
from tkinter import Tk, Label, StringVar, BooleanVar, Spinbox, Button, Entry, Checkbutton
import ctypes
import winsound
import os
import inspect
import pywintypes
import win32process
import win32gui


def main():
    dark_shell = DarkShell()
    while True:
        dark_shell.prompt()


class PositionGUI(Tk):

    def __init__(self, process: DSProcess):

        super(PositionGUI, self).__init__()

        self.process = process
        self.exit_flag = False

        self.title("PosGUI")
        self.protocol("WM_DELETE_WINDOW", self.on_quit)
        self.resizable(False, False)

        Label(self, text="current").grid(column=2, row=2)
        Label(self, text="stable").grid(column=3, row=2)
        Label(self, text="stored").grid(column=4, row=2)
        Label(self, text="X").grid(column=1, row=3)
        Label(self, text="Y").grid(column=1, row=4)
        Label(self, text="Z").grid(column=1, row=5)
        Label(self, text="α").grid(column=1, row=6)

        self.x_current = StringVar()
        Entry(self, width=10, state="readonly", textvariable=self.x_current).grid(column=2, row=3)
        self.x_stable = StringVar()
        Entry(self, width=10, state="readonly", textvariable=self.x_stable).grid(column=3, row=3)
        self.x_stored = StringVar()
        self.x_stored.set(process.get_pos_stable()[0])
        Spinbox(self, from_=-1000, to=1000, format="%.3f", width=10, textvariable=self.x_stored).grid(column=4, row=3)

        self.y_current = StringVar()
        Entry(self, width=10, state="readonly", textvariable=self.y_current).grid(column=2, row=4)
        self.y_stable = StringVar()
        Entry(self, width=10, state="readonly", textvariable=self.y_stable).grid(column=3, row=4)
        self.y_stored = StringVar()
        self.y_stored.set(process.get_pos_stable()[1])
        Spinbox(self, from_=-1000, to=1000, format="%.3f", width=10, textvariable=self.y_stored).grid(column=4, row=4)

        self.z_current = StringVar()
        Entry(self, width=10, state="readonly", textvariable=self.z_current).grid(column=2, row=5)
        self.z_stable = StringVar()
        Entry(self, width=10, state="readonly", textvariable=self.z_stable).grid(column=3, row=5)
        self.z_stored = StringVar()
        self.z_stored.set(process.get_pos_stable()[2])
        Spinbox(self, from_=-1000, to=1000, format="%.3f", width=10, textvariable=self.z_stored).grid(column=4, row=5)

        self.a_current = StringVar()
        Entry(self, width=10, state="readonly", textvariable=self.a_current).grid(column=2, row=6)
        self.a_stable = StringVar()
        Entry(self, width=10, state="readonly", textvariable=self.a_stable).grid(column=3, row=6)
        self.a_stored = StringVar()
        self.a_stored.set(process.get_pos_stable()[3])
        Spinbox(self, from_=-360, to=360, format="%.3f", width=10, textvariable=self.a_stored).grid(column=4, row=6)

        Button(self, width=7, text="store", command=self.store).grid(column=2, row=7)
        Button(self, width=7, text="restore", command=self.restore).grid(column=4, row=7)

        Label(self, text="world:").grid(column=1, row=8)
        self.world = StringVar()
        self.world.set(process.get_world())
        Entry(self, width=10, state="readonly", textvariable=self.world).grid(column=2, row=8)
        Label(self, text="area:").grid(column=1, row=9)
        self.area = StringVar()
        self.area.set(process.get_area())
        Entry(self, width=10, state="readonly", textvariable=self.area).grid(column=2, row=9)

        self.lock_pos = BooleanVar()
        self.lock_pos.set(False)
        Checkbutton(self, text="freeze", var=self.lock_pos, command=self.freeze).grid(column=4, row=9)

        Thread(target=self.update).start()

    def update(self):
        while not self.exit_flag:
            self.x_current.set("%.3f" % self.process.get_pos()[0])
            self.x_stable.set("%.3f" % self.process.get_pos_stable()[0])
            self.y_current.set("%.3f" % self.process.get_pos()[1])
            self.y_stable.set("%.3f" % self.process.get_pos_stable()[1])
            self.z_current.set("%.3f" % self.process.get_pos()[2])
            self.z_stable.set("%.3f" % self.process.get_pos_stable()[2])
            self.a_current.set("%.3f" % self.process.get_pos()[3])
            self.a_stable.set("%.3f" % self.process.get_pos_stable()[3])
            self.world.set(self.process.get_world())
            self.area.set(self.process.get_area())
            sleep(1)

    def freeze(self):
        self.process.lock_pos(self.lock_pos.get())

    def store(self):
        self.x_stored.set(self.x_current.get())
        self.y_stored.set(self.y_current.get())
        self.z_stored.set(self.z_current.get())
        self.a_stored.set(self.a_current.get())

    def restore(self):
        try:
            self.process.jump_pos(
                float(self.x_stored.get()),
                float(self.y_stored.get()),
                float(self.z_stored.get()),
                float(self.a_stored.get())
            )
        except ValueError as e:
            print(e)

    def on_quit(self):
        self.exit_flag = True
        self.destroy()


class DarkSouls(DSProcess):

    def __init__(self):
        super(DarkSouls, self).__init__()
        self.bonfires = defaultdict(DSBonfire)
        self.items = defaultdict(DSItem)
        self.infusions = defaultdict(DSInfusion)
        self.stats = defaultdict(int)

    @staticmethod
    def get_item_name_and_count(args: list):
        i_name = args[1]
        i_count = 1
        try:
            if len(args) >= 3:
                i_count = int(args[2])
        except ValueError:
            print("Wrong parameter type: %s" % args[2])
            return None, 0
        return i_name, i_count

    @staticmethod
    def get_upgrade_value_infusable(infusions: list):
        infusion = radiolist_dialog(
            title="Select infusion type",
            text="How would you like this weapon to be upgraded?",
            values=infusions
        ).run()
        if infusion is None:
            return None
        upgrade = input_dialog(
            title="Enter upgrade value",
            text="Item type: Normal [%s]" % infusion.upper()
        ).run()
        return upgrade, infusion

    @staticmethod
    def get_upgrade_value_pyro_flame(item: DSItem):
        is_pyro_asc = item.get_upgrade_type() == Upgrade.PYRO_FLAME_ASCENDED
        max_upgrade = 5 if is_pyro_asc else 15
        upgrade = input_dialog(
            title="Enter upgrade value",
            text="Item type: %sPyromancy Flame" % "Ascended " if is_pyro_asc else ""
        ).run()
        if int(upgrade) > max_upgrade or int(upgrade) < 0:
            print("Can't upgrade %sPyromancy Flame to +%s" % ("Ascended " if is_pyro_asc else "", upgrade))
            return None
        return upgrade

    @staticmethod
    def get_upgrade_value_armor_or_unique(item: DSItem):
        is_unique = item.get_upgrade_type() == Upgrade.UNIQUE
        max_upgrade = 5 if is_unique else 10
        upgrade = input_dialog(
            title="Enter upgrade value",
            text="Item type: %s" % "Unique" if is_unique else "Armor"
        ).run()
        if int(upgrade) > max_upgrade or int(upgrade) < 0:
            print("Can't upgrade %s to +%s" % ("Unique" if is_unique else "Armor", upgrade))
            return None
        return upgrade

    def print_stats(self):
        print("\n\tHealth: %d/%d" % (self.get_hp(), self.get_hp_mod_max()))
        print("\tStamina: %d\n" % self.get_stamina())
        for stat in self.stats.keys():
            print("\t%s: %d" % (stat.value, self.get_stat(stat)))
        print("\n")

    def bonfire_warp_by_name(self, b_name: str):
        if b_name not in self.bonfires.keys():
            print("Wrong arguments: %s" % b_name)
        else:
            b_id = self.bonfires[b_name].get_id()
            self.set_bonfire(b_id)
            if self.bonfire_warp():
                print("Warped to location ID: %d" % b_id)
            else:
                print("Failed to warp")

    def level_stat(self, s_name: str, s_level: int):
        for stat in self.stats.keys():
            if stat.value != s_name:
                if stat != Stat.SLV:
                    self.stats[stat] = self.get_stat(stat)
            else:
                new_stat = s_level
                cur_stat = self.get_stat(stat)
                soul_level = self.get_soul_level() + (new_stat - cur_stat)
                self.stats[stat] = new_stat
                self.stats[Stat.SLV] = soul_level
                print("%s set to %d" % (stat.value.upper(), new_stat))
        return self.level_up(self.stats)

    def create_item(self, i_name: str, i_count: int, func):
        if i_name not in self.items.keys():
            print("Wrong arguments: %s" % i_name)
        else:
            item = self.items[i_name]
            i_id = item.get_id()
            i_cat = item.get_category()
            if func(i_cat, i_id, i_count):
                print("Created new item, ID: %d" % i_id)
            else:
                print("Failed to create item")

    def upgrade_item(self, i_name: str, i_count: int):
        if i_name not in self.items.keys():
            print("Item '%s' doesn't exist!" % i_name)
        else:
            item = self.items[i_name]
            i_id = item.get_id()
            i_category = item.get_category()
            if item.get_upgrade_type() == Upgrade.NONE:
                print("Can't upgrade this item!")
                return
            elif item.get_upgrade_type() in (Upgrade.ARMOR, Upgrade.UNIQUE):
                upgrade = DarkSouls.get_upgrade_value_armor_or_unique(item)
                if upgrade is None:
                    return
                i_id += int(upgrade)
            elif item.get_upgrade_type() in (Upgrade.PYRO_FLAME, Upgrade.PYRO_FLAME_ASCENDED):
                upgrade = DarkSouls.get_upgrade_value_pyro_flame(item)
                if upgrade is None:
                    return
                i_id += int(upgrade) * 100
            elif item.get_upgrade_type() in (Upgrade.INFUSABLE, Upgrade.INFUSABLE_RESTRICTED):
                values = [
                    (self.infusions[key].get_name(), self.infusions[key].get_name().upper())
                    for key in self.infusions.keys()
                ]
                upgrade, infusion = DarkSouls.get_upgrade_value_infusable(values)
                if upgrade is None:
                    return
                i_id = infuse(item, self.infusions[infusion], int(upgrade))
            else:
                print("Wrong arguments: %s" % i_name)
                return
            if i_id > 0:
                if self.item_get(i_category, i_id, i_count):
                    print("Upgrade successful")
                    return
            print("Upgrade failed")

    def read_bonfires(self):
        bonfires = open("dsres/bonfires.txt", "r").readlines()
        for b in bonfires:
            bonfire = DSBonfire(b.strip())
            self.bonfires[bonfire.get_name()] = bonfire

    def read_items(self):
        item_dir = os.path.join(os.path.dirname(inspect.getfile(inspect.currentframe())), "dsres", "items")
        item_files = [f for f in os.listdir(item_dir) if os.path.isfile(os.path.join(item_dir, f))]
        for file in item_files:
            items = open("dsres/items/%s" % file, "r").readlines()
            category = items[0]
            for i in items[1:]:
                item = DSItem(i.strip(), int(category, 16))
                self.items[item.get_name()] = item

    def read_infusions(self):
        infusions = open("dsres/infusions.txt").readlines()
        for i in infusions:
            infusion = DSInfusion(i.strip())
            self.infusions[infusion.get_name()] = infusion


class DarkShell(DarkSouls):

    PROCESS_NAME = "DARK SOULS"

    def __init__(self):
        super(DarkShell, self).__init__()
        self.game = DarkSouls()
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
            self.execute_command(prompt(
                "~ ", completer=self.completer, history=self.history, enable_history_search=True
            ))
        except KeyboardInterrupt:
            pass

    def execute_command(self, command: str):

        args = command.split()

        try:

            if args[0] == "start":

                self.start()

            elif args[0] in ("exit", "quit"):

                os._exit(0)

            elif args[0] == "clear":

                os.system("cls")

            else:

                self.load_pointers()

                if args[0] == "pos-gui":

                    PositionGUI(self).mainloop()

                elif args[0] in ("enable", "disable"):

                    enable = True if args[0] == "enable" else False

                    if args[1] == "super-armor":

                        if self.set_super_armor(enable):
                            print("SUPER ARMOR %s" % ("enabled" if enable else "disabled"))

                    elif args[1] == "draw":

                        if self.set_draw_enable(enable):
                            print("DRAW %s" % ("enabled" if enable else "disabled"))

                    elif args[1] == "gravity":

                        disable = not enable
                        if self.set_disable_gravity(disable):
                            print("GRAVITY %s" % ("enabled" if not disable else "disabled"))

                    elif args[1] == "no-dead":

                        if self.set_no_dead(enable):
                            print("NO DEAD %s" % ("enabled" if enable else "disabled"))

                    elif args[1] == "no-stamina-consume":

                        if self.set_no_stamina_consume(enable):
                            print("NO STAMINA CONSUME %s" % ("enabled" if enable else "disabled"))

                    elif args[1] == "no-goods-consume":

                        if self.set_no_goods_consume(enable):
                            print("NO GOODS CONSUME %s" % ("enabled" if enable else "disabled"))

                    elif args[1] == "no-update":

                        if self.set_no_update(enable):
                            print("NO UPDATE %s" % ("enabled" if enable else "disabled"))

                    elif args[1] == "no-attack":

                        if self.set_no_attack(enable):
                            print("NO ATTACK %s" % ("enabled" if enable else "disabled"))

                    elif args[1] == "no-move":

                        if self.set_no_move(enable):
                            print("NO MOVE %s" % ("enabled" if enable else "disabled"))

                    elif args[1] == "no-damage":

                        if self.set_no_damage(enable):
                            print("NO DAMAGE %s" % ("enabled" if enable else "disabled"))

                    elif args[1] == "no-hit":

                        if self.set_no_hit(enable):
                            print("NO HIT %s" % ("enabled" if enable else "disabled"))

                    elif args[1] == "death-cam":

                        if self.death_cam(enable):
                            print("Death cam %s" % ("enabled" if enable else "disabled"))

                elif args[0] == "set":

                    try:

                        if args[1] == "speed-game":

                            if self.set_game_speed(float(args[2])):
                                print("Game speed changed to %s" % args[2])

                        elif args[1] == "speed-self":

                            # TODO self speed change implementation
                            pass

                        elif args[1] == "phantom-type":

                            if self.set_phantom_type(int(args[2])):
                                print("Phantom type set to %s" % args[2])

                        elif args[1] == "team-type":

                            if self.set_team_type(int(args[2])):
                                print("Team type set to %s" % args[2])

                        elif args[1] == "hum":

                            if self.set_humanity(int(args[2])):
                                print("Humanity set to %s" % args[2])

                        elif args[1] == "sls":

                            if self.set_souls(int(args[2])):
                                print("Souls set to %s" % args[2])

                        else:

                            if not self.level_stat(args[1], int(args[2])):
                                print("Failed to level")

                    except ValueError:

                        print("Wrong parameter type: %s " % args[2])

                elif args[0] == "get":

                    if args[1] == "stats":
                        self.print_stats()

                elif args[0] == "game-restart":

                    if self.game_restart():
                        print("Game restarted")

                elif args[0] in ("item-drop", "item-get"):

                    i_name, i_count = DarkSouls.get_item_name_and_count(args)
                    if i_count > 0:
                        func = self.item_drop if args[0] == "item-drop" else self.item_get
                        self.create_item(i_name, i_count, func)

                elif args[0] == "item-get-upgrade":

                    i_name, i_count = DarkSouls.get_item_name_and_count(args)
                    if i_count > 0:
                        self.upgrade_item(i_name, i_count)

                elif args[0] == "warp":

                    if args[1] == "bonfire":
                        if not self.bonfire_warp():
                            print("Failed to warp")
                    else:
                        b_name = " ".join(args[1:])
                        self.bonfire_warp_by_name(b_name)

                else:

                    print("Unrecognized command: %s" % args[0])

        except (AttributeError, TypeError, KeyError, IndexError) as e:

            print("%s: couldn't complete the command\n%s" % (type(e), e))

    @staticmethod
    def get_window_pid(title):
        hwnd = win32gui.FindWindow(None, title)
        threadid, pid = win32process.GetWindowThreadProcessId(hwnd)
        return pid

    def start(self):
        try:
            pid = DarkShell.get_window_pid(self.PROCESS_NAME)
            self.attach(pid)
            print("Successfully attached to the DARK SOULS process")
            Thread(target=self.check_alive).start()
            Thread(target=self.disable_fps_disconnect).start()
        except (pywintypes.error, TypeError, RuntimeError) as e:
            print("%s: couldn't attach to the DARK SOULS process" % type(e))
        rbn = Thread(target=self.read_bonfires)
        rit = Thread(target=self.read_items)
        rin = Thread(target=self.read_infusions)
        rbn.start(), rit.start(), rin.start()
        for stat in vars(Stat).values():
            if type(stat) == Stat:
                self.stats[stat] = self.get_stat(stat)
        rbn.join(), rit.join(), rin.join()


if __name__ == "__main__":
    set_title("Dark Shell")
    print("Welcome to Dark Shell")
    print("Type 'start' to find the DARK SOULS process")
    main()
