from prompt_toolkit.completion import NestedCompleter
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.shortcuts import prompt


class DSParser:

    def __init__(self, args: str):
        args = args.split()
        self.command = args[0] if len(args) > 0 else ""
        self.arguments = args[1:] if len(args) > 1 else ""

    def get_command(self):
        return self.command
    
    def get_arguments(self):
        return self.arguments


class DSCmd:
    
    com_prefix = "do_"
    help_prefix = "help_"
    prompt_prefix = "~ "
    
    def __init__(self):
        self.completer = None
        self.history = InMemoryHistory()

    @staticmethod
    def get_method_name(prefix: str, name: str):
        return prefix + name.replace("-", "_")

    def set_nested_completer(self, nest: dict):
        self.completer = NestedCompleter.from_nested_dict(nest)
    
    def cmd_loop(self):
        while True:
            try:
                user_inp = prompt(
                    DSCmd.prompt_prefix,
                    completer=self.completer,
                    history=self.history,
                    enable_history_search=True
                )
                parser = DSParser(user_inp)
                command = parser.get_command()
                arguments = parser.get_arguments()
                self.execute_command(command, arguments)
            except KeyboardInterrupt:
                pass

    def execute_command(self, command, arguments):
        try:
            getattr(self,
                    DSCmd.get_method_name(
                        prefix=DSCmd.com_prefix,
                        name=command if command.strip() else "default")
                    )(arguments)
        except AttributeError as e:
            print("%s: %s" % (type(e).__name__, e))

    def execute_source(self, source):
        if source is not None:
            try:
                commands = open(source, "r").readlines()
                for command in commands:
                    parser = DSParser(command)
                    self.execute_command(
                        command=parser.get_command(),
                        arguments=parser.get_arguments()
                    )
            except (PermissionError, FileNotFoundError, EOFError) as e:
                print("%s: %s" % (type(e).__name__, e))

    def do_help(self, args):
        if len(args) > 0:
            try:
                getattr(self, DSCmd.get_method_name(prefix=DSCmd.help_prefix, name=args[0]))()
            except AttributeError as e:
                print("%s: %s" % (type(e).__name__, e))
        else:
            commands = []
            for name in dir(self.__class__):
                prefix_len = len(DSCmd.com_prefix)
                if name[:prefix_len] == DSCmd.com_prefix:
                    com_name = name[prefix_len:]
                    if com_name != "default":
                        commands.append(com_name.replace("_", "-"))
            commands.sort()
            print("\n")
            for command in commands:
                print("\t%s" % command)
            print("\n")

    def do_default(self, args):
        pass
