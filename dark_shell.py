from dslib.ds_process import Stat
from dslib.ds_gui import DSPositionGUI
from dslib.ds_cmprocessor import DSCmp
from dsres.ds_commands import DS_NEST
from game_wrapper import DarkSouls, ArgSwitcher
from prompt_toolkit.shortcuts import set_title
from threading import Thread
from os import system, _exit
from sys import argv
import win32gui
import win32process


class DarkShell(DSCmp):

    def __init__(self, script=None):
        super(DarkShell, self).__init__()
        self.game = DarkSouls()
        self.switcher = ArgSwitcher(self.game)
        self.set_completer(DS_NEST)
        self.execute_source(script)

    @staticmethod
    def get_window_pid(title):
        hwnd = win32gui.FindWindow(None, title)
        thread_id, pid = win32process.GetWindowThreadProcessId(hwnd)
        return pid

    @staticmethod
    def do_exit(args):
        _exit(0)

    @staticmethod
    def do_quit(args):
        _exit(0)

    @staticmethod
    def do_end(args):
        _exit(0)

    @staticmethod
    def do_clear(args):
        system("cls")

    def do_begin(self, args):
        try:
            pid = DarkShell.get_window_pid(self.game.PROCESS_NAME)
            self.game.attach(pid)
            print("Successfully attached to the DARK SOULS process")
            Thread(target=self.game.check_alive).start()
            Thread(target=self.game.disable_fps_disconnect).start()
        except Exception as e:
            print("%s: %s\nCouldn't attach to the DARK SOULS process" % (type(e).__name__, e))
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
            print("%s: %s\nCouldn't launch position GUI" % (type(e).__name__, e))

    @staticmethod
    def help_set():
        print("\nUsage:\tset [option] [value]")
        print("\nOptions:")
        for opt in DS_NEST["set"].keys():
            print("\t%s" % opt)
        print("\n")

    def do_set(self, args):
        try:
            self.game.prepare()
            self.switcher.switch("set", args)
        except ValueError:
            print("Wrong parameter type: %s " % args[1])
        except Exception as e:
            print("%s: %s\nCouldn't complete the command" % (type(e).__name__, e))

    @staticmethod
    def help_enable():
        print("\nUsage:\tenable [option/flag-id]")
        print("\nOptions:")
        for opt in DS_NEST["enable"].keys():
            print("\t%s" % opt)
        print("\n")

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

                if self.game.set_no_gravity(False):
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

            elif args[0] == "player-dead-mode":

                if self.game.set_player_dead_mode(True):
                    print("DEAD MODE enabled")

            elif args[0] == "no-magic-all":

                if self.game.set_no_magic_all(True):
                    print("NO MAGIC ALL enabled")

            elif args[0] == "player-exterminate":

                if self.game.set_exterminate(True):
                    print("PLAYER EXTERMINATE enabled")

            elif args[0] == "no-ammo-consume-all":

                if self.game.set_no_ammo_consume_all(True):
                    print("NO AMMO CONSUME ALL enabled")

            elif args[0] == "player-hide":

                if self.game.set_hide(True):
                    print("PLAYER HIDE enabled")

            elif args[0] == "player-silence":

                if self.game.set_silence(True):
                    print("PLAYER SILENCE enabled")

            elif args[0] == "no-dead-all":

                if self.game.set_no_dead_all(True):
                    print("NO DEAD ALL enabled")

            elif args[0] == "no-damage-all":

                if self.game.set_no_damage_all(True):
                    print("NO DAMAGE ALL enabled")

            elif args[0] == "no-hit-all":

                if self.game.set_no_hit_all(True):
                    print("No HIT ALL enabled")

            elif args[0] == "no-attack-all":

                if self.game.set_no_attack_all(True):
                    print("NO ATTACK ALL enabled")

            elif args[0] == "no-move-all":

                if self.game.set_no_move_all(True):
                    print("NO MOVE ALL enabled")

            elif args[0] == "no-update-ai":

                if self.game.set_no_update_ai_all(True):
                    print("NO UPDATE AI ALL enabled")

            elif args[0] == "event":

                if self.game.disable_all_area_event(False):
                    print("ALL AREA EVENT enabled")

            elif args[0] == "enemies":

                if self.game.disable_all_area_enemies(False):
                    print("ALL AREA ENEMIES enabled")

            elif args[0] == "map":

                if self.game.disable_all_area_map(False):
                    print("ALL AREA MAP enabled")

            elif args[0] == "obj":

                if self.game.disable_all_area_obj(False):
                    print("ALL AREA OBJ enabled")

            elif args[0] == "obj-break":

                if self.game.enable_all_area_obj_break(True):
                    print("ALL AREA OBJ BREAK enabled")

            elif args[0] == "hi-hit":

                if self.game.disable_all_area_hi_hit(False):
                    print("ALL AREA HI HIT enabled")

            elif args[0] == "lo-hit":

                if self.game.disable_all_area_lo_hit(False):
                    print("ALL AREA LO HIT enabled")

            elif args[0] == "sfx":

                if self.game.disable_all_area_sfx(False):
                    print("ALL AREA SFX enabled")

            elif args[0] == "sound":

                if self.game.disable_all_area_sound(False):
                    print("ALL AREA SOUND enabled")

            elif args[0] == "obj-break-record-mode":

                if self.game.enable_obj_break_record_mode(True):
                    print("OBJ BREAK RECORD MODE enabled")

            elif args[0] == "auto-map-warp-mode":

                if self.game.enable_auto_map_warp_mode(True):
                    print("AUTO MAP WARP MODE enabled")

            elif args[0] == "chr-npc-wander-test":

                if self.game.enable_chr_npc_wander_test(True):
                    print("CHR NPC WANDER TEST enabled")

            elif args[0] == "dbg-chr-all-dead":

                if self.game.enable_dbg_chr_all_dead(True):
                    print("DBG CHR ALL DEAD enabled")

            elif args[0] == "online-mode":

                if self.game.enable_online_mode(True):
                    print("ONLINE MODE enabled")

            else:

                if self.game.write_event_flag(int(args[0]), True):
                    print("EVENT FLAG %s enabled" % args[0])

        except Exception as e:

            print("%s: %s\nCouldn't complete the command" % (type(e).__name__, e))

    @staticmethod
    def help_disable():
        print("\nUsage:\tdisable [option/flag-id]")
        print("\nOptions:")
        for opt in DS_NEST["disable"].keys():
            print("\t%s" % opt)
        print("\n")

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

                if self.game.set_no_gravity(True):
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

            elif args[0] == "player-dead-mode":

                if self.game.set_player_dead_mode(False):
                    print("DEAD MODE disabled")

            elif args[0] == "no-magic-all":

                if self.game.set_no_magic_all(False):
                    print("NO MAGIC ALL disabled")

            elif args[0] == "player-exterminate":

                if self.game.set_exterminate(False):
                    print("PLAYER EXTERMINATE disabled")

            elif args[0] == "no-ammo-consume-all":

                if self.game.set_no_ammo_consume_all(False):
                    print("NO AMMO CONSUME ALL disabled")

            elif args[0] == "player-hide":

                if self.game.set_hide(False):
                    print("PLAYER HIDE disabled")

            elif args[0] == "player-silence":

                if self.game.set_silence(False):
                    print("PLAYER SILENCE disabled")

            elif args[0] == "no-dead-all":

                if self.game.set_no_dead_all(False):
                    print("NO DEAD ALL disabled")

            elif args[0] == "no-damage-all":

                if self.game.set_no_damage_all(False):
                    print("NO DAMAGE ALL disabled")

            elif args[0] == "no-hit-all":

                if self.game.set_no_hit_all(False):
                    print("No HIT ALL disabled")

            elif args[0] == "no-attack-all":

                if self.game.set_no_attack_all(False):
                    print("NO ATTACK ALL disabled")

            elif args[0] == "no-move-all":

                if self.game.set_no_move_all(False):
                    print("NO MOVE ALL disabled")

            elif args[0] == "no-update-ai":

                if self.game.set_no_update_ai_all(False):
                    print("NO UPDATE AI ALL disabled")

            elif args[0] == "event":

                if self.game.disable_all_area_event(True):
                    print("ALL AREA EVENT disabled")

            elif args[0] == "enemies":

                if self.game.disable_all_area_enemies(True):
                    print("ALL AREA ENEMIES disabled")

            elif args[0] == "map":

                if self.game.disable_all_area_map(True):
                    print("ALL AREA MAP disabled")

            elif args[0] == "obj":

                if self.game.disable_all_area_obj(True):
                    print("ALL AREA OBJ disabled")

            elif args[0] == "obj-break":

                if self.game.enable_all_area_obj_break(False):
                    print("ALL AREA OBJ BREAK disabled")

            elif args[0] == "hi-hit":

                if self.game.disable_all_area_hi_hit(True):
                    print("ALL AREA HI HIT disabled")

            elif args[0] == "lo-hit":

                if self.game.disable_all_area_lo_hit(True):
                    print("ALL AREA LO HIT disabled")

            elif args[0] == "sfx":

                if self.game.disable_all_area_sfx(True):
                    print("ALL AREA SFX disabled")

            elif args[0] == "sound":

                if self.game.disable_all_area_sound(True):
                    print("ALL AREA SOUND disabled")

            elif args[0] == "obj-break-record-mode":

                if self.game.enable_obj_break_record_mode(False):
                    print("OBJ BREAK RECORD MODE disabled")

            elif args[0] == "auto-map-warp-mode":

                if self.game.enable_auto_map_warp_mode(False):
                    print("AUTO MAP WARP MODE disabled")

            elif args[0] == "chr-npc-wander-test":

                if self.game.enable_chr_npc_wander_test(False):
                    print("CHR NPC WANDER TEST disabled")

            elif args[0] == "dbg-chr-all-dead":

                if self.game.enable_dbg_chr_all_dead(False):
                    print("DBG CHR ALL DEAD disabled")

            elif args[0] == "online-mode":

                if self.game.enable_online_mode(False):
                    print("ONLINE MODE disabled")
            else:

                if self.game.write_event_flag(int(args[0]), False):
                    print("EVENT FLAG %s disabled" % args[0])

        except Exception as e:

            print("%s: %s\nCouldn't complete the command" % (type(e).__name__, e))

    @staticmethod
    def help_get():
        print("\nUsage:\tget [option]")
        print("\nOptions:")
        for opt in DS_NEST["get"].keys():
            print("\t%s" % opt)
        print("\n")

    def do_get(self, args):

        try:

            self.game.prepare()

            if args[0] == "stats":
                self.game.print_stats()

            else:

                print("FLAG %s: %s" % (args[0], self.game.read_event_flag(int(args[0]))))

        except Exception as e:

            print("%s: %s\nCouldn't complete the command" % (type(e).__name__, e))

    def do_game_restart(self, args):
        try:
            self.game.prepare()
            if self.game.game_restart():
                print("Game restarted")
        except Exception as e:
            print("%s: %s\nCouldn't complete the command" % (type(e).__name__, e))

    def do_menu_kick(self, args):
        self.game.menu_kick()

    @staticmethod
    def help_item_drop():
        print("\nUsage:\titem-drop [item-name]\n")

    def do_item_drop(self, args):
        try:
            self.game.prepare()
            i_name, i_count = DarkSouls.get_item_name_and_count(args)
            if i_count > 0:
                self.game.create_item(i_name, i_count, func=self.game.item_drop)
        except Exception as e:
            print("%s: %s\nCouldn't complete the command" % (type(e).__name__, e))

    @staticmethod
    def help_item_get():
        print("\nUsage:\titem-get [item-name]\n")

    def do_item_get(self, args):
        try:
            self.game.prepare()
            i_name, i_count = DarkSouls.get_item_name_and_count(args)
            if i_count > 0:
                self.game.create_item(i_name, i_count, func=self.game.item_get)
        except Exception as e:
            print("%s: %s\nCouldn't complete the command" % (type(e).__name__, e))

    @staticmethod
    def help_item_get_upgrade():
        print("\nUsage:\titem-get-upgrade [item-name]\n")

    def do_item_get_upgrade(self, args):
        try:
            self.game.prepare()
            i_name, i_count = DarkSouls.get_item_name_and_count(args)
            if i_count > 0:
                self.game.upgrade_item(i_name, i_count)
        except Exception as e:
            print("%s: %s\nCouldn't complete the command" % (type(e).__name__, e))

    @staticmethod
    def help_warp():
        print("\nUsage:\twarp [option [option]]")
        print("\nOptions:")
        for opt in DS_NEST["warp"].keys():
            if DS_NEST["warp"][opt] is not None:
                places = " [ "
                for place in DS_NEST["warp"][opt].keys():
                    places += place + " "
                opt += places + "]"
            print("\t%s" % opt)
        print("\n")

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
            print("%s: %s\nCouldn't complete the command" % (type(e).__name__, e))


if __name__ == "__main__":
    set_title("Dark Shell")
    source = argv[1] if len(argv) > 1 else None
    if source is None:
        print("Welcome to Dark Shell")
        print("Type 'begin' to find the DARK SOULS process")
    DarkShell(source).cmp_loop()
