from dslib.ds_process import DSProcess, Stat
from dslib.ds_gui import DSPositionGUI
from dslib.ds_cmprocessor import DSCmp
from dsobj.ds_bonfire import DSBonfire
from dsobj.ds_item import DSItem, DSInfusion, Upgrade, infuse
from dsres.ds_commands import DS_NEST
from prompt_toolkit.shortcuts import set_title, radiolist_dialog, input_dialog
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


class DarkSouls(DSProcess):

    def __init__(self):
        super(DarkSouls, self).__init__()
        self.bonfires = defaultdict(DSBonfire)
        self.items = defaultdict(DSItem)
        self.infusions = defaultdict(DSInfusion)
        self.stats = defaultdict(int)

    @staticmethod
    def get_item_name_and_count(args: list):
        i_name = args[0]
        i_count = 1
        try:
            if len(args) >= 3:
                i_count = int(args[1])
        except ValueError:
            print("Wrong parameter type: %s" % args[1])
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

    def prepare(self):
        self.check_version()
        self.check_valid()
        self.load_pointers()

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


class DarkShell(DSCmp):

    PROCESS_NAME = "DARK SOULS"

    def __init__(self):
        super(DarkShell, self).__init__()
        self.game = DarkSouls()
        self.set_completer(DS_NEST)

    def has_exited(self):
        return not pid_exists(self.game.id)

    def check_alive(self):
        while True:
            if self.has_exited():
                winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
                ctypes.windll.user32.MessageBoxW(0, "DARK SOULS process is no longer running.",
                                                 "DARKSOULS.exe has exited", 0)
                return
            sleep(10)

    @staticmethod
    def do_exit(args):
        os._exit(0)

    @staticmethod
    def do_quit(args):
        os._exit(0)

    @staticmethod
    def do_clear(args):
        os.system("cls")

    def do_start(self, args):
        try:
            pid = DarkShell.get_window_pid(self.PROCESS_NAME)
            self.game.attach(pid)
            print("Successfully attached to the DARK SOULS process")
            Thread(target=self.check_alive).start()
            Thread(target=self.game.disable_fps_disconnect).start()
        except (pywintypes.error, TypeError, RuntimeError) as e:
            print("%s: couldn't attach to the DARK SOULS process\n%s" % (type(e).__name__, e))
        rbn = Thread(target=self.game.read_bonfires)
        rit = Thread(target=self.game.read_items)
        rin = Thread(target=self.game.read_infusions)
        rbn.start(), rit.start(), rin.start()
        for stat in vars(Stat).values():
            if type(stat) == Stat:
                self.game.stats[stat] = self.game.get_stat(stat)
        rbn.join(), rit.join(), rin.join()

    def do_pos_gui(self, args):
        try:
            self.game.prepare()
            DSPositionGUI(self.game).mainloop()
        except Exception as e:
            print("%s: couldn't launch position GUI\n%s" % (type(e).__name__, e))

    def do_set(self, args):

        try:

            self.game.prepare()

            if args[0] == "speed-game":

                if self.game.set_game_speed(float(args[1])):
                    print("Game speed changed to %s" % args[1])

            elif args[0] == "speed-self":

                # TODO self speed change implementation
                pass

            elif args[0] == "phantom-type":

                if self.game.set_phantom_type(int(args[1])):
                    print("Phantom type set to %s" % args[1])

            elif args[0] == "team-type":

                if self.game.set_team_type(int(args[1])):
                    print("Team type set to %s" % args[1])

            elif args[0] == "hum":

                if self.game.set_humanity(int(args[1])):
                    print("Humanity set to %s" % args[1])

            elif args[0] == "sls":

                if self.game.set_souls(int(args[1])):
                    print("Souls set to %s" % args[1])

            else:

                if not self.game.level_stat(args[0], int(args[1])):
                    print("Failed to level")

        except ValueError:

            print("Wrong parameter type: %s " % args[1])

        except Exception as e:

            print("%s: couldn't complete the command\n%s" % (type(e).__name__, e))

    def do_enable(self, args):

        try:

            self.game.prepare()

            if args[0] == "super-armor":

                if self.game.set_super_armor(True):
                    print("SUPER ARMOR enabled")

            elif args[0] == "draw":

                if self.game.set_draw_enable(True):
                    print("DRAW enabled")

            elif args[0] == "gravity":

                if self.game.set_disable_gravity(False):
                    print("GRAVITY enabled")

            elif args[0] == "no-dead":

                if self.game.set_no_dead(True):
                    print("NO DEAD enabled")

            elif args[0] == "no-stamina-consume":

                if self.game.set_no_stamina_consume(True):
                    print("NO STAMINA CONSUME enabled")

            elif args[0] == "no-goods-consume":

                if self.game.set_no_goods_consume(True):
                    print("NO GOODS CONSUME enabled")

            elif args[0] == "no-update":

                if self.game.set_no_update(True):
                    print("NO UPDATE enabled")

            elif args[0] == "no-attack":

                if self.game.set_no_attack(True):
                    print("NO ATTACK enabled")

            elif args[0] == "no-move":

                if self.game.set_no_move(True):
                    print("NO MOVE enabled")

            elif args[0] == "no-damage":

                if self.game.set_no_damage(True):
                    print("NO DAMAGE enabled")

            elif args[0] == "no-hit":

                if self.game.set_no_hit(True):
                    print("NO HIT enabled")

            elif args[0] == "death-cam":

                if self.game.death_cam(True):
                    print("Death cam enabled")

        except Exception as e:

            print("%s: couldn't complete the command\n%s" % (type(e).__name__, e))

    def do_disable(self, args):

        try:

            self.game.prepare()

            if args[0] == "super-armor":

                if self.game.set_super_armor(False):
                    print("SUPER ARMOR disabled")

            elif args[0] == "draw":

                if self.game.set_draw_enable(False):
                    print("DRAW disabled")

            elif args[0] == "gravity":

                if self.game.set_disable_gravity(True):
                    print("GRAVITY disabled")

            elif args[0] == "no-dead":

                if self.game.set_no_dead(False):
                    print("NO DEAD disabled")

            elif args[0] == "no-stamina-consume":

                if self.game.set_no_stamina_consume(False):
                    print("NO STAMINA CONSUME disabled")

            elif args[0] == "no-goods-consume":

                if self.game.set_no_goods_consume(False):
                    print("NO GOODS CONSUME disabled")

            elif args[0] == "no-update":

                if self.game.set_no_update(False):
                    print("NO UPDATE disabled")

            elif args[0] == "no-attack":

                if self.game.set_no_attack(False):
                    print("NO ATTACK disabled")

            elif args[0] == "no-move":

                if self.game.set_no_move(False):
                    print("NO MOVE disabled")

            elif args[0] == "no-damage":

                if self.game.set_no_damage(False):
                    print("NO DAMAGE disabled")

            elif args[0] == "no-hit":

                if self.game.set_no_hit(False):
                    print("NO HIT disabled")

            elif args[0] == "death-cam":

                if self.game.death_cam(False):
                    print("Death cam disabled")

        except Exception as e:

            print("%s: couldn't complete the command\n%s" % (type(e).__name__, e))

    def do_get(self, args):
        try:
            self.game.prepare()
            if args[0] == "stats":
                self.game.print_stats()
        except Exception as e:
            print("%s: couldn't complete the command\n%s" % (type(e).__name__, e))

    def do_game_restart(self, args):
        try:
            self.game.prepare()
            if self.game.game_restart():
                print("Game restarted")
        except Exception as e:
            print("%s: couldn't complete the command\n%s" % (type(e).__name__, e))

    def do_item_drop(self, args):
        try:
            self.game.prepare()
            i_name, i_count = DarkSouls.get_item_name_and_count(args)
            if i_count > 0:
                self.game.create_item(i_name, i_count, func=self.game.item_drop)
        except Exception as e:
            print("%s: couldn't complete the command\n%s" % (type(e).__name__, e))

    def do_item_get(self, args):
        try:
            self.game.prepare()
            i_name, i_count = DarkSouls.get_item_name_and_count(args)
            if i_count > 0:
                self.game.create_item(i_name, i_count, func=self.game.item_get)
        except Exception as e:
            print("%s: couldn't complete the command\n%s" % (type(e).__name__, e))

    def do_item_get_upgrade(self, args):
        try:
            self.game.prepare()
            i_name, i_count = DarkSouls.get_item_name_and_count(args)
            if i_count > 0:
                self.game.upgrade_item(i_name, i_count)
        except Exception as e:
            print("%s: couldn't complete the command\n%s" % (type(e).__name__, e))

    def do_warp(self, args):
        try:
            self.game.prepare()
            if args[0] == "bonfire":
                if not self.game.bonfire_warp():
                    print("Failed to warp")
            else:
                b_name = " ".join(args[0:])
                self.game.bonfire_warp_by_name(b_name)
        except Exception as e:
            print("%s: couldn't complete the command\n%s" % (type(e).__name__, e))

    @staticmethod
    def get_window_pid(title):
        hwnd = win32gui.FindWindow(None, title)
        threadid, pid = win32process.GetWindowThreadProcessId(hwnd)
        return pid


if __name__ == "__main__":
    set_title("Dark Shell")
    print("Welcome to Dark Shell")
    print("Type 'start' to find the DARK SOULS process")
    DarkShell().cmp_loop()
