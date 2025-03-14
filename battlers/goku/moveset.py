import common.common_statuses as CommonStatuses

def onUse(user):
    user.healHP(10)

def testFunc(**kwargs):
    target = kwargs.get("target")
    target.StatusManager.apply(CommonStatuses.Bleed(5))

skills = {
    "UltraInstinct": {
        "Name": "UltraInstinct",
        "Cost": 6,
        "Target": "None",
        "Flavor": "*dodges*",

        "Dice": [
            {"supertype": "defense", "type": "evade", "min": 99, "max": 99},
            {"supertype": "offense", "type": "blunt", "min": 10, "max": 20},
        ]
    },

    "Test": {
        "Name": "Test",
        "Cost": 6,
        "Target": "SingleEnemy",
        "Flavor": "*dodges*",

        "Dice": [
            {"supertype": "defense", "type": "block", "min": 99, "max": 99},
        ]
    },

    "Donut": {
        "Name": "Donut :3",
        "Cost": 4,
        "Target": "SingleEnemy",
        "Flavor": "Goku donuts {enemy}.",

        "Dice": [
            {"supertype": "offense", "type": "pierce", "min": 20, "max": 20,
             "abilities": {
                 "OnHit": testFunc
             }
            },
        ]
    },

    "GOKUBLAST": {
        "Name": "GOKU BLAST",
        "Target": "SingleEnemy",
        "Flavor": "Goku heals 10 HP then kills {enemy}.",

        "Abilities": {
            # "event": "OnUse", 
            # "abilities": [], # Abilities can either be a function defined here or a name of an ability
            # that's accessed in a global module later
            "OnUse": onUse,
        },

        "Dice": [
            {"supertype": "offense", "type": "blunt", "min": 20, "max": 20, "flavor": "GRIPS YOY TO DEATH"},
            {"supertype": "offense", "type": "pierce", "min": 20, "max": 20},
            {"supertype": "offense", "type": "slash", "min": 20, "max": 20}
        ]
    }
}