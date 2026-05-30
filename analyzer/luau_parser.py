import re
import math
from collections import Counter


class LuauParser:
    def __init__(self, code: str):
        self.code = code

    def parse(self) -> dict:
        code = self.code

        has_loadstring = bool(re.search(r'\bloadstring\b', code))
        has_require = bool(re.search(r'\brequire\b', code))

        gui_elements = re.findall(
            r'(?:Instance\.new|:FindFirstChild|:WaitForChild)\s*\(\s*["\']'
            r'(ScreenGui|Frame|TextLabel|TextButton|TextBox|ImageLabel|ImageButton'
            r'|ScrollingFrame|ViewportFrame|BillboardGui|SurfaceGui)["\']',
            code
        )
        has_screen_gui = bool(re.search(r'\bScreenGui\b', code))
        has_gui = bool(gui_elements) or has_screen_gui

        remote_events = re.findall(
            r'(?:RemoteEvent|RemoteFunction|BindableEvent)\b.*?(?:Name\s*=\s*["\']([^"\']+)["\'])?',
            code
        )
        remote_event_names = re.findall(
            r'(?:FireServer|InvokeServer|FireClient|InvokeClient|OnServerEvent|OnClientEvent)'
            r'\s*[\(:,]?\s*(?:["\']([^"\']+)["\'])?',
            code
        )
        has_remote_event = bool(re.search(r'\b(?:RemoteEvent|RemoteFunction|FireServer|InvokeServer)\b', code))

        has_module_script = bool(re.search(r'\bModuleScript\b', code))

        hex_strings = re.findall(r'\\x[0-9a-fA-F]{2}', code)

        long_strings = re.findall(r'\[=*\[[\s\S]*?\]=*\]', code)

        obf_var_pattern = re.compile(r'\b([a-zA-Z_][a-zA-Z0-9_]{15,})\b')
        all_long_vars = obf_var_pattern.findall(code)
        counter = Counter(all_long_vars)
        obfuscated_vars = [v for v, c in counter.items() if c >= 2 and not self._is_known_api(v)]

        entropy = self._calculate_entropy(code)
        line_count = len(code.split('\n'))

        return {
            "has_gui": has_gui,
            "has_screen_gui": has_screen_gui,
            "has_remote_event": has_remote_event,
            "has_module_script": has_module_script,
            "has_loadstring": has_loadstring,
            "has_require": has_require,
            "gui_elements": list(set(gui_elements)),
            "remote_events": [r for r in remote_event_names if r],
            "hex_string_count": len(hex_strings),
            "long_string_count": len(long_strings),
            "obfuscated_vars": obfuscated_vars[:20],
            "obfuscated_var_count": len(obfuscated_vars),
            "entropy": entropy,
            "line_count": line_count,
        }

    def _calculate_entropy(self, text: str) -> float:
        if not text:
            return 0.0
        counts = Counter(text)
        total = len(text)
        entropy = -sum((c / total) * math.log2(c / total) for c in counts.values())
        return round(entropy, 4)

    def _is_known_api(self, name: str) -> bool:
        known = {
            "workspace", "game", "script", "LocalPlayer", "PlayerGui",
            "ReplicatedStorage", "ServerStorage", "ServerScriptService",
            "StarterGui", "StarterPack", "StarterPlayer", "SoundService",
            "RunService", "UserInputService", "TweenService", "HttpService",
            "PhysicsService", "PathfindingService", "MarketplaceService",
            "Players", "Lighting", "TextService", "VirtualInputManager",
            "RenderStepped", "Heartbeat", "Stepped", "BindToClose",
            "ScreenGui", "TextLabel", "TextButton", "Frame", "ImageLabel",
            "ScrollingFrame", "RemoteEvent", "RemoteFunction", "ModuleScript",
            "Instance", "CFrame", "Vector3", "Vector2", "Color3", "UDim2",
            "UDim", "TweenInfo", "Enum", "task", "coroutine", "table",
            "string", "math", "os", "utf8", "pcall", "xpcall", "require",
            "loadstring", "rawget", "rawset", "setmetatable", "getmetatable",
        }
        return name in known
