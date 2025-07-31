import unittest
import json
from unittest.mock import MagicMock

class TestWorldGeneration(unittest.TestCase):
    def setUp(self):
        # Create mock AI system
        self.mock_ai = MagicMock()
        self.mock_ai.process_prompt.return_value = json.dumps({
            "name": "Test Town",
            "description": "A quaint testing village",
            "features": ["Town square", "Market", "Inn"],
            "npcs": [{"name": "Test NPC", "role": "Mayor"}],
            "quest_hooks": ["Test quest hook"],
            "services": ["Inn", "Blacksmith"],
            "image_prompt": "Fantasy town"
        })
        
        # Create world builder with mock AI
        from dungeon_neo.world_builder import WorldBuilder
        self.builder = WorldBuilder(self.mock_ai)
        
        # Create mock location data
        self.location_data = {
            "name": "Test Town",
            "type": "town",
            "description": "A quaint testing village",
            "features": ["Town square", "Market", "Inn"],
            "npcs": [{"name": "Test NPC", "role": "Mayor"}],
            "quest_hooks": ["Test quest hook"],
            "services": ["Inn", "Blacksmith"],
            "image_prompt": "Fantasy town"
        }

    def test_location_generation(self):
        """Test generating a location"""
        # Added context parameter
        location = self.builder.generate(
            "location", 
            location_type="town",
            context="A small town in the testing kingdom"
        )
        
        # Verify basic structure
        self.assertIsInstance(location, dict)
        self.assertIn("name", location)
        self.assertIn("description", location)
        self.assertIn("features", location)
        self.assertIn("npcs", location)
        self.assertIn("quest_hooks", location)
        self.assertIn("services", location)
        self.assertIn("image_prompt", location)
        
        # Verify content
        self.assertEqual(location["name"], "Test Town")
        self.assertEqual(len(location["features"]), 3)
        self.assertEqual(len(location["npcs"]), 1)
        
        # Verify prompt was called
        self.mock_ai.process_prompt.assert_called_once()

    def test_npc_generation(self):
        """Test generating an NPC"""
        # Set specific response for NPC generation
        self.mock_ai.process_prompt.return_value = json.dumps({
            "name": "Eldrin",
            "role": "Blacksmith",
            "appearance": "Burly with soot-covered face",
            "personality": "Grumpy but kind-hearted",
            "motivation": "Protect his family",
            "secret": "Former adventurer",
            "relationships": {},
            "image_prompt": "Fantasy blacksmith"
        })
        
        # Added context parameter
        npc = self.builder.generate(
            "npc", 
            role="blacksmith", 
            location="Test Town",
            context="Local blacksmith in Test Town"
        )
        
        # Verify structure
        self.assertIsInstance(npc, dict)
        self.assertIn("name", npc)
        self.assertIn("role", npc)
        self.assertIn("appearance", npc)
        self.assertIn("personality", npc)
        self.assertIn("motivation", npc)
        self.assertIn("secret", npc)
        self.assertIn("relationships", npc)
        self.assertIn("image_prompt", npc)
        
        # Verify content
        self.assertEqual(npc["name"], "Eldrin")
        self.assertEqual(npc["role"], "Blacksmith")

    def test_quest_generation(self):
        """Test generating a quest"""
        # Set specific response for quest generation
        self.mock_ai.process_prompt.return_value = json.dumps({
            "name": "Rescue the Blacksmith's Daughter",
            "summary": "The blacksmith's daughter has been kidnapped by goblins",
            "objective": "Rescue her from the nearby caves",
            "rewards": ["Gold", "Special weapon"],
            "complications": ["Goblin chief is stronger than expected"],
            "connections": ["Main story arc"],
            "image_prompt": "Goblin cave rescue"
        })
        
        # Added location and context parameters
        quest = self.builder.generate(
            "quest", 
            quest_type="rescue",
            location="Test Town",
            context="Urgent rescue mission"
        )
        
        # Verify structure
        self.assertIsInstance(quest, dict)
        self.assertIn("name", quest)
        self.assertIn("summary", quest)
        self.assertIn("objective", quest)
        self.assertIn("rewards", quest)
        self.assertIn("complications", quest)
        self.assertIn("connections", quest)
        self.assertIn("image_prompt", quest)
        
        # Verify content
        self.assertEqual(quest["name"], "Rescue the Blacksmith's Daughter")
        self.assertEqual(len(quest["rewards"]), 2)

    def test_faction_generation(self):
        """Test generating a faction"""
        # Set specific response for faction generation
        self.mock_ai.process_prompt.return_value = json.dumps({
            "name": "The Iron Hand",
            "ideology": "Control through strength",
            "goals": ["Dominate the region", "Control trade routes"],
            "resources": ["Mercenaries", "Blackmail material"],
            "relationships": {"The Silver Circle": "Enemy"},
            "activities": ["Extortion", "Smuggling"],
            "image_prompt": "Shadowy organization"
        })
        
        # Added location and context parameters
        faction = self.builder.generate(
            "faction", 
            faction_type="thieves guild",
            location="Test Region",
            context="Secret criminal organization"
        )
        
        # Verify structure
        self.assertIsInstance(faction, dict)
        self.assertIn("name", faction)
        self.assertIn("ideology", faction)
        self.assertIn("goals", faction)
        self.assertIn("resources", faction)
        self.assertIn("relationships", faction)
        self.assertIn("activities", faction)
        self.assertIn("image_prompt", faction)
        
        # Verify content
        self.assertEqual(faction["name"], "The Iron Hand")
        self.assertEqual(len(faction["goals"]), 2)

    def test_invalid_entity_type(self):
        """Test handling of invalid entity types"""
        with self.assertRaises(ValueError) as context:
            self.builder.generate("invalid_type")
        self.assertEqual(str(context.exception), "Unknown entity type: invalid_type")

    def test_json_parsing_failure(self):
        """Test handling of invalid JSON response"""
        # Set invalid JSON response
        self.mock_ai.process_prompt.return_value = "This is not JSON"
        
        # Added context parameter
        result = self.builder.generate(
            "location", 
            location_type="town",
            context="Test context"
        )
        
        # Should return the string response
        self.assertEqual(result, "This is not JSON")

    def test_generation_with_context(self):
        """Test generation with context parameters"""
        self.builder.generate(
            "location", 
            location_type="city", 
            context="Capital of the kingdom"
        )
        
        # Verify prompt includes context
        prompt = self.mock_ai.process_prompt.call_args[0][0]
        self.assertIn("Capital of the kingdom", prompt)

    def test_image_generation_integration(self):
        """Test integration with image generation"""
        # Import and mock image generator
        from dungeon_neo.image_generator import ImageGenerator
        ImageGenerator.generate_image = MagicMock(return_value="https://example.com/image.jpg")
        
        # Generate with image request (added context parameter)
        location = self.builder.generate(
            "location", 
            location_type="town",
            context="Test town context"
        )
        location["image_url"] = ImageGenerator.generate_image(location["image_prompt"])
        
        # Verify image generation
        self.assertIn("image_url", location)
        self.assertEqual(location["image_url"], "https://example.com/image.jpg")
        ImageGenerator.generate_image.assert_called_with("Fantasy town")

if __name__ == "__main__":
    unittest.main(verbosity=2)