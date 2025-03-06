# BLEED
def bleedTick(**kwargs):
    battler = kwargs.get("owner")
    dmg = kwargs.get("status").Potency

    if battler and dmg:
        battler.takeDamage(dmg)

Bleed = {
    "OnDiceRoll": bleedTick
}