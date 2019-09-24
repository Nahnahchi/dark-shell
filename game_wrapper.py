from dsobj.ds_bonfire import DSBonfire
from dsobj.ds_item import DSItem, DSInfusion, Upgrade, infuse
from dslib.ds_process import DSProcess, Stat
from dslib.ds_cmprocessor import DSCmp
from os.path import join, isfile, dirname
from inspect import getfile, currentframe
from collections import defaultdict
from time import sleep
from os import listdir
from prompt_toolkit.shortcuts import radiolist_dialog, input_dialog, yes_no_dialog
import ctypes
import winsound


class DarkSouls(DSProcess):

    PROCESS_NAME = "DARK SOULS"
    STATIC_SOURCE = "static"

    def __init__(self):
        super(DarkSouls, self).__init__()
        self.bonfires = defaultdict(DSBonfire)
        self.items = defaultdict(DSItem)
        self.infusions = defaultdict(DSInfusion)
        self.covenants = defaultdict(int)
        self.stats = defaultdict(int)

    def check_alive(self):
        while True:
            if self.has_exited():
                winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
                ctypes.windll.user32.MessageBoxW(0, "DARK SOULS process is no longer running!",
                                                 "DARKSOULS.exe has exited", 0)
                self.interface = None
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
    def get_upgrade_value_infusable(infusions: list, item: DSItem):
        infusion = radiolist_dialog(
            title="Select infusion type",
            text="How would you like %s to be upgraded?" % item.get_name().upper().replace("-", " "),
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
            title="Enter upgrade value for %s" % item.get_name().upper().replace("-", " "),
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
            title="Enter upgrade value for %s" % item.get_name().upper().replace("-", " "),
            text="Item type: %s" % "Unique" if is_unique else "Armor"
        ).run()
        if int(upgrade) > max_upgrade or int(upgrade) < 0:
            print("Can't upgrade %s to +%s" % ("Unique" if is_unique else "Armor", upgrade))
            return None
        return upgrade

    @staticmethod
    def warn_disable_npc():
        return yes_no_dialog(
            title="Warning",
            text="This command will kill all NPCs in the area. Do you want to proceed?"
        ).run()

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
        try:
            Stat(s_name)
        except ValueError:
            print("Wrong arguments: %s" % s_name)
        else:
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

    def create_item(self, i_name: str, i_count: int, func=None):
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
                upgrade, infusion = DarkSouls.get_upgrade_value_infusable(values, item)
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
        bonfires = open("dsres/misc/bonfires.txt", "r").readlines()
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
        infusions = open("dsres/misc/infusions.txt", "r").readlines()
        for i in infusions:
            infusion = DSInfusion(i.strip())
            self.infusions[infusion.get_name()] = infusion

    def read_covenants(self):
        covenants = open("dsres/misc/covenants.txt", "r").readlines()
        for c in covenants:
            covenant = c.split()
            cov_id = int(covenant[0])
            cov_name = covenant[1]
            self.covenants[cov_name] = cov_id

    def switch(self, command: str, arguments: list):

        dark_souls = self

        class Switcher:

            @classmethod
            def switch(cls):
                case_name = DSCmp.get_method_name(prefix=command+"_", name=arguments[0])
                default = getattr(cls, command + "_default")
                case_method = getattr(cls, case_name, default)
                case_method()

            @staticmethod
            def set_default():
                stat_name = arguments[0]
                stat_value = int(arguments[1])
                if not dark_souls.level_stat(stat_name, stat_value):
                    print("Failed to level")

            @staticmethod
            def get_default():
                flag_id = int(arguments[0])
                print("FLAG %d: %s" % (flag_id, dark_souls.read_event_flag(flag_id)))

            @staticmethod
            def enable_default():
                flag_id = int(arguments[0])
                enable = arguments[1]
                if dark_souls.write_event_flag(flag_id, enable):
                    print("EVENT FLAG %d %s" % (flag_id, ("enabled" if enable else "disabled")))

            @staticmethod
            def static_default():
                with open(DarkSouls.STATIC_SOURCE, "a") as static_source:
                    line = ""
                    for arg in arguments:
                        line += arg + " "
                    static_source.write(line + "\n")

            @staticmethod
            def set_speed_game():
                speed = float(arguments[1])
                if dark_souls.set_game_speed(speed):
                    print("Game speed changed to %f" % speed)

            @staticmethod
            def set_phantom_type():
                phantom_type = int(arguments[1])
                if dark_souls.set_phantom_type(phantom_type):
                    print("Phantom type set to %d" % phantom_type)

            @staticmethod
            def set_team_type():
                team_type = int(arguments[1])
                if dark_souls.set_team_type(team_type):
                    print("Team type set to %d" % team_type)

            @staticmethod
            def set_sls():
                souls = int(arguments[1])
                if dark_souls.set_souls(souls):
                    print("Souls set to %d" % souls)

            @staticmethod
            def set_hum():
                humanity = int(arguments[1])
                if dark_souls.set_humanity(humanity):
                    print("Humanity set to %d" % humanity)

            @staticmethod
            def set_name():
                name = " ".join(arguments[1:])
                if dark_souls.set_name(name):
                    print("Name set to '%s'" % name)

            @staticmethod
            def set_ng():
                new_game = int(arguments[1])
                if dark_souls.set_ng_mode(new_game):
                    print("NG changed to +%d" % new_game)

            @staticmethod
            def set_covenant():
                covenant_name = arguments[1]
                if covenant_name in dark_souls.covenants.keys():
                    covenant_id = dark_souls.covenants[covenant_name]
                    if dark_souls.set_covenant(covenant_id):
                        print("Covenant changed to %s" % covenant_name.upper().replace("-", " "))

            @staticmethod
            def get_stats():
                dark_souls.print_stats()

            @staticmethod
            def enable_super_armor():
                enable = arguments[1]
                if dark_souls.set_super_armor(enable):
                    print("SUPER ARMOR %s" % ("enabled" if enable else "disabled"))

            @staticmethod
            def enable_draw():
                enable = arguments[1]
                if dark_souls.set_draw_enable(enable):
                    print("DRAW %s" % ("enabled" if enable else "disabled"))

            @staticmethod
            def enable_gravity():
                enable = arguments[1]
                if dark_souls.set_no_gravity(not enable):
                    print("GRAVITY %s" % ("enabled" if enable else "disabled"))

            @staticmethod
            def enable_no_dead():
                enable = arguments[1]
                if dark_souls.set_no_dead(enable):
                    print("NO DEAD %s" % ("enabled" if enable else "disabled"))

            @staticmethod
            def enable_no_stamina_consume():
                enable = arguments[1]
                if dark_souls.set_no_stamina_consume(enable):
                    print("NO STAMINA CONSUME %s" % ("enabled" if enable else "disabled"))

            @staticmethod
            def enable_no_goods_consume():
                enable = arguments[1]
                if dark_souls.set_no_goods_consume(enable):
                    print("NO GOODS CONSUME %s" % ("enabled" if enable else "disabled"))

            @staticmethod
            def enable_no_update():
                enable = arguments[1]
                if dark_souls.set_no_update(enable):
                    print("NO UPDATE %s" % ("enabled" if enable else "disabled"))

            @staticmethod
            def enable_no_attack():
                enable = arguments[1]
                if dark_souls.set_no_attack(enable):
                    print("NO ATTACK %s" % ("enabled" if enable else "disabled"))

            @staticmethod
            def enable_no_move():
                enable = arguments[1]
                if dark_souls.set_no_move(enable):
                    print("NO MOVE %s" % ("enabled" if enable else "disabled"))

            @staticmethod
            def enable_no_damage():
                enable = arguments[1]
                if dark_souls.set_no_damage(enable):
                    print("NO DAMAGE %s" % ("enabled" if enable else "disabled"))

            @staticmethod
            def enable_no_hit():
                enable = arguments[1]
                if dark_souls.set_no_hit(enable):
                    print("NO HIT %s" % ("enabled" if enable else "disabled"))

            @staticmethod
            def enable_no_magic_all():
                enable = arguments[1]
                if dark_souls.set_no_magic_all(enable):
                    print("NO MAGIC ALL %s" % ("enabled" if enable else "disabled"))

            @staticmethod
            def enable_no_ammo_consume_all():
                enable = arguments[1]
                if dark_souls.set_no_ammo_consume_all(enable):
                    print("NO AMMO CONSUME ALL %s" % ("enabled" if enable else "disabled"))

            @staticmethod
            def enable_no_dead_all():
                enable = arguments[1]
                if dark_souls.set_no_dead_all(enable):
                    print("NO DEAD ALL %s" % ("enabled" if enable else "disabled"))

            @staticmethod
            def enable_no_damage_all():
                enable = arguments[1]
                if dark_souls.set_no_damage_all(enable):
                    print("NO DAMAGE ALL %s" % ("enabled" if enable else "disabled"))

            @staticmethod
            def enable_no_hit_all():
                enable = arguments[1]
                if dark_souls.set_no_hit_all(enable):
                    print("NO HIT ALL %s" % ("enabled" if enable else "disabled"))

            @staticmethod
            def enable_no_attack_all():
                enable = arguments[1]
                if dark_souls.set_no_attack_all(enable):
                    print("NO ATTACK ALL %s" % ("enabled" if enable else "disabled"))

            @staticmethod
            def enable_no_move_all():
                enable = arguments[1]
                if dark_souls.set_no_move_all(enable):
                    print("NO MOVE ALL %s" % ("enabled" if enable else "disabled"))

            @staticmethod
            def enable_death_cam():
                enable = arguments[1]
                if dark_souls.death_cam(enable):
                    print("DEATH CAM %s" % ("enabled" if enable else "disabled"))

            @staticmethod
            def enable_player_dead_mode():
                enable = arguments[1]
                if dark_souls.set_player_dead_mode(enable):
                    print("PLAYER DEAD MODE %s" % ("enabled" if enable else "disabled"))

            @staticmethod
            def enable_player_exterminate():
                enable = arguments[1]
                if dark_souls.set_exterminate(enable):
                    print("PLAYER EXTERMINATE %s" % ("enabled" if enable else "disabled"))

            @staticmethod
            def enable_player_hide():
                enable = arguments[1]
                if dark_souls.set_hide(enable):
                    print("PLAYER HIDE %s" % ("enabled" if enable else "disabled"))

            @staticmethod
            def enable_player_silence():
                enable = arguments[1]
                if dark_souls.set_silence(enable):
                    print("PLAYER SILENCE %s" % ("enabled" if enable else "disabled"))

            @staticmethod
            def enable_event():
                enable = arguments[1]
                if dark_souls.disable_all_area_event(not enable):
                    print("ALL AREA EVENT %s" % ("enabled" if enable else "disabled"))

            @staticmethod
            def enable_npc():
                enable = arguments[1]
                if not enable:
                    if not dark_souls.warn_disable_npc():
                        return
                if dark_souls.disable_all_area_enemies(not enable):
                    print("ALL AREA ENEMIES %s" % ("enabled" if enable else "disabled"))

            @staticmethod
            def enable_map():
                enable = arguments[1]
                if dark_souls.disable_all_area_map(not enable):
                    print("ALL AREA MAP %s" % ("enabled" if enable else "disabled"))

            @staticmethod
            def enable_obj():
                enable = arguments[1]
                if dark_souls.disable_all_area_obj(not enable):
                    print("ALL AREA OBJ %s" % ("enabled" if enable else "disabled"))

            @staticmethod
            def enable_obj_break():
                enable = arguments[1]
                if dark_souls.enable_all_area_obj_break(enable):
                    print("ALL AREA OBJ BREAK %s" % ("enabled" if enable else "disabled"))

            @staticmethod
            def enable_hi_hit():
                enable = arguments[1]
                if dark_souls.disable_all_area_hi_hit(not enable):
                    print("ALL AREA HI HIT %s" % ("enabled" if enable else "disabled"))

            @staticmethod
            def enable_lo_hit():
                enable = arguments[1]
                if dark_souls.disable_all_area_lo_hit(not enable):
                    print("ALL AREA LO HIT %s" % ("enabled" if enable else "disabled"))

            @staticmethod
            def enable_sfx():
                enable = arguments[1]
                if dark_souls.disable_all_area_sfx(not enable):
                    print("ALL AREA SFX %s" % ("enabled" if enable else "disabled"))

            @staticmethod
            def enable_sound():
                enable = arguments[1]
                if dark_souls.disable_all_area_sound(not enable):
                    print("ALL AREA SOUND %s" % ("enabled" if enable else "disabled"))

            @staticmethod
            def enable_obj_break_record_mode():
                enable = arguments[1]
                if dark_souls.enable_obj_break_record_mode(enable):
                    print("OBJ BREAK RECORD MODE %s" % ("enabled" if enable else "disabled"))

            @staticmethod
            def enable_auto_map_warp_mode():
                enable = arguments[1]
                if dark_souls.enable_auto_map_warp_mode(enable):
                    print("AUTO MAP WARP MODE %s" % ("enabled" if enable else "disabled"))

            @staticmethod
            def enable_chr_npc_wander_test():
                enable = arguments[1]
                if dark_souls.enable_chr_npc_wander_test(enable):
                    print("CHR NPC WANDER TEST %s" % ("enabled" if enable else "disabled"))

            @staticmethod
            def enable_dbg_chr_all_dead():
                enable = arguments[1]
                if dark_souls.enable_dbg_chr_all_dead(enable):
                    print("DBG CHR ALL DEAD %s" % ("enabled" if enable else "disabled"))

            @staticmethod
            def enable_online_mode():
                enable = arguments[1]
                if dark_souls.enable_online_mode(enable):
                    print("ONLINE MODE %s" % ("enabled" if enable else "disabled"))

            @staticmethod
            def static_list():
                lines = open(DarkSouls.STATIC_SOURCE, "r").readlines()
                for line in lines:
                    print("\t", line)

            @staticmethod
            def static_clean():
                open(DarkSouls.STATIC_SOURCE, "w").write("")

        Switcher.switch()
