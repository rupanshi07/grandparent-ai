from database import create_tables, add_elder, get_elder, get_all_elders

print("=" * 50)
print("TESTING DATABASE")
print("=" * 50)

# Step 1 - Create tables
print("\n1. Creating tables...")
create_tables()

# Step 2 - Add a test elder
print("\n2. Adding test elder...")
elder = add_elder(
    name="Dadi Ji",
    phone="+918699303323",    # Replace with real number
    language="hindi",
    call_time="09:00",
    family_contacts=[
        {
            "name": "Son",
            "phone": "+918699303323",  # Replace with real number
            "priority": 1
        },
        {
            "name": "Daughter",
            "phone": "+918699303323",  # Replace with real number
            "priority": 2
        }
    ]
)

# Step 3 - Read it back
print("\n3. Reading elder from database...")
fetched = get_elder(elder.id)
print(f"   Name: {fetched.name}")
print(f"   Phone: {fetched.phone_number}")
print(f"   Language: {fetched.language}")
print(f"   Call time: {fetched.call_time}")
print(f"   Family contacts: {fetched.family_contacts}")
print(f"   Memory: {fetched.memory_summary}")

# Step 4 - Get all elders
print("\n4. Getting all elders...")
all_elders = get_all_elders()
print(f"   Total elders in database: {len(all_elders)}")
for e in all_elders:
    print(f"   - {e.name} ({e.phone_number})")

print("\n" + "=" * 50)
print("ALL DATABASE TESTS PASSED! ✓")
print("=" * 50)