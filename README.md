# dark-shell
This is a command line tool for testing and debugging DARK SOULS - Prepare to Die Edition.

Type `help` for the list of commands and `help [command]` to see the usage and available options.

Example of some of the commands:
```
set name jorgen
set covenant darkwraith
item-get mask-of-the-father
item-get-upgrade zweihander
disable npc
warp firelink-shrine bonfire
```

To manage event flags type `enable [flag-id]` or `disable [flag-id]`, to read flags: `get [flag-id]`.

If you want a certain command to be executed every time the program or the game is reloaded, use the `static` command:
```
static enable no-dead
static item-drop titanite-slab 3
```
