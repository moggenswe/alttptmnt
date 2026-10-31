# Saves a picture of the newest BizHawk window (with Lua gui drawings, which client.screenshot leaves out).
# Used by tools/e2e_run.py; run by hand: powershell -File tools/capture_bizhawk.ps1 -Out shot.png
param([string]$Out, [string]$Version = "2.11.1")
Add-Type -AssemblyName System.Drawing
Add-Type @"
using System; using System.Text; using System.Collections.Generic; using System.Runtime.InteropServices;
public class WCap {
 public delegate bool EnumProc(IntPtr h, IntPtr l);
 [DllImport("user32.dll")] public static extern bool EnumWindows(EnumProc p, IntPtr l);
 [DllImport("user32.dll")] public static extern int GetWindowText(IntPtr h, StringBuilder s, int n);
 [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr h, out uint pid);
 [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr h);
 [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr h, out RECT r);
 [DllImport("user32.dll")] public static extern bool PrintWindow(IntPtr h, IntPtr dc, uint f);
 public struct RECT { public int L,T,R,B; }
 public static IntPtr Find(uint want, string title) { IntPtr found=IntPtr.Zero; EnumWindows((h,l)=>{ uint pid; GetWindowThreadProcessId(h,out pid); var sb=new StringBuilder(256); GetWindowText(h,sb,256); if(pid==want && IsWindowVisible(h) && sb.ToString().Contains(title)) found=h; return true;}, IntPtr.Zero); return found; }
}
"@
$p = Get-Process EmuHawk | Where-Object { $_.Path -like "*$Version*" } | Sort-Object StartTime -Descending | Select-Object -First 1
$hwnd = [WCap]::Find([uint32]$p.Id, "Turtles")
$r = New-Object WCap+RECT; [WCap]::GetWindowRect($hwnd, [ref]$r) | Out-Null
$w=$r.R-$r.L; $h=$r.B-$r.T
$bmp = New-Object System.Drawing.Bitmap $w,$h
$g=[System.Drawing.Graphics]::FromImage($bmp); $dc=$g.GetHdc(); [WCap]::PrintWindow($hwnd,$dc,2) | Out-Null; $g.ReleaseHdc($dc)
$bmp.Save($Out); "$($p.Id) $w x $h"
