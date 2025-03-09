import math

class StatusEffect:
    def __init__(self, stacks=1, name=None, type="Neutral", onApply=None, onExpire=None, events=None):
        self.Name = name
        self.Type = type
        self.Subject = None
        self.Listeners = []
        self.OnApply = onApply
        self.OnExpire = onExpire
        self.Stacks = stacks
        self.Events = events

    def apply(self, battler):
        if self.OnApply:
            self.OnApply(battler)

    def remove(self, battler):
        if self.OnExpire:
            self.OnExpire(battler)

# BLEED
class Bleed(StatusEffect):
    def __init__(self, stacks):
        super().__init__()
        self.Name = "Bleed"
        self.Type = "Ailment"
        self.Stacks = stacks
        self.Events = {
            "OnDiceRoll": self.bleedTick,
            "SceneEnd": self.bleedDecay
        }

    def bleedTick(self, dice):
        battler = dice.Owner
        if battler == self.Subject:
            dmg = self.Stacks
            print(f"{battler.Name} is bleeding out...")
            battler.takeDamage(dmg)

    def bleedDecay(self, scene):
        self.Stacks = math.floor(self.Stacks/2)
        print(f"Bleed on {self.Subject.Name} has decayed to {self.Stacks}.")

        if self.Stacks <= 0:
            self.Subject.StatusManager.remove(self.Name)