from enum import Enum
from dsres.offsets import DSOffsets, Index
from dsres.asm import Scripts
from ctypes import ArgumentError
from math import pi
from colorama import Fore
from traceback import format_exc
from time import sleep
# noinspection PyUnresolvedReferences
from dsbin.imports import DSHook, Kernel32, FasmNet
# noinspection PyUnresolvedReferences
from System import IntPtr, Int32
# noinspection PyUnresolvedReferences
from System.Text import Encoding


def wait_for(predicate, desired_state=True, single_frame=0.016):
    if not callable(predicate):
        return False
    else:
        while predicate() != desired_state:
            sleep(single_frame)
        return True


def ptr(offset: int):
    return IntPtr.op_Explicit(Int32(offset))


class ReadMemoryError(Exception):

    def __init__(self, message="Failed to read memory"):
        self.message = message
        super(ReadMemoryError, self).__init__(self.message)


class WriteMemoryError(Exception):

    def __init__(self, message="Failed to write memory"):
        self.message = message
        super(WriteMemoryError, self).__init__(self.message)


class AsmExecuteError(Exception):

    ERR = {
        0x00000080: "WAIT_ABANDONED",
        0x00000102: "WAIT_TIMEOUT",
        0xFFFFFFFF: "WAIT_FAILED"
    }

    def __init__(self, code, message="Failed to execute assembly"):
        self.message = message
        self.error = AsmExecuteError.ERR[code] if code in AsmExecuteError.ERR.keys() else "REASON_UNKNOWN"
        super(AsmExecuteError, self).__init__(self.message)

    def __str__(self):
        return "%s (%s)" % (self.message, self.error)


class Stats(Enum):

    VIT = "vit"
    ATN = "atn"
    END = "end"
    STR = "str"
    DEX = "dex"
    RES = "res"
    INT = "int"
    FTH = "fth"
    LVL = "slv"
    SLS = "sls"
    HUM = "hum"


class DSProcess:

    GAME_VERSIONS = ({
        0xFC293654: "Steam",
        0xCE9634B4: "Debug",
        0xE91B11E2: "Steamworks Beta"
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

    def __init__(self, process_name, debug=False):
        self._hook = DSHook(self, 5000, 5000, process_name)
        self._debug = debug
        self.version = None
        self.pointers = {}
        self.is_hooked = lambda: self._hook.Hooked
        self.is_loaded = lambda: self.pointers[Index.CHR_FOLLOW_CAM].Resolve() != IntPtr.Zero
        self._hook.Start()
        self.scan_aob()

    def get_version(self):
        return self.version

    def set_version(self, version):
        self.version = version

    def check_version(self):
        try:
            version = self.pointers[Index.CHECK_VERSION].ReadUInt32(0)
            self.set_version(DSProcess.GAME_VERSIONS[version])
        except KeyError:
            if self._debug:
                print(Fore.RED + format_exc() + Fore.RESET)
            self.set_version("Unknown")
        finally:
            try:
                getattr(self, "update_version")()
            except AttributeError:
                if self._debug:
                    print(Fore.RED + format_exc() + Fore.RESET)

    def scan_aob(self):

        p, h, i, o = self.pointers, self._hook, Index, DSOffsets

        p[i.CHECK_VERSION] = h.CreateBasePointer(ptr(o.CHECK_VERSION))

        p[i.POS_LOCK] = h.RegisterAbsoluteAOB(o.POS_LOCK_AOB)
        p[i.NODE_GRAPH] = h.RegisterAbsoluteAOB(o.NODE_GRAPH_AOB)
        p[i.ALL_NO_MAGIC_QTY_CONSUME] = h.RegisterAbsoluteAOB(o.ALL_NO_MAGIC_QTY_CONSUME_AOB,
                                                              o.ALL_NO_MAGIC_QTY_CONSUME_AOB_OFFSET)
        p[i.PLAYER_NO_DEAD] = h.RegisterAbsoluteAOB(o.PLAYER_NO_DEAD_AOB,
                                                    o.PLAYER_NO_DEAD_AOB_OFFSET)
        p[i.PLAYER_EXTERMINATE] = h.RegisterAbsoluteAOB(o.PLAYER_EXTERMINATE_AOB,
                                                        o.PLAYER_EXTERMINATE_AOB_OFFSET)
        p[i.ALL_NO_STAMINA_CONSUME] = h.RegisterAbsoluteAOB(o.ALL_NO_STAMINA_CONSUME_AOB,
                                                            o.ALL_NO_STAMINA_CONSUME_AOB_OFFSET)
        p[i.COMPASS] = h.RegisterAbsoluteAOB(o.COMPASS_AOB)
        p[i.COMPASS_SMALL] = h.CreateChildPointer(p[i.COMPASS], o.COMPASS_SMALL_AOB_OFFSET)
        p[i.COMPASS_LARGE] = h.CreateChildPointer(p[i.COMPASS], o.COMPASS_LARGE_AOB_OFFSET)
        p[i.ALTIMETER] = h.CreateChildPointer(p[i.COMPASS], o.ALTIMETER_AOB_OFFSET)
        p[i.DRAW_MAP] = h.RegisterAbsoluteAOB(o.DRAW_MAP_AOB, o.DRAW_MAP_AOB_OFFSET)

        p[i.CHAR_DATA_A] = h.RegisterAbsoluteAOB(o.CHAR_DATA_A_AOB, o.CHAR_DATA_AOB_OFFSET_A,
                                                 o.CHAR_DATA_OFFSET_A1, o.CHAR_DATA_OFFSET_A2,
                                                 o.CHAR_DATA_OFFSET_A3)
        p[i.CHAR_MAP_DATA] = h.CreateChildPointer(p[i.CHAR_DATA_A], o.CharDataA.CHAR_MAP_DATA_POINTER)
        p[i.ANIM_DATA_A] = h.CreateChildPointer(p[i.CHAR_MAP_DATA], o.CharMapData.ANIM_DATA_POINTER_A)
        p[i.CHAR_POS_DATA] = h.CreateChildPointer(p[i.CHAR_MAP_DATA], o.CharMapData.CHAR_POS_DATA_POINTER)
        p[i.CHAR_DATA_B] = h.RegisterAbsoluteAOB(o.CHAR_DATA_B_AOB, o.CHAR_DATA_AOB_OFFSET_B,
                                                 o.CHAR_DATA_OFFSET_B1, o.CHAR_DATA_OFFSET_B2)
        p[i.GESTURES] = h.CreateChildPointer(p[i.CHAR_DATA_B], o.CharDataB.GESTURES_UNLOCKED_POINTER)
        p[i.GRAPHICS_DATA] = h.RegisterAbsoluteAOB(o.GRAPHICS_DATA_AOB, o.GRAPHICS_DATA_AOB_OFFSET,
                                                   o.GRAPHICS_DATA_OFFSET_1, o.GRAPHICS_DATA_OFFSET_2)
        p[i.WORLD_STATE] = h.RegisterAbsoluteAOB(o.WORLD_STATE_AOB, o.WORLD_STATE_AOB_OFFSET, o.WORLD_STATE_OFFSET)
        p[i.MENU_MANAGER] = h.RegisterAbsoluteAOB(o.MENU_MANGER_AOB, o.MENU_MANGER_AOB_OFFSET, o.MENU_MANGER_OFFSET)
        p[i.CHR_FOLLOW_CAM] = h.RegisterAbsoluteAOB(o.CHR_FOLLOW_CAM_AOB, o.CHR_FOLLOW_CAM_AOB_OFFSET,
                                                    o.CHR_FOLLOW_CAM_OFFSET_1, o.CHR_FOLLOW_CAM_OFFSET_2,
                                                    o.CHR_FOLLOW_CAM_OFFSET_3)
        p[i.EVENT_FLAGS] = h.RegisterAbsoluteAOB(o.EVENT_FLAGS_AOB, o.EVENT_FLAGS_AOB_OFFSET, o.EVENT_FLAGS_OFFSET_1,
                                                 o.EVENT_FLAGS_OFFSET_2)
        p[i.UNKNOWN_A] = h.RegisterAbsoluteAOB(o.UNKNOWN_AOB_A, o.UNKNOWN_AOB_OFFSET_A, o.UNKNOWN_OFFSET_A)
        p[i.UNKNOWN_B] = h.RegisterAbsoluteAOB(o.UNKNOWN_AOB_B, o.UNKNOWN_AOB_OFFSET_B, o.UNKNOWN_OFFSET_B)
        p[i.UNKNOWN_C] = h.RegisterAbsoluteAOB(o.UNKNOWN_AOB_C, o.UNKNOWN_AOB_OFFSET_C, o.UNKNOWN_OFFSET_C)
        p[i.UNKNOWN_D] = h.RegisterAbsoluteAOB(o.UNKNOWN_AOB_D, o.UNKNOWN_AOB_OFFSET_D, o.UNKNOWN_OFFSET_D1,
                                               o.UNKNOWN_OFFSET_D2)

        p[i.ANIM_DATA_B] = h.RegisterAbsoluteAOB(o.UNKNOWN_AOB_E, o.UNKNOWN_AOB_OFFSET_E1, o.UNKNOWN_AOB_OFFSET_E2,
                                                 o.UNKNOWN_OFFSET_E1, o.UNKNOWN_OFFSET_E2, o.UNKNOWN_OFFSET_E3)

        p[i.FUNC_ITEM_GET] = h.RegisterAbsoluteAOB(o.FUNC_ITEM_GET_AOB)
        p[i.FUNC_LEVEL_UP] = h.RegisterAbsoluteAOB(o.FUNC_LEVEL_UP_AOB)
        p[i.FUNC_BONFIRE_WARP] = h.RegisterAbsoluteAOB(o.FUNC_BONFIRE_WARP_AOB)
        p[i.FUNC_BONFIRE_WARP_UNKNOWN] = h.RegisterAbsoluteAOB(o.FUNC_BONFIRE_WARP_UNKNOWN_AOB,
                                                               o.FUNC_BONFIRE_WARP_UNKNOWN_OFFSET)
        p[i.FUNC_ITEM_DROP] = h.RegisterAbsoluteAOB(o.FUNC_ITEM_DROP_AOB)
        p[i.FUNC_ITEM_DROP_UNKNOWN_A] = h.RegisterAbsoluteAOB(o.FUNC_ITEM_DROP_UNKNOWN_AOB_A,
                                                              o.FUNC_ITEM_DROP_UNKNOWN_AOB_OFFSET_A)

        p[i.FUNC_ITEM_DROP_UNKNOWN_B] = h.RegisterAbsoluteAOB(o.FUNC_ITEM_DROP_UNKNOWN_AOB_B,
                                                              o.FUNC_ITEM_DROP_UNKNOWN_AOB_OFFSET_B)

        p[i.GAME_MAN] = h.RegisterAbsoluteAOB(o.GAME_MAN_AOB, DSOffsets.GAME_MAN_AOB_OFFSET)

        h.OnHooked += lambda sender, *e: self.check_version()
        h.OnHooked += lambda sender, *e: self.disable_fps_disconnect()
        h.OnUnhooked += lambda sender, *e: self.set_version(None)

    def execute_asm(self, asm: str):
        byte_array = FasmNet.Assemble("use32\norg 0x0\n" + asm)
        insert_ptr = self._hook.Allocate(len(byte_array))
        byte_array = FasmNet.Assemble("use32\norg " + hex(insert_ptr.ToInt32()) + "\n" + asm)
        Kernel32.WriteBytes(self._hook.Handle, insert_ptr, byte_array)
        result = self._hook.Execute(insert_ptr)
        self._hook.Free(insert_ptr)
        if result != 0:
            raise AsmExecuteError(result)

    @staticmethod
    def get_event_flag_offset(flag_id):
        id_str = str(flag_id).zfill(8)
        if len(id_str) == 8:
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
                return offset, mask
        raise ArgumentError("Unknown event flag ID: %d" % flag_id)

    def read_event_flag(self, flag_id):
        if not self.is_loaded() or not self.is_hooked():
            return None
        address, mask = self.get_event_flag_offset(flag_id)
        return self.pointers[Index.EVENT_FLAGS].ReadFlag32(address, mask)

    def write_event_flag(self, flag_id, value: bool):
        address, mask = self.get_event_flag_offset(flag_id)
        if not self.pointers[Index.EVENT_FLAGS].WriteFlag32(address, mask, value):
            raise WriteMemoryError()

    def listen_for_flag(self, flag_id, flag_state):
        return wait_for(lambda: self.read_event_flag(flag_id), desired_state=flag_state)

    def set_animation_speed(self, speed: float):
        if not self.pointers[Index.ANIM_DATA_A].WriteSingle(DSOffsets.AnimData.PLAY_SPEED, speed):
            raise WriteMemoryError()

    def get_last_animation(self):
        if not self.is_hooked():
            raise ReadMemoryError()
        if not self.is_loaded():
            return -1
        return self.pointers[Index.ANIM_DATA_B].ReadInt32(DSOffsets.UnknownE.LAST_ANIMATION)

    def death_cam(self, enable: bool):
        if not self.pointers[Index.UNKNOWN_B].WriteBoolean(DSOffsets.UnknownB.DEATH_CAM, enable):
            raise WriteMemoryError()

    def game_restart(self):
        if not self.is_hooked():
            raise ReadMemoryError()
        return self.pointers[Index.GAME_MAN].WriteFlag32(DSOffsets.GameMan.B_REQUEST_TO_ENDING, 1, True)

    def disable_fps_disconnect(self):
        if not self.is_hooked():
            raise ReadMemoryError()
        return self.pointers[Index.GAME_MAN].WriteInt32(DSOffsets.GameMan.IS_FPS_DISCONNECTION, 0)

    def unlock_all_gestures(self):
        if not self.is_hooked():
            raise ReadMemoryError()
        result = True
        for gesture in vars(DSOffsets.Gestures).values():
            if isinstance(gesture, int):
                result &= self.pointers[Index.GESTURES].WriteFlag32(gesture, 1, True)
        return result

    def menu_kick(self):
        return self.pointers[Index.UNKNOWN_C].WriteInt32(DSOffsets.UnknownC.MENU_KICK, 2)

    def set_phantom_type(self, value: int):
        if not self.pointers[Index.CHAR_DATA_A].WriteInt32(DSOffsets.CharDataA.PHANTOM_TYPE, value):
            raise WriteMemoryError()

    def get_phantom_type(self):
        if not self.is_hooked():
            raise ReadMemoryError()
        return self.pointers[Index.CHAR_DATA_A].ReadInt32(DSOffsets.CharDataA.PHANTOM_TYPE)

    def set_team_type(self, value: int):
        if not self.pointers[Index.CHAR_DATA_A].WriteInt32(DSOffsets.CharDataA.TEAM_TYPE, value):
            raise WriteMemoryError()

    def get_team_type(self):
        if not self.is_hooked():
            raise ReadMemoryError()
        return self.pointers[Index.CHAR_DATA_A].ReadInt32(DSOffsets.CharDataA.TEAM_TYPE)

    def get_play_region(self):
        if not self.is_hooked():
            raise ReadMemoryError()
        return self.pointers[Index.CHAR_DATA_A].ReadInt32(DSOffsets.CharDataA.PLAY_REGION)

    def set_play_region(self, value: int):
        if not self.pointers[Index.CHAR_DATA_A].WriteInt32(DSOffsets.CharDataA.PLAY_REGION, value):
            raise WriteMemoryError()

    def get_world(self):
        return self.pointers[Index.UNKNOWN_A].ReadByte(DSOffsets.UnknownA.WORLD)

    def get_area(self):
        return self.pointers[Index.UNKNOWN_A].ReadByte(DSOffsets.UnknownA.AREA)

    def set_super_armor(self, enable: bool):
        if not self.pointers[Index.CHAR_DATA_A].WriteFlag32(DSOffsets.CharDataA.CHAR_FLAGS_1,
                                                            DSOffsets.CharFlagsA.SET_SUPER_ARMOR, int(enable)):
            raise WriteMemoryError()

    def set_draw_enable(self, enable: bool):
        if not self.pointers[Index.CHAR_DATA_A].WriteFlag32(DSOffsets.CharDataA.CHAR_FLAGS_1,
                                                            DSOffsets.CharFlagsA.SET_DRAW_ENABLE, int(enable)):
            raise WriteMemoryError()

    def set_no_gravity(self, enable: bool):
        if not self.pointers[Index.CHAR_DATA_A].WriteFlag32(DSOffsets.CharDataA.CHAR_FLAGS_1,
                                                            DSOffsets.CharFlagsA.SET_DISABLE_GRAVITY, int(enable)):
            raise WriteMemoryError()

    def set_no_collision(self, enable: bool):
        if not self.pointers[Index.CHAR_MAP_DATA].WriteFlag32(DSOffsets.CharMapData.CHAR_MAP_FLAGS,
                                                              DSOffsets.CharMapFlags.DISABLE_MAP_HIT, int(enable)):
            raise WriteMemoryError()

    def set_no_dead(self, enable: bool):
        if not self.pointers[Index.CHAR_DATA_A].WriteFlag32(DSOffsets.CharDataA.CHAR_FLAGS_2,
                                                            DSOffsets.CharFlagsB.NO_DEAD, int(enable)):
            raise WriteMemoryError()

    def set_no_move(self, enable: bool):
        if not self.pointers[Index.CHAR_DATA_A].WriteFlag32(DSOffsets.CharDataA.CHAR_FLAGS_2,
                                                            DSOffsets.CharFlagsB.NO_MOVE, int(enable)):
            raise WriteMemoryError()

    def set_no_stamina_consume(self, enable: bool):
        if not self.pointers[Index.CHAR_DATA_A].WriteFlag32(DSOffsets.CharDataA.CHAR_FLAGS_2,
                                                            DSOffsets.CharFlagsB.NO_STAMINA_CONSUME, int(enable)):
            raise WriteMemoryError()

    def set_no_goods_consume(self, enable: bool):
        if not self.pointers[Index.CHAR_DATA_A].WriteFlag32(DSOffsets.CharDataA.CHAR_FLAGS_2,
                                                            DSOffsets.CharFlagsB.NO_GOODS_CONSUME, int(enable)):
            raise WriteMemoryError()

    def set_no_update(self, enable: bool):
        if not self.pointers[Index.CHAR_DATA_A].WriteFlag32(DSOffsets.CharDataA.CHAR_FLAGS_2,
                                                            DSOffsets.CharFlagsB.NO_UPDATE, int(enable)):
            raise WriteMemoryError()

    def set_no_attack(self, enable: bool):
        if not self.pointers[Index.CHAR_DATA_A].WriteFlag32(DSOffsets.CharDataA.CHAR_FLAGS_2,
                                                            DSOffsets.CharFlagsB.NO_ATTACK, int(enable)):
            raise WriteMemoryError()

    def set_no_damage(self, enable: bool):
        if not self.pointers[Index.CHAR_DATA_A].WriteFlag32(DSOffsets.CharDataA.CHAR_FLAGS_2,
                                                            DSOffsets.CharFlagsB.NO_DAMAGE, int(enable)):
            raise WriteMemoryError()

    def set_no_hit(self, enable: bool):
        if not self.pointers[Index.CHAR_DATA_A].WriteFlag32(DSOffsets.CharDataA.CHAR_FLAGS_2,
                                                            DSOffsets.CharFlagsB.NO_HIT, int(enable)):
            raise WriteMemoryError()

    def get_player_dead_mode(self):
        if not self.is_hooked():
            raise ReadMemoryError()
        return self.pointers[Index.CHAR_DATA_A].WriteFlag32(DSOffsets.CharDataA.CHAR_FLAGS_1,
                                                            DSOffsets.CharFlagsA.SET_DEAD_MODE)

    def set_player_dead_mode(self, enable: bool):
        if not self.pointers[Index.CHAR_DATA_A].WriteFlag32(DSOffsets.CharDataA.CHAR_FLAGS_1,
                                                            DSOffsets.CharFlagsA.SET_DEAD_MODE, enable):
            raise WriteMemoryError()

    def set_no_magic_all(self, enable: bool):
        if not self.pointers[Index.ALL_NO_MAGIC_QTY_CONSUME].WriteBoolean(0, enable):
            raise WriteMemoryError()

    def set_no_stamina_all(self, enable: bool):
        if not self.pointers[Index.ALL_NO_STAMINA_CONSUME].WriteBoolean(0, enable):
            raise WriteMemoryError()

    def set_exterminate(self, enable: bool):
        if not self.pointers[Index.PLAYER_EXTERMINATE].WriteBoolean(0, enable):
            raise WriteMemoryError()

    def set_no_ammo_consume_all(self, enable: bool):
        if not self.pointers[Index.ALL_NO_STAMINA_CONSUME].WriteBoolean(DSOffsets.ChrDbg.ALL_NO_ARROW_CONSUME, enable):
            raise WriteMemoryError()

    def set_hide(self, enable: bool):
        if not self.pointers[Index.ALL_NO_STAMINA_CONSUME].WriteBoolean(DSOffsets.ChrDbg.PLAYER_HIDE, enable):
            raise WriteMemoryError()

    def set_silence(self, enable: bool):
        if not self.pointers[Index.ALL_NO_STAMINA_CONSUME].WriteBoolean(DSOffsets.ChrDbg.PLAYER_SILENCE, enable):
            raise WriteMemoryError()

    def set_no_dead_all(self, enable: bool):
        if not self.pointers[Index.ALL_NO_STAMINA_CONSUME].WriteBoolean(DSOffsets.ChrDbg.ALL_NO_DEAD, enable):
            raise WriteMemoryError()

    def set_no_damage_all(self, enable: bool):
        if not self.pointers[Index.ALL_NO_STAMINA_CONSUME].WriteBoolean(DSOffsets.ChrDbg.ALL_NO_DAMAGE, enable):
            raise WriteMemoryError()

    def set_no_hit_all(self, enable: bool):
        if not self.pointers[Index.ALL_NO_STAMINA_CONSUME].WriteBoolean(DSOffsets.ChrDbg.ALL_NO_HIT, enable):
            raise WriteMemoryError()

    def set_no_attack_all(self, enable: bool):
        if not self.pointers[Index.ALL_NO_STAMINA_CONSUME].WriteBoolean(DSOffsets.ChrDbg.ALL_NO_ATTACK, enable):
            raise WriteMemoryError()

    def set_no_move_all(self, enable: bool):
        if not self.pointers[Index.ALL_NO_STAMINA_CONSUME].WriteBoolean(DSOffsets.ChrDbg.ALL_NO_MOVE, enable):
            raise WriteMemoryError()

    def set_no_update_ai_all(self, enable: bool):
        if not self.pointers[Index.ALL_NO_STAMINA_CONSUME].WriteBoolean(DSOffsets.ChrDbg.ALL_NO_UPDATE_AI, enable):
            raise WriteMemoryError()

    def disable_all_area_enemies(self, disable: bool):
        if not self.pointers[Index.GAME_MAN].WriteBoolean(DSOffsets.GameMan.IS_DISABLE_ALL_AREA_ENEMIES, disable):
            raise WriteMemoryError()

    def disable_all_area_event(self, disable: bool):
        if not self.pointers[Index.GAME_MAN].WriteBoolean(DSOffsets.GameMan.IS_DISABLE_ALL_AREA_EVENT, disable):
            raise WriteMemoryError()

    def disable_all_area_map(self, disable: bool):
        if not self.pointers[Index.GAME_MAN].WriteBoolean(DSOffsets.GameMan.IS_DISABLE_ALL_AREA_MAP, disable):
            raise WriteMemoryError()

    def disable_all_area_obj(self, disable: bool):
        if not self.pointers[Index.GAME_MAN].WriteBoolean(DSOffsets.GameMan.IS_DISABLE_ALL_AREA_OBJ, disable):
            raise WriteMemoryError()

    def enable_all_area_obj(self, enable: bool):
        if not self.pointers[Index.GAME_MAN].WriteBoolean(DSOffsets.GameMan.IS_ENABLE_ALL_AREA_OBJ, enable):
            raise WriteMemoryError()

    def enable_all_area_obj_break(self, enable: bool):
        if not self.pointers[Index.GAME_MAN].WriteBoolean(DSOffsets.GameMan.IS_ENABLE_ALL_AREA_OBJ_BREAK, enable):
            raise WriteMemoryError()

    def disable_all_area_hi_hit(self, disable: bool):
        if not self.pointers[Index.GAME_MAN].WriteBoolean(DSOffsets.GameMan.IS_DISABLE_ALL_AREA_HI_HIT, disable):
            raise WriteMemoryError()

    def disable_all_area_lo_hit(self, disable: bool):
        if not self.pointers[Index.GAME_MAN].WriteBoolean(DSOffsets.GameMan.IS_DISABLE_ALL_AREA_LO_HIT, disable):
            raise WriteMemoryError()

    def disable_all_area_sfx(self, disable: bool):
        if not self.pointers[Index.GAME_MAN].WriteBoolean(DSOffsets.GameMan.IS_DISABLE_ALL_AREA_SFX, disable):
            raise WriteMemoryError()

    def disable_all_area_sound(self, disable: bool):
        if not self.pointers[Index.GAME_MAN].WriteBoolean(DSOffsets.GameMan.IS_DISABLE_ALL_AREA_SOUND, disable):
            raise WriteMemoryError()

    def enable_obj_break_record_mode(self, enable: bool):
        if not self.pointers[Index.GAME_MAN].WriteBoolean(DSOffsets.GameMan.IS_OBJ_BREAK_RECORD_MODE, enable):
            raise WriteMemoryError()

    def enable_auto_map_warp_mode(self, enable: bool):
        if not self.pointers[Index.GAME_MAN].WriteBoolean(DSOffsets.GameMan.IS_AUTO_MAP_WARP_MODE, enable):
            raise WriteMemoryError()

    def enable_chr_npc_wander_test(self, enable: bool):
        if not self.pointers[Index.GAME_MAN].WriteBoolean(DSOffsets.GameMan.IS_CHR_NPC_WANDER_TEST, enable):
            raise WriteMemoryError()

    def enable_dbg_chr_all_dead(self, enable: bool):
        if not self.pointers[Index.GAME_MAN].WriteBoolean(DSOffsets.GameMan.IS_DBG_CHR_ALL_DEAD, enable):
            raise WriteMemoryError()

    def enable_online_mode(self, enable: bool):
        if not self.pointers[Index.GAME_MAN].WriteBoolean(DSOffsets.GameMan.IS_ONLINE_MODE, enable):
            raise WriteMemoryError()

    def draw_bounding(self, enable: bool):
        return self.pointers[Index.GRAPHICS_DATA].WriteBoolean(DSOffsets.GraphicsData.DRAW_BOUNDING_BOXES, enable)

    def draw_sprite_masks(self, enable: bool):
        return self.pointers[Index.GRAPHICS_DATA].WriteBoolean(DSOffsets.GraphicsData.DRAW_DEPTH_TEX_EDGE, enable)

    def draw_textures(self, enable: bool):
        return self.pointers[Index.GRAPHICS_DATA].WriteBoolean(DSOffsets.GraphicsData.DRAW_TEXTURES, enable)

    def draw_sprites(self, enable: bool):
        return self.pointers[Index.GRAPHICS_DATA].WriteBoolean(DSOffsets.GraphicsData.NORMAL_DRAW_TEX_EDGE, enable)

    def draw_trans(self, enable: bool):
        return self.pointers[Index.GRAPHICS_DATA].WriteBoolean(DSOffsets.GraphicsData.NORMAL_TRANS, enable)

    def draw_shadows(self, enable: bool):
        return self.pointers[Index.GRAPHICS_DATA].WriteBoolean(DSOffsets.GraphicsData.DRAW_SHADOWS, enable)

    def draw_sprite_shadows(self, enable: bool):
        return self.pointers[Index.GRAPHICS_DATA].WriteBoolean(DSOffsets.GraphicsData.DRAW_SPRITE_SHADOWS, enable)

    def draw_map(self, enable: bool):
        return self.pointers[Index.DRAW_MAP].WriteBoolean(DSOffsets.DrawMap.DRAW_MAP, enable)

    def draw_creatures(self, enable: bool):
        return self.pointers[Index.DRAW_MAP].WriteBoolean(DSOffsets.DrawMap.DRAW_CREATURES, enable)

    def draw_objects(self, enable: bool):
        return self.pointers[Index.DRAW_MAP].WriteBoolean(DSOffsets.DrawMap.DRAW_OBJECTS, enable)

    def draw_sfx(self, enable: bool):
        return self.pointers[Index.DRAW_MAP].WriteBoolean(DSOffsets.DrawMap.DRAW_SFX, enable)

    def draw_compass_large(self, enable: bool):
        return self.pointers[Index.COMPASS_LARGE].WriteBoolean(0, enable)

    def draw_compass_small(self, enable: bool):
        return self.pointers[Index.COMPASS_SMALL].WriteBoolean(0, enable)

    def draw_altimeter(self, enable: bool):
        return self.pointers[Index.ALTIMETER].WriteBoolean(0, enable)

    def draw_nodes(self, enable: bool):
        return self.pointers[Index.NODE_GRAPH].WriteBoolean(DSOffsets.NODE_GRAPH_AOB_OFFSET, enable)

    def override_filter(self, enable: bool):
        return self.pointers[Index.GRAPHICS_DATA].WriteBoolean(DSOffsets.GraphicsData.ENABLE_FILTER, enable)

    def set_brightness(self, red: float, green: float, blue: float):
        self.pointers[Index.GRAPHICS_DATA].WriteSingle(DSOffsets.GraphicsData.BRIGHTNESS_R, red)
        self.pointers[Index.GRAPHICS_DATA].WriteSingle(DSOffsets.GraphicsData.BRIGHTNESS_G, green)
        self.pointers[Index.GRAPHICS_DATA].WriteSingle(DSOffsets.GraphicsData.BRIGHTNESS_B, blue)

    def set_contrast(self, red: float, green: float, blue: float):
        self.pointers[Index.GRAPHICS_DATA].WriteSingle(DSOffsets.GraphicsData.CONTRAST_R, red)
        self.pointers[Index.GRAPHICS_DATA].WriteSingle(DSOffsets.GraphicsData.CONTRAST_G, green)
        self.pointers[Index.GRAPHICS_DATA].WriteSingle(DSOffsets.GraphicsData.CONTRAST_B, blue)

    def set_saturation(self, saturation: float):
        return self.pointers[Index.GRAPHICS_DATA].WriteSingle(DSOffsets.GraphicsData.SATURATION, saturation)

    def set_hue(self, hue: float):
        return self.pointers[Index.GRAPHICS_DATA].WriteSingle(DSOffsets.GraphicsData.HUE, hue)

    def get_class(self):
        if not self.is_hooked():
            raise ReadMemoryError()
        return self.pointers[Index.CHAR_DATA_B].ReadByte(DSOffsets.CharDataB.CLASS)

    def set_class(self, value: int):
        if not self.pointers[Index.CHAR_DATA_B].WriteByte(DSOffsets.CharDataB.CLASS, value):
            raise WriteMemoryError()

    def get_soul_level(self):
        if not self.is_hooked():
            raise ReadMemoryError()
        return self.pointers[Index.CHAR_DATA_B].ReadInt32(DSOffsets.CharDataB.SOUL_LEVEL)

    def get_souls(self):
        if not self.is_hooked():
            raise ReadMemoryError()
        return self.pointers[Index.CHAR_DATA_B].ReadInt32(DSOffsets.CharDataB.SOULS)

    def set_souls(self, value: int):
        if not self.pointers[Index.CHAR_DATA_B].WriteInt32(DSOffsets.CharDataB.SOULS, value):
            raise WriteMemoryError()

    def get_humanity(self):
        if not self.is_hooked():
            raise ReadMemoryError()
        return self.pointers[Index.CHAR_DATA_B].ReadInt32(DSOffsets.CharDataB.HUMANITY)

    def set_humanity(self, value: int):
        if not self.pointers[Index.CHAR_DATA_B].WriteInt32(DSOffsets.CharDataB.HUMANITY, value):
            raise WriteMemoryError()

    def get_hp(self):
        if not self.is_hooked():
            raise ReadMemoryError()
        return self.pointers[Index.CHAR_DATA_B].ReadInt32(DSOffsets.CharDataB.HP)

    def set_hp(self, value: int):
        if not self.pointers[Index.CHAR_DATA_A].WriteInt32(DSOffsets.CharDataA.HP, value):
            raise WriteMemoryError()

    def get_hp_max(self):
        if not self.is_hooked():
            raise ReadMemoryError()
        return self.pointers[Index.CHAR_DATA_B].ReadInt32(DSOffsets.CharDataB.HP_MAX)

    def get_hp_mod_max(self):
        if not self.is_hooked():
            raise ReadMemoryError()
        return self.pointers[Index.CHAR_DATA_B].ReadInt32(DSOffsets.CharDataB.HP_MOD_MAX)

    def get_stamina(self):
        if not self.is_hooked():
            raise ReadMemoryError()
        return self.pointers[Index.CHAR_DATA_B].ReadInt32(DSOffsets.CharDataB.STAMINA_MOD_MAX)

    def get_vitality(self):
        if not self.is_hooked():
            raise ReadMemoryError()
        return self.pointers[Index.CHAR_DATA_B].ReadInt32(DSOffsets.CharDataB.VITALITY)

    def get_attunement(self):
        if not self.is_hooked():
            raise ReadMemoryError()
        return self.pointers[Index.CHAR_DATA_B].ReadInt32(DSOffsets.CharDataB.ATTUNEMENT)

    def get_endurance(self):
        if not self.is_hooked():
            raise ReadMemoryError()
        return self.pointers[Index.CHAR_DATA_B].ReadInt32(DSOffsets.CharDataB.ENDURANCE)

    def get_strength(self):
        if not self.is_hooked():
            raise ReadMemoryError()
        return self.pointers[Index.CHAR_DATA_B].ReadInt32(DSOffsets.CharDataB.STRENGTH)

    def get_dexterity(self):
        if not self.is_hooked():
            raise ReadMemoryError()
        return self.pointers[Index.CHAR_DATA_B].ReadInt32(DSOffsets.CharDataB.DEXTERITY)

    def get_resistance(self):
        if not self.is_hooked():
            raise ReadMemoryError()
        return self.pointers[Index.CHAR_DATA_B].ReadInt32(DSOffsets.CharDataB.RESISTANCE)

    def get_intelligence(self):
        if not self.is_hooked():
            raise ReadMemoryError()
        return self.pointers[Index.CHAR_DATA_B].ReadInt32(DSOffsets.CharDataB.INTELLIGENCE)

    def get_faith(self):
        if not self.is_hooked():
            raise ReadMemoryError()
        return self.pointers[Index.CHAR_DATA_B].ReadInt32(DSOffsets.CharDataB.FAITH)

    def get_stat(self, stat: Stats):
        if stat == Stats.VIT:
            return self.get_vitality()
        elif stat == Stats.ATN:
            return self.get_attunement()
        elif stat == Stats.END:
            return self.get_endurance()
        elif stat == Stats.STR:
            return self.get_strength()
        elif stat == Stats.DEX:
            return self.get_dexterity()
        elif stat == Stats.RES:
            return self.get_resistance()
        elif stat == Stats.INT:
            return self.get_intelligence()
        elif stat == Stats.FTH:
            return self.get_faith()
        elif stat == Stats.LVL:
            return self.get_soul_level()
        elif stat == Stats.SLS:
            return self.get_souls()
        elif stat == Stats.HUM:
            return self.get_humanity()

    def level_up(self, new_stats: dict):

        stats = self._hook.Allocate(2048).ToInt32()
        humanity = self.get_humanity()
        level = DSOffsets.FuncLevelUp

        def write(offs, stat): Kernel32.WriteInt32(self._hook.Handle, ptr(stats + offs), stat)

        write(level.VIT, new_stats[Stats.VIT])
        write(level.ATN, new_stats[Stats.ATN])
        write(level.END, new_stats[Stats.END])
        write(level.STR, new_stats[Stats.STR])
        write(level.DEX, new_stats[Stats.DEX])
        write(level.RES, new_stats[Stats.RES])
        write(level.INT, new_stats[Stats.INT])
        write(level.FTH, new_stats[Stats.FTH])
        write(level.SLV, new_stats[Stats.LVL])
        write(level.SLS, new_stats[Stats.SLS])

        self.set_no_dead(True)
        self.execute_asm(
                Scripts.LEVEL_UP % (stats, stats, self.pointers[Index.FUNC_LEVEL_UP].Resolve().ToInt32())
        )
        self.set_no_dead(False)

        self._hook.Free(ptr(stats))

        self.set_humanity(humanity)

    def get_pos(self):
        return (
            self.pointers[Index.CHAR_POS_DATA].ReadSingle(DSOffsets.CharPosData.POS_X),
            self.pointers[Index.CHAR_POS_DATA].ReadSingle(DSOffsets.CharPosData.POS_Y),
            self.pointers[Index.CHAR_POS_DATA].ReadSingle(DSOffsets.CharPosData.POS_Z),
            (self.pointers[Index.CHAR_POS_DATA].ReadSingle(DSOffsets.CharPosData.POS_ANGLE) + pi) / (pi * 2) * 360
        )

    def get_pos_stable(self):
        return (
            self.pointers[Index.WORLD_STATE].ReadSingle(DSOffsets.WorldState.POS_STABLE_X),
            self.pointers[Index.WORLD_STATE].ReadSingle(DSOffsets.WorldState.POS_STABLE_Y),
            self.pointers[Index.WORLD_STATE].ReadSingle(DSOffsets.WorldState.POS_STABLE_Z),
            (self.pointers[Index.WORLD_STATE].ReadSingle(DSOffsets.WorldState.POS_STABLE_ANGLE) + pi) / (pi * 2) * 360
        )

    def jump_pos(self, x: float, y: float, z: float, a: float):
        self.pointers[Index.CHAR_MAP_DATA].WriteSingle(DSOffsets.CharMapData.WARP_X, x)
        self.pointers[Index.CHAR_MAP_DATA].WriteSingle(DSOffsets.CharMapData.WARP_Y, y)
        self.pointers[Index.CHAR_MAP_DATA].WriteSingle(DSOffsets.CharMapData.WARP_Z, z)
        self.pointers[Index.CHAR_MAP_DATA].WriteSingle(DSOffsets.CharMapData.WARP_ANGLE, a / 360 * 2 * pi - pi)
        self.pointers[Index.CHAR_MAP_DATA].WriteBoolean(DSOffsets.CharMapData.WARP, True)

    def lock_pos(self, lock: bool):
        if lock:
            self.pointers[Index.POS_LOCK].WriteBytes(DSOffsets.POS_LOCK_AOB_OFFSET_1,
                                                     bytes([0x90, 0x90, 0x90, 0x90, 0x90]))
            self.pointers[Index.POS_LOCK].WriteBytes(DSOffsets.POS_LOCK_AOB_OFFSET_2,
                                                     bytes([0x90, 0x90, 0x90, 0x90, 0x90]))
        else:
            self.pointers[Index.POS_LOCK].WriteBytes(DSOffsets.POS_LOCK_AOB_OFFSET_1,
                                                     bytes([0x66, 0x0F, 0xD6, 0x46, 0x10]))
            self.pointers[Index.POS_LOCK].WriteBytes(DSOffsets.POS_LOCK_AOB_OFFSET_2,
                                                     bytes([0x66, 0x0F, 0xD6, 0x46, 0x18]))

    def dump_follow_cam(self):
        return self.pointers[Index.CHR_FOLLOW_CAM].ReadBytes(0, 512)

    def undump_follow_cam(self, byte_arr: bytes):
        return self.pointers[Index.CHR_FOLLOW_CAM].WriteBytes(0, byte_arr)

    def get_bonfire(self):
        if not self.is_hooked():
            raise ReadMemoryError()
        return self.pointers[Index.WORLD_STATE].ReadInt32(DSOffsets.WorldState.LAST_BONFIRE)

    def set_bonfire(self, bonfire_id: int):
        if not self.pointers[Index.WORLD_STATE].WriteInt32(DSOffsets.WorldState.LAST_BONFIRE, bonfire_id):
            raise WriteMemoryError()

    def get_name(self):
        if not self.is_hooked():
            raise ReadMemoryError()
        return self.pointers[Index.CHAR_DATA_B].ReadString(DSOffsets.CharDataB.CHAR_NAME, Encoding.Unicode, 0x22)

    def set_name(self, name: str):
        return self.pointers[Index.CHAR_DATA_B].WriteString(DSOffsets.CharDataB.CHAR_NAME,
                                                            Encoding.Unicode, 0x22, name)

    def get_sex(self):
        if not self.is_hooked():
            raise ReadMemoryError()
        return self.pointers[Index.CHAR_DATA_B].ReadInt16(DSOffsets.CharDataB.GENDER)

    def set_sex(self, value: int):
        if not self.pointers[Index.CHAR_DATA_B].WriteInt16(DSOffsets.CharDataB.GENDER, value):
            raise WriteMemoryError()

    def get_physique(self):
        if not self.is_hooked():
            raise ReadMemoryError()
        return self.pointers[Index.CHAR_DATA_B].ReadByte(DSOffsets.CharDataB.PHYSIQUE)

    def set_physique(self, value: int):
        if not self.pointers[Index.CHAR_DATA_B].WriteByte(DSOffsets.CharDataB.PHYSIQUE, value):
            raise WriteMemoryError()

    def set_covenant(self, value: int):
        if not self.pointers[Index.CHAR_DATA_B].WriteByte(DSOffsets.CharDataB.COVENANT, value):
            raise WriteMemoryError()

    def get_covenant(self):
        if not self.is_hooked():
            raise ReadMemoryError()
        return self.pointers[Index.CHAR_DATA_B].ReadByte(DSOffsets.CharDataB.COVENANT)

    def set_ng_mode(self, value: int):
        if not self.pointers[Index.CHAR_DATA_C].WriteInt32(DSOffsets.CharDataC.NEW_GAME_MODE, value):
            raise WriteMemoryError()

    def item_drop(self, category, item_id, count):
        return \
            self.execute_asm(
                Scripts.ITEM_DROP % (
                    category, item_id, count,
                    self.pointers[Index.FUNC_ITEM_DROP_UNKNOWN_A].Resolve().ToInt32(),
                    self.pointers[Index.FUNC_ITEM_DROP_UNKNOWN_B].Resolve().ToInt32(),
                    self.pointers[Index.FUNC_ITEM_DROP].Resolve().ToInt32()
                )
            )

    def item_get(self, category, item_id, count):
        return \
            self.execute_asm(
                Scripts.ITEM_GET % (
                    self.pointers[Index.CHAR_DATA_B].Resolve().ToInt32() + DSOffsets.CharDataB.INVENTORY_INDEX_START,
                    category, item_id, count,
                    self.pointers[Index.FUNC_ITEM_GET].Resolve().ToInt32()
                )
            )

    def bonfire_warp(self):
        return \
            self.execute_asm(
                Scripts.BONFIRE_WARP % (
                    self.pointers[Index.FUNC_BONFIRE_WARP_UNKNOWN].Resolve().ToInt32(),
                    self.pointers[Index.FUNC_BONFIRE_WARP].Resolve().ToInt32()
                )
            )
