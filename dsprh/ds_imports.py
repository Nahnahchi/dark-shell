import clr
from os.path import dirname, realpath
from sys import path

path.append(dirname(realpath(__file__)))

clr.AddReference("Wrapper")
# noinspection PyUnresolvedReferences
from DarkShellHook import DSHook

clr.AddReference("PropertyHook")
# noinspection PyUnresolvedReferences
from PropertyHookCustom import Kernel32

clr.AddReference("Fasm.NET")
# noinspection PyUnresolvedReferences
from Binarysharp.Assemblers.Fasm import FasmNet
