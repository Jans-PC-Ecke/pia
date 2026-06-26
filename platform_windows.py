# platform_windows.py - Windows-spezifische Implementierungen
import os
import subprocess
import platform
import sys
from typing import Tuple, Optional

IS_WINDOWS = platform.system() == "Windows"

if IS_WINDOWS:
    import pygetwindow as gw
    import pyautogui
    from ctypes import cast, POINTER
    from comtypes import CLSCTX_ALL
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume, ISimpleAudioVolume
    
    # Audio-Steuerung
    devices = AudioUtilities.GetSpeakers()
    interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    volume = cast(interface, POINTER(IAudioEndpointVolume))
    
    def audio_leiser():
        current = volume.GetMasterVolumeLevelScalar()
        volume.SetMasterVolumeLevelScalar(max(0, current - 0.05), None)
    
    def audio_lauter():
        current = volume.GetMasterVolumeLevelScalar()
        volume.SetMasterVolumeLevelScalar(min(1, current + 0.05), None)
    
    def audio_mute():
        volume.SetMute(not volume.GetMute(), None)
    
    # Fenster
    def fenster_liste():
        windows = gw.getAllWindows()
        return "\n".join([f"{w.title}" for w in windows if w.title.strip()])
    
    def fenster_schliessen(name: str):
        windows = gw.getWindowsWithTitle(name)
        for w in windows:
            w.close()
        return len(windows)
    
    # Screenshot
    def screenshot_machen(path: str):
        screenshot = pyautogui.screenshot()
        screenshot.save(path)
        return path
    
    # Programm starten
    def programm_starten(name: str):
        os.startfile(name) if os.path.exists(name) else subprocess.Popen(name, shell=True)
    
    # Systemaktionen
    def system_ausschalten():
        os.system("shutdown /s /t 60")
    
    def system_neustart():
        os.system("shutdown /r /t 60")
else:
    # Dummy-Funktionen für Nicht-Windows
    def audio_leiser(): pass
    def audio_lauter(): pass
    def audio_mute(): pass
    def fenster_liste(): return ""
    def fenster_schliessen(name): return 0
    def screenshot_machen(path): return path
    def programm_starten(name): pass
    def system_ausschalten(): pass
    def system_neustart(): pass