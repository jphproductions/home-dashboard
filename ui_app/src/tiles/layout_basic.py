"""Basic layout helpers (for testing, not used in main app)."""


def get_grid_layout(num_items: int, cols_per_row: int = 2):
    """
    Helper to calculate grid layout for tiles.
    
    Args:
        num_items: Number of items to arrange.
        cols_per_row: Number of columns per row.
    
    Returns:
        List of column counts per row.
    """
    rows = (num_items + cols_per_row - 1) // cols_per_row
    layout = [cols_per_row] * rows
    
    # Adjust last row if needed
    remainder = num_items % cols_per_row
    if remainder > 0:
        layout[-1] = remainder
    
    return layout
