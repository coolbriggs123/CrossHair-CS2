import tkinter as tk
import tkinter.ttk as ttk
from tkinter import colorchooser, simpledialog
import json
import os
import sys

class CustomizationMenu(tk.Toplevel):
    def __init__(self, master, overlay_instance, config_path="config.json"):
        super().__init__(master)
        self.overlay_instance = overlay_instance
        self.config_path = config_path
        self.title("Crosshair Customization")
        self.resizable(True, True)
        self.attributes('-topmost', True)
        
        # Apply dark theme and configure styles
        self.style = ttk.Style(self)
        self.style.theme_use('clam')  # Use a more customizable theme
        self.configure(bg='#1e1e1e')
        
        # Configure base styles for all widgets
        self.style.configure('.', background='#1e1e1e', foreground='white')
        self.style.configure('TFrame', background='#1e1e1e')
        self.style.configure('TLabel', background='#1e1e1e', foreground='white')
        
        # Configure buttons with dark theme
        self.style.configure('TButton', 
                           background='#2e2e2e',
                           foreground='white',
                           padding=6,
                           relief='flat',
                           borderwidth=1)
        self.style.map('TButton',
                     background=[('active', '#3e3e3e'), ('pressed', '#000000')],
                     foreground=[('active', 'white'), ('pressed', 'white')])
        
        # Configure checkbuttons
        self.style.configure('TCheckbutton', 
                           background='#1e1e1e',
                           foreground='white',
                           padding=5)
        
        # Configure spinboxes
        self.style.configure('TSpinbox', 
                           fieldbackground='#2e2e2e',
                           background='#2e2e2e',
                           foreground='white')
        
        # Configure comboboxes
        self.style.configure('TCombobox', 
                           fieldbackground='#2e2e2e',
                           background='#1e1e1e',
                           foreground='white',
                           arrowcolor='white')
        
        # Configure notebook tabs
        self.style.configure('TNotebook', background='#1e1e1e')
        self.style.configure('TNotebook.Tab', 
                           background='#2e2e2e',
                           foreground='white',
                           padding=[10, 5],
                           font=('Segoe UI', 10, 'bold'))
        self.style.map('TNotebook.Tab', 
                     background=[('selected', '#1e1e1e')],
                     foreground=[('selected', 'white')])
        
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
            for preset_name, preset in default_config["presets"].items():
                if preset_name not in self.config["presets"]:
                    self.config["presets"][preset_name] = preset

    def _get_default_config(self):
        """Returns the default configuration dictionary with preset support."""
        return {
            "current_preset": "Default",
            "presets": {
                "Default": {
                    "crosshair_color": [255, 255, 255, 255],
                    "outline_color": [0, 0, 0, 255],
                    "line_thickness": 2,
                    "outline_thickness": 1,
                    "gap": 5,
                    "length": 40,
                    "show_outline": True,
                    "movement_spread_enabled": False,
                    "movement_spread_amount": 10,
                    "movement_spread_speed": 2,
                    "counter_strafe_enabled": True,
                    "counter_strafe_reduction_speed": 5,
                    "counter_strafe_min_spread": 0,
                    "click_spread_enabled": False,
                    "click_spread_amount": 5,
                    "click_spread_speed": 3,
                    "click_spread_button": "left",
                    "crouch_spread_enabled": False,
                    "crouch_spread_amount": 5,
                    "crouch_spread_speed": 2,
                    "jitter_enabled": True,
                    "jitter_amount": 2,
                    "jitter_speed": 0.1,
                    "jitter_offset": 1,
                    "jitter_mode": "random"
                },
                "Classic": {
                    "crosshair_color": [255, 255, 255, 255],
                    "outline_color": [0, 0, 0, 255],
                    "line_thickness": 2,
                    "outline_thickness": 1,
                    "gap": 10,
                    "length": 30,
                    "show_outline": True,
                    "movement_spread_enabled": False,
                    "movement_spread_amount": 10,
                    "movement_spread_speed": 2,
                    "counter_strafe_enabled": True,
                    "counter_strafe_reduction_speed": 5,
                    "counter_strafe_min_spread": 0,
                    "click_spread_enabled": False,
                    "click_spread_amount": 5,
                    "click_spread_speed": 3,
                    "click_spread_button": "left",
                    "crouch_spread_enabled": False,
                    "crouch_spread_amount": 5,
                    "crouch_spread_speed": 2,
                    "jitter_enabled": True,
                    "jitter_amount": 2,
                    "jitter_speed": 0.1,
                    "jitter_offset": 1,
                    "jitter_mode": "random"
                }
            }
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
        self.movement_spread_enabled_var = tk.BooleanVar(value=self.config["movement_spread_enabled"])
        self.movement_spread_amount_var = tk.IntVar(value=self.config["movement_spread_amount"])
        self.movement_spread_speed_var = tk.IntVar(value=self.config["movement_spread_speed"])
        self.counter_strafe_enabled_var = tk.BooleanVar(value=self.config["counter_strafe_enabled"])
        self.counter_strafe_reduction_speed_var = tk.IntVar(value=self.config["counter_strafe_reduction_speed"])
        self.counter_strafe_min_spread_var = tk.IntVar(value=self.config["counter_strafe_min_spread"])
        self.click_spread_enabled_var = tk.BooleanVar(value=self.config["click_spread_enabled"])
        self.click_spread_amount_var = tk.IntVar(value=self.config["click_spread_amount"])
        self.click_spread_speed_var = tk.IntVar(value=self.config["click_spread_speed"])
        self.click_spread_button_var = tk.StringVar(value=self.config["click_spread_button"])
        self.crouch_spread_enabled_var = tk.BooleanVar(value=self.config.get("crouch_spread_enabled", False))
        self.crouch_spread_amount_var = tk.IntVar(value=self.config.get("crouch_spread_amount", 5))
        self.crouch_spread_speed_var = tk.IntVar(value=self.config.get("crouch_spread_speed", 2))
        self.jitter_enabled_var = tk.BooleanVar(value=self.config.get("jitter_enabled", True))
        self.jitter_amount_var = tk.IntVar(value=self.config.get("jitter_amount", 2))
        self.jitter_speed_var = tk.DoubleVar(value=self.config.get("jitter_speed", 0.1))
        self.jitter_offset_var = tk.IntVar(value=self.config.get("jitter_offset", 1))
        self.jitter_mode_var = tk.StringVar(value=self.config.get("jitter_mode", "random"))
        self.current_preset_var = tk.StringVar(value=self.config.get("current_preset", "Default"))

    def _create_widgets(self):
        """Creates and lays out the widgets in the menu with tabs."""
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create notebook for tabs with custom styling
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Create tabs
        crosshair_tab = ttk.Frame(self.notebook)
        movement_tab = ttk.Frame(self.notebook)
        counter_strafe_tab = ttk.Frame(self.notebook)
        click_spread_tab = ttk.Frame(self.notebook)
        crouch_spread_tab = ttk.Frame(self.notebook)
        jitter_tab = ttk.Frame(self.notebook)
        presets_tab = ttk.Frame(self.notebook)
        
        self.notebook.add(crosshair_tab, text="Crosshair")
        self.notebook.add(movement_tab, text="Movement Spread")
        self.notebook.add(counter_strafe_tab, text="Counter-Strafe")
        self.notebook.add(click_spread_tab, text="Click Spread")
        self.notebook.add(crouch_spread_tab, text="Crouch Spread")
        self.notebook.add(jitter_tab, text="Jitter")
        self.notebook.add(presets_tab, text="Presets")
        
        # Crosshair tab
        self._create_crosshair_tab(crosshair_tab)
        
        # Movement Spread tab
        self._create_movement_spread_tab(movement_tab)
        
        # Counter-strafe tab
        self._create_counter_strafe_tab(counter_strafe_tab)
        
        # Click Spread tab
        self._create_click_spread_tab(click_spread_tab)
        
        # Crouch Spread tab
        self._create_crouch_spread_tab(crouch_spread_tab)
        
        # Jitter tab
        self._create_jitter_tab(jitter_tab)
        
        # Presets tab
        self._create_presets_tab(presets_tab)
        
        # Bottom buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=10)
        ttk.Button(button_frame, text="Close Menu", command=self._on_close).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Close App", command=self._close_app).pack(side=tk.RIGHT, padx=5)

    def _create_crosshair_tab(self, parent):
        """Create crosshair settings tab."""
        # Color pickers and basic settings
        color_frame = ttk.Frame(parent)
        color_frame.pack(pady=10, fill=tk.BOTH)
        
        # Crosshair color
        ttk.Label(color_frame, text="Crosshair Color:").pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.crosshair_color_button = ttk.Button(color_frame, text="Pick Color", command=lambda: self._pick_color("crosshair_color", self.crosshair_color_var))
        self.crosshair_color_button.pack(side=tk.RIGHT)
        self.crosshair_color_preview = tk.Label(color_frame, width=2, relief="sunken", bd=1)
        self.crosshair_color_preview.pack(side=tk.RIGHT, padx=5)
        
        # Outline color
        outline_color_frame = ttk.Frame(parent)
        outline_color_frame.pack(pady=10, fill=tk.BOTH)
        ttk.Label(outline_color_frame, text="Outline Color:").pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.outline_color_button = ttk.Button(outline_color_frame, text="Pick Color", command=lambda: self._pick_color("outline_color", self.outline_color_var))
        self.outline_color_button.pack(side=tk.RIGHT)
        self.outline_color_preview = tk.Label(outline_color_frame, width=2, relief="sunken", bd=1)
        self.outline_color_preview.pack(side=tk.RIGHT, padx=5)
        
        # Basic settings
        def create_spinbox(parent, label_text, var, from_=0, to_=100, increment=1):
            frame = ttk.Frame(parent)
            frame.pack(fill=tk.BOTH, expand=True, pady=5)
            ttk.Label(frame, text=label_text).pack(side=tk.LEFT, fill=tk.X, expand=True)
            spinbox = ttk.Spinbox(frame, textvariable=var, from_=from_, to_=to_, increment=increment,
                                  command=self._update_and_save_config) # Instant update
            spinbox.pack(side=tk.RIGHT, fill=tk.X, expand=True)
            # Also trace changes from direct text input (e.g., typing a number)
            var.trace_add('write', lambda *args: self._update_and_save_config())
            return spinbox

        create_spinbox(parent, "Line Thickness:", self.line_thickness_var, from_=1, to_=10)
        create_spinbox(parent, "Outline Thickness:", self.outline_thickness_var, from_=0, to_=5)
        create_spinbox(parent, "Gap:", self.gap_var, from_=0, to_=100)
        create_spinbox(parent, "Segment Length:", self.spread_var, from_=1, to_=200)
        
        # Show outline checkbox
        ttk.Checkbutton(parent, text="Show Outline", variable=self.show_outline_var,
                        command=self._update_and_save_config).pack(anchor=tk.W, pady=5, fill=tk.X)

    def _create_movement_spread_tab(self, parent):
        """Create movement spread settings tab."""
        ttk.Checkbutton(parent, text="Enable Movement Spread", variable=self.movement_spread_enabled_var,
                        command=self._update_and_save_config).pack(anchor=tk.W, pady=2, fill=tk.X)
        
        def create_spinbox(parent, label_text, var, from_=0, to_=100, increment=1):
            frame = ttk.Frame(parent)
            frame.pack(fill=tk.BOTH, expand=True, pady=5)
            ttk.Label(frame, text=label_text).pack(side=tk.LEFT, fill=tk.X, expand=True)
            spinbox = ttk.Spinbox(frame, textvariable=var, from_=from_, to_=to_, increment=increment,
                                  command=self._update_and_save_config)
            spinbox.pack(side=tk.RIGHT, fill=tk.X, expand=True)
            var.trace_add('write', lambda *args: self._update_and_save_config())
            return spinbox

        create_spinbox(parent, "Spread Amount:", self.movement_spread_amount_var, from_=0, to_=50)
        create_spinbox(parent, "Spread Speed:", self.movement_spread_speed_var, from_=1, to_=10)

    def _create_counter_strafe_tab(self, parent):
        """Create counter-strafe settings tab."""
        ttk.Checkbutton(parent, text="Enable Counter-Strafe", variable=self.counter_strafe_enabled_var,
                        command=self._update_and_save_config).pack(anchor=tk.W, pady=2, fill=tk.X)
        
        def create_spinbox(parent, label_text, var, from_=0, to_=100, increment=1):
            frame = ttk.Frame(parent)
            frame.pack(fill=tk.BOTH, expand=True, pady=5)
            ttk.Label(frame, text=label_text).pack(side=tk.LEFT, fill=tk.X, expand=True)
            spinbox = ttk.Spinbox(frame, textvariable=var, from_=from_, to_=to_, increment=increment,
                                  command=self._update_and_save_config)
            spinbox.pack(side=tk.RIGHT, fill=tk.X, expand=True)
            var.trace_add('write', lambda *args: self._update_and_save_config())
            return spinbox

        create_spinbox(parent, "Reduction Speed:", self.counter_strafe_reduction_speed_var, from_=1, to_=20)
        create_spinbox(parent, "Min Spread:", self.counter_strafe_min_spread_var, from_=0, to_=10)

    def _create_click_spread_tab(self, parent):
        """Create click spread settings tab."""
        ttk.Checkbutton(parent, text="Enable Click Spread", variable=self.click_spread_enabled_var,
                        command=self._update_and_save_config).pack(anchor=tk.W, pady=2, fill=tk.X)
        
        def create_spinbox(parent, label_text, var, from_=0, to_=100, increment=1):
            frame = ttk.Frame(parent)
            frame.pack(fill=tk.BOTH, expand=True, pady=5)
            ttk.Label(frame, text=label_text).pack(side=tk.LEFT, fill=tk.X, expand=True)
            spinbox = ttk.Spinbox(frame, textvariable=var, from_=from_, to_=to_, increment=increment,
                                  command=self._update_and_save_config)
            spinbox.pack(side=tk.RIGHT, fill=tk.X, expand=True)
            var.trace_add('write', lambda *args: self._update_and_save_config())
            return spinbox

        create_spinbox(parent, "Spread Amount:", self.click_spread_amount_var, from_=0, to_=50)
        create_spinbox(parent, "Spread Speed:", self.click_spread_speed_var, from_=1, to_=10)
        
        # Button selection
        button_frame = ttk.Frame(parent)
        button_frame.pack(pady=5)
        ttk.Label(button_frame, text="Trigger Button:").pack(side=tk.LEFT)
        self.click_button_dropdown = ttk.Combobox(button_frame, textvariable=self.click_spread_button_var,
                                                  values=["left", "right", "both"], state="readonly")
        self.click_button_dropdown.pack(side=tk.RIGHT)
        self.click_button_dropdown.bind("<<ComboboxSelected>>", lambda e: self._update_and_save_config())

    def _create_crouch_spread_tab(self, parent):
        """Create crouch spread settings tab."""
        ttk.Checkbutton(parent, text="Enable Crouch Spread", variable=self.crouch_spread_enabled_var,
                        command=self._update_and_save_config).pack(anchor=tk.W, pady=2, fill=tk.X)
        
        def create_spinbox(parent, label_text, var, from_=0, to_=100, increment=1):
            frame = ttk.Frame(parent)
            frame.pack(fill=tk.BOTH, expand=True, pady=5)
            ttk.Label(frame, text=label_text).pack(side=tk.LEFT, fill=tk.X, expand=True)
            spinbox = ttk.Spinbox(frame, textvariable=var, from_=from_, to_=to_, increment=increment,
                                  command=self._update_and_save_config)
            spinbox.pack(side=tk.RIGHT, fill=tk.X, expand=True)
            var.trace_add('write', lambda *args: self._update_and_save_config())
            return spinbox

        create_spinbox(parent, "Spread Amount:", self.crouch_spread_amount_var, from_=0, to_=50)
        create_spinbox(parent, "Spread Speed:", self.crouch_spread_speed_var, from_=1, to_=10)

    def _create_jitter_tab(self, parent):
        """Create jitter settings tab."""
        ttk.Checkbutton(parent, text="Enable Jitter", variable=self.jitter_enabled_var,
                        command=self._update_and_save_config).pack(anchor=tk.W, pady=2, fill=tk.X)
        
        def create_jitter_spinbox(parent, label_text, var, from_, to_, increment=1):
            frame = ttk.Frame(parent)
            frame.pack(pady=5, fill=tk.BOTH)
            ttk.Label(frame, text=label_text).pack(side=tk.LEFT, fill=tk.X, expand=True)
            spinbox = ttk.Spinbox(frame, textvariable=var, from_=from_, to_=to_, increment=increment,
                                  command=self._update_and_save_config)
            spinbox.pack(side=tk.RIGHT, fill=tk.X, expand=True)
            var.trace_add('write', lambda *args: self._update_and_save_config())
            return spinbox

        create_jitter_spinbox(parent, "Jitter Amount (pixels):", self.jitter_amount_var, from_=0, to_=20)
        create_jitter_spinbox(parent, "Jitter Speed:", self.jitter_speed_var, from_=1, to_=10, increment=0.01)
        create_jitter_spinbox(parent, "Jitter Offset:", self.jitter_offset_var, from_=0, to_=10)
        
        # Jitter mode dropdown
        mode_frame = ttk.Frame(parent)
        mode_frame.pack(pady=5, fill=tk.BOTH)
        ttk.Label(mode_frame, text="Jitter Mode:").pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.jitter_mode_dropdown = ttk.Combobox(mode_frame, textvariable=self.jitter_mode_var,
                                                 values=["random", "up", "sideways"], state="readonly")
        self.jitter_mode_dropdown.pack(side=tk.RIGHT, fill=tk.X, expand=True)
        self.jitter_mode_dropdown.bind("<<ComboboxSelected>>", lambda e: self._update_and_save_config())

    def _create_presets_tab(self, parent):
        """Create presets management tab."""
        # Preset selection
        ttk.Label(parent, text="Select Preset:").pack(pady=5)
        self.preset_combobox = ttk.Combobox(parent, textvariable=self.current_preset_var, 
                                            values=list(self.config["presets"].keys()))
        self.preset_combobox.pack(pady=5)
        self.preset_combobox.bind("<<ComboboxSelected>>", lambda e: self._apply_preset())
        
        # Save preset button
        ttk.Button(parent, text="Save Current as Preset", command=self._save_preset).pack(pady=5)
        
        # Preset description
        ttk.Label(parent, text="Presets allow you to save and load different crosshair configurations").pack(pady=5)

    def _apply_preset(self):
        """Apply selected preset to current configuration."""
        preset_name = self.current_preset_var.get()
        if preset_name in self.config["presets"]:
            preset = self.config["presets"][preset_name]
            # Update all variables from the preset
            self.crosshair_color_var.set(self._rgb_to_hex(preset["crosshair_color"][:3]))
            self.outline_color_var.set(self._rgb_to_hex(preset["outline_color"][:3]))
            self.line_thickness_var.set(preset["line_thickness"])
            self.outline_thickness_var.set(preset["outline_thickness"])
            self.gap_var.set(preset["gap"])
            self.spread_var.set(preset["length"])
            self.show_outline_var.set(preset["show_outline"])
            self.movement_spread_enabled_var.set(preset["movement_spread_enabled"])
            self.movement_spread_amount_var.set(preset["movement_spread_amount"])
            self.movement_spread_speed_var.set(preset["movement_spread_speed"])
            self.counter_strafe_enabled_var.set(preset["counter_strafe_enabled"])
            self.counter_strafe_reduction_speed_var.set(preset["counter_strafe_reduction_speed"])
            self.counter_strafe_min_spread_var.set(preset["counter_strafe_min_spread"])
            self.click_spread_enabled_var.set(preset["click_spread_enabled"])
            self.click_spread_amount_var.set(preset["click_spread_amount"])
            self.click_spread_speed_var.set(preset["click_spread_speed"])
            self.click_spread_button_var.set(preset["click_spread_button"])
            self.crouch_spread_enabled_var.set(preset["crouch_spread_enabled"])
            self.crouch_spread_amount_var.set(preset["crouch_spread_amount"])
            self.crouch_spread_speed_var.set(preset["crouch_spread_speed"])
            self.jitter_enabled_var.set(preset["jitter_enabled"])
            self.jitter_amount_var.set(preset["jitter_amount"])
            self.jitter_speed_var.set(preset["jitter_speed"])
            self.jitter_offset_var.set(preset["jitter_offset"])
            self.jitter_mode_var.set(preset["jitter_mode"])
            
            self._update_color_previews()
            self._update_and_save_config()

    def _save_preset(self):
        """Save current configuration as a new preset."""
        name = simpledialog.askstring("Save Preset", "Enter a name for this preset:")
        if name and name.strip() != "":
            # Collect current settings from variables
            current_config = {
                "crosshair_color": list(self._hex_to_rgb(self.crosshair_color_var.get())) + [self.config["crosshair_color"][3]],
                "outline_color": list(self._hex_to_rgb(self.outline_color_var.get())) + [self.config["outline_color"][3]],
                "line_thickness": self.line_thickness_var.get(),
                "outline_thickness": self.outline_thickness_var.get(),
                "gap": self.gap_var.get(),
                "length": self.spread_var.get(),
                "show_outline": self.show_outline_var.get(),
                "movement_spread_enabled": self.movement_spread_enabled_var.get(),
                "movement_spread_amount": self.movement_spread_amount_var.get(),
                "movement_spread_speed": self.movement_spread_speed_var.get(),
                "counter_strafe_enabled": self.counter_strafe_enabled_var.get(),
                "counter_strafe_reduction_speed": self.counter_strafe_reduction_speed_var.get(),
                "counter_strafe_min_spread": self.counter_strafe_min_spread_var.get(),
                "click_spread_enabled": self.click_spread_enabled_var.get(),
                "click_spread_amount": self.click_spread_amount_var.get(),
                "click_spread_speed": self.click_spread_speed_var.get(),
                "click_spread_button": self.click_spread_button_var.get(),
                "crouch_spread_enabled": self.crouch_spread_enabled_var.get(),
                "crouch_spread_amount": self.crouch_spread_amount_var.get(),
                "crouch_spread_speed": self.crouch_spread_speed_var.get(),
                "jitter_enabled": self.jitter_enabled_var.get(),
                "jitter_amount": self.jitter_amount_var.get(),
                "jitter_speed": self.jitter_speed_var.get(),
                "jitter_offset": self.jitter_offset_var.get(),
                "jitter_mode": self.jitter_mode_var.get()
            }
            
            # Save to presets
            self.config["presets"][name] = current_config
            self.config["current_preset"] = name
            
            # Update UI
            self.current_preset_var.set(name)
            self.preset_combobox["values"] = list(self.config["presets"].keys())
            
            # Save to file
            with open(self.config_path, "w") as f:
                json.dump(self.config, f, indent=4)
                
            self.overlay_instance.load_config()
            self.overlay_instance.draw_crosshair()

    def _update_widgets_from_config(self):
        """Updates the widget values based on the current config."""
        self.crosshair_color_var.set(self._rgb_to_hex(self.config["crosshair_color"][:3]))
        self.outline_color_var.set(self._rgb_to_hex(self.config["outline_color"][:3]))
        self.line_thickness_var.set(self.config["line_thickness"])
        self.outline_thickness_var.set(self.config["outline_thickness"])
        self.gap_var.set(self.config["gap"])
        self.spread_var.set(self.config["length"])
        self.show_outline_var.set(self.config["show_outline"])
        self.movement_spread_enabled_var.set(self.config["movement_spread_enabled"])
        self.movement_spread_amount_var.set(self.config["movement_spread_amount"])
        self.movement_spread_speed_var.set(self.config["movement_spread_speed"])
        self.counter_strafe_enabled_var.set(self.config["counter_strafe_enabled"])
        self.counter_strafe_reduction_speed_var.set(self.config["counter_strafe_reduction_speed"])
        self.counter_strafe_min_spread_var.set(self.config["counter_strafe_min_spread"])
        self.click_spread_enabled_var.set(self.config["click_spread_enabled"])
        self.click_spread_amount_var.set(self.config["click_spread_amount"])
        self.click_spread_speed_var.set(self.config["click_spread_speed"])
        self.click_spread_button_var.set(self.config["click_spread_button"])
        self.crouch_spread_enabled_var.set(self.config.get("crouch_spread_enabled", False))
        self.crouch_spread_amount_var.set(self.config.get("crouch_spread_amount", 5))
        self.crouch_spread_speed_var.set(self.config.get("crouch_spread_speed", 2))
        self.jitter_enabled_var.set(self.config.get("jitter_enabled", True))
        self.jitter_amount_var.set(self.config.get("jitter_amount", 2))
        self.jitter_speed_var.set(self.config.get("jitter_speed", 0.1))
        self.jitter_offset_var.set(self.config.get("jitter_offset", 1))
        self.jitter_mode_var.set(self.config.get("jitter_mode", "random"))
        self.current_preset_var.set(self.config.get("current_preset", "Default"))
        
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
            # Crouch Spread values
            self.config["crouch_spread_enabled"] = self.crouch_spread_enabled_var.get()
            self.config["crouch_spread_amount"] = self.crouch_spread_amount_var.get()
            self.config["crouch_spread_speed"] = self.crouch_spread_speed_var.get()
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
        # Crouch Spread boolean
        self.config["crouch_spread_enabled"] = self.crouch_spread_enabled_var.get()
        # Jitter settings
        self.config["jitter_enabled"] = self.jitter_enabled_var.get()
        self.config["jitter_amount"] = self.jitter_amount_var.get()
        self.config["jitter_speed"] = self.jitter_speed_var.get()
        self.config["jitter_offset"] = self.jitter_offset_var.get()
        self.config["jitter_mode"] = self.jitter_mode_var.get()

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

    def _close_app(self):
        """Closes the entire application by calling overlay's quit_overlay."""
        self.overlay_instance.quit_overlay()

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
            print(f"  Segment Length: {self.spread}")
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

        def quit_overlay(self):
            print("DummyOverlay: Application closed.")
            root.quit()

    dummy_overlay = DummyOverlay()
    menu = CustomizationMenu(root, dummy_overlay)
    root.mainloop()
