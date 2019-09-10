from ctypes import *
from ctypes.wintypes import HANDLE, LPCVOID, LPVOID, LPDWORD, DWORD, BOOL
from fasm import fasm
import win32con
import win32api


class DSInterface:

    kernel32 = WinDLL('kernel32', use_last_error=True)

    read_process_memory = kernel32.ReadProcessMemory
    read_process_memory.argtypes = (HANDLE, LPCVOID, LPVOID, c_size_t, POINTER(c_size_t))
    read_process_memory.restype = BOOL

    write_process_memory = kernel32.WriteProcessMemory
    write_process_memory.argtypes = (HANDLE, LPVOID, LPCVOID, c_size_t, POINTER(c_size_t))
    write_process_memory.restype = BOOL

    virtual_alloc_ex = kernel32.VirtualAllocEx
    virtual_alloc_ex.argtypes = (HANDLE, LPVOID, LPVOID, DWORD, DWORD)
    virtual_alloc_ex.restype = BOOL

    virtual_free_ex = kernel32.VirtualFreeEx
    virtual_free_ex.argtypes = (HANDLE, LPVOID, c_size_t, DWORD)

    create_remote_thread = kernel32.CreateRemoteThread
    create_remote_thread.argtypes = (HANDLE, LPVOID, c_size_t, c_int, LPVOID, DWORD, LPDWORD)
    create_remote_thread.restype = BOOL

    wait_for_single_object = kernel32.WaitForSingleObject
    wait_for_single_object.argtypes = (HANDLE, DWORD)

    def __init__(self, pid):
        self.process = win32api.OpenProcess(win32con.PROCESS_ALL_ACCESS, False, pid)

    def read_int(self, address):
        return self._read_int(address, True)

    def read_uint(self, address):
        return self._read_int(address, False)

    def read_float(self, address):
        return self._read_float(address)

    def read_str(self, address):
        return self._read_str(address)

    def read_byte(self, address):
        return self._read_byte(address)

    def _read_int(self, address, signed: bool):
        data = c_ulong() if not signed else c_long()
        bytes_read = c_ulong(0)
        if self.read_process_memory(self.process.handle, address, byref(data), sizeof(data), byref(bytes_read)):
            return data.value
        else:
            print("Failed to read memory - error code: ", windll.kernel32.GetLastError())
            windll.kernel32.SetLastError(10000)
            return None

    def _read_float(self, address):
        data = c_float()
        bytes_read = c_ulong(0)
        if DSInterface.read_process_memory(self.process.handle, address, byref(data), sizeof(data), byref(bytes_read)):
            return data.value
        else:
            print("Failed to read memory - error code: ", windll.kernel32.GetLastError())
            windll.kernel32.SetLastError(10000)
            return None

    def _read_str(self, address):
        data = create_unicode_buffer(32)
        bytes_read = c_ulong(0)
        if DSInterface.read_process_memory(self.process.handle, address, byref(data), sizeof(data), byref(bytes_read)):
            return data.value
        else:
            print("Failed to read memory - error code: ", windll.kernel32.GetLastError())
            windll.kernel32.SetLastError(10000)
            return None

    def _read_byte(self, address):
        data = c_byte()
        bytes_read = c_ulong(0)
        if DSInterface.read_process_memory(self.process.handle, address, byref(data), sizeof(data), byref(bytes_read)):
            return data.value
        else:
            print("Failed to read memory - error code: ", windll.kernel32.GetLastError())
            windll.kernel32.SetLastError(10000)
            return None

    def read_flag(self, address, mask):
        flags = self.read_int(address)
        return flags & mask != 0

    def write_flag(self, address, mask, enable: bool):
        flags = self.read_int(address)
        if enable:
            flags |= mask
        else:
            flags &= ~mask
        return self.write_int(address, flags)

    def write_float(self, address, data: float):
        c_data = c_float(data)
        count = c_ulong(0)
        if DSInterface.write_process_memory(self.process.handle, address, byref(c_data), sizeof(c_data), byref(count)):
            return True
        else:
            print("Failed to write memory - error code: ", windll.kernel32.GetLastError())
            windll.kernel32.SetLastError(10000)
            return False

    def write_int(self, address, data: int):
        c_data = c_int(data)
        count = c_ulong(0)
        if DSInterface.write_process_memory(self.process.handle, address, byref(c_data), sizeof(c_data), byref(count)):
            return True
        else:
            print("Failed to write memory - error code: ", windll.kernel32.GetLastError())
            windll.kernel32.SetLastError(10000)
            return False

    def write_bytes(self, address, data: bytes):
        count = c_ulong(0)
        length = len(data)
        c_data = c_char_p(data[count.value:])
        c_int(0)
        if DSInterface.write_process_memory(self.process.handle, address, c_data, length, byref(count)):
            return True
        else:
            print("Failed to write memory - error code: ", windll.kernel32.GetLastError())
            windll.kernel32.SetLastError(10000)
            return False

    def allocate(self, length):
        return DSInterface.virtual_alloc_ex(self.process.handle, 0, length, win32con.MEM_COMMIT,
                                            win32con.PAGE_EXECUTE_READWRITE)

    def free(self, address):
        length = sizeof(c_int(address))
        DSInterface.virtual_free_ex(self.process.handle, address, length, win32con.MEM_RELEASE)

    def execute_asm(self, asm):
        fasm_dll = fasm.get_fasm_dll()
        write_bytes = fasm_dll.Assemble("use32\norg 0x0\n%s\n" % asm)
        start_addr = self.allocate(len(write_bytes))
        write_bytes = fasm_dll.Assemble("use32\norg %s\n%s\n" % (hex(start_addr), asm))
        success = self.write_bytes(start_addr, write_bytes)
        thread_id = c_ulong(0)
        DSInterface.wait_for_single_object(
            DSInterface.create_remote_thread(
                self.process.handle, None, 0, start_addr, None, 0, byref(thread_id)
            ), 0xFFFFFFFF
        )
        self.free(start_addr)
        return success
