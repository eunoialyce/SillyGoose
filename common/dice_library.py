import random
from config import *

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