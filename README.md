# DarkShell
This is a command line tool for testing and debugging DARK SOULS - Prepare to Die Edition.

Type `help` for the list of commands and `help [command]` to see the usage and available options.

Example of some of the commands:
```
set name Giant Dad
set covenant darkwraith
item-get grass-crest-shield 
item-get-upgrade zweihander
disable npc
warp oolacile-township bonfire
```

To manage event flags type `enable [flag-id]` or `disable [flag-id]`, to read flags: `get [flag-id]`.

You can create custom items that you'me modded into GameParams by either:
- Spawning it by ID: `item-get [category-name] [item-ID] [count]`
OR
- Adding it to the list of known items: `item-mod add`
