talents = {

}

def onUse(user):
    user.healHP(10)

skills = {
    "Donut": {
        "Name": "Donut :3",
        "Cost": 4,
        "Target": "SingleEnemy",
        "Flavor": "Goku donuts {enemy}.",

        "Abilities": {
            # "event": "OnUse", 
            # "abilities": [], # Abilities can either be a function defined here or a name of an ability
            # that's accessed in a global module later
            "OnUse": onUse,
        },

        "Dice": [
            {"type": "offense", "damageType": "pierce", "min": 20, "max": 20, "flavor": "GRIPS YOY TO DEATH"},
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
            {"type": "offense", "damageType": "blunt", "min": 1, "max": 20, "flavor": "GRIPS YOY TO DEATH"},
            {"type": "offense", "damageType": "pierce", "min": 1, "max": 20},
            {"type": "offense", "damageType": "slash", "min": 1, "max": 20}
        ]
    }
}