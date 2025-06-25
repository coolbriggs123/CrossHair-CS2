import tkinter as tk
import tkinter.ttk as ttk
import json
import os
import sys
import ctypes # Import ctypes for Windows API calls
import psutil # For process detection
from pynput import keyboard, mouse # Import pynput for global key and mouse listening
import threading # For running pynput listener in a separate thread

# Import the CustomizationMenu directly, as it's in the same directory
from customization_menu import CustomizationMenu

# Windows API constants (remain the same as they apply to any window handle)
if sys.platform == "win32":
    GWL_EXSTYLE = -20
    WS_EX_LAYERED = 0x00080000
    WS_EX_TRANSPARENT = 0x00000020 # Makes window click-through

    # Load user32.dll and define function signatures
    user32 = ctypes.windll.user32
    user32.SetWindowLongA.restype = ctypes.c_long
    user32.SetWindowLongA.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_long]
    user32.GetWindowLongA.restype = ctypes.c_long
    user32.GetWindowLongA.argtypes = [ctypes.c_void_p, ctypes.c_int]
    user32.SetWindowPos.restype = ctypes.c_bool
    user32.SetWindowPos.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_uint]
    HWND_TOPMOST = -1
    SWP_NOMOVE = 0x0002
    SWP_NOSIZE = 0x0001
    SWP_NOACTIVATE = 0x0010

class CrosshairOverlay:
    # Define a unique color that will be made transparent.
    # This color should ideally not be used in your crosshair design.
    TRANSPARENT_COLOR = '#000001' # A very dark, almost black, distinct color
    GAME_PROCESS_NAME = "cs2.exe" # The name of the game executable

    def __init__(self):
        import random
        self.random = random

        # Initialize base values before they're used
        self.base_gap = 0
        self.base_segment_length = 0
        self.current_gap = 0
        self.current_length = 0
        self.target_spread_offset = 0
        
        # Initialize jitter variables
        self.jitter_x = 0
        self.jitter_y = 0
        self.jitter_offset = 0
        self.jitter_direction_x = 1
        self.jitter_direction_y = 1

        # Initialize recoil variables
        self.recoil_offset = 0
        self.target_recoil_offset = 0
        self.recoil_amount = 10  # Pixels to move up when shooting
        self.recoil_speed = 0.5  # Speed of recoil movement
        self.recoil_recovery_speed = 0.2  # Speed of returning to original position

        # ... rest of __init__ ...

        self.root = tk.Tk()
        self.root.withdraw() # Hide the main window initially

        # Get screen resolution
        self.screen_width = self.root.winfo_screenwidth()
        self.screen_height = self.root.winfo_screenheight()

        # Set up the window properties
        self.root.geometry(f"{self.screen_width}x{self.screen_height}+0+0") # Full screen
        self.root.overrideredirect(True) # Remove window decorations (title bar, borders)
        self.root.attributes('-topmost', True) # Always on top
        self.root.attributes('-transparentcolor', self.TRANSPARENT_COLOR) # Make this color transparent

        # Create a canvas to draw on
        self.canvas = tk.Canvas(self.root, bg=self.TRANSPARENT_COLOR, highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Bind escape key to quit and F1 to open customization menu
        # These bindings work because the Tkinter window is the one receiving them
        # Remove Escape key binding to disable global close via Escape
        # self.root.bind('<Escape>', lambda e: self.quit_overlay())
        self.root.bind('<F1>', self._toggle_customization_menu)

        # Extend pynput keyboard listener to handle global F1 key only (remove Escape)
        def on_global_press(key):
            try:
                # Remove Escape key handling to disable global close via Escape
                if key == keyboard.Key.f1:
                    self.root.after(0, self._toggle_customization_menu)
            except Exception as e:
                print(f"Error in global key handler: {e}")

        self.global_keyboard_listener = keyboard.Listener(on_press=on_global_press)
        self.global_keyboard_listener_thread = threading.Thread(target=self.global_keyboard_listener.start)
        self.global_keyboard_listener_thread.daemon = True
        self.global_keyboard_listener_thread.start()

        # Enhanced input tracking
        self.input_state = {
            'keys': set(),          # Currently pressed keys
            'mouse': set(),         # Currently pressed mouse buttons
            'modifiers': set(),     # Currently pressed modifier keys
            'last_key': None,       # Last key pressed
            'last_mouse': None,     # Last mouse button pressed
            'mouse_position': (0, 0) # Current mouse position
        }

        # Enhanced key bindings configuration
        self.key_bindings = {
            'toggle_menu': keyboard.Key.f1,
            'quit': keyboard.Key.esc,
            'movement': {
                'forward': 'w',
                'backward': 's',
                'left': 'a',
                'right': 'd'
            },
            'actions': {
                'crouch': keyboard.Key.ctrl,
                'jump': keyboard.Key.space,
                'shoot': {
                    'primary': mouse.Button.left,
                    'secondary': mouse.Button.right
                }
            }
        }

        # Create reverse mapping for movement keys
        self.movement_key_map = {
            'w': 'forward',
            's': 'backward',
            'a': 'left',
            'd': 'right'
        }

        # Enhanced input listeners
        self._setup_input_listeners()

        # Track if the menu is open to prevent multiple instances
        self.menu_open = False
        self.customization_menu = None

        # Dynamic Spread state variables
        self.current_spread_offset = 0
        self.wasd_keys_pressed = set() # To track currently pressed WASD keys
        self.opposite_keys = {'w': 's', 's': 'w', 'a': 'd', 'd': 'a'}
        self.is_counter_strafing = False
        self.last_movement_key = None # To help with counter-strafe logic
        self.mouse_buttons_pressed = set() # New: To track currently pressed mouse buttons

        # Add lerping variables
        self.current_gap = self.base_gap
        self.current_length = self.base_segment_length
        self.lerp_speed = 0.2  # Adjust this value for faster/smoother transitions

        # Jitter parameters
        self.jitter_enabled = True
        self.jitter_amount = 2  # pixels max jitter offset
        self.jitter_speed = 0.1  # pixels per frame increase rate
        self.jitter_offset = 0.0  # current jitter offset magnitude

        # New crouch spread parameters
        # Removed crouch spread parameters as per user request
        # self.crouch_spread_enabled = False
        # self.crouch_spread_amount = 5
        # self.crouch_spread_speed = 2

        # New jitter mode parameter: "random", "up", "sideways"
        self.jitter_mode = "random"

        # Game status tracking
        self.game_running = False
        self.game_check_interval = 1000 # Check every 1 second

        # pynput keyboard listener setup
        self.keyboard_listener = keyboard.Listener(
            on_press=self._on_key_press,
            on_release=self._on_key_release
        )
        self.keyboard_listener_thread = threading.Thread(target=self.keyboard_listener.start)
        self.keyboard_listener_thread.daemon = True  # Allow the main program to exit even if this thread is running
        self.keyboard_listener_thread.start()
        print("pynput keyboard listener started.")

        # Track ctrl key state for crouch spread
        self.ctrl_pressed = False

        # New pynput mouse listener setup
        self.mouse_listener = mouse.Listener(
            on_move=self._on_mouse_move,
            on_click=self._on_mouse_click,
            on_scroll=self._on_mouse_scroll
        )
        self.mouse_listener_thread = threading.Thread(target=self.mouse_listener.start)
        self.mouse_listener_thread.daemon = True  # Allow the main program to exit
        self.mouse_listener_thread.start()
        print("pynput mouse listener started.")


        # Clickthrough enabled flag
        self.clickthrough_enabled = True

        # Apply platform-specific settings for click-through
        if sys.platform == "win32":
            self._setup_windows_overlay()
        # elif sys.platform == "linux":
        #     self._setup_linux_overlay() # Placeholder for future Linux support

        # Load config
        self.config_path = "config.json"
        self.load_config() # This will now also call rebind_keys()

        print("Open CS2 and press F1 to open the customization menu.")

        # Start checking game status
        self._check_game_status()

    def _lerp(self, current, target, speed):
        """Linear interpolation between current and target values."""
        return current + (target - current) * speed

    def _setup_windows_overlay(self):
        """Applies Windows-specific settings for click-through."""
        hwnd = user32.GetParent(self.root.winfo_id())
        ex_style = user32.GetWindowLongA(hwnd, GWL_EXSTYLE)
        
        if self.clickthrough_enabled:
            new_style = ex_style | WS_EX_LAYERED | WS_EX_TRANSPARENT
        else:
            new_style = (ex_style | WS_EX_LAYERED) & ~WS_EX_TRANSPARENT

        user32.SetWindowLongA(hwnd, GWL_EXSTYLE, new_style)
        user32.SetWindowPos(hwnd, HWND_TOPMOST, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE)

    def _setup_input_listeners(self):
        """Set up enhanced input listeners for keyboard and mouse."""
        # Keyboard listener
        self.keyboard_listener = keyboard.Listener(
            on_press=self._on_key_press,
            on_release=self._on_key_release
        )
        
        # Mouse listener
        self.mouse_listener = mouse.Listener(
            on_move=self._on_mouse_move,
            on_click=self._on_mouse_click,
            on_scroll=self._on_mouse_scroll
        )
        
        # Start listeners in separate threads
        self.keyboard_listener_thread = threading.Thread(
            target=self.keyboard_listener.start,
            daemon=True
        )
        self.mouse_listener_thread = threading.Thread(
            target=self.mouse_listener.start,
            daemon=True
        )
        
        self.keyboard_listener_thread.start()
        self.mouse_listener_thread.start()

    def _on_key_press(self, key):
        """Enhanced key press handler."""
        try:
            key_char = key.char.lower()
        except AttributeError:
            key_char = str(key).replace('Key.', '').lower()

        # Add key to input_state keys and modifiers immediately
        self.input_state['keys'].add(key_char)
        modifier_keys = {'ctrl', 'ctrl_l', 'ctrl_r', 'shift', 'shift_l', 'shift_r', 'alt', 'alt_l', 'alt_r'}
        if key_char in modifier_keys:
            self.input_state['modifiers'].add(key_char)

        # Handle specific key bindings immediately
        if key_char == str(self.key_bindings['toggle_menu']).replace('Key.', '').lower():
            self.root.after(0, self._toggle_customization_menu)
        elif key_char == str(self.key_bindings['quit']).replace('Key.', '').lower():
            self.root.after(0, self.quit_overlay)

        # Update movement state immediately
        self._update_movement_state()

    def _on_key_release(self, key):
        """Enhanced key release handler."""
        try:
            key_char = key.char.lower()
        except AttributeError:
            key_char = str(key).replace('Key.', '').lower()

        # Remove key from input_state keys and modifiers immediately
        self.input_state['keys'].discard(key_char)
        modifier_keys = {'ctrl', 'ctrl_l', 'ctrl_r', 'shift', 'shift_l', 'shift_r', 'alt', 'alt_l', 'alt_r'}
        if key_char in modifier_keys:
            self.input_state['modifiers'].discard(key_char)

        # Update movement state immediately
        self._update_movement_state()

    def _on_mouse_move(self, x, y):
        """Enhanced mouse movement handler."""
        self.input_state['mouse_position'] = (x, y)
        # You could add mouse movement-based features here

    def _on_mouse_click(self, x, y, button, pressed):
        """Enhanced mouse click handler."""
        button_name = str(button).replace('Button.', '') # e.g., 'Button.left' -> 'left'
        
        # Schedule the update on the Tkinter main thread
        self.root.after_idle(lambda: self._process_mouse_event(button_name, pressed))

    def _on_mouse_scroll(self, x, y, dx, dy):
        """Enhanced mouse scroll handler."""
        # You could add scroll-based features here
        pass

    def _is_process_running(self, process_name):
        """Checks if a process with the given name is currently running."""
        for proc in psutil.process_iter(['name']):
            if proc.info['name'] == process_name:
                return True
        return False

    def _check_game_status(self):
        """Periodically checks if the game process is running and updates overlay visibility."""
        # Remove game process check to always show overlay
        if not self.game_running:
            print("Showing overlay without game process check.")
            self.game_running = True
            self.root.deiconify() # Show the window
            self.draw_crosshair() # Initial draw

        # Schedule the next check
        self.root.after(self.game_check_interval, self._check_game_status)

    def load_config(self):
        default_config = {
            "crosshair_color": [255, 255, 255, 255], # Default to opaque white
            "outline_color": [0, 0, 0, 255], # Default to opaque black outline
            "line_thickness": 2,
            "outline_thickness": 1,
            "gap": 5,
            "length": 40, # Defines the total length of each crosshair arm from center
            "show_outline": True,
            # Movement Spread settings
            "movement_spread_enabled": False,
            "movement_spread_amount": 10,
            "movement_spread_speed": 2,
            # Counter-strafe settings
            "counter_strafe_enabled": True,
            "counter_strafe_reduction_speed": 5,
            "counter_strafe_min_spread": 0,
            # New: Click Spread settings
            "click_spread_enabled": False,
            "click_spread_amount": 5,
            "click_spread_speed": 3,
            "click_spread_button": "left",
            # New crouch spread settings
            "crouch_spread_enabled": False,
            "crouch_spread_amount": 5,
            "crouch_spread_speed": 2,
            # Jitter settings
            "jitter_enabled": True,
            "jitter_amount": 5,
            "jitter_speed": 1,
            "jitter_offset": 0,
            "jitter_mode": "random",
            # Dynamic length parameter
            "dynamic_length_enabled": True,
            # Lerp speed parameter
            "lerp_speed": 0.2
        }

        if not os.path.exists(self.config_path):
            with open(self.config_path, "w") as f:
                json.dump(default_config, f, indent=4)
        else:
            with open(self.config_path, "r+") as f:
                config = json.load(f)
                updated = False
                for key, value in default_config.items():
                    if key not in config:
                        config[key] = value
                        updated = True
                if updated:
                    f.seek(0)
                    json.dump(config, f, indent=4)
                    f.truncate()

        with open(self.config_path, "r") as f:
            config = json.load(f)
        
        # Set base_gap equal to the gap from config
        self.gap = config["gap"]
        self.base_gap = self.gap  # base_gap should equal gap

        # Tkinter uses hex color codes, and doesn't directly support alpha in line colors.
        # We'll convert RGB to hex and ignore alpha for line drawing, as the window transparency
        # is handled by -transparentcolor.
        self.crosshair_color = self._rgb_to_hex(config["crosshair_color"][:3])
        self.outline_color = self._rgb_to_hex(config["outline_color"][:3])
        self.line_thickness = config["line_thickness"]
        self.outline_thickness = config["outline_thickness"]
        # self.gap = config["gap"]
        self.base_segment_length = config["length"]
        self.show_outline = config["show_outline"]
        # Movement Spread parameters
        self.movement_spread_enabled = config["movement_spread_enabled"]
        self.movement_spread_amount = config["movement_spread_amount"]
        self.movement_spread_speed = config["movement_spread_speed"]
        # Counter-strafe parameters
        self.counter_strafe_enabled = config["counter_strafe_enabled"]
        self.counter_strafe_reduction_speed = config["counter_strafe_reduction_speed"]
        self.counter_strafe_min_spread = config["counter_strafe_min_spread"]
        # Click Spread parameters
        self.click_spread_enabled = config["click_spread_enabled"]
        self.click_spread_amount = config["click_spread_amount"]
        self.click_spread_speed = config["click_spread_speed"]
        self.click_spread_button = config["click_spread_button"]
        # Crouch Spread parameters
        self.crouch_spread_enabled = config.get("crouch_spread_enabled", False)
        self.crouch_spread_amount = config.get("crouch_spread_amount", 5)
        self.crouch_spread_speed = config.get("crouch_spread_speed", 2)
        # Jitter parameters
        self.jitter_enabled = config["jitter_enabled"]
        self.jitter_amount = config["jitter_amount"]
        self.jitter_speed = config["jitter_speed"]
        self.jitter_offset = 0  # Initialize current jitter offset
        self.jitter_mode = config.get("jitter_mode", "random")
        self.jitter_direction_x = 1
        self.jitter_direction_y = 1

        # Lerp Param
        self.lerp_speed = config.get("lerp_speed", 0.1)
        
        # Dynamic length parameter
        self.dynamic_length_enabled = config.get("dynamic_length_enabled", True)
        
        # Initialize jitter position variables if not already set
        if not hasattr(self, 'jitter_x'):
            self.jitter_x = 0
        if not hasattr(self, 'jitter_y'):
            self.jitter_y = 0

    def _rgb_to_hex(self, rgb):
        """Converts an RGB tuple to a Tkinter-compatible hex color string."""
        return f'#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}'

    def draw_crosshair(self):
        """Draw the crosshair with current settings."""
        if not self.game_running:
            self.canvas.delete("all")
            return

        self.canvas.delete("all")
        center_x = self.screen_width // 2
        center_y = self.screen_height // 2

        # Apply recoil offset
        center_y += self.recoil_offset

        # Apply jitter offset
        center_x += int(self.jitter_x)
        center_y += int(self.jitter_y)

        # Use lerped values for gap and length
        current_gap = self.current_gap
        current_length = self.current_length

        # Calculate segment endpoints
        outer_arm_end = current_gap + current_length
        segments = [
            ((center_x - outer_arm_end, center_y), (center_x - current_gap, center_y)),  # Left
            ((center_x + current_gap, center_y), (center_x + outer_arm_end, center_y)),   # Right
            ((center_x, center_y - outer_arm_end), (center_x, center_y - current_gap)), # Top
            ((center_x, center_y + current_gap), (center_x, center_y + outer_arm_end))   # Bottom
        ]

        # Draw outline if enabled
        if self.show_outline:
            for start, end in segments:
                self.canvas.create_line(*start, *end, 
                                      fill=self.outline_color, 
                                      width=self.outline_thickness)
        
        # Draw main crosshair
        for start, end in segments:
            self.canvas.create_line(*start, *end, 
                                  fill=self.crosshair_color, 
                                  width=self.line_thickness)

    def update_overlay(self):
        """Redraws the crosshair and schedules the next update."""
        # Determine the appropriate speed based on the current state
        if self.is_counter_strafing and self.counter_strafe_enabled:
            current_speed = self.counter_strafe_reduction_speed
        elif self.click_spread_enabled and (
            (self.click_spread_button == "both" and 
             ("left" in self.input_state['mouse'] or 
              "right" in self.input_state['mouse'])) or
            (self.click_spread_button == "left" and 
             "left" in self.input_state['mouse']) or
            (self.click_spread_button == "right" and 
             "right" in self.input_state['mouse'])
        ):
            current_speed = self.click_spread_speed
        elif self.crouch_spread_enabled and ('ctrl' in self.input_state['keys'] or 
                                            'ctrl_l' in self.input_state['keys'] or
                                            'ctrl_r' in self.input_state['keys']):
            current_speed = self.crouch_spread_speed
        else:
            current_speed = self.movement_spread_speed

        # Calculate the lerp factor based on the current speed, clamp between 0 and 1
        lerp_factor = min(current_speed * self.lerp_speed, 1.0)

        # Update recoil if shooting
        if self.click_spread_enabled and (
            (self.click_spread_button == "both" and 
             ("left" in self.input_state['mouse'] or 
              "right" in self.input_state['mouse'])) or
            (self.click_spread_button == "left" and 
             "left" in self.input_state['mouse']) or
            (self.click_spread_button == "right" and 
             "right" in self.input_state['mouse'])
        ):
            self.target_recoil_offset = -self.recoil_amount
        else:
            self.target_recoil_offset = 0

        # Apply recoil lerping
        if self.target_recoil_offset < self.recoil_offset:
            # Moving up (recoil)
            self.recoil_offset = self._lerp(
                self.recoil_offset,
                self.target_recoil_offset,
                self.recoil_speed
            )
        else:
            # Moving down (recovery)
            self.recoil_offset = self._lerp(
                self.recoil_offset,
                self.target_recoil_offset,
                self.recoil_recovery_speed
            )

        # Update current_spread_offset with lerping
        self.current_spread_offset = self._lerp(
            self.current_spread_offset,
            self.target_spread_offset,
            lerp_factor
        )

        # Calculate target gap (base gap + current spread offset)
        target_gap = self.base_gap + self.current_spread_offset
        self.current_gap = self._lerp(
            self.current_gap,
            target_gap,
            lerp_factor
        )

        # Update length based on dynamic_length_enabled setting
        if self.dynamic_length_enabled:
            self.current_length = self._lerp(
                self.current_length,
                self.base_segment_length + self.current_spread_offset,
                lerp_factor
            )
        else:
            self.current_length = self.base_segment_length

        # Jitter animation update
        if self.jitter_enabled and len(self.input_state['mouse']) > 0:
            import math
            # Increase jitter offset by jitter_speed, wrap around 2*pi
            self.jitter_offset += self.jitter_speed
            if self.jitter_offset > 2 * math.pi:
                self.jitter_offset -= 2 * math.pi

            # Calculate target jitter x and y offsets based on jitter_mode
            if self.jitter_mode == "random":
                target_jitter_x = self.random.uniform(-self.jitter_amount, self.jitter_amount)
                target_jitter_y = self.random.uniform(-self.jitter_amount, self.jitter_amount)
            elif self.jitter_mode == "up":
                target_jitter_x = 0
                target_jitter_y = self.jitter_amount * math.sin(self.jitter_offset)
            elif self.jitter_mode == "sideways":
                target_jitter_x = self.jitter_amount * math.sin(self.jitter_offset)
                target_jitter_y = 0
            else:
                target_jitter_x = 0
                target_jitter_y = 0

            # Lerp jitter_x and jitter_y towards target values for smooth jitter
            self.jitter_x = self._lerp(self.jitter_x, target_jitter_x, self.lerp_speed)
            self.jitter_y = self._lerp(self.jitter_y, target_jitter_y, self.lerp_speed)
        else:
            self.jitter_x = 0
            self.jitter_y = 0

        self.draw_crosshair()
        self.root.after(16, self.update_overlay)  # Aim for ~60 FPS

    def _toggle_customization_menu(self, event=None):
        """Opens or brings to the front the customization menu."""
        if not self.menu_open:
            self.customization_menu = CustomizationMenu(self.root, self, self.config_path)
            self.menu_open = True
            # Ensure the menu is destroyed if the main window closes
            self.customization_menu.transient(self.root) # Make it a transient window of the root
            self.customization_menu.grab_set() # Make it modal (optional, but good for settings)
            self.root.wait_window(self.customization_menu) # Wait for menu to close
            self.menu_open = False # Reset flag after menu closes
        else:
            # If menu is already open, bring it to the front
            if self.customization_menu and self.customization_menu.winfo_exists():
                self.customization_menu.lift()
            else:
                # If menu was closed unexpectedly, reset flag and try opening again
                self.menu_open = False
                self._toggle_customization_menu()

    # This method is no longer strictly needed for WASD with pynput,
    # but can be kept as a placeholder for other Tkinter-bound keys.
    def rebind_keys(self):
        """Placeholder for re-binding keys if needed. WASD/Mouse handled by pynput."""
        print("Rebinding keys (WASD/Mouse handled by pynput).")
        # No Tkinter unbind/bind for WASD/Mouse here anymore.

    def _process_key_event(self, key_char, pressed):
        """Process key events in the Tkinter main thread."""
        modifier_keys = {'ctrl', 'ctrl_l', 'ctrl_r', 'shift', 'shift_l', 'shift_r', 'alt', 'alt_l', 'alt_r'}
        if pressed:
            self.input_state['keys'].add(key_char)
            self.input_state['last_key'] = key_char
            if key_char in modifier_keys:
                self.input_state['modifiers'].add(key_char)
        else:
            self.input_state['keys'].discard(key_char)
            if key_char in modifier_keys:
                self.input_state['modifiers'].discard(key_char)
        
        # Handle specific key bindings
        if key_char == str(self.key_bindings['toggle_menu']).replace('Key.', '').lower():
            self._toggle_customization_menu()
        elif key_char == str(self.key_bindings['quit']).replace('Key.', '').lower():
            self.quit_overlay()
        
        # Update movement state
        self._update_movement_state()

    def _process_mouse_event(self, button_name, pressed):
        """Process mouse events in the Tkinter main thread."""
        if pressed:
            self.input_state['mouse'].add(button_name)
            self.input_state['last_mouse'] = button_name
        else:
            self.input_state['mouse'].discard(button_name)
        
        # Update target spread
        self._update_target_spread()

    def _update_movement_state(self):
        """Update movement-related state based on current input."""
        # Reset counter-strafe state
        self.is_counter_strafing = False

        #print(f"Keys pressed for movement state: {self.input_state['keys']}")

        # Check for counter-strafe by directly checking opposite key pairs
        if self.counter_strafe_enabled:
            opposite_pairs = [('w', 's'), ('a', 'd')]
            for key1, key2 in opposite_pairs:
                if key1 in self.input_state['keys'] and key2 in self.input_state['keys']:
                    self.is_counter_strafing = True
                    print(f"Counter-strafing detected with keys: {key1} and {key2}")
                    break
        
        #print(f"Counter-strafing state: {self.is_counter_strafing}")

        # Update target spread
        self._update_target_spread()

    def _update_target_spread(self):
        """Enhanced target spread calculation."""
        # Start with base gap as the minimum spread
        current_spread = self.base_gap
        
        # Movement spread (adds to base gap)
        movement_keys_pressed = any(
            key_char in self.input_state['keys'] 
            for key_char in self.movement_key_map
        )
        # Remove debug print for movement spread
        # print(f"Movement spread enabled: {self.movement_spread_enabled}, Movement keys pressed: {movement_keys_pressed}")
        if self.movement_spread_enabled and movement_keys_pressed:
            if self.is_counter_strafing:
                # Apply counter-strafe reduction
                current_spread += max(
                    self.movement_spread_amount - self.counter_strafe_reduction_speed,
                    self.counter_strafe_min_spread
                )
            else:
                current_spread += self.movement_spread_amount
        
        # Click spread (adds to current spread)
        if self.click_spread_enabled:
            trigger_button = self.click_spread_button
            if (trigger_button == "both" and 
                ("left" in self.input_state['mouse'] or 
                 "right" in self.input_state['mouse'])):
                current_spread = max(current_spread, self.base_gap + self.click_spread_amount)
            elif (trigger_button == "left" and 
                  "left" in self.input_state['mouse']):
                current_spread = max(current_spread, self.base_gap + self.click_spread_amount)
            elif (trigger_button == "right" and 
                  "right" in self.input_state['mouse']):
                current_spread = max(current_spread, self.base_gap + self.click_spread_amount)
        
        # Crouch spread (reduces from total spread) - apply after all other spreads
        if self.crouch_spread_enabled and ('ctrl' in self.input_state['keys'] or 
                                          'ctrl_l' in self.input_state['keys'] or
                                          'ctrl_r' in self.input_state['keys']):
            # Remove debug print for crouch spread
            # print(f"Crouch spread active. Keys: {self.input_state['keys']}")
            current_spread = max(current_spread - self.crouch_spread_amount, self.base_gap)
        else:
            # print(f"Crouch spread inactive. Keys: {self.input_state['keys']}")
            pass
        
        # Calculate final spread offset (total spread minus base gap)
        self.target_spread_offset = current_spread - self.base_gap

    def _apply_clickthrough_setting(self):
        """Apply the clickthrough window style based on current setting."""
        if sys.platform == "win32":
            self._setup_windows_overlay()

    def _get_current_input_state(self):
        """Get a snapshot of the current input state."""
        return {
            'keys': set(self.input_state['keys']),
            'mouse': set(self.input_state['mouse']),
            'modifiers': set(self.input_state['modifiers']),
            'last_key': self.input_state['last_key'],
            'last_mouse': self.input_state['last_mouse'],
            'mouse_position': self.input_state['mouse_position']
        }

    def run(self):
        self.update_overlay() # Start the drawing loop
        self.root.mainloop()

    def quit_overlay(self):
        if self.customization_menu and self.customization_menu.winfo_exists():
            self.customization_menu.destroy() # Close the menu if open
        self.keyboard_listener.stop() # Stop the pynput keyboard listener thread
        self.mouse_listener.stop() # New: Stop the pynput mouse listener thread
        if hasattr(self, 'global_keyboard_listener'):
            self.global_keyboard_listener.stop() # Stop the global keyboard listener thread
        self.root.destroy()
        sys.exit()

if __name__ == "__main__":
    overlay = CrosshairOverlay()
    overlay.run()
