from dslib.ds_gui import DSPositionGUI, DSGraphicsGUI
from dslib.ds_cmd import DSCmd
from dsres.ds_commands import DS_NEST, DS_STATIC, nest_add
from dsres.ds_resources import read_custom_items
from dslib.ds_wrapper import DarkSouls
from prompt_toolkit.shortcuts import set_title
from threading import Thread
from os import system, _exit


class DarkShell(DSCmd):

    def __init__(self):
        super(DarkShell, self).__init__()
        nest_add([item.split()[3] for item in read_custom_items() if len(item.split()) == 4])
        self.set_nested_completer(DS_NEST)
        self.game = DarkSouls()
        open(self.game.STATIC_SOURCE, "a")
        Thread(target=self.execute_static_commands).start()

    def execute_static_commands(self):
        execute = True
        while True:
            if execute:
                if self.game.is_loaded():
                    self.execute_source(self.game.STATIC_SOURCE)
                    execute = False
                else:
                    continue
            if not self.game.is_loaded():
                execute = True

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
            DSPositionGUI(process=self.game).mainloop()
        except Exception as e:
            print("%s: %s\nCouldn't launch position GUI" % (type(e).__name__, e))

    def do_graphics_gui(self, args):
        try:
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
            self.game.switch(command="set", arguments=args)
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
            self.game.switch(command="enable", arguments=args+[False])
        except Exception as e:
            print("%s: %s\nCouldn't complete the command" % (type(e).__name__, e))

    @staticmethod
    def help_get():
        print("\nUsage:\tget [option/flag-id]")
        print("\nOptions:")
        for opt in DS_NEST["get"].keys():
            print("\t%s" % opt)
        print("\n")

    def do_get(self, args):
        try:
            self.game.switch(command="get", arguments=args)
        except Exception as e:
            print("%s: %s\nCouldn't complete the command" % (type(e).__name__, e))

    def do_game_restart(self, args):
        try:
            if self.game.game_restart():
                print("Game restarted")
        except Exception as e:
            print("%s: %s\nCouldn't complete the command" % (type(e).__name__, e))

    def do_menu_kick(self, args):
        self.game.menu_kick()

    @staticmethod
    def help_item_drop():
        print("\nUsage:\titem-drop [item-name [count]]\n")
        print("\titem-drop [category-name] [item-ID] [count]\n")

    def do_item_drop(self, args):
        try:
            if args[0] in DarkSouls.ITEM_CATEGORIES:
                DarkSouls.create_custom_item(args, func=self.game.item_drop)
                return
            i_name, i_count = DarkSouls.get_item_name_and_count(args)
            if i_count > 0:
                self.game.create_item(i_name, i_count, func=self.game.item_drop)
        except Exception as e:
            print("%s: %s\nCouldn't complete the command" % (type(e).__name__, e))

    @staticmethod
    def help_item_get():
        print("\nUsage:\titem-get [item-name [count]]\n")
        print("\titem-get [category-name] [item-ID] [count]\n")

    def do_item_get(self, args):
        try:
            if args[0] in DarkSouls.ITEM_CATEGORIES:
                DarkSouls.create_custom_item(args, func=self.game.item_get)
                return
            i_name, i_count = DarkSouls.get_item_name_and_count(args)
            if i_count > 0:
                self.game.create_item(i_name, i_count, func=self.game.item_get)
        except Exception as e:
            print("%s: %s\nCouldn't complete the command" % (type(e).__name__, e))

    @staticmethod
    def help_item_mod():
        print("\nUsage:\titem-mod add\n")
        print("\titem-mod remove [item-name]\n")
        print("\titem-mod clear\n")

    def do_item_mod(self, args):
        try:
            if DarkSouls.add_new_item(args):
                self.set_nested_completer(DS_NEST)
                Thread(target=self.game.read_items).start()
        except Exception as e:
            print("%s: %s\nCouldn't complete the command" % (type(e).__name__, e))

    @staticmethod
    def help_item_get_upgrade():
        print("\nUsage:\titem-get-upgrade [item-name]\n")

    def do_item_get_upgrade(self, args):
        try:
            i_name, i_count = DarkSouls.get_item_name_and_count(args)
            if i_count > 0:
                self.game.upgrade_item(i_name, i_count)
        except Exception as e:
            print("%s: %s\nCouldn't complete the command" % (type(e).__name__, e))

    @staticmethod
    def help_warp():
        print("\nUsage:\twarp [area-name [bonfire-name]]")
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
            if args[0] == "bonfire":
                if not self.game.bonfire_warp():
                    print("Failed to warp | Memory couldn't be written")
            else:
                b_name = " ".join(args[0:])
                self.game.bonfire_warp_by_name(b_name)
        except Exception as e:
            print("%s: %s\nCouldn't complete the command" % (type(e).__name__, e))

    def do_unlock_all_gestures(self, args):
        try:
            if self.game.unlock_all_gestures():
                print("All gestures unlocked")
        except Exception as e:
            print("%s: %s\nCouldn't complete the command" % (type(e).__name__, e))


if __name__ == "__main__":
    set_title("Dark Shell")
    print("Welcome to Dark Shell")
    DarkShell().cmd_loop()
