import os
import random
import math
import copy
import time
import json
import importlib
import itertools

allies = []
enemies = []
basicStats = ["Hatred", "Fluency", "Solidarity", "Rationality", "Stability"]

class Dice:
    def __init__(self, min, max, supertype, type="none", prefixes=None, flavor=None, owner=None):
        self.Supertype = supertype
        self.Type = type
        self.Min = min
        self.Max = max
        self.Prefixes = prefixes
        self.Flavor = flavor
        self.Owner = owner

    def roll(self):
        result = random.randint(self.Min, self.Max)
        # Fire OnDiceRoll event here
        self.Result = result
        print(f"{self.Type} {self.Min}~{self.Max}, rolled {result}")
        return result
    
    def diceDamage(self, target):
        damage = round((self.Owner.Hatred/10 + self.Result) * target.DmgResist.get(self.Type, 1))
        target.takeDamage(damage)
        return damage
    
    def clash(self, targetDice):
        selfResult = self.roll()
        targetResult = targetDice.roll()
        result = {}

        if selfResult > targetResult:
            print(f"{self.Owner.Name} wins the clash!")
            result["winner"] = self.Owner
            result["loser"] = targetDice.Owner
            result["damage"] = self.diceDamage(targetDice.Owner)
        elif targetResult > selfResult:
            print(f"{targetDice.Owner.Name} wins the clash!")
            result["winner"] = targetDice.Owner
            result["loser"] = self.Owner
            result["damage"] = targetDice.diceDamage(self.Owner)
        else:
            print("It's a draw!")

        return result

class Skill:
    def __init__(self, owner, name, cost=0, abilities={}, diceList=[], flavor=None, target=None):
        self.Name = name
        self.Owner = owner
        self.Cost = cost
        self.FlavorText = flavor or f"You cast {self.Name}."
        self.Target = target or "SingleEnemy"
        self.Abilities = abilities
        self.DiceList = diceList

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
                    owner = self,
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

    def healHP(self, amount):
        self.Health = min(self.Health + amount, self.MaxHealth)
        print(f"Healed {self.Name} for {amount} HP. {self.Health}/{self.MaxHealth}")

    def healSP(self, amount):
        self.Sanity = min(self.Sanity + amount, self.MaxSanity)
        print(f"Healed {self.Name} for {amount} Sanity. {self.Sanity}/{self.MaxSanity}")        

    def unopposed(self, target):
        # check for counter dice here
        while len(self.ClashDice) > 0:
            nextDice = self.ClashDice[0]
            if nextDice.Supertype == "offense":
                nextDice.roll()
                nextDice.diceDamage(target)
                self.ClashDice.pop(0)
            else:
                self.StoredDice.append(nextDice)
                print(f"Stored {nextDice.Type} {nextDice.Min}~{nextDice.Max} for future clashes.")
                self.ClashDice.pop(0)

            input("Enter to proceed")

    def resolveClash(self, target):
        while (len(self.ClashDice) > 0 and len(target.ClashDice) > 0):
            dice1 = self.ClashDice[0]
            dice2 = target.ClashDice[0]

            clashResult = dice1.clash(dice2)
            print(clashResult)

            # TODO: Make Evade and Counter dice recycle (aka not pop)
            winner = clashResult.get("winner")
            loser = clashResult.get("loser")

            self.ClashDice.pop(0)
            target.ClashDice.pop(0)

            input("Enter to proceed")

        self.unopposed(target)
        target.unopposed(self)

        self.ClashDice = []
        target.ClashDice = []
    
    def useSkill(self, skill: Skill, intercepting=None):
        self.Radiance -= skill.Cost

        target = self
        targetType = skill.Target
        
        # TODO: implement target types SingleAlly, AllAllies, AllEnemies, SingleBattler, AllBattlers
        # maybe split the TargetType into tuples like this?? ("Single", "Enemy")
        if intercepting:
            target = intercepting.Owner
        else:
            outGroup, target = None, None

            if targetType == "SingleEnemy":
                print("Which enemy will you target?")

                outGroup = allies if self in enemies else enemies

            if outGroup:
                for index, ally in enumerate(outGroup):
                    print(f"{index}: {ally.Name}")

                targetIndex = int(input("Choose a target: "))
                target = outGroup[targetIndex]

        flavorText = skill.FlavorText.format(enemy=target.Name)
        print(flavorText)
        
        abilities = skill.Abilities
        if abilities.get("OnUse"):
            abilities["OnUse"](self)
        
        self.ClashDice = [Dice(owner=self, **dice) for dice in skill.DiceList]

        # CLASH LOGIC WOOOOOOOOO i hate this
        if len(target.ClashDice) > 0:
            self.resolveClash(target)
        else:
            interceptSkill = target.interceptInput()
            if interceptSkill:
                target.useSkill(interceptSkill, skill)
            else:
                # Unopposed attack
                self.unopposed(target)

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

        if selectSkill:
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