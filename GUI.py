import tkinter as tk
from tkinter import messagebox

def get_coordinates():
    try:
        x = float(x_entry.get())
        y = float(y_entry.get())
        result_label.config(text=f"Coordinates entered: ({x}, {y})")
        messagebox.showinfo("Success", f"Coordinates ({x}, {y}) have been recorded.")
    except ValueError:
        messagebox.showerror("Error", "Please enter valid numbers for both X and Y coordinates.")

# Create the main window
root = tk.Tk()
root.title("Coordinate Input")
root.geometry("350x200")
root.resizable(False, False)

# Create a frame for better organization
frame = tk.Frame(root, padx=20, pady=20)
frame.pack(fill="both", expand=True)

# X coordinate input
x_label = tk.Label(frame, text="X Coordinate:")
x_label.grid(row=0, column=0, sticky="w", pady=(0, 10))
x_entry = tk.Entry(frame, width=15)
x_entry.grid(row=0, column=1, sticky="w", pady=(0, 10))

# Y coordinate input
y_label = tk.Label(frame, text="Y Coordinate:")
y_label.grid(row=1, column=0, sticky="w", pady=(0, 10))
y_entry = tk.Entry(frame, width=15)
y_entry.grid(row=1, column=1, sticky="w", pady=(0, 10))

# Button to submit coordinates
submit_button = tk.Button(frame, text="Submit", command=get_coordinates, width=10)
submit_button.grid(row=2, column=0, columnspan=2, pady=(10, 0))

# Label to display the result
result_label = tk.Label(frame, text="Enter coordinates and click Submit")
result_label.grid(row=3, column=0, columnspan=2, pady=(10, 0))

# Start the application
if __name__ == "__main__":
    root.mainloop()