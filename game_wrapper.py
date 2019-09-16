from dsobj.ds_bonfire import DSBonfire
from dsobj.ds_item import DSItem, DSInfusion, Upgrade, infuse
from dslib.ds_process import DSProcess, Stat
from dslib.ds_cmprocessor import DSCmp
from os.path import join, isfile, dirname
from inspect import getfile, currentframe
from collections import defaultdict
from time import sleep
from os import listdir
from prompt_toolkit.shortcuts import radiolist_dialog, input_dialog
import ctypes
import winsound


class DarkSouls(DSProcess):

    PROCESS_NAME = "DARK SOULS"

    def __init__(self):
        super(DarkSouls, self).__init__()
        self.bonfires = defaultdict(DSBonfire)
        self.items = defaultdict(DSItem)
        self.infusions = defaultdict(DSInfusion)
        self.stats = defaultdict(int)

    def check_alive(self):
        while True:
            if self.has_exited():
                winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
                ctypes.windll.user32.MessageBoxW(0, "DARK SOULS process is no longer running!",
                                                 "DARKSOULS.exe has exited", 0)
                return
            sleep(10)

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
        item_dir = join(dirname(getfile(currentframe())), "dsres", "items")
        item_files = [f for f in listdir(item_dir) if isfile(join(item_dir, f))]
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


class ArgSwitcher:

    def __init__(self, process: DarkSouls):
        self.game = process

    def switch(self, command, arguments):
        case_name = DSCmp.get_method_name("case_" + command + "_", arguments[0])
        case_method = getattr(self, case_name, self.case_set_default)
        case_method(arguments)

    def case_set_speed_game(self, args):
        if self.game.set_game_speed(float(args[1])):
            print("Game speed changed to %s" % args[1])

    def case_set_phantom_type(self, args):
        if self.game.set_phantom_type(int(args[1])):
            print("Phantom type set to %s" % args[1])

    def case_set_team_type(self, args):
        if self.game.set_team_type(int(args[1])):
            print("Team type set to %s" % args[1])

    def case_set_sls(self, args):
        if self.game.set_souls(int(args[1])):
            print("Souls set to %s" % args[1])

    def case_set_hum(self, args):
        if self.game.set_humanity(int(args[1])):
            print("Humanity set to %s" % args[1])

    def case_set_default(self, args):
        try:
            Stat(args[0])
        except ValueError:
            print("Wrong arguments: %s" % args[0])
        if not self.game.level_stat(args[0], int(args[1])):
            print("Failed to level")
