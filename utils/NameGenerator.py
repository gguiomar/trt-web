import random

class NameGenerator:
    """
    Generates monkey-themed names for players who qualify for the leaderboard.
    """
    
    # Monkey species/types
    MONKEY_TYPES = [
        "Capuchin", "Macaque", "Baboon", "Tamarin", "Marmoset", "Gibbon", "Mandrill",
        "Howler", "Spider", "Squirrel", "Rhesus", "Langur", "Colobus", "Vervet",
        "Mangabey", "Proboscis", "Tarsier", "Lemur", "Bonobo", "Chimp", "Gorilla",
        "Orangutan", "Siamang", "Gelada", "Drill", "Patas", "Guereza", "Douc",
        "Snub-Nosed", "Woolly", "Uakari", "Saki", "Titi", "Muriqui", "Indri"
    ]
    
    # Adjectives that could describe monkeys or their behavior
    ADJECTIVES = [
        "Agile", "Clever", "Swift", "Nimble", "Curious", "Playful", "Wise", "Tricky",
        "Mischievous", "Acrobatic", "Daring", "Brave", "Mighty", "Noble", "Cunning",
        "Vigilant", "Energetic", "Vibrant", "Jovial", "Spirited", "Tenacious", "Keen",
        "Astute", "Perceptive", "Observant", "Resourceful", "Inventive", "Crafty",
        "Shrewd", "Witty", "Dexterous", "Adept", "Skilled", "Ageless", "Primal"
    ]
    
    # Titles or roles that could be assigned to monkeys
    TITLES = [
        "King", "Queen", "Captain", "Chief", "Master", "Guardian", "Watcher", "Scout",
        "Explorer", "Voyager", "Ranger", "Hunter", "Gatherer", "Sage", "Elder",
        "Sentinel", "Protector", "Champion", "Warrior", "Defender", "Seeker", "Tracker",
        "Pathfinder", "Navigator", "Adventurer", "Wanderer", "Nomad", "Traveler",
        "Acrobat", "Trickster", "Jester", "Mystic", "Oracle", "Seer", "Visionary"
    ]
    
    @classmethod
    def generate_name(cls):
        """Generate a single monkey-themed name"""
        name_type = random.choice([1, 2, 3])
        
        if name_type == 1:
            # Format: Adjective + Monkey Type (e.g., "Clever Capuchin")
            return f"{random.choice(cls.ADJECTIVES)} {random.choice(cls.MONKEY_TYPES)}"
        elif name_type == 2:
            # Format: Monkey Type + Title (e.g., "Gibbon Guardian")
            return f"{random.choice(cls.MONKEY_TYPES)} {random.choice(cls.TITLES)}"
        else:
            # Format: Adjective + Title (e.g., "Nimble Navigator")
            return f"{random.choice(cls.ADJECTIVES)} {random.choice(cls.TITLES)}"
    
    @classmethod
    def generate_options(cls, count=3):
        """Generate multiple unique name options"""
        names = set()
        while len(names) < count:
            names.add(cls.generate_name())
        return list(names)
