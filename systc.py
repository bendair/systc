import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import math
from datetime import datetime, timedelta
from enum import Enum

class InterpolationType(Enum):
    LINEAR = "Linear"
    BEZIER = "Bezier"
    STEP = "Step"
    EASE_IN = "Ease In"
    EASE_OUT = "Ease Out"
    EASE_IN_OUT = "Ease In-Out"

class AnimationParameter:
    def __init__(self, name, min_value=0.0, max_value=100.0, default_value=0.0, param_type="float"):
        self.name = name
        self.min_value = min_value
        self.max_value = max_value
        self.default_value = default_value
        self.param_type = param_type
        self.keyframes = []
        self.visible = True
        self.color = "#4CAF50"
        
    def add_keyframe(self, frame, value, interpolation=InterpolationType.LINEAR):
        # Remove existing keyframe at same frame
        self.keyframes = [kf for kf in self.keyframes if kf.frame != frame]
        # Add new keyframe
        keyframe = Keyframe(frame, value, interpolation)
        self.keyframes.append(keyframe)
        self.keyframes.sort(key=lambda kf: kf.frame)
        
    def remove_keyframe(self, frame):
        self.keyframes = [kf for kf in self.keyframes if kf.frame != frame]
        
    def get_value_at_frame(self, frame):
        if not self.keyframes:
            return self.default_value
            
        # Find surrounding keyframes
        before_kf = None
        after_kf = None
        
        for kf in self.keyframes:
            if kf.frame <= frame:
                before_kf = kf
            if kf.frame >= frame and after_kf is None:
                after_kf = kf
                
        # If we're exactly on a keyframe
        if before_kf and before_kf.frame == frame:
            return before_kf.value
            
        # If only one side exists
        if before_kf is None:
            return after_kf.value if after_kf else self.default_value
        if after_kf is None:
            return before_kf.value
            
        # Interpolate between keyframes
        return self.interpolate(before_kf, after_kf, frame)
        
    def interpolate(self, kf1, kf2, frame):
        if kf1.frame == kf2.frame:
            return kf1.value
            
        t = (frame - kf1.frame) / (kf2.frame - kf1.frame)
        
        if kf1.interpolation == InterpolationType.STEP:
            return kf1.value
        elif kf1.interpolation == InterpolationType.LINEAR:
            return kf1.value + (kf2.value - kf1.value) * t
        elif kf1.interpolation == InterpolationType.EASE_IN:
            t = t * t
            return kf1.value + (kf2.value - kf1.value) * t
        elif kf1.interpolation == InterpolationType.EASE_OUT:
            t = 1 - (1 - t) * (1 - t)
            return kf1.value + (kf2.value - kf1.value) * t
        elif kf1.interpolation == InterpolationType.EASE_IN_OUT:
            if t < 0.5:
                t = 2 * t * t
            else:
                t = 1 - 2 * (1 - t) * (1 - t)
            return kf1.value + (kf2.value - kf1.value) * t
        elif kf1.interpolation == InterpolationType.BEZIER:
            # Simple cubic bezier approximation
            t = t * t * (3 - 2 * t)
            return kf1.value + (kf2.value - kf1.value) * t
        else:
            return kf1.value + (kf2.value - kf1.value) * t

class Keyframe:
    def __init__(self, frame, value, interpolation=InterpolationType.LINEAR):
        self.frame = frame
        self.value = value
        self.interpolation = interpolation
        self.selected = False

class TimelineApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Universal Timeline App with Animation Graph")
        self.root.geometry("1400x900")
        
        # Standard frame rates
        self.standard_frame_rates = {
            "23.976 fps (Cinema)": 23.976,
            "24 fps (Cinema)": 24.0,
            "25 fps (PAL)": 25.0,
            "29.97 fps (NTSC)": 29.97,
            "30 fps": 30.0,
            "50 fps (PAL Progressive)": 50.0,
            "59.94 fps (NTSC Progressive)": 59.94,
            "60 fps": 60.0,
            "120 fps (High Frame Rate)": 120.0
        }
        
        # Timeline data
        self.current_frame_rate = 30.0
        self.timeline_duration = 3600
        self.current_frame = 0
        self.markers = []
        self.clips = []
        self.zoom_level = 1.0
        self.scroll_position = 0
        
        # Animation system
        self.animation_parameters = {}
        self.selected_parameter = None
        self.animation_zoom_y = 1.0
        self.animation_pan_y = 0.0
        self.dragging_keyframe = None
        
        # Graph colors for parameters
        self.parameter_colors = [
            "#4CAF50", "#2196F3", "#FF9800", "#E91E63", "#9C27B0",
            "#00BCD4", "#8BC34A", "#FF5722", "#607D8B", "#795548"
        ]
        
        self.setup_ui()
        self.add_default_parameters()
        self.update_timeline_display()
        
    def add_default_parameters(self):
        """Add some common animation parameters as examples"""
        self.add_animation_parameter("Position X", -1000, 1000, 0)
        self.add_animation_parameter("Position Y", -1000, 1000, 0)
        self.add_animation_parameter("Scale", 0, 10, 1)
        self.add_animation_parameter("Rotation", -360, 360, 0)
        self.add_animation_parameter("Opacity", 0, 100, 100)
        
    def setup_ui(self):
        # Create main paned window
        main_paned = ttk.PanedWindow(self.root, orient=tk.VERTICAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Top frame for timeline
        timeline_frame = ttk.Frame(main_paned)
        main_paned.add(timeline_frame, weight=1)
        
        # Bottom frame for animation graph
        animation_frame = ttk.Frame(main_paned)
        main_paned.add(animation_frame, weight=2)
        
        # Setup timeline UI
        self.setup_timeline_ui(timeline_frame)
        
        # Setup animation UI
        self.setup_animation_ui(animation_frame)
        
    def setup_timeline_ui(self, parent):
        # Control panel
        control_frame = ttk.LabelFrame(parent, text="Timeline Controls", padding=10)
        control_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        # Frame rate controls
        fps_frame = ttk.Frame(control_frame)
        fps_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(fps_frame, text="Frame Rate:").pack(side=tk.LEFT, padx=(0, 5))
        
        self.fps_var = tk.StringVar(value="30 fps")
        self.fps_combo = ttk.Combobox(fps_frame, textvariable=self.fps_var, width=20)
        self.fps_combo['values'] = list(self.standard_frame_rates.keys()) + ["Custom..."]
        self.fps_combo.pack(side=tk.LEFT, padx=(0, 10))
        self.fps_combo.bind('<<ComboboxSelected>>', self.on_fps_change)
        
        self.custom_fps_var = tk.StringVar(value="30.0")
        self.custom_fps_entry = ttk.Entry(fps_frame, textvariable=self.custom_fps_var, width=10)
        self.custom_fps_entry.pack(side=tk.LEFT, padx=5)
        self.custom_fps_entry.bind('<Return>', self.on_custom_fps_change)
        
        ttk.Button(fps_frame, text="Apply Custom FPS", 
                  command=self.on_custom_fps_change).pack(side=tk.LEFT, padx=5)
        
        # Timeline duration and playback controls
        duration_frame = ttk.Frame(control_frame)
        duration_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(duration_frame, text="Duration (frames):").pack(side=tk.LEFT, padx=(0, 5))
        self.duration_var = tk.StringVar(value=str(self.timeline_duration))
        ttk.Entry(duration_frame, textvariable=self.duration_var, width=10).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(duration_frame, text="Update Duration", 
                  command=self.update_duration).pack(side=tk.LEFT, padx=5)
        
        # Playback controls
        playback_frame = ttk.Frame(control_frame)
        playback_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(playback_frame, text="⏮", command=self.go_to_start).pack(side=tk.LEFT, padx=2)
        ttk.Button(playback_frame, text="⏪", command=self.step_backward).pack(side=tk.LEFT, padx=2)
        ttk.Button(playback_frame, text="⏸", command=self.pause).pack(side=tk.LEFT, padx=2)
        ttk.Button(playback_frame, text="▶", command=self.play).pack(side=tk.LEFT, padx=2)
        ttk.Button(playback_frame, text="⏩", command=self.step_forward).pack(side=tk.LEFT, padx=2)
        ttk.Button(playback_frame, text="⏭", command=self.go_to_end).pack(side=tk.LEFT, padx=2)
        
        # Current frame display
        self.current_frame_var = tk.StringVar()
        ttk.Label(playback_frame, text="Frame:").pack(side=tk.LEFT, padx=(20, 5))
        self.frame_entry = ttk.Entry(playback_frame, textvariable=self.current_frame_var, width=10)
        self.frame_entry.pack(side=tk.LEFT, padx=5)
        self.frame_entry.bind('<Return>', self.go_to_frame)
        
        # Time display
        self.time_display_var = tk.StringVar()
        ttk.Label(playback_frame, textvariable=self.time_display_var).pack(side=tk.LEFT, padx=20)
        
        # Tools
        tools_frame = ttk.Frame(control_frame)
        tools_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(tools_frame, text="Add Marker", command=self.add_marker).pack(side=tk.LEFT, padx=2)
        ttk.Button(tools_frame, text="Add Clip", command=self.add_clip).pack(side=tk.LEFT, padx=2)
        ttk.Button(tools_frame, text="Clear All", command=self.clear_all).pack(side=tk.LEFT, padx=2)
        
        # Zoom controls
        ttk.Button(tools_frame, text="Zoom In", command=self.zoom_in).pack(side=tk.LEFT, padx=10)
        ttk.Button(tools_frame, text="Zoom Out", command=self.zoom_out).pack(side=tk.LEFT, padx=2)
        ttk.Button(tools_frame, text="Fit All", command=self.zoom_fit).pack(side=tk.LEFT, padx=2)
        
        # File operations
        ttk.Button(tools_frame, text="Save Timeline", command=self.save_timeline).pack(side=tk.RIGHT, padx=2)
        ttk.Button(tools_frame, text="Load Timeline", command=self.load_timeline).pack(side=tk.RIGHT, padx=2)
        
        # Timeline canvas
        timeline_canvas_frame = ttk.LabelFrame(parent, text="Timeline", padding=5)
        timeline_canvas_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        canvas_frame = ttk.Frame(timeline_canvas_frame)
        canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        self.timeline_canvas = tk.Canvas(canvas_frame, bg='#2b2b2b', height=200)
        
        h_scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.HORIZONTAL, command=self.timeline_canvas.xview)
        v_scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=self.timeline_canvas.yview)
        
        self.timeline_canvas.configure(xscrollcommand=h_scrollbar.set, yscrollcommand=v_scrollbar.set)
        
        self.timeline_canvas.grid(row=0, column=0, sticky='nsew')
        h_scrollbar.grid(row=1, column=0, sticky='ew')
        v_scrollbar.grid(row=0, column=1, sticky='ns')
        
        canvas_frame.grid_rowconfigure(0, weight=1)
        canvas_frame.grid_columnconfigure(0, weight=1)
        
        # Bind timeline canvas events
        self.timeline_canvas.bind('<Button-1>', self.on_timeline_click)
        self.timeline_canvas.bind('<B1-Motion>', self.on_timeline_drag)
        
    def setup_animation_ui(self, parent):
        # Animation controls
        anim_control_frame = ttk.LabelFrame(parent, text="Animation Controls", padding=10)
        anim_control_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        # Parameter management
        param_frame = ttk.Frame(anim_control_frame)
        param_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(param_frame, text="Parameters:").pack(side=tk.LEFT, padx=(0, 5))
        
        self.param_listbox = tk.Listbox(param_frame, height=3)
        self.param_listbox.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        self.param_listbox.bind('<<ListboxSelect>>', self.on_parameter_select)
        
        param_buttons = ttk.Frame(param_frame)
        param_buttons.pack(side=tk.RIGHT, padx=5)
        
        ttk.Button(param_buttons, text="Add Parameter", command=self.show_add_parameter_dialog).pack(pady=2)
        ttk.Button(param_buttons, text="Remove Parameter", command=self.remove_parameter).pack(pady=2)
        ttk.Button(param_buttons, text="Edit Parameter", command=self.edit_parameter).pack(pady=2)
        
        # Keyframe controls
        keyframe_frame = ttk.Frame(anim_control_frame)
        keyframe_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(keyframe_frame, text="Value:").pack(side=tk.LEFT, padx=(0, 5))
        self.keyframe_value_var = tk.StringVar()
        self.keyframe_value_entry = ttk.Entry(keyframe_frame, textvariable=self.keyframe_value_var, width=10)
        self.keyframe_value_entry.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(keyframe_frame, text="Interpolation:").pack(side=tk.LEFT, padx=(10, 5))
        self.interpolation_var = tk.StringVar(value=InterpolationType.LINEAR.value)
        interpolation_combo = ttk.Combobox(keyframe_frame, textvariable=self.interpolation_var, width=15)
        interpolation_combo['values'] = [interp.value for interp in InterpolationType]
        interpolation_combo.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(keyframe_frame, text="Add Keyframe", command=self.add_keyframe).pack(side=tk.LEFT, padx=10)
        ttk.Button(keyframe_frame, text="Remove Keyframe", command=self.remove_keyframe).pack(side=tk.LEFT, padx=5)
        
        # Graph zoom controls
        zoom_frame = ttk.Frame(anim_control_frame)
        zoom_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(zoom_frame, text="Graph:").pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(zoom_frame, text="Zoom In Y", command=self.zoom_in_y).pack(side=tk.LEFT, padx=2)
        ttk.Button(zoom_frame, text="Zoom Out Y", command=self.zoom_out_y).pack(side=tk.LEFT, padx=2)
        ttk.Button(zoom_frame, text="Fit Y", command=self.fit_y).pack(side=tk.LEFT, padx=2)
        ttk.Button(zoom_frame, text="Reset View", command=self.reset_graph_view).pack(side=tk.LEFT, padx=10)
        
        # Current parameter values display
        self.param_values_var = tk.StringVar()
        ttk.Label(zoom_frame, textvariable=self.param_values_var).pack(side=tk.RIGHT, padx=10)
        
        # Animation graph canvas
        graph_frame = ttk.LabelFrame(parent, text="Animation Graph", padding=5)
        graph_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        graph_canvas_frame = ttk.Frame(graph_frame)
        graph_canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        self.graph_canvas = tk.Canvas(graph_canvas_frame, bg='#1e1e1e', height=300)
        
        graph_h_scrollbar = ttk.Scrollbar(graph_canvas_frame, orient=tk.HORIZONTAL, command=self.graph_canvas.xview)
        graph_v_scrollbar = ttk.Scrollbar(graph_canvas_frame, orient=tk.VERTICAL, command=self.graph_canvas.yview)
        
        self.graph_canvas.configure(xscrollcommand=graph_h_scrollbar.set, yscrollcommand=graph_v_scrollbar.set)
        
        self.graph_canvas.grid(row=0, column=0, sticky='nsew')
        graph_h_scrollbar.grid(row=1, column=0, sticky='ew')
        graph_v_scrollbar.grid(row=0, column=1, sticky='ns')
        
        graph_canvas_frame.grid_rowconfigure(0, weight=1)
        graph_canvas_frame.grid_columnconfigure(0, weight=1)
        
        # Bind graph canvas events
        self.graph_canvas.bind('<Button-1>', self.on_graph_click)
        self.graph_canvas.bind('<B1-Motion>', self.on_graph_drag)
        self.graph_canvas.bind('<ButtonRelease-1>', self.on_graph_release)
        self.graph_canvas.bind('<Button-3>', self.on_graph_right_click)
        self.graph_canvas.bind('<MouseWheel>', self.on_graph_mouse_wheel)
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(parent, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.pack(fill=tk.X, padx=10, pady=(5, 0))
        
        # Initialize displays
        self.update_parameter_list()
        self.update_time_display()
        self.update_parameter_values()
        
    def add_animation_parameter(self, name, min_val=0.0, max_val=100.0, default_val=0.0):
        """Add a new animation parameter"""
        if name in self.animation_parameters:
            return False
            
        color_index = len(self.animation_parameters) % len(self.parameter_colors)
        param = AnimationParameter(name, min_val, max_val, default_val)
        param.color = self.parameter_colors[color_index]
        
        self.animation_parameters[name] = param
        self.update_parameter_list()
        self.update_animation_display()
        return True
        
    def show_add_parameter_dialog(self):
        """Show dialog to add new animation parameter"""
        dialog = ParameterDialog(self.root, "Add Parameter")
        if dialog.result:
            name, min_val, max_val, default_val = dialog.result
            if self.add_animation_parameter(name, min_val, max_val, default_val):
                self.status_var.set(f"Added parameter '{name}'")
            else:
                messagebox.showerror("Error", f"Parameter '{name}' already exists")
                
    def remove_parameter(self):
        """Remove selected parameter"""
        selection = self.param_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a parameter to remove")
            return
            
        param_name = self.param_listbox.get(selection[0])
        if messagebox.askyesno("Confirm", f"Remove parameter '{param_name}' and all its keyframes?"):
            del self.animation_parameters[param_name]
            self.selected_parameter = None
            self.update_parameter_list()
            self.update_animation_display()
            self.status_var.set(f"Removed parameter '{param_name}'")
            
    def edit_parameter(self):
        """Edit selected parameter"""
        selection = self.param_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a parameter to edit")
            return
            
        param_name = self.param_listbox.get(selection[0])
        param = self.animation_parameters[param_name]
        
        dialog = ParameterDialog(self.root, "Edit Parameter", param_name, 
                               param.min_value, param.max_value, param.default_value)
        if dialog.result:
            new_name, min_val, max_val, default_val = dialog.result
            
            # Update parameter
            if new_name != param_name:
                # Rename parameter
                del self.animation_parameters[param_name]
                param.name = new_name
                self.animation_parameters[new_name] = param
                
            param.min_value = min_val
            param.max_value = max_val
            param.default_value = default_val
            
            self.update_parameter_list()
            self.update_animation_display()
            self.status_var.set(f"Updated parameter '{new_name}'")
            
    def update_parameter_list(self):
        """Update the parameter listbox"""
        self.param_listbox.delete(0, tk.END)
        for param_name in sorted(self.animation_parameters.keys()):
            self.param_listbox.insert(tk.END, param_name)
            
    def on_parameter_select(self, event):
        """Handle parameter selection"""
        selection = self.param_listbox.curselection()
        if selection:
            param_name = self.param_listbox.get(selection[0])
            self.selected_parameter = param_name
            self.update_animation_display()
            self.update_keyframe_controls()
            
    def update_keyframe_controls(self):
        """Update keyframe control values based on current frame and selected parameter"""
        if not self.selected_parameter:
            self.keyframe_value_var.set("")
            return
            
        param = self.animation_parameters[self.selected_parameter]
        current_value = param.get_value_at_frame(self.current_frame)
        self.keyframe_value_var.set(f"{current_value:.2f}")
        
        # Find keyframe at current frame to set interpolation
        for kf in param.keyframes:
            if kf.frame == self.current_frame:
                self.interpolation_var.set(kf.interpolation.value)
                break
        else:
            self.interpolation_var.set(InterpolationType.LINEAR.value)
            
    def add_keyframe(self):
        """Add keyframe at current frame for selected parameter"""
        if not self.selected_parameter:
            messagebox.showwarning("No Parameter", "Please select a parameter first")
            return
            
        try:
            value = float(self.keyframe_value_var.get())
            param = self.animation_parameters[self.selected_parameter]
            
            # Clamp value to parameter range
            value = max(param.min_value, min(param.max_value, value))
            
            # Get interpolation type
            interp_name = self.interpolation_var.get()
            interpolation = next(interp for interp in InterpolationType if interp.value == interp_name)
            
            param.add_keyframe(self.current_frame, value, interpolation)
            self.update_animation_display()
            self.update_parameter_values()
            self.status_var.set(f"Added keyframe for '{self.selected_parameter}' at frame {self.current_frame}")
            
        except ValueError:
            messagebox.showerror("Invalid Value", "Please enter a valid numeric value")
            
    def remove_keyframe(self):
        """Remove keyframe at current frame for selected parameter"""
        if not self.selected_parameter:
            messagebox.showwarning("No Parameter", "Please select a parameter first")
            return
            
        param = self.animation_parameters[self.selected_parameter]
        param.remove_keyframe(self.current_frame)
        self.update_animation_display()
        self.update_parameter_values()
        self.status_var.set(f"Removed keyframe for '{self.selected_parameter}' at frame {self.current_frame}")
        
    def update_parameter_values(self):
        """Update the display of current parameter values"""
        if not self.animation_parameters:
            self.param_values_var.set("No parameters")
            return
            
        values = []
        for name, param in self.animation_parameters.items():
            value = param.get_value_at_frame(self.current_frame)
            values.append(f"{name}: {value:.2f}")
            
        self.param_values_var.set(" | ".join(values[:3]) + ("..." if len(values) > 3 else ""))
        
    def on_fps_change(self, event=None):
        selected = self.fps_var.get()
        if selected == "Custom...":
            return
        if selected in self.standard_frame_rates:
            self.current_frame_rate = self.standard_frame_rates[selected]
            self.custom_fps_var.set(str(self.current_frame_rate))
            self.update_timeline_display()
            self.update_time_display()
            
    def on_custom_fps_change(self, event=None):
        try:
            fps = float(self.custom_fps_var.get())
            if fps <= 0:
                raise ValueError("Frame rate must be positive")
            self.current_frame_rate = fps
            self.fps_var.set("Custom...")
            self.update_timeline_display()
            self.update_time_display()
            self.status_var.set(f"Frame rate set to {fps} fps")
        except ValueError as e:
            messagebox.showerror("Invalid Frame Rate", f"Please enter a valid frame rate: {e}")
            
    def update_duration(self):
        try:
            duration = int(self.duration_var.get())
            if duration <= 0:
                raise ValueError("Duration must be positive")
            self.timeline_duration = duration
            if self.current_frame >= duration:
                self.current_frame = duration - 1
            self.update_timeline_display()
            self.update_time_display()
        except ValueError as e:
            messagebox.showerror("Invalid Duration", f"Please enter a valid duration: {e}")
            
    def frame_to_time(self, frame):
        """Convert frame number to time string (HH:MM:SS:FF)"""
        total_seconds = frame / self.current_frame_rate
        hours = int(total_seconds // 3600)
        minutes = int((total_seconds % 3600) // 60)
        seconds = int(total_seconds % 60)
        frame_remainder = int(frame % self.current_frame_rate)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}:{frame_remainder:02d}"
        
    def update_time_display(self):
        self.current_frame_var.set(str(self.current_frame))
        time_str = self.frame_to_time(self.current_frame)
        duration_str = self.frame_to_time(self.timeline_duration - 1)
        self.time_display_var.set(f"Time: {time_str} / {duration_str}")
        self.update_keyframe_controls()
        self.update_parameter_values()
        
    def update_timeline_display(self):
        self.timeline_canvas.delete("all")
        
        canvas_width = max(1000, int(self.timeline_duration * self.zoom_level))
        canvas_height = 200
        self.timeline_canvas.configure(scrollregion=(0, 0, canvas_width, canvas_height))
        
        # Draw time ruler
        self.draw_time_ruler(self.timeline_canvas, canvas_width, canvas_height)
        
        # Draw clips
        self.draw_clips(self.timeline_canvas, canvas_height)
        
        # Draw markers  
        self.draw_markers(self.timeline_canvas, canvas_height)
        
        # Draw playhead
        self.draw_playhead(self.timeline_canvas, canvas_height)
        
        # Update animation display as well
        self.update_animation_display()
        
    def update_animation_display(self):
        """Update the animation graph display"""
        self.graph_canvas.delete("all")
        
        if not self.animation_parameters:
            return
            
        canvas_width = max(1000, int(self.timeline_duration * self.zoom_level))
        canvas_height = 300
        self.graph_canvas.configure(scrollregion=(0, 0, canvas_width, canvas_height))
        
        # Draw grid
        self.draw_animation_grid(canvas_width, canvas_height)
        
        # Draw parameter curves
        self.draw_parameter_curves(canvas_width, canvas_height)
        
        # Draw keyframes
        self.draw_keyframes(canvas_width, canvas_height)
        
        # Draw current frame indicator
        self.draw_animation_playhead(canvas_width, canvas_height)
        
    def draw_animation_grid(self, width, height):
        """Draw grid for animation graph"""
        # Vertical lines (time)
        step = max(1, int(30 / self.zoom_level))
        for frame in range(0, self.timeline_duration, step):
            x = frame * self.zoom_level
            if x < width:
                self.graph_canvas.create_line(x, 0, x, height, fill='#333333', width=1)
            
        # Horizontal lines (values)
        for i in range(5):
            y = height * i / 4
            self.graph_canvas.create_line(0, y, width, y, fill='#333333', width=1)
            
    def draw_parameter_curves(self, width, height):
        """Draw animation curves for all parameters"""
        if not self.animation_parameters:
            return
            
        for param_name, param in self.animation_parameters.items():
            if not param.visible or not param.keyframes:
                continue
                
            # Sample points along the timeline
            points = []
            sample_rate = max(1, int(1 / self.zoom_level))
            
            for frame in range(0, self.timeline_duration, sample_rate):
                x = frame * self.zoom_level
                if x > width:
                    break
                    
                value = param.get_value_at_frame(frame)
                
                # Normalize value to canvas height
                value_range = param.max_value - param.min_value
                if value_range > 0:
                    normalized = (value - param.min_value) / value_range
                    y = height - (normalized * height * 0.8) - (height * 0.1)
                else:
                    y = height / 2
                    
                points.extend([x, y])
                
            # Draw curve
            if len(points) >= 4:
                self.graph_canvas.create_line(points, fill=param.color, width=2, smooth=True)
                
    def draw_keyframes(self, width, height):
        """Draw keyframes as points on the curves"""
        for param_name, param in self.animation_parameters.items():
            if not param.visible:
                continue
                
            for kf in param.keyframes:
                x = kf.frame * self.zoom_level
                if x > width:
                    continue
                
                # Normalize value to canvas height
                value_range = param.max_value - param.min_value
                if value_range > 0:
                    normalized = (kf.value - param.min_value) / value_range
                    y = height - (normalized * height * 0.8) - (height * 0.1)
                else:
                    y = height / 2
                    
                # Draw keyframe point
                size = 6 if kf.selected else 4
                color = '#FFFFFF' if kf.selected else param.color
                self.graph_canvas.create_oval(x-size, y-size, x+size, y+size, 
                                            fill=color, outline='black', width=2,
                                            tags=f"keyframe_{param_name}_{kf.frame}")
                                            
    def draw_animation_playhead(self, width, height):
        """Draw playhead on animation graph"""
        x = self.current_frame * self.zoom_level
        self.graph_canvas.create_line(x, 0, x, height, fill='#FFC107', width=3, tags="anim_playhead")
        
    # Graph interaction methods
    def on_graph_click(self, event):
        """Handle mouse click on animation graph"""
        canvas_x = self.graph_canvas.canvasx(event.x)
        canvas_y = self.graph_canvas.canvasy(event.y)
        
        # Check if clicking on a keyframe
        clicked_item = self.graph_canvas.find_closest(canvas_x, canvas_y)[0]
        tags = self.graph_canvas.gettags(clicked_item)
        
        if any(tag.startswith("keyframe_") for tag in tags):
            # Select keyframe
            keyframe_tag = next(tag for tag in tags if tag.startswith("keyframe_"))
            parts = keyframe_tag.split("_")
            if len(parts) >= 3:
                param_name = "_".join(parts[1:-1])
                frame = int(parts[-1])
                self.select_keyframe(param_name, frame)
        else:
            # Move playhead
            frame = int(canvas_x / self.zoom_level)
            frame = max(0, min(frame, self.timeline_duration - 1))
            self.current_frame = frame
            self.update_time_display()
            self.update_timeline_display()
            
    def on_graph_drag(self, event):
        """Handle mouse drag on animation graph"""
        if self.dragging_keyframe:
            canvas_x = self.graph_canvas.canvasx(event.x)
            canvas_y = self.graph_canvas.canvasy(event.y)
            
            # Update keyframe position
            new_frame = max(0, min(int(canvas_x / self.zoom_level), self.timeline_duration - 1))
            
            # Calculate new value based on y position
            param = self.animation_parameters[self.dragging_keyframe['param']]
            height = 300
            normalized_y = 1 - ((canvas_y - 0.1 * height) / (0.8 * height))
            normalized_y = max(0, min(1, normalized_y))
            new_value = param.min_value + normalized_y * (param.max_value - param.min_value)
            new_value = max(param.min_value, min(param.max_value, new_value))
            
            # Update keyframe
            old_kf = self.dragging_keyframe['keyframe']
            param.remove_keyframe(old_kf.frame)
            param.add_keyframe(new_frame, new_value, old_kf.interpolation)
            
            self.update_animation_display()
            self.update_parameter_values()
            
    def on_graph_release(self, event):
        """Handle mouse release on animation graph"""
        self.dragging_keyframe = None
        
    def on_graph_right_click(self, event):
        """Handle right-click on animation graph"""
        # Context menu for keyframes could be added here
        pass
        
    def on_graph_mouse_wheel(self, event):
        """Handle mouse wheel on animation graph"""
        if event.state & 0x4:  # Ctrl key held
            # Zoom Y
            if event.delta > 0:
                self.zoom_in_y()
            else:
                self.zoom_out_y()
        else:
            # Scroll horizontally
            self.graph_canvas.xview_scroll(int(-1 * (event.delta / 120)), "units")
            
    def select_keyframe(self, param_name, frame):
        """Select a keyframe"""
        if param_name in self.animation_parameters:
            param = self.animation_parameters[param_name]
            for kf in param.keyframes:
                kf.selected = (kf.frame == frame)
                if kf.selected:
                    self.dragging_keyframe = {'param': param_name, 'keyframe': kf}
            self.update_animation_display()
            
    # Zoom methods for animation graph
    def zoom_in_y(self):
        """Zoom in on Y axis"""
        self.animation_zoom_y = min(self.animation_zoom_y * 1.2, 5.0)
        self.update_animation_display()
        
    def zoom_out_y(self):
        """Zoom out on Y axis"""
        self.animation_zoom_y = max(self.animation_zoom_y / 1.2, 0.2)
        self.update_animation_display()
        
    def fit_y(self):
        """Fit all parameter values in view"""
        if not self.animation_parameters:
            return
            
        all_values = []
        for param in self.animation_parameters.values():
            for kf in param.keyframes:
                all_values.append(kf.value)
                
        if all_values:
            self.animation_zoom_y = 1.0
            self.animation_pan_y = 0.0
            self.update_animation_display()
            
    def reset_graph_view(self):
        """Reset animation graph view"""
        self.animation_zoom_y = 1.0
        self.animation_pan_y = 0.0
        self.update_animation_display()
        
    # Timeline drawing methods
    def draw_time_ruler(self, canvas, width, height):
        """Draw time ruler"""
        ruler_height = 40
        
        # Calculate tick intervals
        pixels_per_second = self.current_frame_rate * self.zoom_level
        if pixels_per_second > 100:
            major_interval = self.current_frame_rate  # 1 second
            minor_interval = self.current_frame_rate / 4  # 0.25 seconds
        elif pixels_per_second > 50:
            major_interval = self.current_frame_rate * 2  # 2 seconds
            minor_interval = self.current_frame_rate / 2  # 0.5 seconds
        elif pixels_per_second > 20:
            major_interval = self.current_frame_rate * 5  # 5 seconds
            minor_interval = self.current_frame_rate  # 1 second
        else:
            major_interval = self.current_frame_rate * 10  # 10 seconds
            minor_interval = self.current_frame_rate * 2  # 2 seconds
            
        # Draw ruler background
        canvas.create_rectangle(0, 0, width, ruler_height, fill='#404040', outline='')
        
        # Draw ticks and labels
        for frame in range(0, self.timeline_duration, int(minor_interval)):
            x = frame * self.zoom_level
            if x > width:
                break
                
            if frame % int(major_interval) == 0:
                # Major tick
                canvas.create_line(x, 0, x, ruler_height, fill='white', width=2)
                time_str = self.frame_to_time(frame)
                canvas.create_text(x + 5, 10, text=time_str, fill='white', anchor='nw', font=('Arial', 8))
            else:
                # Minor tick
                canvas.create_line(x, ruler_height - 10, x, ruler_height, fill='#cccccc', width=1)
            
    def draw_clips(self, canvas, height):
        """Draw timeline clips"""
        clip_track_y = 60
        clip_height = 40
        
        for i, clip in enumerate(self.clips):
            start_x = clip['start'] * self.zoom_level
            end_x = clip['end'] * self.zoom_level
            y = clip_track_y + (i % 3) * (clip_height + 5)  # Multiple tracks
            
            # Draw clip rectangle
            canvas.create_rectangle(start_x, y, end_x, y + clip_height, 
                                  fill='#4CAF50', outline='#2E7D32', width=2, tags=f"clip_{i}")
            
            # Draw clip label
            if end_x - start_x > 50:  # Only show label if clip is wide enough
                canvas.create_text((start_x + end_x) / 2, y + clip_height / 2,
                                 text=clip['label'], fill='white', font=('Arial', 9), tags=f"clip_{i}")
                                 
    def draw_markers(self, canvas, height):
        """Draw timeline markers"""
        for i, marker in enumerate(self.markers):
            x = marker['frame'] * self.zoom_level
            
            # Draw marker line
            canvas.create_line(x, 40, x, height - 20, fill='#FF5722', width=2, tags=f"marker_{i}")
            
            # Draw marker flag
            canvas.create_polygon(x, 40, x + 15, 45, x + 15, 55, x, 50, 
                                fill='#FF5722', outline='#D84315', tags=f"marker_{i}")
            
            # Draw marker label
            canvas.create_text(x + 18, 47, text=marker['label'], fill='#FF5722', 
                             anchor='w', font=('Arial', 8), tags=f"marker_{i}")
                             
    def draw_playhead(self, canvas, height):
        """Draw timeline playhead"""
        x = self.current_frame * self.zoom_level
        
        # Draw playhead line
        canvas.create_line(x, 0, x, height, fill='#FFC107', width=3, tags="playhead")
        
        # Draw playhead indicator
        canvas.create_polygon(x - 8, 0, x + 8, 0, x, 15, 
                            fill='#FFC107', outline='#FF8F00', tags="playhead")
                            
    # Timeline interaction methods
    def on_timeline_click(self, event):
        """Handle timeline click"""
        canvas_x = self.timeline_canvas.canvasx(event.x)
        frame = int(canvas_x / self.zoom_level)
        frame = max(0, min(frame, self.timeline_duration - 1))
        self.current_frame = frame
        self.update_time_display()
        self.update_timeline_display()
        
    def on_timeline_drag(self, event):
        """Handle timeline drag"""
        self.on_timeline_click(event)
        
    # Playback control methods
    def go_to_start(self):
        self.current_frame = 0
        self.update_time_display()
        self.update_timeline_display()
        
    def go_to_end(self):
        self.current_frame = self.timeline_duration - 1
        self.update_time_display()
        self.update_timeline_display()
        
    def step_forward(self):
        if self.current_frame < self.timeline_duration - 1:
            self.current_frame += 1
            self.update_time_display()
            self.update_timeline_display()
            
    def step_backward(self):
        if self.current_frame > 0:
            self.current_frame -= 1
            self.update_time_display()
            self.update_timeline_display()
            
    def play(self):
        self.status_var.set("Playing...")
        
    def pause(self):
        self.status_var.set("Paused")
        
    def go_to_frame(self, event=None):
        try:
            frame = int(self.current_frame_var.get())
            frame = max(0, min(frame, self.timeline_duration - 1))
            self.current_frame = frame
            self.update_time_display()
            self.update_timeline_display()
        except ValueError:
            messagebox.showerror("Invalid Frame", "Please enter a valid frame number")
            
    # Utility methods
    def zoom_in(self):
        self.zoom_level = min(self.zoom_level * 1.5, 10.0)
        self.update_timeline_display()
        
    def zoom_out(self):
        self.zoom_level = max(self.zoom_level / 1.5, 0.1)
        self.update_timeline_display()
        
    def zoom_fit(self):
        canvas_width = self.timeline_canvas.winfo_width()
        if canvas_width > 1:
            self.zoom_level = max(0.1, canvas_width / self.timeline_duration)
            self.update_timeline_display()
            
    def add_marker(self):
        import tkinter.simpledialog
        label = tkinter.simpledialog.askstring("Add Marker", f"Enter label for marker at frame {self.current_frame}:")
        if label:
            self.markers.append({'frame': self.current_frame, 'label': label})
            self.update_timeline_display()
            self.status_var.set(f"Added marker '{label}' at frame {self.current_frame}")
            
    def add_clip(self):
        dialog = ClipDialog(self.root, self.current_frame, self.timeline_duration)
        if dialog.result:
            self.clips.append(dialog.result)
            self.update_timeline_display()
            self.status_var.set(f"Added clip '{dialog.result['label']}'")
            
    def clear_all(self):
        if messagebox.askyesno("Clear All", "Are you sure you want to clear all markers and clips?"):
            self.markers.clear()
            self.clips.clear()
            self.update_timeline_display()
            self.status_var.set("Cleared all markers and clips")
            
    def save_timeline(self):
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filename:
            timeline_data = {
                'frame_rate': self.current_frame_rate,
                'duration': self.timeline_duration,
                'markers': self.markers,
                'clips': self.clips,
                'animation_parameters': {
                    name: {
                        'min_value': param.min_value,
                        'max_value': param.max_value,
                        'default_value': param.default_value,
                        'keyframes': [(kf.frame, kf.value, kf.interpolation.value) for kf in param.keyframes]
                    }
                    for name, param in self.animation_parameters.items()
                }
            }
            try:
                with open(filename, 'w') as f:
                    json.dump(timeline_data, f, indent=2)
                self.status_var.set(f"Timeline saved to {filename}")
            except Exception as e:
                messagebox.showerror("Save Error", f"Failed to save timeline: {e}")
                
    def load_timeline(self):
        filename = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filename:
            try:
                with open(filename, 'r') as f:
                    timeline_data = json.load(f)
                
                self.current_frame_rate = timeline_data.get('frame_rate', 30.0)
                self.timeline_duration = timeline_data.get('duration', 3600)
                self.markers = timeline_data.get('markers', [])
                self.clips = timeline_data.get('clips', [])
                
                # Load animation parameters
                if 'animation_parameters' in timeline_data:
                    self.animation_parameters.clear()
                    for name, param_data in timeline_data['animation_parameters'].items():
                        param = AnimationParameter(
                            name, 
                            param_data['min_value'], 
                            param_data['max_value'], 
                            param_data['default_value']
                        )
                        for frame, value, interp_name in param_data['keyframes']:
                            interpolation = next(interp for interp in InterpolationType if interp.value == interp_name)
                            param.add_keyframe(frame, value, interpolation)
                        
                        # Assign color
                        color_index = len(self.animation_parameters) % len(self.parameter_colors)
                        param.color = self.parameter_colors[color_index]
                        
                        self.animation_parameters[name] = param
                
                # Update UI
                self.custom_fps_var.set(str(self.current_frame_rate))
                self.duration_var.set(str(self.timeline_duration))
                self.fps_var.set("Custom...")
                
                self.update_parameter_list()
                self.update_timeline_display()
                self.update_time_display()
                self.status_var.set(f"Timeline loaded from {filename}")
                
            except Exception as e:
                messagebox.showerror("Load Error", f"Failed to load timeline: {e}")


class ClipDialog:
    def __init__(self, parent, current_frame, max_duration):
        self.result = None
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Add Clip")
        self.dialog.geometry("400x200")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self.dialog.geometry("+%d+%d" % (parent.winfo_rootx() + 50, parent.winfo_rooty() + 50))
        
        frame = ttk.Frame(self.dialog, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="Label:").grid(row=0, column=0, sticky='w', pady=5)
        self.label_var = tk.StringVar(value=f"Clip {current_frame}")
        ttk.Entry(frame, textvariable=self.label_var, width=30).grid(row=0, column=1, pady=5, padx=(10, 0))
        
        ttk.Label(frame, text="Start Frame:").grid(row=1, column=0, sticky='w', pady=5)
        self.start_var = tk.StringVar(value=str(current_frame))
        ttk.Entry(frame, textvariable=self.start_var, width=30).grid(row=1, column=1, pady=5, padx=(10, 0))
        
        ttk.Label(frame, text="End Frame:").grid(row=2, column=0, sticky='w', pady=5)
        self.end_var = tk.StringVar(value=str(min(current_frame + 60, max_duration - 1)))
        ttk.Entry(frame, textvariable=self.end_var, width=30).grid(row=2, column=1, pady=5, padx=(10, 0))
        
        button_frame = ttk.Frame(frame)
        button_frame.grid(row=3, column=0, columnspan=2, pady=20)
        
        ttk.Button(button_frame, text="OK", command=self.ok_clicked).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.cancel_clicked).pack(side=tk.LEFT, padx=5)
        
        self.dialog.bind('<Return>', lambda e: self.ok_clicked())
        self.dialog.wait_window()
        
    def ok_clicked(self):
        try:
            label = self.label_var.get().strip()
            start = int(self.start_var.get())
            end = int(self.end_var.get())
            
            if not label:
                raise ValueError("Label cannot be empty")
            if start >= end:
                raise ValueError("Start frame must be less than end frame")
            if start < 0 or end < 0:
                raise ValueError("Frame numbers must be non-negative")
                
            self.result = {'label': label, 'start': start, 'end': end}
            self.dialog.destroy()
            
        except ValueError as e:
            messagebox.showerror("Invalid Input", str(e))
            
    def cancel_clicked(self):
        self.dialog.destroy()


class ParameterDialog:
    def __init__(self, parent, title, name="", min_val=0.0, max_val=100.0, default_val=0.0):
        self.result = None
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("450x250")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self.dialog.geometry("+%d+%d" % (parent.winfo_rootx() + 50, parent.winfo_rooty() + 50))
        
        frame = ttk.Frame(self.dialog, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="Parameter Name:").grid(row=0, column=0, sticky='w', pady=5)
        self.name_var = tk.StringVar(value=name)
        ttk.Entry(frame, textvariable=self.name_var, width=30).grid(row=0, column=1, pady=5, padx=(10, 0))
        
        ttk.Label(frame, text="Minimum Value:").grid(row=1, column=0, sticky='w', pady=5)
        self.min_var = tk.StringVar(value=str(min_val))
        ttk.Entry(frame, textvariable=self.min_var, width=30).grid(row=1, column=1, pady=5, padx=(10, 0))
        
        ttk.Label(frame, text="Maximum Value:").grid(row=2, column=0, sticky='w', pady=5)
        self.max_var = tk.StringVar(value=str(max_val))
        ttk.Entry(frame, textvariable=self.max_var, width=30).grid(row=2, column=1, pady=5, padx=(10, 0))
        
        ttk.Label(frame, text="Default Value:").grid(row=3, column=0, sticky='w', pady=5)
        self.default_var = tk.StringVar(value=str(default_val))
        ttk.Entry(frame, textvariable=self.default_var, width=30).grid(row=3, column=1, pady=5, padx=(10, 0))
        
        button_frame = ttk.Frame(frame)
        button_frame.grid(row=4, column=0, columnspan=2, pady=20)
        
        ttk.Button(button_frame, text="OK", command=self.ok_clicked).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.cancel_clicked).pack(side=tk.LEFT, padx=5)
        
        self.dialog.bind('<Return>', lambda e: self.ok_clicked())
        self.dialog.wait_window()
        
    def ok_clicked(self):
        try:
            name = self.name_var.get().strip()
            min_val = float(self.min_var.get())
            max_val = float(self.max_var.get())
            default_val = float(self.default_var.get())
            
            if not name:
                raise ValueError("Parameter name cannot be empty")
            if min_val >= max_val:
                raise ValueError("Minimum value must be less than maximum value")
            if default_val < min_val or default_val > max_val:
                raise ValueError("Default value must be between minimum and maximum values")
                
            self.result = (name, min_val, max_val, default_val)
            self.dialog.destroy()
            
        except ValueError as e:
            messagebox.showerror("Invalid Input", str(e))
            
    def cancel_clicked(self):
        self.dialog.destroy()


def main():
    import tkinter.simpledialog
    tk.simpledialog = tkinter.simpledialog
    
    root = tk.Tk()
    app = TimelineApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
