from dslib.ds_process import Stat
from dslib.ds_gui import DSPositionGUI, DSGraphicsGUI
from dslib.ds_cmprocessor import DSCmp
from dsres.ds_commands import DS_NEST, DS_STATIC
from game_wrapper import DarkSouls
from prompt_toolkit.shortcuts import set_title
from threading import Thread
from os import system, _exit
from sys import argv
from time import sleep
import win32gui
import win32process


class DarkShell(DSCmp):

    def __init__(self, script=None):
        super(DarkShell, self).__init__()
        self.run_static = True if script is None else False
        self.game = DarkSouls()
        self.set_nested_completer(DS_NEST)
        self.execute_source(script)

    def execute_static_commands(self):
        execute = True
        while True:
            if execute:
                if self.game.can_read():
                    self.execute_source(self.game.STATIC_SOURCE)
                    execute = False
                else:
                    sleep(1)
                    continue
            if not self.game.can_read():
                execute = True
            sleep(1)

    @staticmethod
    def get_window_pid(title):
        hwnd = win32gui.FindWindow(None, title)
        thread_id, pid = win32process.GetWindowThreadProcessId(hwnd)
        return pid

    @staticmethod
    def do_clear(args):
        system("cls")

    @staticmethod
    def do_exit(args):
        _exit(0)

    @staticmethod
    def do_quit(args):
        _exit(0)

    @staticmethod
    def do_end(args):
        _exit(0)

    def do_begin(self, args):
        try:
            pid = DarkShell.get_window_pid(self.game.PROCESS_NAME)
            self.game.attach(pid)
            self.game.prepare()
            print("Successfully attached to the DARK SOULS process")
            print("Game version: %s" % self.game.version)
            Thread(target=self.game.check_alive).start()
            Thread(target=self.game.disable_fps_disconnect).start()
        except Exception as e:
            print("%s: %s\nCouldn't attach to the DARK SOULS process" % (type(e).__name__, e))
        else:
            rbn = Thread(target=self.game.read_bonfires)
            rit = Thread(target=self.game.read_items)
            rin = Thread(target=self.game.read_infusions)
            rco = Thread(target=self.game.read_covenants)
            rbn.start(), rit.start(), rin.start(), rco.start()
            for stat in vars(Stat).values():
                if type(stat) == Stat:
                    self.game.stats[stat] = self.game.get_stat(stat)
            rbn.join(), rit.join(), rin.join(), rco.join()
            if self.run_static:
                Thread(target=self.execute_static_commands).start()

    @staticmethod
    def help_static():
        print("\nUsage:\t",
              "static [command [args]]\n\t",
              "static list\n\t",
              "static clean\n\t",
              "static remove [line-num]")
        print("\nOptions:")
        for opt in DS_STATIC.keys():
            print("\t%s" % opt)
        print("\n")

    def do_static(self, args):
        try:
            if args[0] in DS_STATIC.keys():
                self.game.switch(command="static", arguments=args)
            else:
                if args[0] not in DS_NEST.keys():
                    print("Unrecognized command: %s" % args[0])
                else:
                    print("Command '%s' can't be static!" % args[0])
        except FileNotFoundError:
            pass

    def do_pos_gui(self, args):
        try:
            self.game.prepare()
            DSPositionGUI(process=self.game).mainloop()
        except Exception as e:
            print("%s: %s\nCouldn't launch position GUI" % (type(e).__name__, e))

    def do_graphics_gui(self, args):
        try:
            self.game.prepare()
            DSGraphicsGUI(process=self.game).mainloop()
        except Exception as e:
            print("%s: %s\nCouldn't launch graphics GUI" % (type(e).__name__, e))

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
            self.game.switch(command="set", arguments=args)
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
            self.game.switch(command="enable", arguments=args+[True])
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
            self.game.switch(command="enable", arguments=args+[False])
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
            self.game.switch(command="get", arguments=args)
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
    DarkShell(script=source).cmp_loop()
