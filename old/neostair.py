from dungeon_neo.generator_neo import DungeonGeneratorNeo

generator = DungeonGeneratorNeo({'add_stairs': 2})
generator.create_dungeon()

# Verify stairs were placed
assert len(generator.stairs) == 2
assert generator.stairs[0]['key'] in ['down', 'up']
assert generator.stairs[1]['key'] in ['down', 'up']
assert generator.stairs[0]['key'] != generator.stairs[1]['key']

# Verify cell flags using row/col instead of position
down_pos = (generator.stairs[0]['row'], generator.stairs[0]['col'])
up_pos = (generator.stairs[1]['row'], generator.stairs[1]['col'])
assert generator.cell[down_pos[0]][down_pos[1]] & generator.STAIR_DN
assert generator.cell[up_pos[0]][up_pos[1]] & generator.STAIR_UP