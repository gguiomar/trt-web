import random
import sqlite3
import os

class NameGenerator:
    """
    Generates monkey-themed names for players who qualify for the leaderboard.
    Names are always in the format: DescriptorMonkeyType (e.g., "AgileCapuchin")
    """
    
    # Monkey species/types
    MONKEY_TYPES = [
        "Capuchin", "Macaque", "Baboon", "Tamarin", "Marmoset", "Gibbon", "Mandrill",
        "Howler", "Spider", "Squirrel", "Rhesus", "Langur", "Colobus", "Vervet",
        "Mangabey", "Proboscis", "Tarsier", "Lemur", "Bonobo", "Chimp", "Gorilla",
        "Orangutan", "Siamang", "Gelada", "Drill", "Patas", "Guereza", "Douc",
        "SnubNosed", "Woolly", "Uakari", "Saki", "Titi", "Muriqui", "Indri"
    ]
    
    # Combined descriptors (adjectives + titles) for more variety
    DESCRIPTORS = [
        # Adjectives that could describe monkeys or their behavior
        "Agile", "Clever", "Swift", "Nimble", "Curious", "Playful", "Wise", "Tricky",
        "Mischievous", "Acrobatic", "Daring", "Brave", "Mighty", "Noble", "Cunning",
        "Vigilant", "Energetic", "Vibrant", "Jovial", "Spirited", "Tenacious", "Keen",
        "Astute", "Perceptive", "Observant", "Resourceful", "Inventive", "Crafty",
        "Shrewd", "Witty", "Dexterous", "Adept", "Skilled", "Ageless", "Primal",
        # Titles or roles that could be assigned to monkeys
        "King", "Queen", "Captain", "Chief", "Master", "Guardian", "Watcher", "Scout",
        "Explorer", "Voyager", "Ranger", "Hunter", "Gatherer", "Sage", "Elder",
        "Sentinel", "Protector", "Champion", "Warrior", "Defender", "Seeker", "Tracker",
        "Pathfinder", "Navigator", "Adventurer", "Wanderer", "Nomad", "Traveler",
        "Acrobat", "Trickster", "Jester", "Mystic", "Oracle", "Seer", "Visionary"
    ]
    
    @classmethod
    def _get_existing_names(cls):
        """Get all existing custom display names from the database"""
        try:
            from utils.config import BASE_DIR
            db_path = os.path.join(BASE_DIR, 'logs', 'users.db')
            
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Get all custom display names (not default "Player_" names)
            cursor.execute("""
                SELECT display_name FROM users 
                WHERE display_name IS NOT NULL 
                AND display_name != '' 
                AND NOT display_name LIKE 'Player_%'
            """)
            
            existing_names = {row[0] for row in cursor.fetchall()}
            conn.close()
            
            return existing_names
        except Exception as e:
            print(f"Error getting existing names: {e}")
            return set()
    
    @classmethod
    def generate_name(cls, existing_names=None):
        """Generate a single monkey-themed name in format: DescriptorMonkeyType"""
        if existing_names is None:
            existing_names = set()
        
        # Generate name in format: DescriptorMonkeyType (no spaces)
        descriptor = random.choice(cls.DESCRIPTORS)
        monkey_type = random.choice(cls.MONKEY_TYPES)
        return f"{descriptor}{monkey_type}"
    
    @classmethod
    def generate_options(cls, count=3):
        """Generate multiple unique name options that aren't already taken"""
        existing_names = cls._get_existing_names()
        names = set()
        max_attempts = count * 50  # Safety limit to prevent infinite loops
        attempts = 0
        
        while len(names) < count and attempts < max_attempts:
            name = cls.generate_name(existing_names)
            if name not in existing_names:
                names.add(name)
            attempts += 1
        
        if len(names) < count:
            print(f"Warning: Could only generate {len(names)} unique names out of {count} requested")
        
        return list(names)
