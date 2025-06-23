import tkinter as tk
import tkinter.ttk as ttk
from tkinter import colorchooser
import json
import os
import sys

class CustomizationMenu(tk.Toplevel):
    def __init__(self, master, overlay_instance, config_path="config.json"):
        super().__init__(master)
        self.overlay_instance = overlay_instance
        self.config_path = config_path
        self.title("Crosshair Customization")
        self.geometry("300x900") # Increased size for new options
        self.resizable(False, False) # Prevent resizing
        self.attributes('-topmost', True) # Keep menu on top

        # Bind the close button (X) to our custom close method
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self._load_config()
        self._setup_variables()
        self._create_widgets()
        self._update_widgets_from_config()

    def _load_config(self):
        """Loads the current configuration from the JSON file."""
        if not os.path.exists(self.config_path):
            # If config doesn't exist, create a default one (should be handled by overlay)
            # For menu, we'll just use default values if file is missing
            self.config = self._get_default_config()
        else:
            with open(self.config_path, "r") as f:
                self.config = json.load(f)
            # Ensure all default keys are present for backward compatibility
            default_config = self._get_default_config()
            for key, value in default_config.items():
                if key not in self.config:
                    self.config[key] = value

    def _get_default_config(self):
        """Returns the default configuration dictionary."""
        return {
            "crosshair_color": [255, 255, 255, 255],
            "outline_color": [0, 0, 0, 255],
            "line_thickness": 2,
            "outline_thickness": 1,
            "gap": 5,
            "length": 40, # Defines the length of each crosshair segment
            "show_outline": True,
            # Movement Spread settings
            "movement_spread_enabled": False,
            "movement_spread_amount": 10, # How much gap/segment length increases when moving
            "movement_spread_speed": 2,   # How fast it changes per frame
            # Counter-strafe settings
            "counter_strafe_enabled": True, # Enable counter-strafe accuracy
            "counter_strafe_reduction_speed": 5, # How fast spread reduces on counter-strafe
            "counter_strafe_min_spread": 0, # Minimum spread during a counter-strafe
            # Click Spread settings
            "click_spread_enabled": False,
            "click_spread_amount": 5, # How much gap/segment length increases on click
            "click_spread_speed": 3, # How fast it changes per frame on click
            "click_spread_button": "left", # Which mouse button triggers it ("left", "right", "both")
            # Jitter settings
            "jitter_enabled": True,
            "jitter_amount": 2,
            "jitter_speed": 0.1
        }

    def _setup_variables(self):
        """Sets up Tkinter variables to hold configuration values."""
        self.crosshair_color_var = tk.StringVar(value=self._rgb_to_hex(self.config["crosshair_color"][:3]))
        self.outline_color_var = tk.StringVar(value=self._rgb_to_hex(self.config["outline_color"][:3]))
        self.line_thickness_var = tk.IntVar(value=self.config["line_thickness"])
        self.outline_thickness_var = tk.IntVar(value=self.config["outline_thickness"])
        self.gap_var = tk.IntVar(value=self.config["gap"])
        self.spread_var = tk.IntVar(value=self.config["length"])
        self.show_outline_var = tk.BooleanVar(value=self.config["show_outline"])
        # Movement Spread variables
        self.movement_spread_enabled_var = tk.BooleanVar(value=self.config["movement_spread_enabled"])
        self.movement_spread_amount_var = tk.IntVar(value=self.config["movement_spread_amount"])
        self.movement_spread_speed_var = tk.IntVar(value=self.config["movement_spread_speed"])
        # Counter-strafe variables
        self.counter_strafe_enabled_var = tk.BooleanVar(value=self.config["counter_strafe_enabled"])
        self.counter_strafe_reduction_speed_var = tk.IntVar(value=self.config["counter_strafe_reduction_speed"])
        self.counter_strafe_min_spread_var = tk.IntVar(value=self.config["counter_strafe_min_spread"])
        # Click Spread variables
        self.click_spread_enabled_var = tk.BooleanVar(value=self.config["click_spread_enabled"])
        self.click_spread_amount_var = tk.IntVar(value=self.config["click_spread_amount"])
        self.click_spread_speed_var = tk.IntVar(value=self.config["click_spread_speed"])
        self.click_spread_button_var = tk.StringVar(value=self.config["click_spread_button"])
        # Jitter variables
        self.jitter_enabled_var = tk.BooleanVar(value=self.config.get("jitter_enabled", True))
        self.jitter_amount_var = tk.IntVar(value=self.config.get("jitter_amount", 2))
        self.jitter_speed_var = tk.DoubleVar(value=self.config.get("jitter_speed", 0.1))


    def _create_widgets(self):
        """Creates and lays out the widgets in the menu."""
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Helper for creating labeled spinboxes
        def create_spinbox(parent, label_text, var, from_=0, to_=100, increment=1):
            frame = ttk.Frame(parent)
            frame.pack(fill=tk.X, pady=5)
            ttk.Label(frame, text=label_text).pack(side=tk.LEFT)
            spinbox = ttk.Spinbox(frame, textvariable=var, width=5, from_=from_, to_=to_, increment=increment,
                                  command=self._update_and_save_config) # Instant update
            spinbox.pack(side=tk.RIGHT)
            # Also trace changes from direct text input (e.g., typing a number)
            var.trace_add('write', lambda *args: self._update_and_save_config())
            return spinbox

        # Crosshair Color
        color_frame = ttk.Frame(main_frame)
        color_frame.pack(fill=tk.X, pady=5)
        ttk.Label(color_frame, text="Crosshair Color:").pack(side=tk.LEFT)
        self.crosshair_color_button = ttk.Button(color_frame, text="Pick Color", command=lambda: self._pick_color("crosshair_color", self.crosshair_color_var))
        self.crosshair_color_button.pack(side=tk.RIGHT)
        self.crosshair_color_preview = tk.Label(color_frame, width=2, relief="sunken", bd=1)
        self.crosshair_color_preview.pack(side=tk.RIGHT, padx=5)

        # Outline Color
        outline_color_frame = ttk.Frame(main_frame)
        outline_color_frame.pack(fill=tk.X, pady=5)
        ttk.Label(outline_color_frame, text="Outline Color:").pack(side=tk.LEFT)
        self.outline_color_button = ttk.Button(outline_color_frame, text="Pick Color", command=lambda: self._pick_color("outline_color", self.outline_color_var))
        self.outline_color_button.pack(side=tk.RIGHT)
        self.outline_color_preview = tk.Label(outline_color_frame, width=2, relief="sunken", bd=1)
        self.outline_color_preview.pack(side=tk.RIGHT, padx=5)

        # Spinboxes
        create_spinbox(main_frame, "Line Thickness:", self.line_thickness_var, from_=1, to_=10)
        create_spinbox(main_frame, "Outline Thickness:", self.outline_thickness_var, from_=0, to_=5)
        create_spinbox(main_frame, "Gap:", self.gap_var, from_=0, to_=100)
        create_spinbox(main_frame, "Segment Length:", self.spread_var, from_=1, to_=200) # Changed label here

        # Show Outline Checkbox
        ttk.Checkbutton(main_frame, text="Show Outline", variable=self.show_outline_var,
                        command=self._update_and_save_config).pack(anchor=tk.W, pady=5)

        # Movement Spread Section
        movement_spread_frame = ttk.LabelFrame(main_frame, text="Movement Spread (WASD)", padding="10")
        movement_spread_frame.pack(fill=tk.X, pady=10)

        ttk.Checkbutton(movement_spread_frame, text="Enable Movement Spread", variable=self.movement_spread_enabled_var,
                        command=self._update_and_save_config).pack(anchor=tk.W, pady=2)

        create_spinbox(movement_spread_frame, "Spread Amount:", self.movement_spread_amount_var, from_=0, to_=50)
        create_spinbox(movement_spread_frame, "Spread Speed:", self.movement_spread_speed_var, from_=1, to_=10)

        # Counter-Strafe Section
        counter_strafe_frame = ttk.LabelFrame(main_frame, text="Counter-Strafe Accuracy", padding="10")
        counter_strafe_frame.pack(fill=tk.X, pady=10)

        ttk.Checkbutton(counter_strafe_frame, text="Enable Counter-Strafe", variable=self.counter_strafe_enabled_var,
                        command=self._update_and_save_config).pack(anchor=tk.W, pady=2)

        create_spinbox(counter_strafe_frame, "Reduction Speed:", self.counter_strafe_reduction_speed_var, from_=1, to_=20)
        create_spinbox(counter_strafe_frame, "Min Spread:", self.counter_strafe_min_spread_var, from_=0, to_=10)

        # Click Spread Section
        click_spread_frame = ttk.LabelFrame(main_frame, text="Click Spread", padding="10")
        click_spread_frame.pack(fill=tk.X, pady=10)

        ttk.Checkbutton(click_spread_frame, text="Enable Click Spread", variable=self.click_spread_enabled_var,
                        command=self._update_and_save_config).pack(anchor=tk.W, pady=2)

        create_spinbox(click_spread_frame, "Spread Amount:", self.click_spread_amount_var, from_=0, to_=50)
        create_spinbox(click_spread_frame, "Spread Speed:", self.click_spread_speed_var, from_=1, to_=10)

        # Jitter Section
        jitter_frame = ttk.LabelFrame(main_frame, text="Jitter Settings", padding="10")
        jitter_frame.pack(fill=tk.X, pady=10)

        ttk.Checkbutton(jitter_frame, text="Enable Jitter", variable=self.jitter_enabled_var,
                        command=self._update_and_save_config).pack(anchor=tk.W, pady=2)

        def create_jitter_spinbox(parent, label_text, var, from_, to_, increment=1):
            frame = ttk.Frame(parent)
            frame.pack(fill=tk.X, pady=5)
            ttk.Label(frame, text=label_text).pack(side=tk.LEFT)
            spinbox = ttk.Spinbox(frame, textvariable=var, width=5, from_=from_, to_=to_, increment=increment,
                                  command=self._update_and_save_config)
            spinbox.pack(side=tk.RIGHT)
            var.trace_add('write', lambda *args: self._update_and_save_config())
            return spinbox

        create_jitter_spinbox(jitter_frame, "Jitter Amount (pixels):", self.jitter_amount_var, from_=0, to_=20)
        create_jitter_spinbox(jitter_frame, "Jitter Speed:", self.jitter_speed_var, from_=1, to_=10)


        # Close Button
        ttk.Button(main_frame, text="Close Menu", command=self._on_close).pack(pady=5)

        # Close App Button
        ttk.Button(main_frame, text="Close App", command=self._close_app).pack(pady=5)

    def _close_app(self):
        """Closes the entire application by calling overlay's quit_overlay."""
        self.overlay_instance.quit_overlay()


    def _update_widgets_from_config(self):
        """Updates the widget values based on the current config."""
        self.crosshair_color_var.set(self._rgb_to_hex(self.config["crosshair_color"][:3]))
        self.outline_color_var.set(self._rgb_to_hex(self.config["outline_color"][:3]))
        self.line_thickness_var.set(self.config["line_thickness"])
        self.outline_thickness_var.set(self.config["outline_thickness"])
        self.gap_var.set(self.config["gap"])
        self.spread_var.set(self.config["length"])
        self.show_outline_var.set(self.config["show_outline"])
        # Update Movement Spread widgets
        self.movement_spread_enabled_var.set(self.config["movement_spread_enabled"])
        self.movement_spread_amount_var.set(self.config["movement_spread_amount"])
        self.movement_spread_speed_var.set(self.config["movement_spread_speed"])
        # Update Counter-strafe widgets
        self.counter_strafe_enabled_var.set(self.config["counter_strafe_enabled"])
        self.counter_strafe_reduction_speed_var.set(self.config["counter_strafe_reduction_speed"])
        self.counter_strafe_min_spread_var.set(self.config["counter_strafe_min_spread"])
        # Update Click Spread widgets
        self.click_spread_enabled_var.set(self.config["click_spread_enabled"])
        self.click_spread_amount_var.set(self.config["click_spread_amount"])
        self.click_spread_speed_var.set(self.config["click_spread_speed"])
        self.click_spread_button_var.set(self.config["click_spread_button"])
        # Update Jitter widgets
        self.jitter_enabled_var.set(self.config.get("jitter_enabled", True))
        self.jitter_amount_var.set(self.config.get("jitter_amount", 2))
        self.jitter_speed_var.set(self.config.get("jitter_speed", 1))
        self._update_color_previews()

    def _update_color_previews(self):
        """Updates the color preview labels."""
        self.crosshair_color_preview.config(bg=self.crosshair_color_var.get())
        self.outline_color_preview.config(bg=self.outline_color_var.get())

    def _pick_color(self, config_key, var):
        """Opens a color picker dialog and updates the variable and config."""
        color_code = colorchooser.askcolor(title="Choose color")[1] # [1] gives hex code
        if color_code:
            var.set(color_code)
            rgb = self._hex_to_rgb(color_code)
            # Keep alpha from original config, or default to 255 if not present
            alpha = self.config[config_key][3] if len(self.config[config_key]) > 3 else 255
            self.config[config_key] = list(rgb) + [alpha]
            self._update_color_previews()
            self._update_and_save_config() # Trigger instant update after color change

    def _rgb_to_hex(self, rgb):
        """Converts an RGB tuple to a Tkinter-compatible hex color string."""
        return f'#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}'

    def _hex_to_rgb(self, hex_color):
        """Converts a hex color string to an RGB tuple."""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    def _update_and_save_config(self):
        """Updates config dictionary from Tkinter variables, saves to file, and tells overlay to update."""
        # Ensure integer values from spinboxes are correctly parsed
        try:
            self.config["line_thickness"] = self.line_thickness_var.get()
            self.config["outline_thickness"] = self.outline_thickness_var.get()
            self.config["gap"] = self.gap_var.get()
            self.config["length"] = self.spread_var.get() # This still maps to 'length' in config
            # Movement Spread values
            self.config["movement_spread_amount"] = self.movement_spread_amount_var.get()
            self.config["movement_spread_speed"] = self.movement_spread_speed_var.get()
            # Counter-strafe values
            self.config["counter_strafe_reduction_speed"] = self.counter_strafe_reduction_speed_var.get()
            self.config["counter_strafe_min_spread"] = self.counter_strafe_min_spread_var.get()
            # Click Spread values
            self.config["click_spread_amount"] = self.click_spread_amount_var.get()
            self.config["click_spread_speed"] = self.click_spread_speed_var.get()
        except tk.TclError:
            # This can happen if the spinbox content is not a valid integer (e.g., empty string)
            print("Invalid numeric input detected. Skipping update.")
            return

        # Update color values (already handled by _pick_color, but ensure consistency)
        current_ch_rgb = self._hex_to_rgb(self.crosshair_color_var.get())
        current_ol_rgb = self._hex_to_rgb(self.outline_color_var.get())

        # Preserve alpha if it exists in the original config, otherwise default to 255
        ch_alpha = self.config["crosshair_color"][3] if len(self.config["crosshair_color"]) > 3 else 255
        ol_alpha = self.config["outline_color"][3] if len(self.config["outline_color"]) > 3 else 255

        self.config["crosshair_color"] = list(current_ch_rgb) + [ch_alpha]
        self.config["outline_color"] = list(current_ol_rgb) + [ol_alpha]
        
        self.config["show_outline"] = self.show_outline_var.get()
        # Movement Spread boolean
        self.config["movement_spread_enabled"] = self.movement_spread_enabled_var.get()
        # Counter-strafe boolean
        self.config["counter_strafe_enabled"] = self.counter_strafe_enabled_var.get()
        # Click Spread boolean and button
        self.config["click_spread_enabled"] = self.click_spread_enabled_var.get()
        self.config["click_spread_button"] = self.click_spread_button_var.get()

        # Jitter settings
        self.config["jitter_enabled"] = self.jitter_enabled_var.get()
        self.config["jitter_amount"] = self.jitter_amount_var.get()
        self.config["jitter_speed"] = self.jitter_speed_var.get()

        # Save to file
        with open(self.config_path, "w") as f:
            json.dump(self.config, f, indent=4)

        # Tell the overlay instance to reload its config and redraw
        self.overlay_instance.load_config() # This will now call rebind_keys internally
        self.overlay_instance.draw_crosshair() # Force redraw immediately

    def _on_close(self):
        """Handles the menu closing event."""
        self.overlay_instance.menu_open = False # Inform the overlay that the menu is closed
        self.destroy() # Destroy the Toplevel window

# Example usage (for testing the menu independently)
if __name__ == "__main__":
    # Create a dummy root window and overlay instance for testing
    root = tk.Tk()
    root.withdraw() # Hide the dummy root

    class DummyOverlay:
        def __init__(self):
            self.menu_open = False
            self.crosshair_color = (255, 255, 255)
            self.outline_color = (0, 0, 0)
            self.line_thickness = 2
            self.outline_thickness = 1
            self.gap = 5
            self.spread = 40
            self.show_outline = True
            # Dummy values for new dynamic spread
            self.movement_spread_enabled = False
            self.movement_spread_amount = 10
            self.movement_spread_speed = 2
            self.counter_strafe_enabled = True
            self.counter_strafe_reduction_speed = 5
            self.counter_strafe_min_spread = 0
            # Dummy values for click spread
            self.click_spread_enabled = False
            self.click_spread_amount = 5
            self.click_spread_speed = 3
            self.click_spread_button = "left"
            self.base_gap = 5 # Needed for load_config to set
            self.base_length = 40 # Needed for load_config to set
            print("DummyOverlay initialized.")

        def load_config(self):
            print("DummyOverlay: Config reloaded.")
            # In a real scenario, you'd reload from config.json here
            # For dummy, we'll just print current values
            print(f"  Crosshair Color: {self.crosshair_color}")
            print(f"  Outline Color: {self.outline_color}")
            print(f"  Line Thickness: {self.line_thickness}")
            print(f"  Gap: {self.gap}")
            print(f"  Segment Length: {self.spread}") # Changed label here
            print(f"  Show Outline: {self.show_outline}")
            print(f"  Movement Spread Enabled: {self.movement_spread_enabled}")
            print(f"  Movement Spread Amount: {self.movement_spread_amount}")
            print(f"  Movement Spread Speed: {self.movement_spread_speed}")
            print(f"  Counter-Strafe Enabled: {self.counter_strafe_enabled}")
            print(f"  Counter-Strafe Reduction Speed: {self.counter_strafe_reduction_speed}")
            print(f"  Counter-Strafe Min Spread: {self.counter_strafe_min_spread}")
            print(f"  Click Spread Enabled: {self.click_spread_enabled}")
            print(f"  Click Spread Amount: {self.click_spread_amount}")
            print(f"  Click Spread Speed: {self.click_spread_speed}")
            print(f"  Click Spread Button: {self.click_spread_button}")
            self.rebind_keys() # Call rebind_keys on dummy too

        def draw_crosshair(self):
            print("DummyOverlay: Crosshair redrawn.")

        def rebind_keys(self):
            print(f"DummyOverlay: Rebinding WASD keys and mouse.")

    dummy_overlay = DummyOverlay()
    menu = CustomizationMenu(root, dummy_overlay)
    root.mainloop()
