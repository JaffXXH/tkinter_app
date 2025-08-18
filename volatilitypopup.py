import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict

class VolatilityPopup:
    def __init__(self, parent, maturity: str, original_values: Dict[str, float], 
                 new_values: Dict[str, float], offset: float):
        self.parent = parent
        self.maturity = maturity
        self.original_values = original_values
        self.new_values = new_values
        self.offset = offset
        
        self.create_popup()
        self.create_widgets()
        
    def create_popup(self):
        self.popup = tk.Toplevel(self.parent)
        self.popup.title("Volatility Adjustment Confirmation")
        self.popup.geometry("400x300")
        self.popup.resizable(False, False)
        self.popup.grab_set()  # Make it modal
        
        # Center the popup relative to parent
        parent_x = self.parent.winfo_x()
        parent_y = self.parent.winfo_y()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()
        
        popup_width = 400
        popup_height = 300
        
        position_x = parent_x + (parent_width - popup_width) // 2
        position_y = parent_y + (parent_height - popup_height) // 2
        
        self.popup.geometry(f"+{position_x}+{position_y}")
        
    def create_widgets(self):
        # Main frame
        main_frame = ttk.Frame(self.popup, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(
            title_frame, 
            text=f"Volatility Adjustment for {self.maturity}",
            font=("Arial", 12, "bold")
        ).pack(side=tk.LEFT)
        
        # Offset info
        offset_frame = ttk.Frame(main_frame)
        offset_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(
            offset_frame,
            text=f"Applied Offset: {self.offset:+.1f}",
            font=("Arial", 10)
        ).pack(side=tk.LEFT)
        
        # Volatility comparison table
        table_frame = ttk.Frame(main_frame)
        table_frame.pack(fill=tk.BOTH, expand=True)
        
        # Table headers
        headers = ["Type", "Original", "New", "Change"]
        for col, header in enumerate(headers):
            ttk.Label(
                table_frame,
                text=header,
                font=("Arial", 10, "bold"),
                borderwidth=1,
                relief="solid",
                padding=5
            ).grid(row=0, column=col, sticky="nsew")
            
        # Table data
        vol_types = ["ATM", "10D", "25D"]
        for row, vol_type in enumerate(vol_types, start=1):
            original = self.original_values[vol_type]
            new = self.new_values[vol_type]
            change = new - original
            
            # Type column
            ttk.Label(
                table_frame,
                text=vol_type,
                font=("Arial", 10),
                borderwidth=1,
                relief="solid",
                padding=5
            ).grid(row=row, column=0, sticky="nsew")
            
            # Original value
            ttk.Label(
                table_frame,
                text=f"{original:.1f}",
                font=("Arial", 10),
                borderwidth=1,
                relief="solid",
                padding=5
            ).grid(row=row, column=1, sticky="nsew")
            
            # New value (highlighted)
            ttk.Label(
                table_frame,
                text=f"{new:.1f}",
                font=("Arial", 10, "bold"),
                background="#e6f3ff",
                borderwidth=1,
                relief="solid",
                padding=5
            ).grid(row=row, column=2, sticky="nsew")
            
            # Change (colored based on direction)
            change_color = "#4CAF50" if change >= 0 else "#F44336"
            ttk.Label(
                table_frame,
                text=f"{change:+.1f}",
                font=("Arial", 10),
                foreground="white",
                background=change_color,
                borderwidth=1,
                relief="solid",
                padding=5
            ).grid(row=row, column=3, sticky="nsew")
            
        # Configure grid weights
        for col in range(4):
            table_frame.grid_columnconfigure(col, weight=1)
        
        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(15, 0))
        
        ttk.Button(
            button_frame,
            text="Confirm",
            command=self.on_confirm
        ).pack(side=tk.RIGHT, padx=5)
        
        ttk.Button(
            button_frame,
            text="Cancel",
            command=self.on_cancel
        ).pack(side=tk.RIGHT)
        
    def on_confirm(self):
        self.popup.destroy()
        messagebox.showinfo(
            "Confirmed",
            f"Volatility adjustment for {self.maturity} has been applied.",
            parent=self.parent
        )
        
    def on_cancel(self):
        self.popup.destroy()
        messagebox.showinfo(
            "Cancelled",
            "No changes were made.",
            parent=self.parent
        )


# Example usage:
if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("800x600")
    
    # Sample data
    maturity = "1M"
    original_values = {"ATM": 14.4, "10D": 15.7, "25D": 14.0}
    new_values = {"ATM": 15.4, "10D": 16.7, "25D": 15.0}
    offset = 1.0
    
    def show_popup():
        VolatilityPopup(root, maturity, original_values, new_values, offset)
    
    ttk.Button(root, text="Show Popup", command=show_popup).pack(pady=20)
    
    root.mainloop()