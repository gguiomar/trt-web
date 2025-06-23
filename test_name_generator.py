from utils.NameGenerator import NameGenerator

def test_name_generator():
    """Test the new NameGenerator functionality"""
    
    print("=== TESTING NEW NAME GENERATOR ===\n")
    
    # Test single name generation
    print("1. SINGLE NAME GENERATION:")
    for i in range(5):
        name = NameGenerator.generate_name()
        print(f"   {name}")
    
    # Test multiple options generation
    print(f"\n2. MULTIPLE OPTIONS GENERATION:")
    options = NameGenerator.generate_options(3)
    print(f"   Generated {len(options)} options:")
    for i, name in enumerate(options, 1):
        print(f"   {i}. {name}")
    
    # Test uniqueness
    print(f"\n3. UNIQUENESS TEST:")
    all_names = set()
    for _ in range(20):
        options = NameGenerator.generate_options(3)
        for name in options:
            all_names.add(name)
    
    print(f"   Generated {len(all_names)} unique names from 20 generations")
    print(f"   Sample names: {list(all_names)[:10]}")
    
    # Test format consistency
    print(f"\n4. FORMAT CONSISTENCY:")
    test_names = [NameGenerator.generate_name() for _ in range(10)]
    all_proper_format = True
    
    for name in test_names:
        # Check if name has no spaces and ends with a monkey type
        has_spaces = ' ' in name
        ends_with_monkey = any(name.endswith(monkey) for monkey in NameGenerator.MONKEY_TYPES)
        
        if has_spaces or not ends_with_monkey:
            all_proper_format = False
            print(f"   ❌ Invalid format: {name}")
        else:
            print(f"   ✅ Valid format: {name}")
    
    if all_proper_format:
        print(f"   ✅ All names follow the correct DescriptorMonkeyType format!")
    
    # Show statistics
    print(f"\n5. STATISTICS:")
    print(f"   Total descriptors: {len(NameGenerator.DESCRIPTORS)}")
    print(f"   Total monkey types: {len(NameGenerator.MONKEY_TYPES)}")
    print(f"   Total possible combinations: {len(NameGenerator.DESCRIPTORS) * len(NameGenerator.MONKEY_TYPES):,}")

if __name__ == "__main__":
    test_name_generator()
