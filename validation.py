from tkinter import ttk, messagebox
def edit_offset(self, maturity: str) -> None:
    """Enable editing of the offset value for a specific maturity."""
    cell = self.offset_cells[maturity]
    
    # Create a temporary validated entry
    entry = ttk.Entry(
        cell.master,
        validate="key",
        validatecommand=(cell.master.register(
            lambda proposed_value, m=maturity: self.validate_offset(proposed_value, m)
        , '%P'),
        font=("Arial", 10),
        justify=tk.CENTER
    )
    
    entry.insert(0, self.offset_entries[maturity].get())
    entry.grid(row=cell.grid_info()['row'], column=cell.grid_info()['column'], 
               sticky="nsew", padx=1, pady=1)
    entry.focus_set()
    
    def save_offset(event=None):
        if self.validate_offset(entry.get(), maturity):
            self.offset_entries[maturity].set(entry.get())
            self.update_offset_cell_color(maturity)
        entry.destroy()
    
    entry.bind("<Return>", save_offset)
    entry.bind("<FocusOut>", save_offset)

def validate_offset(self, proposed_value: str, maturity: str) -> bool:
    """Validate the offset value."""
    try:
        if proposed_value == "":
            return True
        float(proposed_value)
        return True
    except ValueError:
        return False