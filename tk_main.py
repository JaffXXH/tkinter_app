import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, List, Tuple
from volatilitypopup import VolatilityPopup

class VolatilityTableApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Volatility Surface Manager")
        self.root.geometry("1000x600")
        
        # Initialize data structures
        self.volatility_data: Dict[str, Dict[str, float]] = {
            "1D": {"ATM": 15.2, "10D": 16.5, "25D": 14.8, "Offset": 0.0},
            "2D": {"ATM": 15.0, "10D": 16.3, "25D": 14.6, "Offset": 0.0},
            "1W": {"ATM": 14.8, "10D": 16.1, "25D": 14.4, "Offset": 0.0},
            "2W": {"ATM": 14.6, "10D": 15.9, "25D": 14.2, "Offset": 0.0},
            "1M": {"ATM": 14.4, "10D": 15.7, "25D": 14.0, "Offset": 0.0},
            "3M": {"ATM": 14.2, "10D": 15.5, "25D": 13.8, "Offset": 0.0},
            "6M": {"ATM": 14.0, "10D": 15.3, "25D": 13.6, "Offset": 0.0},
            "1Y": {"ATM": 13.8, "10D": 15.1, "25D": 13.4, "Offset": 0.0},
        }
        
        self.original_volatility_data = {
            maturity: {k: v for k, v in values.items() if k != "Offset"}
            for maturity, values in self.volatility_data.items()
        }
        
        self.setup_ui()
        
    def setup_ui(self) -> None:
        """Initialize all UI components."""
        self.setup_styles()
        self.create_main_frame()
        self.create_table()
        self.create_controls()
        
    def setup_styles(self) -> None:
        """Configure custom styles for the application."""
        style = ttk.Style()
        style.configure("TFrame", background="#f0f0f0")
        style.configure("TButton", padding=6, font=("Arial", 10))
        style.configure("Header.TLabel", font=("Arial", 10, "bold"), padding=5)
        style.configure("Normal.TLabel", font=("Arial", 10), padding=5)
        style.configure("Offset.TLabel", font=("Arial", 10), padding=5, background="#d3d3d3")
        style.configure("OffsetActive.TLabel", font=("Arial", 10), padding=5, background="#ffa500")
        
    def create_main_frame(self) -> None:
        """Create the main container frame."""
        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
    def create_table(self) -> None:
        """Create and populate the volatility table."""
        # Create frame for the table
        table_frame = ttk.Frame(self.main_frame)
        table_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Table headers
        headers = ["Maturity", "ATM", "10D", "25D", "Offset"]
        
        # Create header row
        for col, header in enumerate(headers):
            label = ttk.Label(table_frame, text=header, style="Header.TLabel")
            label.grid(row=0, column=col, sticky="nsew", padx=1, pady=1)
            table_frame.grid_columnconfigure(col, weight=1)
        
        # Create data rows
        self.offset_entries: Dict[str, tk.StringVar] = {}
        self.offset_cells: Dict[str, ttk.Label] = {}
        
        for row, maturity in enumerate(self.volatility_data.keys(), start=1):
            # Maturity column
            ttk.Label(table_frame, text=maturity, style="Normal.TLabel").grid(
                row=row, column=0, sticky="nsew", padx=1, pady=1
            )
            
            # Volatility columns
            for col, vol_type in enumerate(["ATM", "10D", "25D"], start=1):
                ttk.Label(table_frame, 
                          text=f"{self.volatility_data[maturity][vol_type]:.1f}", 
                          style="Normal.TLabel").grid(
                    row=row, column=col, sticky="nsew", padx=1, pady=1
                )
            
            # Offset column
            offset_var = tk.StringVar(value=f"{self.volatility_data[maturity]['Offset']:.1f}")
            self.offset_entries[maturity] = offset_var
            
            offset_cell = ttk.Label(table_frame, textvariable=offset_var, 
                                   style="Offset.TLabel")
            offset_cell.grid(row=row, column=4, sticky="nsew", padx=1, pady=1)
            self.offset_cells[maturity] = offset_cell
            
            # Make offset cell respond to clicks
            offset_cell.bind("<Button-1>", lambda e, m=maturity: self.edit_offset(m))
        
    def create_controls(self) -> None:
        """Create control buttons and selection widgets."""
        control_frame = ttk.Frame(self.main_frame)
        control_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Maturity selection
        ttk.Label(control_frame, text="Apply to Maturity:").pack(side=tk.LEFT, padx=(0, 5))
        self.maturity_var = tk.StringVar(value="1D")
        maturity_menu = ttk.OptionMenu(
            control_frame, self.maturity_var, "1D", *self.volatility_data.keys()
        )
        maturity_menu.pack(side=tk.LEFT, padx=(0, 20))
        
        # Offset entry
        ttk.Label(control_frame, text="Offset Value:").pack(side=tk.LEFT, padx=(0, 5))
        self.offset_entry = ttk.Entry(control_frame, width=8)
        self.offset_entry.pack(side=tk.LEFT, padx=(0, 20))
        self.offset_entry.insert(0, "0.0")
        
        # Buttons
        apply_button = ttk.Button(control_frame, text="Apply Offset", command=self.apply_offset)
        apply_button.pack(side=tk.LEFT, padx=(0, 10))
        
        reset_button = ttk.Button(control_frame, text="Reset All", command=self.reset_all)
        reset_button.pack(side=tk.LEFT)
    ##this
    def edit_offset(self, maturity: str) -> None:
        """Enable editing of the offset value for a specific maturity."""
        # Create a temporary entry widget for editing
        cell = self.offset_cells[maturity]
        x, y, width, height = cell.grid_info()['column'], cell.grid_info()['row'], cell.winfo_width(), cell.winfo_height()
        
        entry_frame = cell.master
        entry = ttk.Entry(entry_frame, width=8, font=("Arial", 10), justify=tk.CENTER)
        entry.insert(0, self.offset_entries[maturity].get())
        entry.grid(row=y, column=x, sticky="nsew", padx=1, pady=1)
        entry.focus_set()
        
        def save_offset(event=None):
            try:
                new_value = float(entry.get())
                self.offset_entries[maturity].set(f"{new_value:.1f}")
                self.update_offset_cell_color(maturity)
            except ValueError:
                pass
            entry.destroy()
        ##this
        entry.bind("<Return>", save_offset)
        entry.bind("<FocusOut>", save_offset)
    
    def apply_offset(self) -> None:
        """Apply the offset to the selected maturity."""
        maturity = self.maturity_var.get()
        
        try:
            offset_value = float(self.offset_entry.get())

            # Calculate new values
            new_values = {
                vol_type: self.original_volatility_data[maturity][vol_type] + offset_value
                for vol_type in ["ATM", "10D", "25D"]
            }

            # Show confirmation popup
            VolatilityPopup(
                self.root,
                maturity,
                self.original_volatility_data[maturity],
                new_values,
                offset_value
            )

            # Only update if user confirms (move this to popup's on_confirm)
            self.offset_entries[maturity].set(f"{offset_value:.1f}")
            self.update_offset_cell_color(maturity)
            self.update_volatilities(maturity, offset_value)

        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter a valid number", parent=self.root)

        
    def update_volatilities(self, maturity: str, offset: float) -> None:
        """Update volatility values based on the applied offset."""
        # Update ATM vol
        atm_vol = self.original_volatility_data[maturity]["ATM"] + offset
        self.volatility_data[maturity]["ATM"] = atm_vol
        
        # Update other vols (here we just add the same offset, but you could implement more complex logic)
        for vol_type in ["10D", "25D"]:
            self.volatility_data[maturity][vol_type] = (
                self.original_volatility_data[maturity][vol_type] + offset
            )
        
        # Refresh the table
        self.refresh_table()
        
    def refresh_table(self) -> None:
        """Refresh the table with updated volatility values."""
        table_frame = self.offset_cells["1D"].master  # Get reference to the table frame
        
        for row, maturity in enumerate(self.volatility_data.keys(), start=1):
            for col, vol_type in enumerate(["ATM", "10D", "25D"], start=1):
                # Find the label widget in the grid and update its text
                for child in table_frame.grid_slaves(row=row, column=col):
                    if isinstance(child, ttk.Label):
                        child.config(text=f"{self.volatility_data[maturity][vol_type]:.1f}")
                        break
        
    def update_offset_cell_color(self, maturity: str) -> None:
        """Update the background color of the offset cell based on its value."""
        try:
            offset_value = float(self.offset_entries[maturity].get())
            if offset_value == 0:
                self.offset_cells[maturity].configure(style="Offset.TLabel")
            else:
                self.offset_cells[maturity].configure(style="OffsetActive.TLabel")
        except ValueError:
            pass
        
    def reset_all(self) -> None:
        """Reset all offsets to zero and revert to original volatility values."""
        for maturity in self.volatility_data.keys():
            self.offset_entries[maturity].set("0.0")
            self.update_offset_cell_color(maturity)
            self.volatility_data[maturity].update(self.original_volatility_data[maturity])
        
        self.refresh_table()
        self.offset_entry.delete(0, tk.END)
        self.offset_entry.insert(0, "0.0")


def main():
    root = tk.Tk()
    app = VolatilityTableApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()