import clr
from os.path import dirname, realpath
from sys import path
path.append(dirname(realpath(__file__)))
clr.AddReference("Wrapper")
clr.AddReference("PropertyHook")
clr.AddReference("Fasm.NET")
# noinspection PyUnresolvedReferences
from DarkShellHook import DSHook
# noinspection PyUnresolvedReferences
from PropertyHookCustom import Kernel32
# noinspection PyUnresolvedReferences
from Binarysharp.Assemblers.Fasm import FasmNet
