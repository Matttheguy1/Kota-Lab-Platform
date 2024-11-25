import tkinter as tk
from tkinter import ttk
import math


class PIDSliderGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("PID+FF Parameter Adjustment")

        # Configure style for the labels
        style = ttk.Style()
        style.configure("BW.TLabel", font=("Arial", 12, "bold"))

        # Create frames for better organization
        self.sliders_frame = ttk.Frame(root, padding="10")
        self.sliders_frame.grid(row=0, column=0)

        self.values_frame = ttk.Frame(root, padding="10")
        self.values_frame.grid(row=0, column=1)

        # Initialize variables to store values
        self.p_var = tk.DoubleVar()
        self.i_var = tk.DoubleVar()
        self.d_var = tk.DoubleVar()
        self.ff_var = tk.DoubleVar()

        # Create sliders and labels
        self.create_slider("P", self.p_var, 0)
        self.create_slider("I", self.i_var, 1)
        self.create_slider("D", self.d_var, 2)
        self.create_slider("FF", self.ff_var, 3)

        # Create value display labels
        self.p_value_label = ttk.Label(self.values_frame, text="0.1")
        self.i_value_label = ttk.Label(self.values_frame, text="0.1")
        self.d_value_label = ttk.Label(self.values_frame, text="0.1")
        self.ff_value_label = ttk.Label(self.values_frame, text="0.1")

        # Grid value labels
        self.p_value_label.grid(row=0, column=0, pady=5)
        self.i_value_label.grid(row=1, column=0, pady=5)
        self.d_value_label.grid(row=2, column=0, pady=5)
        self.ff_value_label.grid(row=3, column=0, pady=5)

    def create_slider(self, label_text, variable, row):
        # Create and configure label
        label = ttk.Label(self.sliders_frame, text=label_text, style="BW.TLabel")
        label.grid(row=row, column=0, padx=5)

        # Create slider
        slider = ttk.Scale(
            self.sliders_frame,
            from_=0,
            to=1000,
            orient="horizontal",
            length=300,
            variable=variable,
            command=lambda x, var=variable, lbl=label_text: self.update_value(var, lbl)
        )
        slider.grid(row=row, column=1, pady=5)

        # Set initial value
        slider.set(0)  # This will trigger the update_value callback

    def scale_to_log(self, scale_val):
        # Convert linear scale (0-1000) to logarithmic scale (0.1-100)
        min_val = math.log10(0.1)
        max_val = math.log10(100)
        scale_normalized = float(scale_val) / 1000.0
        log_val = math.pow(10, min_val + (max_val - min_val) * scale_normalized)
        return round(log_val, 3)

    def update_value(self, variable, label_type):
        # Get the current value and convert it to logarithmic scale
        value = self.scale_to_log(variable.get())

        # Update the appropriate label
        if label_type == "P":
            self.p_value_label.config(text=f"{value:.3f}")
        elif label_type == "I":
            self.i_value_label.config(text=f"{value:.3f}")
        elif label_type == "D":
            self.d_value_label.config(text=f"{value:.3f}")
        elif label_type == "FF":
            self.ff_value_label.config(text=f"{value:.3f}")


if __name__ == "__main__":
    root = tk.Tk()
    app = PIDSliderGUI(root)
    root.mainloop()