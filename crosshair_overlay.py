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
        # Remove Escape key binding to quit_overlay to disable global close via Escape
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

        # Track if the menu is open to prevent multiple instances
        self.menu_open = False
        self.customization_menu = None

        # Dynamic Spread state variables
        self.current_spread_offset = 0
        self.target_spread_offset = 0
        self.wasd_keys_pressed = set() # To track currently pressed WASD keys
        self.opposite_keys = {'w': 's', 's': 'w', 'a': 'd', 'd': 'a'}
        self.is_counter_strafing = False
        self.last_movement_key = None # To help with counter-strafe logic
        self.mouse_buttons_pressed = set() # New: To track currently pressed mouse buttons

        # Jitter parameters
        self.jitter_enabled = True
        self.jitter_amount = 2  # pixels max jitter offset
        self.jitter_speed = 0.1  # pixels per frame increase rate
        self.jitter_offset = 0.0  # current jitter offset magnitude

        # Game status tracking
        self.game_running = False
        self.game_check_interval = 1000 # Check every 1 second

        # pynput keyboard listener setup
        self.keyboard_listener = keyboard.Listener(
            on_press=self._pynput_on_press,
            on_release=self._pynput_on_release
        )
        self.keyboard_listener_thread = threading.Thread(target=self.keyboard_listener.start)
        self.keyboard_listener_thread.daemon = True # Allow the main program to exit even if this thread is running
        self.keyboard_listener_thread.start()
        print("pynput keyboard listener started.")

        # New: pynput mouse listener setup
        self.mouse_listener = mouse.Listener(
            on_click=self._pynput_on_click
        )
        self.mouse_listener_thread = threading.Thread(target=self.mouse_listener.start)
        self.mouse_listener_thread.daemon = True # Allow the main program to exit
        self.mouse_listener_thread.start()
        print("pynput mouse listener started.")


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

    def _setup_windows_overlay(self):
        """Applies Windows-specific settings for click-through."""
        # Get the window handle (HWND) of the Tkinter window
        hwnd = user32.GetParent(self.root.winfo_id()) # winfo_id() gets the HWND

        # Get current extended style
        ex_style = user32.GetWindowLongA(hwnd, GWL_EXSTYLE)

        # Set new extended style: layered and transparent
        # WS_EX_LAYERED enables per-pixel alpha blending (though we use transparentcolor here)
        # WS_EX_TRANSPARENT makes the window click-through
        user32.SetWindowLongA(hwnd, GWL_EXSTYLE, ex_style | WS_EX_LAYERED | WS_EX_TRANSPARENT)

        # Set window to be always on top (redundant with Tkinter's -topmost but good for robustness)
        user32.SetWindowPos(hwnd, HWND_TOPMOST, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE)

    def _is_process_running(self, process_name):
        """Checks if a process with the given name is currently running."""
        for proc in psutil.process_iter(['name']):
            if proc.info['name'] == process_name:
                return True
        return False

    def _check_game_status(self):
        """Periodically checks if the game process is running and updates overlay visibility."""
        is_running = self._is_process_running(self.GAME_PROCESS_NAME)

        if is_running and not self.game_running:
            print(f"{self.GAME_PROCESS_NAME} detected. Showing overlay.")
            self.game_running = True
            self.root.deiconify() # Show the window
            self.draw_crosshair() # Initial draw
        elif not is_running and self.game_running:
            print(f"{self.GAME_PROCESS_NAME} not detected. Hiding overlay.")
            self.game_running = False
            self.root.withdraw() # Hide the window
        
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
            "click_spread_button": "left"
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
        
        # Tkinter uses hex color codes, and doesn't directly support alpha in line colors.
        # We'll convert RGB to hex and ignore alpha for line drawing, as the window transparency
        # is handled by -transparentcolor.
        self.crosshair_color = self._rgb_to_hex(config["crosshair_color"][:3])
        self.outline_color = self._rgb_to_hex(config["outline_color"][:3])
        self.line_thickness = config["line_thickness"]
        self.outline_thickness = config["outline_thickness"]
        self.gap = config["gap"]
        # Renamed self.spread to self.segment_length to reflect its new meaning
        self.segment_length = config["length"] 
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

        # Store base values for dynamic spread calculation
        self.base_gap = self.gap
        # Renamed self.base_length to self.base_segment_length
        self.base_segment_length = self.segment_length

        # Rebind keys after loading config, in case the dynamic spread key changed
        # (No longer needed for WASD with pynput, but kept for future potential Tkinter bindings)
        # self.rebind_keys() # This method is now effectively a no-op for WASD

    def _rgb_to_hex(self, rgb):
        """Converts an RGB tuple to a Tkinter-compatible hex color string."""
        return f'#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}'

    def draw_crosshair(self):
        # Only draw if the game is running
        if not self.game_running:
            self.canvas.delete("all")
            return

        self.canvas.delete("all") # Clear previous drawings

        center_x = self.screen_width // 2
        center_y = self.screen_height // 2

        # Add jitter offset if jitter enabled and mouse button pressed
        jitter_x = 0
        jitter_y = 0
        if self.jitter_enabled and self.mouse_buttons_pressed:
            max_jitter = int(self.jitter_offset)
            jitter_x = self.random.randint(-max_jitter, max_jitter)
            jitter_y = self.random.randint(-max_jitter, max_jitter)

        center_x += jitter_x
        center_y += jitter_y
        
        # Apply current dynamic spread offset to both gap and segment length
        current_gap = self.base_gap + self.current_spread_offset
        current_segment_length = self.base_segment_length + self.current_spread_offset

        # Calculate the outer end of the crosshair arm from the center
        # This is the start of the segment (current_gap) plus the length of the segment (current_segment_length)
        outer_arm_end = current_gap + current_segment_length

        # Horizontal segments
        left_start = (center_x - outer_arm_end, center_y)
        left_end = (center_x - current_gap, center_y)
        right_start = (center_x + current_gap, center_y)
        right_end = (center_x + outer_arm_end, center_y)

        # Vertical segments
        top_start = (center_x, center_y - outer_arm_end)
        top_end = (center_x, center_y - current_gap)
        bottom_start = (center_x, center_y + current_gap)
        bottom_end = (center_x, center_y + outer_arm_end)

        segments = [
            (left_start, left_end),
            (right_start, right_end),
            (top_start, top_end),
            (bottom_start, bottom_end)
        ]
        
        # Draw outline if enabled
        if self.show_outline:
            for start, end in segments:
                self.canvas.create_line(start[0], start[1], end[0], end[1], 
                                        fill=self.outline_color, width=self.outline_thickness)
        
        # Draw main crosshair
        for start, end in segments:
            self.canvas.create_line(start[0], start[1], end[0], end[1], 
                                    fill=self.crosshair_color, width=self.line_thickness)

    def _toggle_customization_menu(self, event=None):
        """Opens or brings to front the customization menu."""
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

    def _pynput_on_press(self, key):
        """Callback for pynput global keyboard press events."""
        try:
            key_char = key.char.lower()
        except AttributeError:
            # Special keys (e.g., Shift, Control) don't have a .char attribute
            key_char = str(key).replace('Key.', '').lower() # e.g., 'Key.shift' -> 'shift'

        if key_char in ['w', 'a', 's', 'd']:
            # Schedule the update on the Tkinter main thread
            self.root.after_idle(lambda: self._handle_wasd_press(key_char))

    def _pynput_on_release(self, key):
        """Callback for pynput global keyboard release events."""
        try:
            key_char = key.char.lower()
        except AttributeError:
            key_char = str(key).replace('Key.', '').lower()

        if key_char in ['w', 'a', 's', 'd']:
            # Schedule the update on the Tkinter main thread
            self.root.after_idle(lambda: self._handle_wasd_release(key_char))

    def _pynput_on_click(self, x, y, button, pressed):
        """Callback for pynput global mouse click events."""
        button_name = str(button).replace('Button.', '') # e.g., 'Button.left' -> 'left'
        
        # Schedule the update on the Tkinter main thread
        self.root.after_idle(lambda: self._handle_mouse_click(button_name, pressed))

    def _handle_wasd_press(self, key_char):
        """Handles WASD key presses for movement spread and counter-strafe (called on Tkinter thread)."""
        if key_char not in ['w', 'a', 's', 'd']:
            return

        # Check for counter-strafe
        if self.counter_strafe_enabled and key_char in self.opposite_keys:
            opposite_key = self.opposite_keys[key_char]
            if opposite_key in self.wasd_keys_pressed:
                self.is_counter_strafing = True
            else:
                self.is_counter_strafing = False # Reset if previous was not a counter-strafe

        self.wasd_keys_pressed.add(key_char)
        self.last_movement_key = key_char # Keep track of the last pressed key

        self._update_target_spread()

    def _handle_wasd_release(self, key_char):
        """Handles WASD key releases for movement spread and counter-strafe (called on Tkinter thread)."""
        if key_char not in ['w', 'a', 's', 'd']:
            return

        if key_char in self.wasd_keys_pressed:
            self.wasd_keys_pressed.remove(key_char)
        
        # If the released key was the one causing a counter-strafe, or if no movement keys are left
        # reset counter-strafe state.
        if not self.wasd_keys_pressed:
            self.is_counter_strafing = False
            self.last_movement_key = None
        elif self.is_counter_strafing and self.last_movement_key == key_char:
            # If the key that initiated the counter-strafe is released,
            # and its opposite is still held, we are no longer counter-strafing.
            # This is a simplified logic, more complex scenarios might need more state.
            if self.opposite_keys.get(key_char) in self.wasd_keys_pressed:
                 self.is_counter_strafing = False

        self._update_target_spread()

    def _handle_mouse_click(self, button_name, pressed):
        """Handles mouse button presses/releases for click spread (called on Tkinter thread)."""
        if pressed:
            self.mouse_buttons_pressed.add(button_name)
        else:
            if button_name in self.mouse_buttons_pressed:
                self.mouse_buttons_pressed.remove(button_name)
        
        self._update_target_spread()

    def _update_target_spread(self):
        """Determines the target spread based on movement and click state."""
        movement_target_spread = 0
        if self.movement_spread_enabled:
            if self.is_counter_strafing and self.counter_strafe_enabled:
                movement_target_spread = self.counter_strafe_min_spread
            elif self.wasd_keys_pressed:
                movement_target_spread = self.movement_spread_amount
        
        click_target_spread = 0
        if self.click_spread_enabled:
            trigger_button = self.click_spread_button
            if trigger_button == "left" and "left" in self.mouse_buttons_pressed:
                click_target_spread = self.click_spread_amount
            elif trigger_button == "right" and "right" in self.mouse_buttons_pressed:
                click_target_spread = self.click_spread_amount
            elif trigger_button == "both" and ("left" in self.mouse_buttons_pressed or "right" in self.mouse_buttons_pressed):
                click_target_spread = self.click_spread_amount
        
        # The overall target spread is the maximum of movement spread and click spread
        self.target_spread_offset = max(movement_target_spread, click_target_spread)

    def update_overlay(self):
        """Redraws the crosshair and schedules the next update."""
        # Determine the speed for interpolation
        # If counter-strafing, use reduction speed. Otherwise, use the faster of movement/click speeds if active.
        current_speed = self.movement_spread_speed # Default to movement speed
        
        if self.is_counter_strafing and self.counter_strafe_enabled:
            current_speed = self.counter_strafe_reduction_speed
        elif self.target_spread_offset > self.current_spread_offset: # Expanding
            if self.click_spread_enabled and (self.click_spread_button == "both" and ("left" in self.mouse_buttons_pressed or "right" in self.mouse_buttons_pressed) or \
                                              self.click_spread_button == "left" and "left" in self.mouse_buttons_pressed or \
                                              self.click_spread_button == "right" and "right" in self.mouse_buttons_pressed):
                current_speed = self.click_spread_speed
            else:
                current_speed = self.movement_spread_speed
        elif self.target_spread_offset < self.current_spread_offset: # Contracting
            # When contracting, use the faster of the two speeds to return to base
            current_speed = self.click_spread_speed


        # Update current_spread_offset towards target_spread_offset
        if self.current_spread_offset < self.target_spread_offset:
            self.current_spread_offset = min(self.current_spread_offset + current_speed, self.target_spread_offset)
        elif self.current_spread_offset > self.target_spread_offset:
            self.current_spread_offset = max(self.current_spread_offset - current_speed, self.target_spread_offset)

        # Update jitter offset magnitude
        if self.jitter_enabled:
            if self.mouse_buttons_pressed:
                # Increase jitter offset up to max jitter amount
                self.jitter_offset = min(self.jitter_offset + self.jitter_speed, self.jitter_amount)
            else:
                # Decrease jitter offset down to zero
                self.jitter_offset = max(self.jitter_offset - self.jitter_speed, 0)

        self.draw_crosshair()
        self.root.after(16, self.update_overlay) # Aim for ~60 FPS (1000ms / 60 frames = ~16.6ms)

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
