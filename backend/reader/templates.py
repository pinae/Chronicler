"""One sentence template per predicate, used to phrase readout questions in plain language."""

PREDICATE_TEMPLATES = {
    "gives": "{who} gives {what} to {to}",
    "takes": "{who} takes {what}",
    "steals": "{who} steals {what} from {from}",
    "helps": "{who} helps {whom}",
    "harms": "{who} harms {whom}",
    "protects": "{who} protects {whom}",
    "saves": "{who} saves {whom}",
    "kills": "{who} kills {whom}",
    "trusts": "{who} trusts {whom}",
    "distrusts": "{who} distrusts {whom}",
    "promises": "{who} makes a promise to {whom}",
    "breaks": "{who} breaks with {whom}",
    "allies": "{who} allies with {whom}",
    "opposes": "{who} opposes {whom}",
    "learns": "{who} learns that {what}",
    "hides": "{who} hides {what}",
    "reveals": "{who} reveals {what}",
    "says": "{who} says that {what}",
    "believes": "{who} believes that {what}",
    "has": "{who} has {what}",
    "is_at": "{who} is at {where}",
    "is": "{who} is {trait}",
    "wants": "{who} wants {what}",
    "fears": "{who} fears {what}",
    "seeks": "{who} seeks {what}",
    "avoids": "{who} avoids {what}",
}

# Roles that name people when left unspecified ("someone"); every other role names a thing.
PERSON_ROLES = {"who", "whom", "to", "from"}
