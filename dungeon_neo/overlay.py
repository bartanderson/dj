# File: dungeon_neo/overlay.py
class Overlay:
    def __init__(self, primitive, **params):
        self.primitive = primitive
        self.params = params
        
    def render(self, draw, x, y, cell_size):
        """Render the overlay on a given ImageDraw object"""
        # Convert cell coordinates to pixel coordinates
        x_pix = x * cell_size
        y_pix = y * cell_size
        
        if self.primitive == "circle":
            size = self.params.get("size", 1.0) * cell_size
            color = self.params.get("color", (255, 0, 0))
            draw.ellipse([
                x_pix + (cell_size - size)//2, 
                y_pix + (cell_size - size)//2,
                x_pix + (cell_size + size)//2,
                y_pix + (cell_size + size)//2
            ], fill=color)
            
        elif self.primitive == "text":
            text = self.params.get("content", "?")
            color = self.params.get("color", (255, 255, 255))
            size = self.params.get("size", 1.0)
            # Simple text rendering - would need font for better implementation
            draw.text(
                (x_pix + cell_size//4, y_pix + cell_size//4), 
                text, 
                fill=color
            )