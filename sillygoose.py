import os
import random
import math
import time
import json
import importlib
import itertools

allies = []
enemies = []
basicStats = ["Hatred", "Fluency", "Solidarity", "Rationality", "Stability"]

class Dice:
    def __init__(self, min, max, type, damageType=None, flavor=None):
        self.Type = type
        self.DamageType = damageType
        self.Min = min
        self.Max = max
        self.Flavor = flavor

    def roll(self):
        result = random.randint(self.Min, self.Max)
        self.Result = result
        print(f"{self.DamageType} {self.Min}~{self.Max}, rolled {result}")
        return result

class Skill:
    def __init__(self, name, cost=0, abilities=None, diceList=None, flavor=None, target=None):
        self.Name = name
        self.Cost = cost
        self.FlavorText = flavor or f"You cast {self.Name}."
        self.Target = target or "SingleEnemy"
        self.Abilities = abilities or {}

        if diceList:
            self.DiceList = [Dice(**dice) for dice in diceList]

class Battler:
    def __init__(self, name, stats, skills=None, passives=None):
        self.Name = name
        self.Level = stats["level"]
        self.Tags = stats["tags"]
        self.DmgResist = stats["resistances"]

        # Set the basic stats from Hatred to Stability
        for basicStat in basicStats:
            setattr(self, basicStat, stats[str.lower(basicStat)])
        
        self.MaxHealth = math.floor(self.Solidarity * 2.5)
        self.MaxSanity = math.floor(self.Stability * 1.5)
        self.MaxRadiance = round(self.Rationality / 10)
        self.Health = self.MaxHealth
        self.Sanity = self.MaxSanity
        self.Radiance = self.MaxRadiance
        self.StatusEffects = {}
        self.ClashDice = []
        self.StoredDice = []
        
        self.Skills = {}
        self.Talents = {}

        if skills:
            for skillName, skillData in skills.skills.items():
                self.Skills[skillName] = Skill(
                    name=skillData["Name"],
                    abilities=skillData.get("Abilities"),
                    diceList=skillData.get("Dice"),
                    flavor=skillData.get("Flavor"),
                    target=skillData.get("Target")
                )

            self.Talents = skills.talents

        self.Passives = passives

    def die(self):
        print(f"{self.Name} perishes.")
        self.Faction.remove(self)

    def takeDamage(self, damage):
        self.Health -= damage
        print(f"{self.Name} took {damage} damage! {self.Health}/{self.MaxHealth}")

        if self.Health <= 0:
            self.die()
    
    def diceDamage(self, attacker, dice):
        damage = round((attacker.Hatred/10 + dice.Result) * self.DmgResist.get(dice.DamageType, 1))
        self.takeDamage(damage)

    def healHP(self, amount):
        self.Health = min(self.Health + amount, self.MaxHealth)
        print(f"Healed {self.Name} for {amount} HP. {self.Health}/{self.MaxHealth}")

    def useSkill(self, skill):
        self.Radiance -= skill.Cost

        target = skill.Target
        if target == "SingleEnemy":
            print("Which enemy will you target?")

            outGroup = allies if self in enemies else enemies
            for index, ally in enumerate(outGroup):
                print(f"{index}: {ally.Name}")
            
            targetIndex = int(input("Choose a target: "))
            target = outGroup[targetIndex]
            flavorText = skill.FlavorText.format(enemy=target.Name)
            print(flavorText)
            abilities = skill.Abilities

            if abilities.get("OnUse"):
                abilities["OnUse"](self)
            
            # CLASH LOGIC WOOOOOOOOO i hate this
            if len(target.ClashDice) > 0:
                for dice1, dice2 in itertools.zip_longest(skill.DiceList, target.ClashDice):
                    dice1Result = dice1 and dice1.roll()
                    dice2Result = dice2 and dice2.roll()

                    if dice1 and dice2:
                        if dice1Result > dice2Result:
                            print(f"{self.Name} wins the clash!")
                            target.diceDamage(self, dice1)
                        elif dice2Result > dice1Result:
                            print(f"{target.Name} wins the clash!")
                            self.diceDamage(target, dice2)
                        else:
                            print("It's a draw!")
                    elif dice1:
                        target.diceDamage(self, dice1)
                    elif dice2:
                        self.diceDamage(target, dice2)
                
                    input("Enter to proceed")

                
                self.ClashDice = []
                target.ClashDice = []
            else:
                interceptSkill = target.interceptInput()
                if interceptSkill:
                    self.ClashDice = skill.DiceList
                    target.useSkill(interceptSkill)
                else:
                    # Unopposed attack
                    for dice in skill.DiceList:
                        dice.roll()
                        target.diceDamage(self, dice)
                        input("Enter to proceed")

    def interceptInput(self):
        intercept = input(f"An attack is en route to {self.Name}. Will they intercept? Y for yes: ")
        if intercept.lower() == "y":
            return self.inputSkill()
    
    def inputSkill(self):
        print("Skills:")
        for skill in self.Skills:
            print(skill)

        userChoice = input("Choose a skill: ")

        if userChoice.lower() == "no":
            print("Nothing happened.")
            return None

        if userChoice in self.Skills:
            skill = self.Skills[userChoice]
            if self.Radiance >= skill.Cost:
                return skill
            else:
                print("Not enough Radiance T^T")
                self.inputSkill()
        else:
            print("That skill doesn't exist.")
            self.inputSkill()

    def turn(self):
        print(f"It's {self.Name}'s turn. What will they do?")
        selectSkill = self.inputSkill()
        self.useSkill(selectSkill)

def loadBattler(name):
    path = os.path.join(os.getcwd(), "battlers", name, "data.json")
    skillPath = f"battlers.{name}.skills"

    if os.path.exists(path):
        with open(path) as raw:
            data = json.load(raw)
            skillsLib = importlib.import_module(skillPath)
            newBattler = Battler(data["name"], data, skillsLib)
            print("Loaded", name, "successfully")
            return newBattler
    else:
        print("Your character doesn't exist yet silly :3")

def addAlly(ally: Battler):
    ally.Faction = allies
    allies.append(ally)

def addEnemy(enemy: Battler):
    enemy.Faction = enemies
    enemies.append(enemy)

def teamFlavor(teamList):
    finalString = ""
    for character in teamList:
        if character == teamList[0]:
            finalString += f"{character.Name}"
        elif character == teamList[-1]:
            finalString += f" and {character.Name}"
        else:
            finalString += f", {character.Name}"
    
    return finalString

turnOwner = None
def battle():
    print("Battle time!")
    print("Right,", teamFlavor(allies), "will strum with all their might against", teamFlavor(enemies) + "!")
    print("Rolling for initiative...")

    for battler in (allies + enemies):
        battler.Initiative = random.randint(1, battler.Fluency)
        print(f"{battler.Name} rolled a {battler.Initiative} for initiative!")

    allBattlers = sorted(allies + enemies, key=lambda x: x.Initiative)

    while len(allies) > 0 and len(enemies) > 0:
        # Scene Start
        for battler in allBattlers:
            battler.Radiance = battler.MaxRadiance

        for battler in allBattlers:
            battler.turn()
        
        # Scene End

print("Hiiii :3")
addAlly(loadBattler("goku"))
addEnemy(loadBattler("goku"))
battle()
#input("Press enter to close the program.")