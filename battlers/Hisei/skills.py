talents = {

}

skills = {
    "GreatswordRend": {
        "Name": "Greatsword Rend",
        "Cost": 10,
        "Target": "SingleEnemy",
        "Flavor": "Hisei grips her blade with both hands, bring two powerful and heavy slashes at {enemy}. The frigid touch of her blade freezes even the rainwater around the two. ",

        "Dice": [
            {"supertype": "offense", "type": "slash", "min": 8, "max": 16},
            {"supertype": "offense", "type": "slash", "min": 8, "max": 16}
        ]
    },

    "RavagingCrash": {
        "Name": "Ravaging Crash",
        "Cost": 15,
        "Target": "SingleEnemy",
        "Flavor": "valid crashout",

        "Abilities": {

        },

        "Dice": [
            {"supertype": "offense", "type": "slash", "min": 7, "max": 14},
            {"supertype": "offense", "type": "pierce", "min": 8, "max": 16},
            {"supertype": "defense", "type": "evade", "min": 5, "max": 10},
            {"supertype": "offense", "type": "slash", "min": 5, "max": 15},
            {"supertype": "offense", "type": "slash", "prefixes":["counter"], "min": 9, "max": 18}
        ]
    },

    "DDC": {
        "Name": "DiamondDustCrush",
        "Cost": 30,
        "Target": "SingleEnemy",
        "Flavor": "idk",

        "Dice": [
            {"supertype": "defense", "type": "evade", "min": 4, "max": 12},
            {"supertype": "offense", "type": "blunt", "min": 3, "max": 10},
            {"supertype": "offense", "type": "slash", "min": 5, "max": 12},
            {"supertype": "offense", "type": "slash", "min": 5, "max": 12},
            {"supertype": "offense", "type": "slash", "min": 5, "max": 12}
        ]
    }
}