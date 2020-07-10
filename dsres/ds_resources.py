from os.path import join, isfile
from os import listdir, getcwd
import sys

ROOT = getattr(sys, '_MEIPASS', getcwd())


def get_item_dir():
    return join(ROOT, "dsres", "items")


def get_item_files():
    item_dir = get_item_dir()
    item_files = [f for f in listdir(item_dir) if isfile(join(item_dir, f))]
    return item_files


def validate_item(name: str):
    for file in get_item_files():
        for item in get_items(file)[1:]:
            item = item.strip()
            if item:
                if name in item.split()[3]:
                    return False
    return True


def write_custom_item(category: str, name: str, item_id: int):
    if not validate_item(name):
        raise KeyError("Item '%s' already exists!" % " ".join(name.split("-")).title())
    for file in get_item_files():
        if file[0:6] == "custom" and category in file[7:-4]:
            with open(join(get_item_dir(), file), "a") as f:
                f.write("\n%d %d %d %s" % (item_id, 1, 0, name))
                return True
    return False


def read_custom_items():
    items = []
    for file in get_item_files():
        if file[0:6] == "custom":
            with open(join(get_item_dir(), file), "r") as f:
                for line in f.readlines()[1:]:
                    if line.strip():
                        items.append(line)
    return items


def remove_custom_item(item: str):
    for file in get_item_files():
        if file[0:6] == "custom":
            with open(join(get_item_dir(), file), "r+") as f:
                lines = f.readlines()
                f.seek(0)
                f.write(lines[0].strip())
                for line in lines[1:]:
                    if line.strip():
                        if line.split()[3].strip() != item:
                            f.write("\n" + line.strip())
                f.truncate()


def clear_custom_items(categories: dict):
    for file in get_item_files():
        if file[0:6] == "custom":
            with open(join(get_item_dir(), file), "r+") as f:
                for category in categories.keys():
                    if category in file[7:-4]:
                        f.seek(0)
                        f.write(hex(categories[category]).lstrip("0x").zfill(8))
                        f.truncate()


def get_bonfires():
    return open("%s/bonfires.txt" % join(ROOT, "dsres", "misc"), "r").readlines()


def get_items(file_name: str):
    return open("%s/%s" % (join(ROOT, "dsres", "items"), file_name), "r").readlines()


def get_infusions():
    return open("%s/infusions.txt" % join(ROOT, "dsres", "misc"), "r").readlines()


def get_covenants():
    return open("%s/covenants.txt" % join(ROOT, "dsres", "misc"), "r").readlines()
