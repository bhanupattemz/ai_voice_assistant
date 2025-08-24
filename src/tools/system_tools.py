from typing import List
from langchain.agents import Tool
import os
import platform
import screen_brightness_control as sbc
import psutil
import time
import GPUtil
import wmi
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from comtypes import CLSCTX_ALL
import pythoncom
import pyautogui


class SystemToolFactory:
    def __init__(self):
        pass

    def set_brightness(self, value) -> str:
        try:
            value = int(value)
            value = max(0, min(100, value))
            sbc.set_brightness(value)
            return f"💡 Display brightness set to {value}%"
        except Exception as e:
            return f"⚠️ Failed to set brightness: {str(e)}"

    def set_volume(self, value) -> str:
        try:
            pythoncom.CoInitialize()
            value = int(value)
            value = max(0, min(100, value))
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume = interface.QueryInterface(IAudioEndpointVolume)
            volume.SetMasterVolumeLevelScalar(value / 100.0, None)

            if value == 0:
                return "🔇 System audio muted"
            else:
                return f"🔊 System volume set to {value}%"
        except Exception as e:
            return f"⚠️ Failed to set volume: {str(e)}"

    def system_measurements(self, query: str = "") -> str:
        report = []
        cpu_usage = psutil.cpu_percent(interval=1)
        cpu_temp, fan_speed = "N/A", "N/A"
        try:
            temps = psutil.sensors_temperatures()
            if temps:
                for name, entries in temps.items():
                    for entry in entries:
                        if (
                            "core" in entry.label.lower()
                            or "cpu" in entry.label.lower()
                        ):
                            cpu_temp = f"{entry.current}°C"
                            break
        except Exception:
            pass

        if cpu_temp == "N/A" and platform.system() == "Windows":
            try:
                w = wmi.WMI(namespace="root\\OpenHardwareMonitor")
                sensors = w.Sensor()
                for sensor in sensors:
                    if sensor.SensorType == "Temperature" and "CPU" in sensor.Name:
                        cpu_temp = f"{sensor.Value}°C"
                    if sensor.SensorType == "Fan" and "CPU" in sensor.Name:
                        fan_speed = f"{sensor.Value} RPM"
            except Exception:
                pass

        report.append(f"CPU Usage: {cpu_usage}% (Processor load)")
        report.append(f"CPU Temperature: {cpu_temp}")
        report.append(f"Fan Speed: {fan_speed}")

        mem = psutil.virtual_memory()
        report.append(
            f"RAM Usage: {mem.percent}% ({round(mem.used/(1024**3), 2)}GB / {round(mem.total/(1024**3), 2)}GB)"
        )

        disk = psutil.disk_usage("/")

        file_path = "disk_speed_test.tmp"
        size_mb = 20
        data = os.urandom(1024 * 1024)

        try:
            start = time.time()
            with open(file_path, "wb") as f:
                for _ in range(size_mb):
                    f.write(data)
            write_time = time.time() - start

            start = time.time()
            with open(file_path, "rb") as f:
                for _ in range(size_mb):
                    f.read(1024 * 1024)
            read_time = time.time() - start

            os.remove(file_path)
            write_speed = round(size_mb / write_time, 2)
            read_speed = round(size_mb / read_time, 2)
        except Exception:
            write_speed, read_speed = "N/A", "N/A"

        report.append(
            f"Disk Usage: {disk.percent}% ({round(disk.used/(1024**3), 2)}GB / {round(disk.total/(1024**3), 2)}GB)"
        )
        report.append(f"Disk Speed: Write {write_speed}MB/s, Read {read_speed}MB/s")

        try:
            gpus = GPUtil.getGPUs()
            if gpus:
                gpu = gpus[0]
                report.append(f"GPU: {gpu.name}")
                report.append(f"    ▸ Load: {gpu.load*100:.1f}%")
                report.append(f"    ▸ Temperature: {gpu.temperature}°C")
                report.append(f"    ▸ Memory: {gpu.memoryUsed}MB / {gpu.memoryTotal}MB")
            else:
                report.append(" GPU: No dedicated GPU detected")
        except Exception:
            report.append("GPU: Unable to retrieve GPU information")

        try:
            duration = 3
            net1 = psutil.net_io_counters()
            time.sleep(duration)
            net2 = psutil.net_io_counters()

            upload_speed = (net2.bytes_sent - net1.bytes_sent) / (
                1024 * 1024 * duration
            )
            download_speed = (net2.bytes_recv - net1.bytes_recv) / (
                1024 * 1024 * duration
            )

            report.append(
                f"Network Speed: ↑{round(upload_speed, 2)}MB/s ↓{round(download_speed, 2)}MB/s"
            )
        except Exception:
            report.append("Network Speed: Unable to measure")

        return "\n".join(report)

    def quick_settings(self, setting: str):
        mapping = {
            "wifi": "qs1",
            "bluetooth": "qs2",
            "airplane": "qs3",
            "hotspot": "qs4",
            "saver": "qs5",
            "night": "qs6",
        }
        if setting in mapping:
            qs_key = mapping[setting]
        else:
            qs_key = setting

        if not qs_key.startswith("qs") or not qs_key[2:].isdigit():
            return f"Invalid setting: {setting}"

        index = int(qs_key[2:]) - 1

        pyautogui.hotkey("win", "a")
        time.sleep(0.5)

        for _ in range(index):
            pyautogui.hotkey("right")
            time.sleep(0.1)

        pyautogui.hotkey("enter")
        time.sleep(0.2)

        pyautogui.hotkey("esc")

        return f"{setting} toggled successfully "

    def create_tools(self) -> List[Tool]:
        """Create tools synchronously (backward compatibility)."""
        return [
            Tool(
                name="brightness_control",
                func=self.set_brightness,
                description="""Adjust the display brightness level of the system screen.
                
                **Use this tool when user asks to:**
                - Change screen brightness / make screen brighter or dimmer
                - Set specific brightness percentage (e.g., "set brightness to 50%")
                - Adjust screen illumination for comfort
                - "Increase brightness", "dim the screen", "make it brighter"
                
                **Input:** integer between 0-100 (brightness percentage, 0 = darkest, 100 = brightest)
                **Examples:** "make screen brighter" -> use 80 | "dim to 30%" -> use 30""",
            ),
            Tool(
                name="volume_control",
                func=self.set_volume,
                description="""Control the system audio volume level.
                
                **Use this tool when user asks to:**
                - Change system volume up or down
                - Set specific volume percentage (e.g., "set volume to 75%")
                - Mute or unmute the system audio
                - Adjust sound levels for speakers/headphones
                - "Turn up volume", "mute audio", "set volume to 50%"
                
                **Input:** integer between 0-100 (volume percentage, 0 = mute, 100 = maximum)
                **Examples:** "turn volume to 50%" -> use 50 | "mute audio" -> use 0""",
            ),
            Tool(
                name="system_performance_monitor",
                func=self.system_measurements,
                description="""Get comprehensive system performance metrics and hardware status information.
                
                **Use this tool when user asks about ANY of these:**
                
                **CPU Related:**
                - CPU usage, performance, load, processor stats
                - CPU temperature, thermal status
                - "How much CPU is being used?", "CPU performance", "processor load"
                
                **Memory/RAM:**
                - RAM usage, memory consumption, available memory
                - "How much RAM is used?", "memory usage", "available memory"
                
                **Storage/Disk:**
                - Disk space, storage usage, available storage
                - Disk read/write speeds, storage performance
                - "How much disk space?", "storage usage", "disk performance"
                
                **GPU/Graphics:**
                - GPU usage, graphics card performance, video card stats
                - GPU temperature, graphics memory usage
                - "GPU performance", "graphics card usage", "video memory", "GPU load"
                
                **Network:**
                - Internet speed, network performance, upload/download speeds
                - "Internet speed", "network speed", "connection speed"
                
                **General System:**
                - Overall system performance, hardware status, system diagnostics
                - Fan speeds, temperatures, resource utilization
                - "System performance", "hardware status", "computer performance"
                
                **Input:** Optional string (not used currently)
                **Examples:** 
                - "Check GPU performance" -> use this tool
                - "How much RAM is being used?" -> use this tool  
                - "What's my disk usage?" -> use this tool
                - "System performance check" -> use this tool""",
            ),
            Tool(
                name="quick_settings",
                func=self.quick_settings,
                description="""
                Toggle Windows Quick Settings (Wi-Fi, Bluetooth, Airplane Mode, Mobile Hotspot, Energy Saver, Night Light) 
                using either **names** or **button positions**.
                
                **Inputs:**
                - `setting` (str): One of ["wifi", "bluetooth", "airplane", "hotspot", "saver", "night"]  
                   OR "qsN" where N is the quick setting button number (qs1–qs9).
                
                Note: "qsN" refers to the tile position in Quick Settings (depends on layout).  
                For example, "qs1" = first button, "qs2" = second button, etc.
                
                **Examples:**
                - quick_settings("bluetooth") → "bluetooth toggled successfully"
                - quick_settings("wifi") → "wifi toggled successfully"
                - quick_settings("qs3") → "qs3 toggled successfully"
                """,
            ),
        ]


_system_factory = SystemToolFactory()


system_tools = _system_factory.create_tools()
