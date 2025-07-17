class DMTools:
    def __init__(self, state):
        self.state = state
    
    def set_property(self, x, y, prop, value):
        cell = self.state.get_cell(x, y)
        if cell: cell.properties[prop] = value
    
    def add_entity(self, x, y, entity_type, **kwargs):
        cell = self.state.get_cell(x, y)
        if cell: cell.entities.append(Entity(entity_type, **kwargs))
    
    def describe_cell(self, x, y, text):
        self.set_property(x, y, "description", text)

    def add_overlay(self, x, y, primitive, **params):
        cell = self.state.get_cell(x, y)
        if not cell:
            return {"success": False, "message": "Invalid coordinates"}
        
        # Handle special primitive types
        if primitive == "blood":
            return self._add_blood_overlay(cell, params)
        elif primitive == "glow":
            return self._add_glow_overlay(cell, params)
        
        # Default primitive handling
        cell.overlays.append(Overlay(primitive, **params))
        return {"success": True, "message": f"Added {primitive} overlay"}
    
    def _add_blood_overlay(self, cell, params):
        size = params.get("size", 1.0)
        intensity = min(5, max(1, params.get("intensity", 3)))
        
        # Blood stain effect
        cell.overlays.append(Overlay("circle", 
            color=(150, 0, 0), 
            size=size * 0.8
        ))
        
        # Spatter effect based on intensity
        for _ in range(intensity * 2):
            cell.overlays.append(Overlay("circle", 
                color=(180, 10, 10), 
                size=size * random.uniform(0.1, 0.3),
                offset=(
                    random.uniform(-0.4, 0.4),
                    random.uniform(-0.4, 0.4)
                )
            ))
        
        return {"success": True, "message": "Added blood effect"}
    
    def _add_glow_overlay(self, cell, params):
        color = self._parse_color(params.get("color", "yellow"))
        intensity = min(10, max(1, params.get("intensity", 5)))
        
        # Add multiple concentric circles for glow effect
        for i in range(intensity):
            alpha = 150 - (i * 10)
            size = 1.0 + (i * 0.1)
            cell.overlays.append(Overlay("circle", 
                color=(*color, alpha),
                size=size
            ))
        
        return {"success": True, "message": "Added glow effect"}
    
    def _parse_color(self, color_input):
        """Convert color name or hex to RGB tuple"""
        if isinstance(color_input, tuple):
            return color_input
        
        colors = {
            "red": (255, 0, 0),
            "green": (0, 255, 0),
            "blue": (0, 0, 255),
            "yellow": (255, 255, 0),
            "purple": (128, 0, 128),
            "blood": (150, 0, 0),
            "poison": (0, 150, 0),
            "arcane": (100, 0, 200),
        }
        
        # Try to find by name
        if color_input.lower() in colors:
            return colors[color_input.lower()]
        
        # Try to parse hex
        if isinstance(color_input, str) and color_input.startswith("#"):
            try:
                hex_color = color_input.lstrip("#")
                return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
            except:
                pass
        
        # Default to white
        return (255, 255, 255)
