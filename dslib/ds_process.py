from enum import Enum, auto
from collections import defaultdict
from dslib.ds_interface import DSInterface
from dslib.ds_offsets import DSPointersRelease, DSPointersDebug
from ctypes import ArgumentError


class Data(Enum):

    CHAR_DATA_A = auto()
    ANIM_DATA = auto()
    CHAR_POS_DATA = auto()
    CHAR_MAP_DATA = auto()
    CHAR_DATA_B = auto()
    GRAPHICS_DATA = auto()
    WORLD_STATE = auto()
    MENU_MANAGER = auto()
    CHR_FOLLOW_CAM = auto()
    EVENT_FLAGS = auto()
    UNKNOWN_A = auto()
    UNKNOWN_B = auto()
    UNKNOWN_C = auto()
    UNKNOWN_D = auto()
    GESTURES = auto()
    GAME_MAN = auto()


class DSProcess:

    CHECK_VERSION = 0x400080

    DARKSOULS_VERSIONS = ({
        0xFC293654: "Steam",
        0xCE9634B4: "Debug",
        0xE91B11E2: "Beta"
    })

    EVENT_FLAG_GROUPS = {
        "0": 0x00000,
        "1": 0x00500,
        "5": 0x05F00,
        "6": 0x0B900,
        "7": 0x11300
    }

    EVENT_FLAG_AREAS = {
        "000": 0,
        "100": 1,
        "101": 2,
        "102": 3,
        "110": 4,
        "120": 5,
        "121": 6,
        "130": 7,
        "131": 8,
        "132": 9,
        "140": 10,
        "141": 11,
        "150": 12,
        "151": 13,
        "160": 14,
        "170": 15,
        "180": 16,
        "181": 17
    }

    class Scripts:

        ITEM_DROP = "mov ebp, %s\n" \
                    "mov ebx, %s\n" \
                    "mov ecx, 0xFFFFFFFF\n" \
                    "mov edx, %s\n" \
                    "mov eax, [%s]\n" \
                    "mov [eax + 0x828], ebp\n" \
                    "mov [eax + 0x82C], ebx\n" \
                    "mov [eax + 0x830], ecx\n" \
                    "mov [eax + 0x834], edx\n" \
                    "mov eax, [%s]\n" \
                    "push eax\n" \
                    "call %s\n" \
                    "ret\n"

        ITEM_GET = "﻿mov edi, %s\n" \
                   "mov ecx, %s\n" \
                   "mov esi, %s\n" \
                   "mov ebp, %s\n" \
                   "mov ebx, 0xFFFFFFFF\n" \
                   "push 0x0\n" \
                   "push 0x1\n" \
                   "push ebp\n" \
                   "push esi\n" \
                   "push ecx\n" \
                   "push edi\n" \
                   "call %s\n" \
                   "ret\n"

        BONFIRE_WARP = "mov esi, [%s]\n" \
                       "mov edi, 0x1\n" \
                       "push edi\n" \
                       "call %s\n" \
                       "ret\n"

        LEVEL_UP = "mov eax, %s\n" \
                   "mov ecx, %s\n" \
                   "call %s\n" \
                   "ret\n"

    def __init__(self, pid):
        self.pointers = defaultdict(int)
        self.id = pid
        self.interface = DSInterface(pid)
        try:
            self.version = self.DARKSOULS_VERSIONS[self.interface.read_uint(self.CHECK_VERSION)]
        except KeyError:
            self.version = "Unknown"
        finally:
            self.valid = True if self.version == "Steam" or self.version == "Debug" else False
            if not self.valid:
                raise Exception("Your DARK SOULS version is not supported")
            else:
                self.offsets = DSPointersRelease if self.version == "Steam" else DSPointersDebug
                self.load_pointers()

    def load_pointers(self):

        offsets = self.offsets
        read_mem = self.interface.read_int

        pointer1 = read_mem(offsets.CHAR_DATA_POINTER_A1)
        pointer1 = read_mem(pointer1 + offsets.CHAR_DATA_POINTER_A2)
        self.pointers[Data.CHAR_DATA_A] = self.interface.read_int(pointer1 + offsets.CHAR_DATA_POINTER_A3)
        self.pointers[Data.CHAR_MAP_DATA] = read_mem(self.pointers[Data.CHAR_DATA_A] +
                                                     offsets.CharDataA.CHAR_MAP_DATA_POINTER)
        self.pointers[Data.ANIM_DATA] = read_mem(self.pointers[Data.CHAR_MAP_DATA] +
                                                 offsets.CharMapData.ANIM_DATA_POINTER)
        self.pointers[Data.CHAR_POS_DATA] = read_mem(self.pointers[Data.CHAR_MAP_DATA] +
                                                     offsets.CharMapData.CHAR_POS_DATA_POINTER)

        pointer1 = read_mem(offsets.CHAR_DATA_POINTER_B1)
        self.pointers[Data.CHAR_DATA_B] = read_mem(pointer1 + offsets.CHAR_DATA_POINTER_B2)

        pointer1 = read_mem(offsets.GRAPHICS_DATA_POINTER_1)
        self.pointers[Data.GRAPHICS_DATA] = read_mem(pointer1 + offsets.GRAPHICS_DATA_POINTER_2)

        self.pointers[Data.WORLD_STATE] = read_mem(offsets.WORLD_STATE_POINTER)

        self.pointers[Data.MENU_MANAGER] = read_mem(offsets.MENU_MANGER_POINTER)

        pointer1 = read_mem(offsets.CHR_FOLLOW_CAM_POINTER_1)
        pointer1 = read_mem(pointer1 + offsets.CHR_FOLLOW_CAM_POINTER_2)
        self.pointers[Data.CHR_FOLLOW_CAM] = read_mem(pointer1 + offsets.CHR_FOLLOW_CAM_POINTER_3)

        pointer1 = read_mem(offsets.EVENT_FLAGS_POINTER_1)
        self.pointers[Data.EVENT_FLAGS] = read_mem(pointer1 + offsets.EVENT_FLAGS_POINTER_2)

        self.pointers[Data.UNKNOWN_A] = read_mem(offsets.UNKNOWN_POINTER_A)
        self.pointers[Data.UNKNOWN_B] = read_mem(offsets.UNKNOWN_POINTER_B)
        self.pointers[Data.UNKNOWN_C] = read_mem(offsets.UNKNOWN_POINTER_C)
        pointer1 = read_mem(offsets.UNKNOWN_POINTER_D1)
        self.pointers[Data.UNKNOWN_D] = read_mem(pointer1 + offsets.UNKNOWN_POINTER_D2)

        self.pointers[Data.GESTURES] = read_mem(self.pointers[Data.CHAR_DATA_B] +
                                                offsets.CharDataB.GESTURES_UNLOCKED_POINTER)

        self.pointers[Data.GAME_MAN] = read_mem(offsets.GAME_MAN_POINTER)

    def get_event_flag_addr(self, flag_id):
        id_str = str(flag_id).zfill(8)
        if len(id_str) != 8:
            raise ArgumentError("Unknown event flag ID: %d" % flag_id)
        else:
            group = id_str[0:1]
            area = id_str[1:4]
            section = int(id_str[4:5])
            number = int(id_str[5:8])
            if group in self.EVENT_FLAG_GROUPS.keys() and area in self.EVENT_FLAG_AREAS.keys():
                offset = self.EVENT_FLAG_GROUPS[group]
                offset += self.EVENT_FLAG_AREAS[area] * 0x500
                offset += section * 128
                offset += int((number - (number % 32)) / 8)
                mask = 0x80000000 >> (number % 32)
                return self.pointers[Data.EVENT_FLAGS] + offset, mask

    def read_event_flag(self, flag_id):
        address, mask = self.get_event_flag_addr(flag_id)
        return self.interface.read_flag(address, mask)

    def write_event_flag(self, flag_id, value: bool):
        address, mask = self.get_event_flag_addr(flag_id)
        return self.interface.write_flag(address, mask, value)

    def set_game_speed(self, speed: float):
        self.interface.write_float(self.pointers[Data.ANIM_DATA] + self.offsets.AnimData.PLAY_SPEED, speed)

    def death_cam(self):
        self.interface.write_flag(self.pointers[Data.UNKNOWN_B] + self.offsets.UnknownB.DEATH_CAM, 1, True)

    def game_restart(self):
        self.interface.write_flag(self.pointers[Data.GAME_MAN] + self.offsets.GameMan.B_REQUEST_TO_ENDING, 1, True)

    def disable_fps_disconnect(self):
        self.interface.write_flag(self.pointers[Data.GAME_MAN] +
                                  self.offsets.GameMan.IS_FPS_DISCONNECTION, 1, True)

    def unlock_all_gestures(self):
        for gesture in vars(self.offsets.Gestures).values():
            if type(gesture) == int:
                self.interface.write_flag(self.pointers[Data.GESTURES] + gesture, 1, True)

    def get_class(self):
        return self.interface.read_int(self.pointers[Data.CHAR_DATA_B] + self.offsets.CharDataB.CLASS)

    def set_class(self, value):
        self.interface.write_int(self.pointers[Data.CHAR_DATA_B] + self.offsets.CharDataB.CLASS, value)

    def get_soul_level(self):
        return self.interface.read_int(self.pointers[Data.CHAR_DATA_B] + self.offsets.CharDataB.SOUL_LEVEL)

    def set_soul_level(self, value):
        self.interface.write_int(self.pointers[Data.CHAR_DATA_B] + self.offsets.CharDataB.SOUL_LEVEL, value)

    def get_souls(self):
        return self.interface.read_int(self.pointers[Data.CHAR_DATA_B] + self.offsets.CharDataB.SOULS)

    def set_souls(self, value):
        self.interface.write_int(self.pointers[Data.CHAR_DATA_B] + self.offsets.CharDataB.SOULS, value)

    def get_humanity(self):
        return self.interface.read_int(self.pointers[Data.CHAR_DATA_B] + self.offsets.CharDataB.HUMANITY)

    def set_humanity(self, value):
        self.interface.write_int(self.pointers[Data.CHAR_DATA_B] + self.offsets.CharDataB.HUMANITY, value)

    def get_hp(self):
        return self.interface.read_int(self.pointers[Data.CHAR_DATA_B] + self.offsets.CharDataB.HP)

    def set_hp(self, value):
        self.interface.write_int(self.pointers[Data.CHAR_DATA_B] + self.offsets.CharDataB.HP, value)

    def get_max_hp(self):
        return self.interface.read_int(self.pointers[Data.CHAR_DATA_B] + self.offsets.CharDataB.HP_MAX)

    def set_max_hp(self, value):
        self.interface.write_int(self.pointers[Data.CHAR_DATA_B] + self.offsets.CharDataB.HP_MAX, value)

    def get_max_hp_mod(self):
        return self.interface.read_int(self.pointers[Data.CHAR_DATA_B] + self.offsets.CharDataB.HP_MOD_MAX)

    def set_max_hp_mod(self, value):
        self.interface.write_int(self.pointers[Data.CHAR_DATA_B] + self.offsets.CharDataB.HP_MOD_MAX, value)

    def get_vitality(self):
        return self.interface.read_int(self.pointers[Data.CHAR_DATA_B] + self.offsets.CharDataB.VITALITY)

    def set_vitality(self, value):
        self.interface.write_int(self.pointers[Data.CHAR_DATA_B] + self.offsets.CharDataB.VITALITY, value)

    def get_attunement(self):
        return self.interface.read_int(self.pointers[Data.CHAR_DATA_B] + self.offsets.CharDataB.ATTUNEMENT)

    def set_attunement(self, value):
        self.interface.write_int(self.pointers[Data.CHAR_DATA_B] + self.offsets.CharDataB.ATTUNEMENT, value)

    def get_endurance(self):
        return self.interface.read_int(self.pointers[Data.CHAR_DATA_B] + self.offsets.CharDataB.ENDURANCE)

    def set_endurance(self, value):
        self.interface.write_int(self.pointers[Data.CHAR_DATA_B] + self.offsets.CharDataB.ENDURANCE, value)

    def get_strength(self):
        return self.interface.read_int(self.pointers[Data.CHAR_DATA_B] + self.offsets.CharDataB.STRENGTH)

    def set_strength(self, value):
        self.interface.write_int(self.pointers[Data.CHAR_DATA_B] + self.offsets.CharDataB.STRENGTH, value)

    def get_dexterity(self):
        return self.interface.read_int(self.pointers[Data.CHAR_DATA_B] + self.offsets.CharDataB.DEXTERITY)

    def set_dexterity(self, value):
        self.interface.write_int(self.pointers[Data.CHAR_DATA_B] + self.offsets.CharDataB.DEXTERITY, value)

    def get_resistance(self):
        return self.interface.read_int(self.pointers[Data.CHAR_DATA_B] + self.offsets.CharDataB.RESISTANCE)

    def set_resistance(self, value):
        self.interface.write_int(self.pointers[Data.CHAR_DATA_B] + self.offsets.CharDataB.RESISTANCE, value)

    def get_intelligence(self):
        return self.interface.read_int(self.pointers[Data.CHAR_DATA_B] + self.offsets.CharDataB.INTELLIGENCE)

    def set_intelligence(self, value):
        self.interface.write_int(self.pointers[Data.CHAR_DATA_B] + self.offsets.CharDataB.INTELLIGENCE, value)

    def get_faith(self):
        return self.interface.read_int(self.pointers[Data.CHAR_DATA_B] + self.offsets.CharDataB.FAITH)

    def set_faith(self, value):
        self.interface.write_int(self.pointers[Data.CHAR_DATA_B] + self.offsets.CharDataB.FAITH, value)

    def level_up(self, vitality, attunement, endurance, strength,
                 dexterity, resistance, intelligence, faith, soul_level):

        stats = self.interface.allocate(2048)
        souls = self.get_souls()
        humanity = self.get_humanity()
        set_stat = self.interface.write_int
        level = self.offsets.FuncLevelUp

        set_stat(stats + level.VIT, vitality)
        set_stat(stats + level.ATN, attunement)
        set_stat(stats + level.END, endurance)
        set_stat(stats + level.STR, strength)
        set_stat(stats + level.DEX, dexterity)
        set_stat(stats + level.RES, resistance)
        set_stat(stats + level.INT, intelligence)
        set_stat(stats + level.FTH, faith)
        set_stat(stats + level.SLV, soul_level)
        set_stat(stats + level.SLS, souls)

        self.interface.execute_asm(
            self.Scripts.LEVEL_UP % (stats, stats, self.offsets.FUNC_LEVEL_UP_POINTER)
        )

        self.interface.free(stats)

        self.set_humanity(humanity)

    def item_drop(self, category, item_id, count):
        self.interface.execute_asm(
            self.Scripts.ITEM_DROP % (
                category, item_id, count,
                self.offsets.FUNC_ITEM_DROP_UNKNOWN_1,
                self.offsets.FUNC_ITEM_DROP_UNKNOWN_2,
                self.offsets.FUNC_ITEM_DROP_POINTER)
        )

    def item_get(self, category, item_id, count):
        self.interface.execute_asm(
            self.Scripts.ITEM_GET % (
                self.pointers[Data.CHAR_DATA_B] + self.offsets.CharDataB.INVENTORY_INDEX_START,
                category, item_id, count,
                self.offsets.FUNC_ITEM_GET_POINTER
            )
        )

    def dark_sign_warp(self):
        self.interface.execute_asm(
            self.Scripts.BONFIRE_WARP % (
                self.offsets.FUNC_BONFIRE_WARP_UNKNOWN,
                self.offsets.FUNC_BONFIRE_WARP_POINTER)
        )