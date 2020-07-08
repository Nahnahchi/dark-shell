using System;
using PropertyHookCustom;

namespace DarkShellHook
{
    public class DSHook : PHook 
    {
        public DSHook(object caller, int refreshInterval, int minLifetime, string processName) : 
            base(caller, refreshInterval, minLifetime, p => p.MainWindowTitle == processName)
        {

        }
    }
}
