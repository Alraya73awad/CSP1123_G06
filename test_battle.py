from battle import BattleBot, full_battle, CHARACTER_ITEMS

# Create two bots with base stats
bot1 = BattleBot(
    name="Alpha",
    hp=120,
    energy=100,
    proc=25,
    defense=15,
    speed=10,
    clk=8,
    luck=10,
    weapon_atk=5,
    weapon_type="melee",
    special_effect="Core Meltdown",
    items=[CHARACTER_ITEMS[0], CHARACTER_ITEMS[2]]  # Armor Plating + Regen Core
)

bot2 = BattleBot(
    name="Beta",
    hp=100,
    energy=100,
    proc=30,
    defense=10,
    speed=12,
    clk=9,
    luck=15,
    weapon_atk=7,
    weapon_type="ranged",
    special_effect="Time Dilation",
    items=[CHARACTER_ITEMS[1], CHARACTER_ITEMS[4]]  # Overclock Unit + Energy Recycler
)

# Run the battle
result = full_battle(bot1, bot2, arena="neutral")

# Print results
print("Winner:", result["winner"])
print("Alpha Points:", result["botA_points"])
print("Beta Points:", result["botB_points"])
print("\n--- Battle Log ---")
for entry_type, text in result["log"]:
    print(f"[{entry_type.upper()}] {text}")