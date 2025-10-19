from django.contrib import admin

from votingapp.models import *

# Register your models here.
admin.site.register(VotingRules)
admin.site.register(Constitution)
admin.site.register(Users)
admin.site.register(Roles)
admin.site.register(ProvisionHistory)
admin.site.register(Category)
admin.site.register(AllowedAccess)
admin.site.register(RecognizedRegions)
admin.site.register(JudicialChallenges)
admin.site.register(TemporaryPosition)
admin.site.register(TransactionLog)