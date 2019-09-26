from enum import Enum, auto
from collections import defaultdict
from dslib.ds_interface import DSInterface
from dsres.ds_offsets import DSPointersRelease, DSPointersDebug
from dsres.ds_asm import Scripts
from ctypes import ArgumentError
from math import pi
from psutil import pid_exists


class Data(Enum):

    CHAR_DATA_A = auto()
    ANIM_DATA = auto()
    CHAR_POS_DATA = auto()
    CHAR_MAP_DATA = auto()
    CHAR_DATA_B = auto()
    CHAR_DATA_C = auto()
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


class Stat(Enum):

    VIT = "vit"
    ATN = "atn"
    END = "end"
    STR = "str"
    DEX = "dex"
    RES = "res"
    INT = "int"
    FTH = "fth"
    SLV = "slv"
    SLS = "sls"
    HUM = "hum"


class DSProcess:

    CHECK_VERSION = 0x400080

    GAME_VERSIONS = ({
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

    def __init__(self):
        self.pointers = defaultdict(int)
        self.id = 0
        self.interface = None
        self.version = None
        self.offsets = None

    def can_read(self):
        try:
            test_pointer = self.interface.dummy_read_int(self.offsets.CHAR_DATA_POINTER_A1)
            test_pointer = self.interface.dummy_read_int(test_pointer + self.offsets.CHAR_DATA_POINTER_A2)
            test_pointer = self.interface.dummy_read_int(test_pointer + self.offsets.CHAR_DATA_POINTER_A3)
            return test_pointer is not None
        except (TypeError, AttributeError):
            return False

    def has_exited(self):
        return not pid_exists(self.id)

    def attach(self, pid):
        self.id = pid
        self.interface = DSInterface(pid)

    def prepare(self):
        self.check_version()
        self.check_valid()
        self.load_pointers()

    def check_version(self):
        try:
            version = self.interface.read_uint(DSProcess.CHECK_VERSION)
            if version is not None:
                self.version = DSProcess.GAME_VERSIONS[version]
            else:
                raise RuntimeError("Couldn't read game's version")
        except KeyError:
            self.version = "Unknown"

    def check_valid(self):
        valid = True if self.version in ("Steam", "Debug") else False
        if not valid:
            raise RuntimeError("Your DARK SOULS version is not supported")
        else:
            self.offsets = DSPointersRelease if self.version == "Steam" else DSPointersDebug

    def load_pointers(self):

        pointers = self.pointers
        offsets = self.offsets
        read_mem = self.interface.read_int

        pointer1 = read_mem(offsets.CHAR_DATA_POINTER_A1)
        pointer1 = read_mem(pointer1 + offsets.CHAR_DATA_POINTER_A2)
        pointers[Data.CHAR_DATA_A] = read_mem(pointer1 + offsets.CHAR_DATA_POINTER_A3)
        pointers[Data.CHAR_MAP_DATA] = read_mem(pointers[Data.CHAR_DATA_A] + offsets.CharDataA.CHAR_MAP_DATA_POINTER)
        pointers[Data.ANIM_DATA] = read_mem(pointers[Data.CHAR_MAP_DATA] + offsets.CharMapData.ANIM_DATA_POINTER)
        pointers[Data.CHAR_POS_DATA] = read_mem(pointers[Data.CHAR_MAP_DATA] +
                                                offsets.CharMapData.CHAR_POS_DATA_POINTER)

        pointer1 = read_mem(offsets.CHAR_DATA_POINTER_B1)
        pointers[Data.CHAR_DATA_B] = read_mem(pointer1 + offsets.CHAR_DATA_POINTER_B2)

        pointers[Data.CHAR_DATA_C] = read_mem(offsets.CHAR_DATA_POINTER_B1)

        pointer1 = read_mem(offsets.GRAPHICS_DATA_POINTER_1)
        pointers[Data.GRAPHICS_DATA] = read_mem(pointer1 + offsets.GRAPHICS_DATA_POINTER_2)

        pointers[Data.WORLD_STATE] = read_mem(offsets.WORLD_STATE_POINTER)

        pointers[Data.MENU_MANAGER] = read_mem(offsets.MENU_MANGER_POINTER)

        pointer1 = read_mem(offsets.CHR_FOLLOW_CAM_POINTER_1)
        pointer1 = read_mem(pointer1 + offsets.CHR_FOLLOW_CAM_POINTER_2)
        pointers[Data.CHR_FOLLOW_CAM] = read_mem(pointer1 + offsets.CHR_FOLLOW_CAM_POINTER_3)

        pointer1 = read_mem(offsets.EVENT_FLAGS_POINTER_1)
        pointers[Data.EVENT_FLAGS] = read_mem(pointer1 + offsets.EVENT_FLAGS_POINTER_2)

        pointers[Data.UNKNOWN_A] = read_mem(offsets.UNKNOWN_POINTER_A)
        pointers[Data.UNKNOWN_B] = read_mem(offsets.UNKNOWN_POINTER_B)
        pointers[Data.UNKNOWN_C] = read_mem(offsets.UNKNOWN_POINTER_C)
        pointer1 = read_mem(offsets.UNKNOWN_POINTER_D1)
        pointers[Data.UNKNOWN_D] = read_mem(pointer1 + offsets.UNKNOWN_POINTER_D2)

        pointers[Data.GESTURES] = read_mem(pointers[Data.CHAR_DATA_B] +
                                           offsets.CharDataB.GESTURES_UNLOCKED_POINTER)

        pointers[Data.GAME_MAN] = read_mem(offsets.GAME_MAN_POINTER)

    def get_event_flag_addr(self, flag_id):
        id_str = str(flag_id).zfill(8)
        if len(id_str) != 8:
            raise ArgumentError("Unknown event flag ID: %d" % flag_id)
        else:
            group = id_str[0:1]
            area = id_str[1:4]
            section = int(id_str[4:5])
            number = int(id_str[5:8])
            if group in DSProcess.EVENT_FLAG_GROUPS.keys() and area in DSProcess.EVENT_FLAG_AREAS.keys():
                offset = DSProcess.EVENT_FLAG_GROUPS[group]
                offset += DSProcess.EVENT_FLAG_AREAS[area] * 0x500
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
        return self.interface.write_float(self.pointers[Data.ANIM_DATA] + self.offsets.AnimData.PLAY_SPEED, speed)

    def death_cam(self, enable: bool):
        return self.interface.write_bool(self.pointers[Data.UNKNOWN_B] + self.offsets.UnknownB.DEATH_CAM, enable)

    def game_restart(self):
        return self.interface.write_flag(self.pointers[Data.GAME_MAN] +
                                         self.offsets.GameMan.B_REQUEST_TO_ENDING, 1, True)

    def disable_fps_disconnect(self):
        return self.interface.write_int(self.pointers[Data.GAME_MAN] +
                                        self.offsets.GameMan.IS_FPS_DISCONNECTION, 0)

    def unlock_all_gestures(self):
        success = True
        for gesture in vars(self.offsets.Gestures).values():
            if isinstance(gesture, int):
                success &= self.interface.write_flag(self.pointers[Data.GESTURES] + gesture, 1, True)
        return success

    def menu_kick(self):
        return self.interface.write_int(self.pointers[Data.UNKNOWN_C] + self.offsets.UnknownC.MENU_KICK, 2)

    def set_phantom_type(self, value: int):
        return self.interface.write_int(self.pointers[Data.CHAR_DATA_A] + self.offsets.CharDataA.PHANTOM_TYPE, value)

    def set_team_type(self, value: int):
        return self.interface.write_int(self.pointers[Data.CHAR_DATA_A] + self.offsets.CharDataA.TEAM_TYPE, value)

    def set_super_armor(self, enable: bool):
        return self.interface.write_flag(self.pointers[Data.CHAR_DATA_A] + self.offsets.CharDataA.CHAR_FLAGS_1,
                                         self.offsets.CharFlagsA.SET_SUPER_ARMOR, int(enable))

    def set_draw_enable(self, enable: bool):
        return self.interface.write_flag(self.pointers[Data.CHAR_DATA_A] + self.offsets.CharDataA.CHAR_FLAGS_1,
                                         self.offsets.CharFlagsA.SET_DRAW_ENABLE, int(enable))

    def set_no_gravity(self, enable: bool):
        return self.interface.write_flag(self.pointers[Data.CHAR_DATA_A] + self.offsets.CharDataA.CHAR_FLAGS_1,
                                         self.offsets.CharFlagsA.SET_DISABLE_GRAVITY, int(enable))

    def set_no_dead(self, enable: bool):
        return self.interface.write_flag(self.pointers[Data.CHAR_DATA_A] + self.offsets.CharDataA.CHAR_FLAGS_2,
                                         self.offsets.CharFlagsB.NO_DEAD, int(enable))

    def set_no_move(self, enable: bool):
        return self.interface.write_flag(self.pointers[Data.CHAR_DATA_A] + self.offsets.CharDataA.CHAR_FLAGS_2,
                                         self.offsets.CharFlagsB.NO_MOVE, int(enable))

    def set_no_stamina_consume(self, enable: bool):
        return self.interface.write_flag(self.pointers[Data.CHAR_DATA_A] + self.offsets.CharDataA.CHAR_FLAGS_2,
                                         self.offsets.CharFlagsB.NO_STAMINA_CONSUME, int(enable))

    def set_no_goods_consume(self, enable: bool):
        return self.interface.write_flag(self.pointers[Data.CHAR_DATA_A] + self.offsets.CharDataA.CHAR_FLAGS_2,
                                         self.offsets.CharFlagsB.NO_GOODS_CONSUME, int(enable))

    def set_no_update(self, enable: bool):
        return self.interface.write_flag(self.pointers[Data.CHAR_DATA_A] + self.offsets.CharDataA.CHAR_FLAGS_2,
                                         self.offsets.CharFlagsB.NO_UPDATE, int(enable))

    def set_no_attack(self, enable: bool):
        return self.interface.write_flag(self.pointers[Data.CHAR_DATA_A] + self.offsets.CharDataA.CHAR_FLAGS_2,
                                         self.offsets.CharFlagsB.NO_ATTACK, int(enable))

    def set_no_damage(self, enable: bool):
        return self.interface.write_flag(self.pointers[Data.CHAR_DATA_A] + self.offsets.CharDataA.CHAR_FLAGS_2,
                                         self.offsets.CharFlagsB.NO_DAMAGE, int(enable))

    def set_no_hit(self, enable: bool):
        return self.interface.write_flag(self.pointers[Data.CHAR_DATA_A] + self.offsets.CharDataA.CHAR_FLAGS_2,
                                         self.offsets.CharFlagsB.NO_HIT, int(enable))

    def get_player_dead_mode(self):
        return self.interface.read_flag(self.pointers[Data.CHAR_DATA_A] + self.offsets.CharDataA.CHAR_FLAGS_1,
                                        self.offsets.CharFlagsA.SET_DEAD_MODE)

    def set_player_dead_mode(self, enable: bool):
        return self.interface.write_flag(self.pointers[Data.CHAR_DATA_A] + self.offsets.CharDataA.CHAR_FLAGS_1,
                                         self.offsets.CharFlagsA.SET_DEAD_MODE, enable)

    def set_no_magic_all(self, enable: bool):
        return self.interface.write_bool(self.offsets.ALL_NO_MAGIC_QTY_CONSUME, enable)

    def set_no_stamina_all(self, enable: bool):
        return self.interface.write_bool(self.offsets.ALL_NO_STAMINA_CONSUME, enable)

    def set_exterminate(self, enable: bool):
        return self.interface.write_bool(self.offsets.PLAYER_EXTERMINATE, enable)

    def set_no_ammo_consume_all(self, enable: bool):
        return self.interface.write_bool(self.offsets.ALL_NO_ARROW_CONSUME, enable)

    def set_hide(self, enable: bool):
        return self.interface.write_bool(self.offsets.PLAYER_HIDE, enable)

    def set_silence(self, enable: bool):
        return self.interface.write_bool(self.offsets.PLAYER_SILENCE, enable)

    def set_no_dead_all(self, enable: bool):
        return self.interface.write_bool(self.offsets.ALL_NO_DEAD, enable)

    def set_no_damage_all(self, enable: bool):
        return self.interface.write_bool(self.offsets.ALL_NO_DAMAGE, enable)

    def set_no_hit_all(self, enable: bool):
        return self.interface.write_bool(self.offsets.ALL_NO_HIT, enable)

    def set_no_attack_all(self, enable: bool):
        return self.interface.write_bool(self.offsets.ALL_NO_ATTACK, enable)

    def set_no_move_all(self, enable: bool):
        return self.interface.write_bool(self.offsets.ALL_NO_MOVE, enable)

    def set_no_update_ai_all(self, enable: bool):
        return self.interface.write_bool(self.offsets.ALL_NO_UPDATE_AI, enable)

    def disable_all_area_enemies(self, disable: bool):
        return self.interface.write_bool(self.pointers[Data.GAME_MAN] +
                                         self.offsets.GameMan.IS_DISABLE_ALL_AREA_ENEMIES, disable)

    def disable_all_area_event(self, disable: bool):
        return self.interface.write_bool(self.pointers[Data.GAME_MAN] +
                                         self.offsets.GameMan.IS_DISABLE_ALL_AREA_EVENT, disable)

    def disable_all_area_map(self, disable: bool):
        return self.interface.write_bool(self.pointers[Data.GAME_MAN] +
                                         self.offsets.GameMan.IS_DISABLE_ALL_AREA_MAP, disable)

    def disable_all_area_obj(self, disable: bool):
        return self.interface.write_bool(self.pointers[Data.GAME_MAN] +
                                         self.offsets.GameMan.IS_DISABLE_ALL_AREA_OBJ, disable)

    def enable_all_area_obj(self, enable: bool):
        return self.interface.write_bool(self.pointers[Data.GAME_MAN] +
                                         self.offsets.GameMan.IS_ENABLE_ALL_AREA_OBJ, enable)

    def enable_all_area_obj_break(self, enable: bool):
        return self.interface.write_bool(self.pointers[Data.GAME_MAN] +
                                         self.offsets.GameMan.IS_ENABLE_ALL_AREA_OBJ_BREAK, enable)

    def disable_all_area_hi_hit(self, disable: bool):
        return self.interface.write_bool(self.pointers[Data.GAME_MAN] +
                                         self.offsets.GameMan.IS_DISABLE_ALL_AREA_HI_HIT, disable)

    def disable_all_area_lo_hit(self, disable: bool):
        return self.interface.write_bool(self.pointers[Data.GAME_MAN] +
                                         self.offsets.GameMan.IS_DISABLE_ALL_AREA_LO_HIT, disable)

    def disable_all_area_sfx(self, disable: bool):
        return self.interface.write_bool(self.pointers[Data.GAME_MAN] +
                                         self.offsets.GameMan.IS_DISABLE_ALL_AREA_SFX, disable)

    def disable_all_area_sound(self, disable: bool):
        return self.interface.write_bool(self.pointers[Data.GAME_MAN] +
                                         self.offsets.GameMan.IS_DISABLE_ALL_AREA_SOUND, disable)

    def enable_obj_break_record_mode(self, enable: bool):
        return self.interface.write_bool(self.pointers[Data.GAME_MAN] +
                                         self.offsets.GameMan.IS_OBJ_BREAK_RECORD_MODE, enable)

    def enable_auto_map_warp_mode(self, enable: bool):
        return self.interface.write_bool(self.pointers[Data.GAME_MAN] +
                                         self.offsets.GameMan.IS_AUTO_MAP_WARP_MODE, enable)

    def enable_chr_npc_wander_test(self, enable: bool):
        return self.interface.write_bool(self.pointers[Data.GAME_MAN] +
                                         self.offsets.GameMan.IS_CHR_NPC_WANDER_TEST, enable)

    def enable_dbg_chr_all_dead(self, enable: bool):
        return self.interface.write_bool(self.pointers[Data.GAME_MAN] +
                                         self.offsets.GameMan.IS_DBG_CHR_ALL_DEAD, enable)

    def enable_online_mode(self, enable: bool):
        return self.interface.write_bool(self.pointers[Data.GAME_MAN] +
                                         self.offsets.GameMan.IS_ONLINE_MODE, enable)

    def draw_bounding(self, enable: bool):
        return self.interface.write_bool(self.pointers[Data.GRAPHICS_DATA] +
                                         self.offsets.GraphicsData.DRAW_BOUNDING_BOXES, enable)

    def draw_sprite_masks(self, enable: bool):
        return self.interface.write_bool(self.pointers[Data.GRAPHICS_DATA] +
                                         self.offsets.GraphicsData.DRAW_DEPTH_TEX_EDGE, enable)

    def draw_textures(self, enable: bool):
        return self.interface.write_bool(self.pointers[Data.GRAPHICS_DATA] +
                                         self.offsets.GraphicsData.DRAW_TEXTURES, enable)

    def draw_sprites(self, enable: bool):
        return self.interface.write_bool(self.pointers[Data.GRAPHICS_DATA] +
                                         self.offsets.GraphicsData.NORMAL_DRAW_TEX_EDGE, enable)

    def draw_trans(self, enable: bool):
        return self.interface.write_bool(self.pointers[Data.GRAPHICS_DATA] +
                                         self.offsets.GraphicsData.NORMAL_TRANS, enable)

    def draw_shadows(self, enable: bool):
        return self.interface.write_bool(self.pointers[Data.GRAPHICS_DATA] +
                                         self.offsets.GraphicsData.DRAW_SHADOWS, enable)

    def draw_sprite_shadows(self, enable: bool):
        return self.interface.write_bool(self.pointers[Data.GRAPHICS_DATA] +
                                         self.offsets.GraphicsData.DRAW_SPRITE_SHADOWS, enable)

    def draw_map(self, enable: bool):
        return self.interface.write_bool(self.offsets.DRAW_MAP, enable)

    def draw_creatures(self, enable: bool):
        return self.interface.write_bool(self.offsets.DRAW_CREATURES, enable)

    def draw_objects(self, enable: bool):
        return self.interface.write_bool(self.offsets.DRAW_OBJECTS, enable)

    def draw_sfx(self, enable: bool):
        return self.interface.write_bool(self.offsets.DRAW_SFX, enable)

    def draw_compass_large(self, enable: bool):
        return self.interface.write_bool(self.offsets.COMPASS_LARGE, enable)

    def draw_compass_small(self, enable: bool):
        return self.interface.write_bool(self.offsets.COMPASS_SMALL, enable)

    def draw_altimeter(self, enable: bool):
        return self.interface.write_bool(self.offsets.ALTIMETER, enable)

    def draw_nodes(self, enable: bool):
        return self.interface.write_bool(self.offsets.NODE_GRAPH, enable)

    def override_filter(self, enable: bool):
        return self.interface.write_bool(self.pointers[Data.GRAPHICS_DATA] +
                                         self.offsets.GraphicsData.ENABLE_FILTER, enable)

    def set_brightness(self, red: float, green: float, blue: float):
        self.interface.write_float(self.pointers[Data.GRAPHICS_DATA] + self.offsets.GraphicsData.BRIGHTNESS_R, red)
        self.interface.write_float(self.pointers[Data.GRAPHICS_DATA] + self.offsets.GraphicsData.BRIGHTNESS_G, green)
        self.interface.write_float(self.pointers[Data.GRAPHICS_DATA] + self.offsets.GraphicsData.BRIGHTNESS_B, blue)

    def set_contrast(self, red: float, green: float, blue: float):
        self.interface.write_float(self.pointers[Data.GRAPHICS_DATA] + self.offsets.GraphicsData.CONTRAST_R, red)
        self.interface.write_float(self.pointers[Data.GRAPHICS_DATA] + self.offsets.GraphicsData.CONTRAST_G, green)
        self.interface.write_float(self.pointers[Data.GRAPHICS_DATA] + self.offsets.GraphicsData.CONTRAST_B, blue)

    def set_saturation(self, saturation: float):
        return self.interface.write_float(self.pointers[Data.GRAPHICS_DATA] +
                                        self.offsets.GraphicsData.SATURATION, saturation)

    def set_hue(self, hue: float):
        return self.interface.write_float(self.pointers[Data.GRAPHICS_DATA] + self.offsets.GraphicsData.HUE, hue)

    def get_class(self):
        return self.interface.read_int(self.pointers[Data.CHAR_DATA_B] + self.offsets.CharDataB.CLASS)

    def set_class(self, value):
        return self.interface.write_int(self.pointers[Data.CHAR_DATA_B] + self.offsets.CharDataB.CLASS, value)

    def get_soul_level(self):
        return self.interface.read_int(self.pointers[Data.CHAR_DATA_B] + self.offsets.CharDataB.SOUL_LEVEL)

    def set_soul_level(self, value):
        return self.interface.write_int(self.pointers[Data.CHAR_DATA_B] + self.offsets.CharDataB.SOUL_LEVEL, value)

    def get_souls(self):
        return self.interface.read_int(self.pointers[Data.CHAR_DATA_B] + self.offsets.CharDataB.SOULS)

    def set_souls(self, value):
        return self.interface.write_int(self.pointers[Data.CHAR_DATA_B] + self.offsets.CharDataB.SOULS, value)

    def get_humanity(self):
        return self.interface.read_int(self.pointers[Data.CHAR_DATA_B] + self.offsets.CharDataB.HUMANITY)

    def set_humanity(self, value):
        return self.interface.write_int(self.pointers[Data.CHAR_DATA_B] + self.offsets.CharDataB.HUMANITY, value)

    def get_hp(self):
        return self.interface.read_int(self.pointers[Data.CHAR_DATA_B] + self.offsets.CharDataB.HP)

    def set_hp(self, value):
        return self.interface.write_int(self.pointers[Data.CHAR_DATA_A] + self.offsets.CharDataA.HP, value)

    def get_hp_max(self):
        return self.interface.read_int(self.pointers[Data.CHAR_DATA_B] + self.offsets.CharDataB.HP_MAX)

    def set_hp_max(self, value):
        return self.interface.write_int(self.pointers[Data.CHAR_DATA_B] + self.offsets.CharDataB.HP_MAX, value)

    def get_hp_mod_max(self):
        return self.interface.read_int(self.pointers[Data.CHAR_DATA_B] + self.offsets.CharDataB.HP_MOD_MAX)

    def set_hp_mod_max(self, value):
        return self.interface.write_int(self.pointers[Data.CHAR_DATA_B] + self.offsets.CharDataB.HP_MOD_MAX, value)

    def get_stamina(self):
        return self.interface.read_int(self.pointers[Data.CHAR_DATA_B] + self.offsets.CharDataB.STAMINA_MOD_MAX)

    def get_vitality(self):
        return self.interface.read_int(self.pointers[Data.CHAR_DATA_B] + self.offsets.CharDataB.VITALITY)

    def set_vitality(self, value):
        return self.interface.write_int(self.pointers[Data.CHAR_DATA_B] + self.offsets.CharDataB.VITALITY, value)

    def get_attunement(self):
        return self.interface.read_int(self.pointers[Data.CHAR_DATA_B] + self.offsets.CharDataB.ATTUNEMENT)

    def set_attunement(self, value):
        return self.interface.write_int(self.pointers[Data.CHAR_DATA_B] + self.offsets.CharDataB.ATTUNEMENT, value)

    def get_endurance(self):
        return self.interface.read_int(self.pointers[Data.CHAR_DATA_B] + self.offsets.CharDataB.ENDURANCE)

    def set_endurance(self, value):
        return self.interface.write_int(self.pointers[Data.CHAR_DATA_B] + self.offsets.CharDataB.ENDURANCE, value)

    def get_strength(self):
        return self.interface.read_int(self.pointers[Data.CHAR_DATA_B] + self.offsets.CharDataB.STRENGTH)

    def set_strength(self, value):
        return self.interface.write_int(self.pointers[Data.CHAR_DATA_B] + self.offsets.CharDataB.STRENGTH, value)

    def get_dexterity(self):
        return self.interface.read_int(self.pointers[Data.CHAR_DATA_B] + self.offsets.CharDataB.DEXTERITY)

    def set_dexterity(self, value):
        return self.interface.write_int(self.pointers[Data.CHAR_DATA_B] + self.offsets.CharDataB.DEXTERITY, value)

    def get_resistance(self):
        return self.interface.read_int(self.pointers[Data.CHAR_DATA_B] + self.offsets.CharDataB.RESISTANCE)

    def set_resistance(self, value):
        return self.interface.write_int(self.pointers[Data.CHAR_DATA_B] + self.offsets.CharDataB.RESISTANCE, value)

    def get_intelligence(self):
        return self.interface.read_int(self.pointers[Data.CHAR_DATA_B] + self.offsets.CharDataB.INTELLIGENCE)

    def set_intelligence(self, value):
        return self.interface.write_int(self.pointers[Data.CHAR_DATA_B] + self.offsets.CharDataB.INTELLIGENCE, value)

    def get_faith(self):
        return self.interface.read_int(self.pointers[Data.CHAR_DATA_B] + self.offsets.CharDataB.FAITH)

    def set_faith(self, value):
        return self.interface.write_int(self.pointers[Data.CHAR_DATA_B] + self.offsets.CharDataB.FAITH, value)

    def get_stat(self, stat: Stat):
        if stat == Stat.VIT:
            return self.get_vitality()
        elif stat == Stat.ATN:
            return self.get_attunement()
        elif stat == Stat.END:
            return self.get_endurance()
        elif stat == Stat.STR:
            return self.get_strength()
        elif stat == Stat.DEX:
            return self.get_dexterity()
        elif stat == Stat.RES:
            return self.get_resistance()
        elif stat == Stat.INT:
            return self.get_intelligence()
        elif stat == Stat.FTH:
            return self.get_faith()
        elif stat == Stat.SLV:
            return self.get_soul_level()
        elif stat == Stat.SLS:
            return self.get_souls()
        elif stat == Stat.HUM:
            return self.get_humanity()

    def level_up(self, new_stats: dict):

        stats = self.interface.allocate(2048)
        humanity = self.get_humanity()
        set_stat = self.interface.write_int
        level = self.offsets.FuncLevelUp

        set_stat(stats + level.VIT, new_stats[Stat.VIT])
        set_stat(stats + level.ATN, new_stats[Stat.ATN])
        set_stat(stats + level.END, new_stats[Stat.END])
        set_stat(stats + level.STR, new_stats[Stat.STR])
        set_stat(stats + level.DEX, new_stats[Stat.DEX])
        set_stat(stats + level.RES, new_stats[Stat.RES])
        set_stat(stats + level.INT, new_stats[Stat.INT])
        set_stat(stats + level.FTH, new_stats[Stat.FTH])
        set_stat(stats + level.SLV, new_stats[Stat.SLV])
        set_stat(stats + level.SLS, new_stats[Stat.SLS])

        self.set_no_dead(True)
        success = \
            self.interface.execute_asm(
                Scripts.LEVEL_UP % (stats, stats, self.offsets.FUNC_LEVEL_UP_POINTER)
            )
        self.set_no_dead(False)

        self.interface.free(stats)

        self.set_humanity(humanity)

        return success

    def get_pos(self):
        return (
            self.interface.read_float(self.pointers[Data.CHAR_POS_DATA] + self.offsets.CharPosData.POS_X),
            self.interface.read_float(self.pointers[Data.CHAR_POS_DATA] + self.offsets.CharPosData.POS_Y),
            self.interface.read_float(self.pointers[Data.CHAR_POS_DATA] + self.offsets.CharPosData.POS_Z),
            (self.interface.read_float(self.pointers[Data.CHAR_POS_DATA] + self.offsets.CharPosData.POS_ANGLE)
             + pi) / (pi * 2) * 360
        )

    def get_pos_stable(self):
        return (
            self.interface.read_float(self.pointers[Data.WORLD_STATE] + self.offsets.WorldState.POS_STABLE_X),
            self.interface.read_float(self.pointers[Data.WORLD_STATE] + self.offsets.WorldState.POS_STABLE_Y),
            self.interface.read_float(self.pointers[Data.WORLD_STATE] + self.offsets.WorldState.POS_STABLE_Z),
            (self.interface.read_float(self.pointers[Data.WORLD_STATE] + self.offsets.WorldState.POS_STABLE_ANGLE)
             + pi) / (pi * 2) * 360
        )

    def jump_pos(self, x, y, z, a):
        self.interface.write_float(self.pointers[Data.CHAR_MAP_DATA] + self.offsets.CharMapData.WARP_X, x)
        self.interface.write_float(self.pointers[Data.CHAR_MAP_DATA] + self.offsets.CharMapData.WARP_Y, y)
        self.interface.write_float(self.pointers[Data.CHAR_MAP_DATA] + self.offsets.CharMapData.WARP_Z, z)
        self.interface.write_float(self.pointers[Data.CHAR_MAP_DATA] + self.offsets.CharMapData.WARP_ANGLE,
                                   a / 360 * 2 * pi - pi)
        self.interface.write_int(self.pointers[Data.CHAR_MAP_DATA] + self.offsets.CharMapData.WARP, 1)

    def lock_pos(self, lock: bool):
        if lock:
            self.interface.write_bytes(self.offsets.POS_LOCK_1, bytes([0x90, 0x90, 0x90, 0x90, 0x90]))
            self.interface.write_bytes(self.offsets.POS_LOCK_2, bytes([0x90, 0x90, 0x90, 0x90, 0x90]))
        else:
            self.interface.write_bytes(self.offsets.POS_LOCK_1, bytes([0x66, 0x0F, 0xD6, 0x46, 0x10]))
            self.interface.write_bytes(self.offsets.POS_LOCK_2, bytes([0x66, 0x0F, 0xD6, 0x46, 0x18]))

    def get_world(self):
        return self.interface.read_byte(self.pointers[Data.UNKNOWN_A] + self.offsets.UnknownA.WORLD)

    def get_area(self):
        return self.interface.read_byte(self.pointers[Data.UNKNOWN_A] + self.offsets.UnknownA.AREA)

    def get_bonfire(self):
        return self.interface.read_int(self.pointers[Data.WORLD_STATE] + self.offsets.WorldState.LAST_BONFIRE)

    def set_bonfire(self, bonfire_id: int):
        return self.interface.write_int(self.pointers[Data.WORLD_STATE] +
                                        self.offsets.WorldState.LAST_BONFIRE, bonfire_id)

    def set_name(self, name: str):
        return self.interface.write_str(self.pointers[Data.CHAR_DATA_B] +
                                        self.offsets.CharDataB.CHAR_NAME, name, length=128)

    def set_covenant(self, value: int):
        return self.interface.write_int(self.pointers[Data.CHAR_DATA_B] + self.offsets.CharDataB.COVENANT, value)

    def set_ng_mode(self, value: int):
        return self.interface.write_int(self.pointers[Data.CHAR_DATA_C] + self.offsets.CharDataC.NEW_GAME_MODE, value)

    def item_drop(self, category, item_id, count):
        return \
            self.interface.execute_asm(
                Scripts.ITEM_DROP % (
                    category, item_id, count,
                    self.offsets.FUNC_ITEM_DROP_UNKNOWN_1,
                    self.offsets.FUNC_ITEM_DROP_UNKNOWN_2,
                    self.offsets.FUNC_ITEM_DROP_POINTER)
            )

    def item_get(self, category, item_id, count):
        return \
            self.interface.execute_asm(
                Scripts.ITEM_GET % (
                    self.pointers[Data.CHAR_DATA_B] + self.offsets.CharDataB.INVENTORY_INDEX_START,
                    category, item_id, count,
                    self.offsets.FUNC_ITEM_GET_POINTER)
            )

    def bonfire_warp(self):
        return \
            self.interface.execute_asm(
                Scripts.BONFIRE_WARP % (
                    self.offsets.FUNC_BONFIRE_WARP_UNKNOWN,
                    self.offsets.FUNC_BONFIRE_WARP_POINTER)
            )
