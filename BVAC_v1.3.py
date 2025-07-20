import tkinter as tk
from tkinter import ttk, messagebox
import csv
import math

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
    return 5 * round(n / 5)

def round_up_to_5(n: float) -> int:
    return 5 * math.ceil(n / 5)

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
root = tk.Tk()
root.title("BattleTech Vehicle Armour Calculator")
root.geometry("460x560")
root.resizable(True, True)

frame = ttk.Frame(root, padding=10)
frame.pack(fill=tk.BOTH, expand=True)

frame.rowconfigure(6, weight=1)
frame.columnconfigure(0, weight=1)
frame.columnconfigure(1, weight=1)

# Tonnage input
ttk.Label(frame, text="Armour Tonnage:").grid(column=0, row=0, sticky=tk.W)
entry_tonnage = ttk.Entry(frame)
entry_tonnage.grid(column=1, row=0, sticky=tk.W)

# Armour type dropdown
ttk.Label(frame, text="Armour Type:").grid(column=0, row=1, sticky=tk.W)
armour_type = tk.StringVar(value=ARMOUR_OPTIONS[0])
ttk.OptionMenu(frame, armour_type, ARMOUR_OPTIONS[0], *ARMOUR_OPTIONS).grid(column=1, row=1, sticky=tk.W)

# Save to CSV option (default off)
save_csv = tk.BooleanVar(value=False)
ttk.Checkbutton(frame, text="Save CSV file", variable=save_csv).grid(column=0, row=2, columnspan=2, sticky=tk.W, pady=(10, 0))

# Rounding option
round_each_location = tk.BooleanVar(value=False)
ttk.Checkbutton(
    frame,
    text="Round each location's points to nearest multiple of 5 and add leftover to front",
    variable=round_each_location
).grid(column=0, row=3, columnspan=2, sticky=tk.W)

# Remove turret option
remove_turret = tk.BooleanVar(value=False)
ttk.Checkbutton(
    frame,
    text="Remove Turret and evenly distribute its share",
    variable=remove_turret
).grid(column=0, row=4, columnspan=2, sticky=tk.W)

# Calculate button
ttk.Button(frame, text="Calculate", command=run_calculation).grid(column=0, row=5, columnspan=2, pady=10)

# Results output
result_text = tk.Text(frame)
result_text.grid(column=0, row=6, columnspan=2, pady=5, sticky="nsew")

root.mainloop()
