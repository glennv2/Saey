DOMAIN = "saey_pellet"

BURNER_STATES = {
    0x0000: "Off",
    0x0101: "Ignition starting",
    0x0102: "Ignition starting, load wood",
    0x0103: "Ignition starting, fire on",
    0x0104: "Ignition starting, fire on and vent",
    0x010A: "Fire on, wait for cooldown",
    0x0200: "Stove On, Clean",
    0x0201: "Stove On",
    0x0301: "Stove power off",
    0x0801: "Cooldown sequence 1",
    0x0802: "Cooldown sequence 2",
    0x1000: "Eco Idle",
    0x0401: "Turbo Mode",
}

ERROR_CODES = {
    1: "Ignition failure",
    2: "Defective suction",
    3: "Insufficient air intake",
    5: "Out of pellets",
    9: "Exhaust motor failure",
    14: "Overheating",
}