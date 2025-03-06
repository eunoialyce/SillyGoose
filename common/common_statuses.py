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

# BLEED
def bleedTick(**kwargs):
    battler = kwargs.get("owner")
    dmg = kwargs.get("status").Potency

    if battler and dmg:
        battler.takeDamage(dmg)

class Bleed(StatusEffect):
    def __init__(self):
        self.Events = {
            "OnDiceRoll": bleedTick
        }