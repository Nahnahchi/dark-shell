import ctypes, struct, sys

__all__ = "FASM", "FasmStateError", "FasmError"


def get_fasm_dll():
    return FASM("fasm/fasm.dll")


class FasmStateError(RuntimeError):
    __FasmState = {
         0 : "OK",
         1 : "WORKING",
         2 : "ERROR",
        -1 : "INVALID_PARAMETER",
        -2 : "OUT_OF_MEMORY",
        -3 : "STACK_OVERFLOW",
        -4 : "SOURCE_NOT_FOUND",
        -5 : "UNEXPECTED_END_OF_SOURCE",
        -6 : "CANNOT_GENERATE_CODE",
        -7 : "FORMAT_LIMITATIONS_EXCEDDED",
        -8 : "WRITE_FAILED"
        }

    def __init__(self, *args):
        errCode = args[0]
        msg = FasmStateError.__FasmState[errCode]
        self.args = [errCode, msg]
        self.message = msg
        return super(FasmStateError, self).__init__(*self.args)


class FasmError(RuntimeError):

    __FasmErrors = {
        -101 : "FILE_NOT_FOUND",
        -102 : "ERROR_READING_FILE",
        -103 : "INVALID_FILE_FORMAT",
        -104 : "INVALID_MACRO_ARGUMENTS",
        -105 : "INCOMPLETE_MACRO",
        -106 : "UNEXPECTED_CHARACTERS",
        -107 : "INVALID_ARGUMENT",
        -108 : "ILLEGAL_INSTRUCTION",
        -109 : "INVALID_OPERAND",
        -110 : "INVALID_OPERAND_SIZE",
        -111 : "OPERAND_SIZE_NOT_SPECIFIED",
        -112 : "OPERAND_SIZES_DO_NOT_MATCH",
        -113 : "INVALID_ADDRESS_SIZE",
        -114 : "ADDRESS_SIZES_DO_NOT_AGREE",
        -115 : "PREFIX_CONFLICT",
        -116 : "LONG_IMMEDIATE_NOT_ENCODABLE",
        -117 : "RELATIVE_JUMP_OUT_OF_RANGE",
        -118 : "INVALID_EXPRESSION",
        -119 : "INVALID_ADDRESS",
        -120 : "INVALID_VALUE",
        -121 : "VALUE_OUT_OF_RANGE",
        -122 : "UNDEFINED_SYMBOL",
        -123 : "INVALID_USE_OF_SYMBOL",
        -124 : "NAME_TOO_LONG",
        -125 : "INVALID_NAME",
        -126 : "RESERVED_WORD_USED_AS_SYMBOL",
        -127 : "SYMBOL_ALREADY_DEFINED",
        -128 : "MISSING_END_QUOTE",
        -129 : "MISSING_END_DIRECTIVE",
        -130 : "UNEXPECTED_INSTRUCTION",
        -131 : "EXTRA_CHARACTERS_ON_LINE",
        -132 : "SECTION_NOT_ALIGNED_ENOUGH",
        -133 : "SETTING_ALREADY_SPECIFIED",
        -134 : "DATA_ALREADY_DEFINED",
        -135 : "TOO_MANY_REPEATS",
        -136 : "SYMBOL_OUT_OF_SCOPE",
        -140 : "USER_ERROR",
        -141 : "ASSERTION_FAILED"
        }

    def __init__(self, *args):
        errCode = args[0]
        errLine = args[1]
        msg = FasmError.__FasmErrors[errCode]
        self.args = [errCode, errLine, msg]
        self.message = "Error %s at line %i" % (msg, errLine)
        return super(FasmError, self).__init__(*self.args)


class FASM:

    def __init__(self, dllPath):
        try:
            self.__fasm_dll = ctypes.WinDLL(dllPath)
        except:
            raise RuntimeError("Can't load FASM.DLL")

        try:
            raw = self.__fasm_dll.fasm_GetVersion()
            self.__hi_ver = raw & 0xFFFF
            self.__lo_ver = raw >> 16
        except:
            raise RuntimeError("Can't retrive version info")

    def GetVersion(self):
        """ Return fasm version """
        return self.__hi_ver, self.__lo_ver

    def Assemble(self, source, memorySize = 0x10000, passes = 100, pipes = 0):
        """ Assemble source and return byte array """
        
        buff = ctypes.create_string_buffer(memorySize)
        if sys.hexversion < 0x03000000:
            srcPtr = ctypes.c_char_p(source)
        else:
            srcPtr = ctypes.c_char_p(source.encode('utf-8'))

        if self.__lo_ver < 70:
            state = self.__fasm_dll.fasm_Assemble(srcPtr, buff, len(buff), passes)
        else:
            state = self.__fasm_dll.fasm_Assemble(srcPtr, buff, len(buff), passes, pipes)

        if state == 0: # OK
            size, outDataPtr = struct.unpack_from('II', buff, 4)
            offset = outDataPtr - ctypes.addressof(buff)
            return buff[offset:offset + size]

        if state == 2: # ERROR
            errCode, lineHeaderPtr = struct.unpack_from('iI', buff, 4)
            offset = lineHeaderPtr - ctypes.addressof(buff)
            _, line = struct.unpack_from("pi", buff, offset)
            raise FasmError(errCode, line)

        raise FasmStateError(state)

    def AssembleAsStr(self, source, memorySize = 0x10000, passes = 100, pipes = 0):
        """ Assemble source and return byte array present as string """

        byte_arr = self.Assemble(source, memorySize, passes, pipes)
        if sys.hexversion < 0x03000000:
            return ", ".join("0x%02X" % ord(b) for b in byte_arr)
        else:
            return ", ".join("0x%02X" % (b) for b in byte_arr)