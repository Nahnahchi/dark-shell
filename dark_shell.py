from dslib.gui import DSPositionGUI, DSGraphicsGUI
from dslib.cmd import DSCmd
from dslib.process import wait_for
from dsres.commands import DS_NEST, nest_add
from dsres.resources import read_mod_items
from dslib.manager import DarkSouls
from dsobj.item import DSItem
from prompt_toolkit.shortcuts import set_title
from threading import Thread, Event
from os import system, _exit
from _version import __version__, check_for_updates, MetaError
from sys import argv, _getframe
from traceback import format_exc
from colorama import Fore, init

_DEBUG = False
_FLAGS = {
    "help": ("-h", "--help"),
    "debug": ("-d", "--debug")
}


class DarkShell(DSCmd):

    def __init__(self):
        super(DarkShell, self).__init__(_DEBUG)
        sync_evt = Event()
        nest_add([DSItem(item.strip(), -1).get_name() for item in read_mod_items()])
        self.set_nested_completer(DS_NEST)
        self.game_man = DarkSouls(_DEBUG)
        Thread(target=self._execute_static_commands, args=(sync_evt,)).start()
        Thread(target=self._execute_waiting_commands, args=(sync_evt,)).start()
        Thread(target=self.game_man.load_saved_func, args=(sync_evt,)).start()

    def _execute_static_commands(self, sync_execute: Event):
        sync_execute.wait()
        while True:
            wait_for(self.game_man.is_loaded)
            static_commands = DarkSouls.STATIC_FUNC.copy()
            for func, args in static_commands.items():
                try:
                    self.game_man.switch(command=func[0], arguments=args)
                except Exception as e:
                    print(Fore.RED + (format_exc() if _DEBUG else "%s in '%s' — %s" % (
                        type(e).__name__, _getframe().f_code.co_name, e)) + Fore.RESET)
            wait_for(self.game_man.is_loaded, desired_state=False)

    def _execute_waiting_commands(self, sync_execute: Event):
        sync_execute.wait()
        waiting_commands = DarkSouls.WAITING_FUNC.copy()
        for evt_hash, entry in waiting_commands.items():
            try:
                event = Event()
                flag_id = entry["val"][0]
                flag_state = entry["val"][1]
                command = entry["arg"][0]
                args = entry["arg"][1:]
                Thread(target=self.game_man.start_listen, args=(evt_hash, flag_id, flag_state, event)).start()
                Thread(target=self._delay_command, args=(command, args, event)).start()
            except Exception as e:
                print(Fore.RED + (format_exc() if _DEBUG else "%s in '%s' — %s" % (
                    type(e).__name__, _getframe().f_code.co_name, e)) + Fore.RESET)

    def _delay_command(self, command: str, args: list, evt: Event):
        evt.wait()
        self.execute_command(command, args)

    @staticmethod
    def help_clear():
        pass

    @staticmethod
    def do_clear(args):
        system("cls")

    @staticmethod
    def help_exit():
        pass

    @staticmethod
    def do_exit(args):
        _exit(0)

    @staticmethod
    def help_meta():
        print(Fore.LIGHTBLUE_EX + "\nUsage:" + Fore.LIGHTYELLOW_EX + "\tmeta [option [option]]")
        print(Fore.LIGHTBLUE_EX + "\nOptions:" + Fore.LIGHTYELLOW_EX)
        for com in DS_NEST["meta"].keys():
            if DS_NEST["meta"][com] is not None:
                opts = " [ "
                for opt in DS_NEST["meta"][com].keys():
                    opts += opt + " "
                com += opts + "]"
            print("\t%s" % com)
        print(Fore.RESET)

    def do_meta(self, args):
        try:
            self.game_man.switch(command="meta", arguments=args)
        except Exception as e:
            print(Fore.RED + (format_exc() if _DEBUG else "%s: %s" % (type(e).__name__, e)) + Fore.RESET)

    @staticmethod
    def help_on_flag():
        print(Fore.LIGHTBLUE_EX + "\nUsage:" + Fore.LIGHTYELLOW_EX + "\ton-flag [option [option]]")
        print(Fore.LIGHTBLUE_EX + "\nOptions:" + Fore.LIGHTYELLOW_EX)
        for opt in DS_NEST["on-flag"].keys():
            print("\t%s" % opt)
        print(Fore.RESET)

    def do_on_flag(self, args):
        try:
            wait_evt = Event()
            self.game_man.switch(command="on-flag", arguments=["notify", wait_evt])
            Thread(target=self._delay_command, args=(args[0], args[1:], wait_evt)).start()
            DarkSouls.WAITING_FUNC[hash(wait_evt)].update({"arg": args})
            self.game_man.save_func()
        except Exception as e:
            print(Fore.RED + (format_exc() if _DEBUG else "%s: %s" % (type(e).__name__, e)) + Fore.RESET)

    @staticmethod
    def help_pos_gui():
        pass

    def do_pos_gui(self, args):
        try:
            DSPositionGUI(process=self.game_man).mainloop()
        except Exception as e:
            print(Fore.RED + (format_exc() if _DEBUG else "%s: %s" % (type(e).__name__, e)) + Fore.RESET)

    @staticmethod
    def help_graphics_gui():
        pass

    def do_graphics_gui(self, args):
        try:
            DSGraphicsGUI(process=self.game_man).mainloop()
        except Exception as e:
            print(Fore.RED + (format_exc() if _DEBUG else "%s: %s" % (type(e).__name__, e)) + Fore.RESET)

    @staticmethod
    def help_set():
        print("\nUsage:\tset [option] [value]")
        print("\nOptions:")
        for opt in DS_NEST["set"].keys():
            print("\t%s" % opt)
        print("\n")

    def do_set(self, args):
        try:
            self.game_man.switch(command="set", arguments=args)
        except Exception as e:
            print(Fore.RED + (format_exc() if _DEBUG else "%s: %s" % (type(e).__name__, e)) + Fore.RESET)

    @staticmethod
    def help_enable():
        print("\nUsage:\tenable [option/flag-id]")
        print("\nOptions:")
        for opt in DS_NEST["enable"].keys():
            print("\t%s" % opt)
        print("\n")

    def do_enable(self, args):
        try:
            self.game_man.switch(command="enable", arguments=args + [True])
        except Exception as e:
            print(Fore.RED + (format_exc() if _DEBUG else "%s: %s" % (type(e).__name__, e)) + Fore.RESET)

    @staticmethod
    def help_disable():
        print("\nUsage:\tdisable [option/flag-id]")
        print("\nOptions:")
        for opt in DS_NEST["disable"].keys():
            print("\t%s" % opt)
        print("\n")

    def do_disable(self, args):
        try:
            self.game_man.switch(command="enable", arguments=args + [False])
        except Exception as e:
            print(Fore.RED + (format_exc() if _DEBUG else "%s: %s" % (type(e).__name__, e)) + Fore.RESET)

    @staticmethod
    def help_get():
        print("\nUsage:\tget [option/flag-id]")
        print("\nOptions:")
        for opt in DS_NEST["get"].keys():
            print("\t%s" % opt)
        print("\n")

    def do_get(self, args):
        try:
            self.game_man.switch(command="get", arguments=args)
        except Exception as e:
            print(Fore.RED + (format_exc() if _DEBUG else "%s: %s" % (type(e).__name__, e)) + Fore.RESET)

    @staticmethod
    def help_game_restart():
        pass

    def do_game_restart(self, args):
        try:
            if self.game_man.game_restart():
                print("Game restarted")
        except Exception as e:
            print(Fore.RED + (format_exc() if _DEBUG else "%s: %s" % (type(e).__name__, e)) + Fore.RESET)

    @staticmethod
    def help_force_menu():
        pass

    def do_force_menu(self, args):
        self.game_man.menu_kick()

    @staticmethod
    def help_item_drop():
        print("\nUsage:\titem-drop [item-name [count]]\n")
        print("\titem-drop [category-name] [item-ID] [count]\n")

    def do_item_drop(self, args):
        try:
            if len(args) > 0 and args[0] in DarkSouls.ITEM_CATEGORIES:
                DarkSouls.create_custom_item(args, func=self.game_man.item_drop)
                return
            i_name, i_count = DarkSouls.get_item_name_and_count(args)
            if i_count > 0:
                self.game_man.create_item(i_name, i_count, func=self.game_man.item_drop)
        except Exception as e:
            print(Fore.RED + (format_exc() if _DEBUG else "%s: %s" % (type(e).__name__, e)) + Fore.RESET)

    @staticmethod
    def help_item_get():
        print("\nUsage:\titem-get [item-name [count]]\n")
        print("\titem-get [category-name] [item-ID] [count]\n")

    def do_item_get(self, args):
        try:
            if len(args) > 0 and args[0] in DarkSouls.ITEM_CATEGORIES:
                DarkSouls.create_custom_item(args, func=self.game_man.item_get)
                return
            i_name, i_count = DarkSouls.get_item_name_and_count(args)
            if i_count > 0:
                self.game_man.create_item(i_name, i_count, func=self.game_man.item_get)
        except Exception as e:
            print(Fore.RED + (format_exc() if _DEBUG else "%s: %s" % (type(e).__name__, e)) + Fore.RESET)

    @staticmethod
    def help_item_mod():
        print("\nUsage:\titem-mod add\n")
        print("\titem-mod remove [item-name]\n")
        print("\titem-mod list\n")
        print("\titem-mod clear\n")

    def do_item_mod(self, args):
        try:
            if DarkSouls.add_new_item(args):
                self.set_nested_completer(DS_NEST)
                Thread(target=self.game_man.read_items).start()
        except Exception as e:
            print(Fore.RED + (format_exc() if _DEBUG else "%s: %s" % (type(e).__name__, e)) + Fore.RESET)

    @staticmethod
    def help_item_get_upgrade():
        print("\nUsage:\titem-get-upgrade [item-name]\n")

    def do_item_get_upgrade(self, args):
        try:
            i_name, i_count = DarkSouls.get_item_name_and_count(args)
            if i_count > 0:
                self.game_man.upgrade_item(i_name, i_count)
        except Exception as e:
            print(Fore.RED + (format_exc() if _DEBUG else "%s: %s" % (type(e).__name__, e)) + Fore.RESET)

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
            if len(args) == 0:
                DarkSouls.raise_warp_error("")
            if args[0] == "bonfire":
                self.game_man.bonfire_warp()
            else:
                b_name = " ".join(args[0:])
                self.game_man.bonfire_warp_by_name(b_name)
        except Exception as e:
            print(Fore.RED + (format_exc() if _DEBUG else "%s: %s" % (type(e).__name__, e)) + Fore.RESET)

    @staticmethod
    def help_notify():
        pass

    def do_notify(self, args):
        try:
            Thread(target=self.game_man.notify).start()
        except Exception as e:
            print(Fore.RED + (format_exc() if _DEBUG else "%s: %s" % (type(e).__name__, e)) + Fore.RESET)

    @staticmethod
    def help_unlock_all_gestures():
        pass

    def do_unlock_all_gestures(self, args):
        try:
            if self.game_man.unlock_all_gestures():
                print("All gestures unlocked")
        except Exception as e:
            print(Fore.RED + (format_exc() if _DEBUG else "%s: %s" % (type(e).__name__, e)) + Fore.RESET)


def has_flag(key: str):
    for arg in argv:
        if arg in _FLAGS[key]:
            return True
    return False


if __name__ == "__main__":
    init()
    if has_flag("debug"):
        _DEBUG = True
    if has_flag("help"):
        print(Fore.LIGHTBLUE_EX + "Available options:" + Fore.LIGHTYELLOW_EX)
        for f in _FLAGS.values():
            print("\t%s" % str(f))
        exit()
    print(Fore.LIGHTYELLOW_EX + "Loading..." + Fore.RESET)
    set_title("DarkShell")
    try:
        if _DEBUG:
            raise MetaError(reason="Skipping the update check", message="Debug State")
        is_latest, version = check_for_updates()
    except MetaError as ex:
        if _DEBUG:
            print(Fore.LIGHTYELLOW_EX + str(ex) + Fore.RESET)
        is_latest, version = True, __version__
    if not _DEBUG:
        DarkShell.do_clear(args=[])
    print(Fore.LIGHTBLUE_EX + "Welcome to DarkShell %s%s" % (
        "v" + __version__, (" (v%s is available)" % version) if not is_latest else "" + Fore.RESET))
    try:
        DarkShell().cmd_loop()
    except Exception as ex:
        print(Fore.RED + (format_exc() if _DEBUG else "FATAL | %s: %s" % (type(ex).__name__, ex)) + Fore.RESET)
        input()
        _exit(1)
