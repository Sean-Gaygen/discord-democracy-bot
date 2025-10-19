from democracy import Democracybot
from django_modles_shadow import *
from TextFormatting import TextFormatting
from VotingSys import VotingSys
from WebsiteHandler import WebsiteHandler

new_const = Constitution()

new_const.amendment_number = 13
new_const.amendment_text = "gug"
new_const.deprecated = False

print(WebsiteHandler.get_constitution(5))