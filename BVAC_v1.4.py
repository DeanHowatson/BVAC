import tkinter as tk
from tkinter import ttk, messagebox
import csv
import math
import os
import json

# File to store settings
SETTINGS_FILE = "settings.json"

# Armour types with points per ton
RAW_ARMOUR_TYPES = {
    "Standard": 16.0,
    "Ferro-Fibrous": 17.92,
    "Light Ferro-Fibrous": 16.96,
    "Heavy Ferro-Fibrous": 19.84,
    "Hardened": 8.0,
    "Ballistic Reinforced": 12.0,
    "Clan Ferro-Fibrous": 19.20,
    "Clan Ferro-Lamellor": 14.0
}

# Format options for dropdown (shows points per ton)
ARMOUR_OPTIONS = [f"{name} ({value:.2f} pts/ton)" for name, value in RAW_ARMOUR_TYPES.items()]
ARMOUR_LOOKUP = dict(zip(ARMOUR_OPTIONS, RAW_ARMOUR_TYPES.values()))

def round_to_nearest_5(n: float) -> int:
    """Rounds a number to the nearest multiple of 5."""
    return 5 * round(n / 5)

def round_up_to_5(n: float) -> int:
    """Rounds a number up to the nearest multiple of 5."""
    return 5 * math.ceil(n / 5)

def save_settings():
    """Saves the current dark mode setting to a JSON file."""
    with open(SETTINGS_FILE, "w") as f:
        json.dump({"dark_mode": dark_mode.get()}, f)

def load_settings():
    """Loads dark mode setting from a JSON file if it exists."""
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r") as f:
            return json.load(f)
    return {"dark_mode": True}

def calculate_armour_distribution(total_armour_points: int, round_each: bool = False, remove_turret: bool = False) -> dict:
    """
    Distribute total armour points to vehicle facings.
    Handles optional turret removal and optional rounding.
    """

    # Original distribution
    base_distribution = {
        "Front": 0.30,
        "Left Side": 0.208,
        "Right Side": 0.208,
        "Rear": 0.117,
        "Turret": 0.167
    }

    distribution_percent = base_distribution.copy()

    # Remove Turret and redistribute its percentage evenly
    if remove_turret:
        turret_share = distribution_percent.pop("Turret")
        for loc in distribution_percent:
            distribution_percent[loc] += turret_share / len(distribution_percent)

    # Calculate unrounded point allocations
    raw_allocations = {loc: total_armour_points * pct for loc, pct in distribution_percent.items()}

    if not round_each:
        # Basic integer rounding
        armour_distribution = {loc: round(points) for loc, points in raw_allocations.items()}
        allocated = sum(armour_distribution.values())
        leftover = total_armour_points - allocated
        if leftover > 0:
            for loc in distribution_percent:
                if leftover == 0:
                    break
                armour_distribution[loc] += 1
                leftover -= 1
    else:
        # Rounding to nearest 5 (front rounds up)
        rounded_allocations = {}
        for loc, points in raw_allocations.items():
            if loc == "Front":
                rounded_allocations[loc] = round_up_to_5(points)
            else:
                rounded_allocations[loc] = round_to_nearest_5(points)

        total_rounded = sum(rounded_allocations.values())

        if total_rounded > total_armour_points:
            overage = total_rounded - total_armour_points
            if "Rear" in rounded_allocations and rounded_allocations["Rear"] >= overage:
                rounded_allocations["Rear"] -= overage
            else:
                deficit = overage - rounded_allocations.get("Rear", 0)
                rounded_allocations["Rear"] = 0
                if "Turret" in rounded_allocations:
                    rounded_allocations["Turret"] = max(0, rounded_allocations["Turret"] - deficit)
        elif total_rounded < total_armour_points:
            rounded_allocations["Front"] += total_armour_points - total_rounded

        armour_distribution = rounded_allocations

    return armour_distribution

def run_calculation():
    """Main calculation function triggered by GUI."""
    try:
        tons = float(entry_tonnage.get())
        selected_label = armour_type.get()
        points_per_ton = ARMOUR_LOOKUP[selected_label]
        total_armour_points = int(tons * points_per_ton)

        layout = calculate_armour_distribution(
            total_armour_points,
            round_each=round_each_location.get(),
            remove_turret=remove_turret.get()
        )

        # Clear and display results
        result_text.delete("1.0", tk.END)
        result_text.insert(tk.END, f"Armour Type: {selected_label}\n")
        result_text.insert(tk.END, f"Total Armour Points: {total_armour_points}\n")
        result_text.insert(tk.END, f"Total Armour Weight: {tons:.2f} tons\n\n")

        draw_diagram(layout)

        for loc, pts in layout.items():
            weight = pts / points_per_ton
            result_text.insert(tk.END, f"{loc}: {pts} points ({weight:.2f} tons)\n")

        # Save CSV if enabled
        if save_csv.get():
            with open("armour_distribution.csv", mode='w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(["Facing", "Armour Points", "Weight (tons)"])
                for loc, pts in layout.items():
                    weight = pts / points_per_ton
                    writer.writerow([loc, pts, f"{weight:.2f}"])
            messagebox.showinfo("Success", "Armour distribution saved to 'armour_distribution.csv'")

    except ValueError:
        messagebox.showerror("Input Error", "Please enter a valid number for tonnage.")

# --- GUI Setup ---
def draw_diagram(layout):
    """Draws a top-down vehicle layout on canvas showing armor per facing."""
    canvas.delete("all")
    canvas.create_rectangle(80, 20, 120, 60, fill="gray20")  # Front
    canvas.create_text(100, 40, text=f"Fr\n{layout.get('Front', 0)}", font=("Arial", 8), fill="white")

    canvas.create_rectangle(40, 60, 80, 100, fill="gray20")  # Left
    canvas.create_text(60, 80, text=f"Ls\n{layout.get('Left Side', 0)}", font=("Arial", 8), fill="white")

    canvas.create_rectangle(120, 60, 160, 100, fill="gray20")  # Right
    canvas.create_text(140, 80, text=f"Rs\n{layout.get('Right Side', 0)}", font=("Arial", 8), fill="white")

    canvas.create_rectangle(80, 100, 120, 140, fill="gray20")  # Rear
    canvas.create_text(100, 120, text=f"Rr\n{layout.get('Rear', 0)}", font=("Arial", 8), fill="white")

    if "Turret" in layout:
        canvas.create_rectangle(80, 60, 120, 100, fill="gray40")
        canvas.create_text(100, 80, text=f"Tu\n{layout.get('Turret', 0)}", font=("Arial", 8), fill="white")

def create_tooltip(widget, text):
    """Creates a tooltip popup for any given widget."""
    tooltip = tk.Toplevel(widget)
    tooltip.withdraw()
    tooltip.overrideredirect(True)
    label = tk.Label(tooltip, text=text, background="lightyellow", relief="solid", borderwidth=1, font=("Arial", 8))
    label.pack()

    def enter(event):
        x = widget.winfo_rootx() + 20
        y = widget.winfo_rooty() + 20
        tooltip.geometry(f"+{x}+{y}")
        tooltip.deiconify()

    def leave(event):
        tooltip.withdraw()

    widget.bind("<Enter>", enter)
    widget.bind("<Leave>", leave)

def apply_dark_mode():
    """Applies dark theme to the GUI."""
    root.configure(bg="gray15")
    style = ttk.Style()
    style.theme_use("clam")
    style.configure("TFrame", background="gray15")
    style.configure("TLabel", background="gray15", foreground="white")
    style.configure("TCheckbutton", background="gray15", foreground="white")
    style.configure("TButton", background="gray20", foreground="white")
    style.configure("TEntry", fieldbackground="gray25", foreground="white")
    style.configure("TMenubutton", background="gray20", foreground="white")
    result_text.configure(bg="gray20", fg="white")
    canvas.configure(bg="gray15")

def apply_light_mode():
    """Applies light (default) theme to the GUI."""
    root.configure(bg="SystemButtonFace")
    style = ttk.Style()
    style.theme_use("clam")
    style.configure("TFrame", background="SystemButtonFace")
    style.configure("TLabel", background="SystemButtonFace", foreground="black")
    style.configure("TCheckbutton", background="SystemButtonFace", foreground="black")
    style.configure("TButton", background="SystemButtonFace", foreground="black")
    style.configure("TEntry", fieldbackground="white", foreground="black")
    style.configure("TMenubutton", background="SystemButtonFace", foreground="black")
    result_text.configure(bg="white", fg="black")
    canvas.configure(bg="white")

def toggle_mode():
    """Toggles between light and dark mode and saves preference."""
    if dark_mode.get():
        apply_dark_mode()
    else:
        apply_light_mode()
    save_settings()

# GUI Setup
root = tk.Tk()
root.title("BattleTech Vehicle Armour Calculator")
root.geometry("480x650")

frame = ttk.Frame(root, padding=10)
frame.pack(fill=tk.BOTH, expand=True)

frame.rowconfigure(9, weight=1)
frame.columnconfigure(0, weight=1)
frame.columnconfigure(1, weight=1)

# Load saved settings
settings = load_settings()
dark_mode = tk.BooleanVar(value=settings.get("dark_mode", True))
toggle = ttk.Checkbutton(frame, text="Dark Mode", variable=dark_mode, command=toggle_mode)
toggle.grid(column=0, row=0, columnspan=2, sticky=tk.E)

# Tonnage input
ttk.Label(frame, text="Armour Tonnage:").grid(column=0, row=1, sticky=tk.W)
entry_tonnage = ttk.Entry(frame)
entry_tonnage.grid(column=1, row=1, sticky=tk.W)
create_tooltip(entry_tonnage, "How many tons of armour the vehicle carries")

# Armour type dropdown
ttk.Label(frame, text="Armour Type:").grid(column=0, row=2, sticky=tk.W)
armour_type = tk.StringVar(value=ARMOUR_OPTIONS[0])
menu = ttk.OptionMenu(frame, armour_type, ARMOUR_OPTIONS[0], *ARMOUR_OPTIONS)
menu.grid(column=1, row=2, sticky=tk.W)
create_tooltip(menu, "Select armour type to determine points per ton")

# Save to CSV option (default off)
save_csv = tk.BooleanVar(value=False)
check_csv = ttk.Checkbutton(frame, text="Save CSV file", variable=save_csv)
check_csv.grid(column=0, row=3, columnspan=2, sticky=tk.W, pady=(10, 0))
create_tooltip(check_csv, "Save the result to a CSV file")

# Rounding option
round_each_location = tk.BooleanVar(value=False)
check_round = ttk.Checkbutton(frame, text="Round to nearest 5 and add leftover to front", variable=round_each_location)
check_round.grid(column=0, row=4, columnspan=2, sticky=tk.W)
create_tooltip(check_round, "Rounds each facing to nearest 5 (front always rounds up)")

# Remove turret option
remove_turret = tk.BooleanVar(value=False)
check_turret = ttk.Checkbutton(frame, text="Remove Turret and distribute its share", variable=remove_turret)
check_turret.grid(column=0, row=5, columnspan=2, sticky=tk.W)
create_tooltip(check_turret, "Eliminates turret and spreads its armor to other facings")

# Calculate button
btn = ttk.Button(frame, text="Calculate", command=run_calculation)
btn.grid(column=0, row=6, columnspan=2, pady=10)

# Results output

canvas = tk.Canvas(frame, width=200, height=160)
canvas.grid(column=0, row=7, columnspan=2, pady=10)

result_text = tk.Text(frame, height=10)
result_text.grid(column=0, row=8, columnspan=2, pady=5, sticky="nsew")

# Apply initial mode
if dark_mode.get():
    apply_dark_mode()
else:
    apply_light_mode()

root.mainloop()
