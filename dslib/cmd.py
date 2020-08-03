from prompt_toolkit.completion import Completion, NestedCompleter, WordCompleter, CompleteEvent
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.shortcuts import prompt
from prompt_toolkit.document import Document
from traceback import format_exc
from colorama import Fore
from sys import _getframe
from typing import Iterable


class DSCompleter(NestedCompleter):

    def get_completions(self, document: Document, complete_event: CompleteEvent) -> Iterable[Completion]:
        text = document.text_before_cursor.lstrip()
        stripped_len = len(document.text_before_cursor) - len(text)
        if " " in text:
            first_term = text.split()[0]
            completer = self.options.get(first_term)
            if completer is not None:
                remaining_text = text[len(first_term):].lstrip()
                move_cursor = len(text) - len(remaining_text) + stripped_len
                new_document = Document(
                    remaining_text,
                    cursor_position=document.cursor_position - move_cursor,
                )
                for c in completer.get_completions(new_document, complete_event):
                    yield c
        else:
            completer = WordCompleter(
                list(self.options.keys()), ignore_case=self.ignore_case, WORD=True
            )
            for c in completer.get_completions(document, complete_event):
                yield c


class DSCmd:

    com_prefix = "do"
    help_prefix = "help"
    default = "default"
    prompt_prefix = "~ "
    
    def __init__(self, debug=False):
        self._debug = debug
        self._completer = None
        self._history = InMemoryHistory()

    class Parser:

        def __init__(self, args: str):
            args = args.split()
            self.command = args[0] if len(args) > 0 else DSCmd.default
            self.arguments = args[1:] if len(args) > 1 else [DSCmd.default]

        def get_command(self):
            return self.command

        def get_arguments(self):
            return self.arguments

    @staticmethod
    def get_method_name(prefix: str, name: str):
        return prefix.replace("-", "_") + "_" + name.replace("-", "_")

    def set_nested_completer(self, nest: dict):
        self._completer = DSCompleter.from_nested_dict(nest)
    
    def cmd_loop(self):
        while True:
            try:
                user_inp = prompt(
                    DSCmd.prompt_prefix,
                    completer=self._completer,
                    history=self._history,
                    enable_history_search=True
                )
                parser = DSCmd.Parser(user_inp)
                self.execute_command(
                    command=parser.get_command(),
                    arguments=parser.get_arguments()
                )
            except KeyboardInterrupt:
                if self._debug:
                    print(Fore.RED + format_exc() + Fore.RESET)

    def execute_command(self, command, arguments):
        try:
            getattr(
                self, DSCmd.get_method_name(
                    prefix=DSCmd.com_prefix,
                    name=command
                )
            )(arguments)
        except AttributeError as e:
            print(Fore.RED + (format_exc() if self._debug else "%s in '%s' — %s" % (
                type(e).__name__, _getframe().f_code.co_name, e)) + Fore.RESET)

    def do_help(self, args):
        if args[0] != DSCmd.default:
            try:
                getattr(self, DSCmd.get_method_name(prefix=DSCmd.help_prefix, name=args[0]))()
            except AttributeError as e:
                print(Fore.RED + (format_exc() if self._debug else "%s in '%s' — %s" % (
                    type(e).__name__, _getframe().f_code.co_name, e)) + Fore.RESET)
        else:
            prefix = DSCmd.get_method_name(prefix=DSCmd.com_prefix, name="")
            prefix_len = len(prefix)
            commands = []
            for name in dir(self.__class__):
                if name[:prefix_len] == prefix:
                    com_name = name[prefix_len:]
                    if com_name != DSCmd.default:
                        commands.append(com_name.replace("_", "-"))
            commands.sort()
            print(Fore.LIGHTYELLOW_EX)
            for command in commands:
                print("\t%s" % command)
            print(Fore.RESET)

    def do_default(self, args):
        if self._debug:
            print(Fore.BLUE + "time for crab" + Fore.RESET)