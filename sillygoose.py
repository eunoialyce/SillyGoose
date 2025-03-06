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

# abstract bullshit plstohelp
class Listener:
    def __init__(self, observer, event, callback):
        self.Observer = observer
        self.Event = event
        self.Callback = callback

class EventManager:
    def __init__(self):
        self.listeners = {}

    def listen(self, listener: Listener):
        event = listener.Event
        if event in self.listeners:
            self.listeners[event].append(listener)
        else:
            self.listeners[event] = [listener]

    def clean(self, listener: Listener):
        event = listener.Event
        if event in self.listeners:
            self.listeners[event].remove(listener)
            if not self.listeners[event]: #if the list is empty
                del self.listeners[event]

    def fire(self, event, *args, **kwargs):
        if event in self.listeners:
            for listener in self.listeners[event]:
                listener.Callback(*args, **kwargs)
maid = EventManager()

class StatusEffect:
    def __init__(self, name, duration, apply_effect, remove_effect=None):
        self.Name = name
        self.Duration = duration
        self.ApplyEffect = apply_effect
        self.RemoveEffect = remove_effect

    def apply(self, battler):
        self.ApplyEffect(battler)

    def remove(self, battler):
        if self.RemoveEffect:
            self.RemoveEffect(battler)

class Dice:
    def __init__(self, min, max, supertype, type="none", prefixes=[], abilities={}, flavor=None, owner=None):
        self.Supertype = supertype
        self.Type = type
        self.Min = min
        self.Max = max
        self.Prefixes = prefixes
        self.Abilities = abilities or {}
        self.Flavor = flavor
        self.Owner = owner

    # inspired by lor spaghetti, the Dice object could contain a list called diceBuffs that passives and other buffs
    # add dicts to, each with keys like "DmgMultiplier" or "ClashPower" and so on
    # and these methods could iterate through these buffs to apply them after firing the event

    def roll(self):
        result = random.randint(self.Min, self.Max)
        self.Result = result
        print(f"{self.Type} {self.Min}~{self.Max}, rolled {result}")

        # Fire OnDiceRoll event here
        maid.fire("OnDiceRoll", self)
        return self.Result
    
    def blockma(self, target, clashResult):
        maid.fire("OnBlock", self)

        # insert additional buffs to dmg here
        damage = clashResult["winner"].Result - clashResult["loser"].Result
        print(f"{self.Owner.Name} blocked {clashResult["loser"].Owner.Name}'s attack.")
        target.takeSanityDamage(damage)
        return damage

    def diceDamage(self, target, clashResult=None):
        initDamage = self.Result

        if clashResult:
            if clashResult.get("loser") and clashResult["loser"].Type == "block":
                initDamage =- clashResult["loser"].Result
                print(f"{self.Owner} broke through {clashResult['loser'].Owner}'s block.")

        if self.Flavor:
            print(self.Flavor.format(enemy=target.Name))
        
        damage = round((self.Owner.Hatred/10 + initDamage) * target.DmgResist.get(self.Type, 1))
        sanDamage = round(damage/2)
        target.takeDamage(damage)
        target.takeSanityDamage(sanDamage)

        if self.Abilities.get("OnHit"):
            self.Abilities["OnHit"](
                dice=self,
                target=target,
                clashResult=clashResult,
                damage=damage
            )

        return damage
    
    def clash(self, targetDice):
        selfResult = self.roll()
        targetResult = targetDice.roll()
        result = {}

        if selfResult > targetResult:
            print(f"{self.Owner.Name} wins the clash.")
            result["winner"] = self
            result["loser"] = targetDice
            #result["damage"] = self.diceDamage(targetDice.Owner)
        elif targetResult > selfResult:
            print(f"{targetDice.Owner.Name} wins the clash.")
            result["winner"] = targetDice
            result["loser"] = self
            #result["damage"] = targetDice.diceDamage(self.Owner)
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
        self.Abilities = abilities or {}
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
        print(f"{self.Name} took {damage} damage. {self.Health}/{self.MaxHealth}")

        if self.Health <= 0:
            self.die()

    def takeSanityDamage(self, damage):
        self.Sanity -= damage
        print(f"{self.Name} lost {damage} Sanity. {self.Sanity}/{self.MaxSanity}")

        if self.Health <= 0:
            print(f"{self.Name} was staggered!")

    def healHP(self, amount):
        self.Health = min(self.Health + amount, self.MaxHealth)
        print(f"Healed {self.Name} for {amount} HP. {self.Health}/{self.MaxHealth}")

    def healSP(self, amount):
        self.Sanity = min(self.Sanity + amount, self.MaxSanity)
        print(f"Healed {self.Name} for {amount} Sanity. {self.Sanity}/{self.MaxSanity}")        

    def evalClashResult(self, target, clashResult):
        winner = clashResult.get("winner")
        loser = clashResult.get("loser")

        if winner and loser:
            if winner.Supertype == "offense":
                winner.diceDamage(loser.Owner, clashResult)
            elif winner.Type == "block":
                winner.blockma(loser.Owner, clashResult)
            elif winner.Type == "evade":
                print(f"{winner.Owner.Name} evaded {loser.Owner.Name}'s attack.")
                winner.Owner.healSP(winner.Result)

                if loser.Supertype == "defense":
                    print("NO RECYLFCING")
                    winner.Owner.ClashDice.pop(0)
                
            if winner.Type != "evade" and not ("counter" in winner.Prefixes):
                winner.Owner.ClashDice.pop(0)
            # i hate unbreakables do not @ me
            loser.Owner.ClashDice.pop(0)
        else:
            # Draw and nothing happens
            self.ClashDice.pop(0)
            target.ClashDice.pop(0)

    def unopposed(self, target):
        # check for counter dice here
        while len(self.ClashDice) > 0:
            nextDice = self.ClashDice[0]

            # unopposed attack
            # checks for target's clash dice
            # genius!
            if (len(target.StoredDice) > 0 or len(target.ClashDice) > 0) and target.Health > 0:
                # this is going to cause so many inexplicable bugs
                # but i kind of dont care rn... fix only when it breaks
                target.ClashDice.extend(target.StoredDice)
                target.StoredDice.clear()

                targetDice = target.ClashDice[0]
                clashResult = nextDice.clash(targetDice)
                self.evalClashResult(target, clashResult)
            else:
                #target.ClashDice.clear()
                if nextDice.Supertype == "offense" and not ("counter" in nextDice.Prefixes):
                    if target.Health > 0:
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

            willContinue = False
            if "counter" in dice1.Prefixes:
                self.StoredDice.append(dice1)
                print(f"Stored {dice1.Type} {dice1.Min}~{dice1.Max} counter dice for later.")
                self.ClashDice.pop(0)
                willContinue = True

            if "counter" in dice2.Prefixes:
                target.StoredDice.append(dice2)
                print(f"Stored {dice2.Type} {dice2.Min}~{dice2.Max} counter dice for later.")
                target.ClashDice.pop(0)
                willContinue = True

            if willContinue:
                print('continued')
                continue

            if target.Health > 0:
                clashResult = dice1.clash(dice2)
                self.evalClashResult(target, clashResult)
            # TODO: Make Evade and Counter dice recycle (aka not pop)

            input("Enter to proceed")

        self.unopposed(target)
        target.unopposed(self)

        self.ClashDice.clear()
        target.ClashDice.clear()
    
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
                return self.inputSkill()
        else:
            print("That skill doesn't exist.")
            return self.inputSkill()
        
    def applyStatus(status: StatusEffect):
        if self.StatusEffects.get(status.Name):

    def turn(self):
        print(f"It's {self.Name}'s turn. What will they do?")
        selectSkill = self.inputSkill()

        if selectSkill:
            self.useSkill(selectSkill)

def loadBattler(name):
    path = os.path.join(os.getcwd(), "battlers", name, "data.json")
    skillPath = f"battlers.{name}.moveset"

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

    allBattlers = sorted(allies + enemies, key=lambda x: x.Initiative, reverse=True)
    global curScene
    curScene = 1

    while len(allies) > 0 and len(enemies) > 0:
        # Scene Start
        print(f"Scene {curScene} START")

        for battler in allBattlers:
            battler.Radiance = battler.MaxRadiance

        for battler in allBattlers:
            if battler.Health > 0:
                battler.turn()
        
        # Scene End
        input(f"Scene {curScene} END")
        curScene = curScene + 1

print("Hiiii :3")
addAlly(loadBattler("Hisei"))
goku = addEnemy(loadBattler("goku"))
addEnemy(goku)
print(True if [] else False)
battle()
#input("Press enter to close the program.")