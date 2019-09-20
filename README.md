# dark-shell
This is a command line tool for testing and debugging DARK SOULS - Prepare to Die Edition.

Type `help` for the list of commands and `help [command]` to see the usage and available options.

To run a script create a text file with something like:
```
begin
set name jorgen
set covenant darkwraith
item-get mask-of-the-father
item-get-upgrade zweihander
disable npc
warp firelink-shrine bonfire
end
```
Pass the script to the program as a parameter: `python dark_shell.py myscript.txt`.

To manage event flags type `enable [flag-id]` or `disable [flag-id]`, to read flags: `get [flag-id]`.
