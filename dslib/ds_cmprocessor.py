from prompt_toolkit.completion import NestedCompleter
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.shortcuts import prompt


class DSParser:

    def __init__(self, args: str):
        args = args.split()
        self.command = args[0]
        self.arguments = args[1:]

    def get_command(self):
        return self.command
    
    def get_arguments(self):
        return self.arguments


class DSCmp:
    
    com_prefix = "do_"
    prompt_prefix = "~ "
    
    def __init__(self):
        self.completer = None
        self.history = InMemoryHistory()
    
    def set_completer(self, nest: dict):
        self.completer = NestedCompleter.from_nested_dict(nest)
    
    def cmp_loop(self):
        while True:
            user_inp = prompt(
                DSCmp.prompt_prefix,
                completer=self.completer,
                history=self.history,
                enable_history_search=True
            )
            parser = DSParser(user_inp)
            command = parser.get_command()
            arguments = parser.get_arguments()
            self.execute_command(command, arguments)
    
    def execute_command(self, command, arguments):
        try:
            ds_command = getattr(self, DSCmp.com_prefix + command.replace("-", "_"))
            ds_command(arguments)
        except AttributeError as e:
            print("%s: %s" % (type(e).__name__, e))

    def do_help(self, args):
        if len(args) > 0:
            try:
                getattr(self, "help_" + args[0])()
            except AttributeError as e:
                print("%s: %s" % (type(e).__name__, e))
        else:
            commands = []
            for name in dir(self.__class__):
                if name[:len(DSCmp.com_prefix)] == DSCmp.com_prefix:
                    commands.append(name[len(DSCmp.com_prefix):].replace("_", "-"))
            commands.sort()
            for command in commands:
                print("\t%s" % command)
