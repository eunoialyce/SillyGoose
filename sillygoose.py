import os
import random
import math
import time
import json
import importlib
from functools import partial

import common.common_statuses as CommonStatuses
import common.event_manager as EventMod
from config import * # allies, enemies alongside stuff like Bloodfeast n shit

StatusEffect = CommonStatuses.StatusEffect

# abstract bullshit plstohelp
Listener = EventMod.Listener
EventManager = EventMod.EventManager

class StatusManager:
    def __init__(self, battler):
        self.Battler = battler
        self.StatusEffects = {}

    def apply(self, status):
        if self.StatusEffects.get(status.Name):
            # add logic or custom update functions for nonstackable statuses idk
            self.StatusEffects[status.Name].Stacks += status.Stacks
        else:
            status.Subject = self.Battler
            self.StatusEffects[status.Name] = status
            for eventName, callback in status.Events.items():
                newListener = Listener(status, eventName, callback)
                status.Listeners.append(newListener)
                maid.listen(newListener)
    
    def remove(self, status: str):
        if self.StatusEffects.get(status):
            print(status, "has expired.")
            
            for listener in status.Listeners:
                maid.clean(listener)

            del self.StatusEffects[status]

class ActionManager:
    def __init__(self, battler):
        self.Battler = battler

    def useSkill(self, skill, intercepting=None):
        battler = self.Battler
        battler.Radiance -= skill.Cost

        target = battler
        targetType = skill.Target
        
        # TODO: implement target types SingleAlly, AllAllies, AllEnemies, SingleBattler, AllBattlers
        # maybe split the TargetType into tuples like this?? ("Single", "Enemy")
        if intercepting:
            target = intercepting.User
        else:
            outGroup = None

            if targetType == "SingleEnemy":
                print("Which enemy will you target?")

                outGroup = allies if battler in enemies else enemies

            if outGroup:
                for index, ally in enumerate(outGroup):
                    print(f"{index}: {ally.Name}")

                targetIndex = int(input("Choose a target: "))
                target = outGroup[targetIndex]

        flavorText = skill.FlavorText.format(enemy=target.Name)
        print(flavorText)
        
        abilities = skill.Abilities
        if abilities.get("OnUse"):
            abilities["OnUse"](battler)
        
        battler.DiceManager.ClashDice.extend([Dice(owner=battler, **dice) for dice in skill.DiceList])

        # CLASH LOGIC WOOOOOOOOO i hate this
        if target.ClashDice:
            battler.DiceManager.resolveClash(target)
        else:
            interceptSkill = target.ActionManager.interceptInput()
            if interceptSkill:
                target.ActionManager.useSkill(interceptSkill, skill)
            else:
                # Unopposed attack
                battler.DiceManager.unopposed(target)

    def interceptInput(self):
        intercept = input(f"An attack is en route to {self.Battler.Name}. Will they intercept? Y for yes: ")
        if intercept.lower() == "y":
            return self.inputSkill()
    
    def inputSkill(self):
        battler = self.Battler

        print("Skills:")
        for skill in battler.Skills:
            print(skill)

        userChoice = input("Choose a skill: ")

        if userChoice.lower() == "no":
            print("Nothing happened.")
            return None

        if userChoice in battler.Skills:
            skill = battler.Skills[userChoice]
            if battler.Radiance >= skill.Cost:
                return skill
            else:
                print("Not enough Radiance T^T")
                return self.inputSkill()
        else:
            print("That skill doesn't exist.")
            return self.inputSkill()

    def turn(self):
        if (not allies) or (not enemies):
            return

        battler = self.Battler
        print(f"It's {battler.Name}'s turn. What will they do?")
        selectSkill = self.inputSkill()

        if selectSkill:
            self.useSkill(selectSkill)

class DiceManager:
    def __init__(self, battler):
        self.Battler = battler
        self.ClashDice = []
        self.StoredDice = []
    
    def storeDice(self, dice):
        self.StoredDice.append(dice)
        print(f"Stored {dice.Type} {dice.Min}~{dice.Max} for future clashes.")
        self.ClashDice.pop(0)

    def resolveClash(self, target):
        while self.ClashDice and target.ClashDice and self.Battler.canAct() and target.canAct():
            dice1 = self.ClashDice[0]
            dice2 = target.ClashDice[0]

            willContinue = False
            if "counter" in dice1.Prefixes:
                self.storeDice(dice1)
                willContinue = True

            if "counter" in dice2.Prefixes:
                target.DiceManager.storeDice(dice2)
                willContinue = True

            if willContinue:
                print('continued')
                continue

            if target.Health > 0:
                clashResult = dice1.clash(dice2)
                self.evalClashResult(target, clashResult)

            input("Enter to proceed")

        self.unopposed(target)
        target.DiceManager.unopposed(self.Battler)

        self.ClashDice.clear()
        target.ClashDice.clear()

    def unopposed(self, target):
        # check for counter dice here
        while self.ClashDice and self.Battler.canAct():
            nextDice = self.ClashDice[0]

            # unopposed attack
            # checks for target's clash dice
            # genius!
            if (target.StoredDice or target.ClashDice) and target.Health > 0:
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
                    self.storeDice(nextDice)

            input("Enter to proceed")

    # Might replace this function with a DiceBehavior class later so each individual dice can just
    # determine what their behavior is when they win or lose clashes, etc.
    def evalClashResult(self, target, clashResult):
        winner = clashResult.get("winner")
        loser = clashResult.get("loser")

        if winner and loser:
            if ("ranged" in loser.Prefixes) and not ("ranged" in winner.Prefixes):
                #ur a silly goose if you make ranged defense dice
                if winner.Type != "evade":
                    print(f"{winner.Name} parried {loser.Name}'s projectile.")
                else:
                    print(f"{winner.Name} evaded {loser.Name}'s projectile.")
            else:
                if winner.Supertype == "offense":
                    winner.diceDamage(loser.Owner, clashResult)
                elif winner.Type == "block":
                    winner.blockma(loser.Owner, clashResult)
                elif winner.Type == "evade":
                    if loser.Type != "evade":
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

        # Fire OnDiceRoll event here
        maid.fire("OnDiceRoll", self)
        print(f"{self.Type} {self.Min}~{self.Max}, rolled {self.Result}")
        return self.Result
    
    def blockma(self, target, clashResult):
        maid.fire("OnBlock", self)

        # insert additional buffs to dmg here
        damage = clashResult["winner"].Result - clashResult["loser"].Result
        print(f"{self.Owner.Name} blocked {clashResult["loser"].Owner.Name}'s attack.")
        target.takeSanityDamage(damage)
        return damage

    def diceDamage(self, target, clashResult=None):
        #logic for heavy dice here
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
            maid.fire("ClashWin", self)
            maid.fire("ClashLose", targetDice)
            #result["damage"] = self.diceDamage(targetDice.Owner)
        elif targetResult > selfResult:
            print(f"{targetDice.Owner.Name} wins the clash.")
            result["winner"] = targetDice
            result["loser"] = self
            maid.fire("ClashWin", targetDice)
            maid.fire("ClashLose", self)
            #result["damage"] = targetDice.diceDamage(self.Owner)
        else:
            print("It's a draw!")

        return result

class Skill:
    def __init__(self, user, name, cost=0, abilities=None, diceList=None, flavor=None, target=None, cooldown=None):
        self.Name = name
        self.User = user
        self.Cost = cost
        self.Cooldown = cooldown
        self.FlavorText = flavor or f"You cast {self.Name}."
        self.Target = target or "SingleEnemy"
        self.Abilities = abilities or {}
        self.DiceList = diceList or []
    
    def selectTarget(self):
        pass

class Passive:
    def __init__(self, owner, event, callback):
        self.Owner = owner
        self.Event = event
        self.Callback = partial(callback, self)
        self.Listener = Listener(self.Owner, self.Event, self.Callback)
        maid.listen(self.Listener)
    
    def disable(self):
        maid.clean(self.Listener)

class Battler:
    def __init__(self, name, stats, skills=None):
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
        self.StatusManager = StatusManager(self)
        self.DiceManager = DiceManager(self)
        self.ActionManager = ActionManager(self)

        self.StatusEffects = self.StatusManager.StatusEffects
        self.ClashDice = self.DiceManager.ClashDice
        self.StoredDice = self.DiceManager.StoredDice
        
        self.Skills = {}
        self.Talents = {}
        self.Passives = []

        if skills:
            for skillName, skillData in skills.skills.items():
                self.Skills[skillName] = Skill(
                    name=skillData["Name"],
                    user = self,
                    abilities=skillData.get("Abilities"),
                    diceList=skillData.get("Dice"),
                    flavor=skillData.get("Flavor"),
                    target=skillData.get("Target")
                )

            self.Talents = hasattr(skills, "talents") and skills.talents

            if hasattr(skills, "passives"):
                for eventName, callback in skills.passives.items():
                    newPassive = Passive(self, eventName, callback)
                    self.Passives.append(newPassive)

    def canAct(self):
        # logic for checking if a character can act
        if self.Health > 0 and self.Sanity > 0 and battleData["SkipScene"] != True:
            return True

    def die(self):
        print(f"{self.Name} perishes.")
        self.Faction.remove(self)

        for passive in self.Passives:
            passive.disable()

    def takeDamage(self, damage):
        self.Health -= damage
        print(f"{self.Name} took {damage} damage. {self.Health}/{self.MaxHealth}")

        if self.Health <= 0:
            self.die()

    def takeSanityDamage(self, damage):
        self.Sanity -= damage
        print(f"{self.Name} lost {damage} Sanity. {self.Sanity}/{self.MaxSanity}")

        if self.Sanity <= 0:
            print(f"{self.Name} was staggered!")

    def healHP(self, amount):
        self.Health = min(self.Health + amount, self.MaxHealth)
        print(f"Healed {self.Name} for {amount} HP. {self.Health}/{self.MaxHealth}")

    def healSP(self, amount):
        self.Sanity = min(self.Sanity + amount, self.MaxSanity)
        print(f"Healed {self.Name} for {amount} Sanity. {self.Sanity}/{self.MaxSanity}")

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
    print(f"Right, {teamFlavor(allies)} will strum with all their might against {teamFlavor(enemies)}!")
    print("Rolling for initiative...")

    for battler in (allies + enemies):
        battler.Initiative = random.randint(1, battler.Fluency)
        input(f"{battler.Name} rolled a {battler.Initiative} for initiative!")

    allBattlers = sorted(allies + enemies, key=lambda x: x.Initiative, reverse=True)
    global curScene

    while allies and enemies: # empty lists return false
        # Scene Start
        maid.fire("SceneStart", curScene)
        input(f"Scene {curScene} START")

        for battler in allBattlers:
            battler.Radiance = battler.MaxRadiance
            if battler.Sanity <= 0:
                battleData["Unstagger"].append(battler)

        for battler in allBattlers:
            if battler.canAct():
                battler.ActionManager.turn()
        
        # Scene End
        input(f"Scene {curScene} END")
        maid.fire("SceneEnd", curScene)

        for battler in allBattlers:
            battler.DiceManager.ClashDice.clear()
            battler.DiceManager.StoredDice.clear()
            print("Cleared all dice.")

            if battler in battleData["Unstagger"]:
                battler.Sanity = battler.MaxSanity

        battleData["SkipScene"] = False
        curScene = curScene + 1

print("Hiiii :3")
addAlly(loadBattler("Nobody"))
goku = loadBattler("goku")
addEnemy(goku)

battle()
#input("Press enter to close the program.")