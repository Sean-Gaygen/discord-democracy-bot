from astral import moon
import datetime
import typing
import enum
import zoneinfo

from django.db import models
from django.utils import timezone
from datetime import timedelta


class voteEnum(enum.IntEnum):

	YAE_ENUM = 0
	NAY_ENUM = 1
	ABSTAIN_ENUM = 2


class riggingEnum(enum.IntEnum):

	NOT_RIGGED = 0
	MUST_PASS = 1
	MUST_FAIL = 2


class votingStyle(enum.IntEnum):

	FIRST_PASS_THE_POST = 0
	APPROVAL = 1


class tieBreakingMethod(enum.IntEnum):

	COINFLIP = 0
	PASSES = 1
	FAILS = 2


class positionExpiresOptions(enum.IntEnum):

	LOSE_ROLE = 0
	CHARGED_MONEY = 1
	RE_ELECTION = 2


class transactionType(enum.IntEnum):

	INCOME_PAYMENT = 0
	CRACK = 1


class moonPhaseQuarters(enum.IntEnum):

	NEW_MOON = 0
	WAXING_HALF_MOON = 1
	FULL_MOON = 2
	WANING_HALF_MOON = 3


	@staticmethod
	def get_phase_by_date(date: datetime.datetime) -> 'moonPhaseQuarters':

		moon_phase: float = moon.phase(date)

		if 0 <= moon_phase < 7:

			return moonPhaseQuarters.NEW_MOON

		elif 7 <= moon_phase < 14:

			return moonPhaseQuarters.WANING_HALF_MOON
		
		elif 14 <= moon_phase < 21:

			return moonPhaseQuarters.FULL_MOON
		
		elif 21 <= moon_phase < 28:

			return moonPhaseQuarters.WANING_HALF_MOON
		
		else:

			return moonPhaseQuarters.NEW_MOON
	

	@staticmethod
	def get_current_moon_quarter() -> 'moonPhaseQuarters':

		return moonPhaseQuarters.get_phase_by_date(datetime.datetime.now(tz=zoneinfo.ZoneInfo("America/New_York")))


class VotingRules(models.Model):
	
	registration_cooldown_hours = models.SmallIntegerField()
	accepting_new_registrations = models.BooleanField()
	voting_style = models.PositiveSmallIntegerField()
	poll_availability_hours = models.SmallIntegerField()
	tiebreaking_method = models.PositiveSmallIntegerField()
	is_sending_notifications = models.BooleanField()
	is_electoral_college_active = models.BooleanField()
	name_of_government = models.TextField(default='')
	name_of_judiciary = models.TextField(default='')
	allowed_open_proposals = models.SmallIntegerField(default=10)
	ubi_amount = models.IntegerField(default=500)

	def get_poll_close_from_now(self):

		return timezone.now() + timedelta(hours=self.poll_availability_hours, seconds=16)
		# We add 16 seconds to account for the latency of the bot posting the poll.

	def __str__(self):

		return f"""Registration Cooldown = {self.registration_cooldown_hours}\n
New registrations are {'not' if self.accepting_new_registrations else ''} allowed\n
voting style = {self.voting_style}\n
poll availability period = {self.poll_availability_hours}\n
tiebreaking method = {self.tiebreaking_method}\n
is sending notification = {self.is_sending_notifications}\n
is EC active = {self.is_electoral_college_active}"""


class Constitution(models.Model):

	amendment_number = models.IntegerField(primary_key=True)
	amendment_text = models.TextField()
	message_id = models.TextField(default = '', blank=True)
	deprecated = models.BooleanField(default=False)
	has_been_challenged = models.BooleanField(default=False)

	def __str__(self):

		return f"{self.amendment_number}: {self.amendment_text} - Currently {'active' if not self.deprecated else 'inactive'}."


class Users(models.Model):

	user_id = models.TextField(primary_key=True)
	name = models.TextField()
	can_vote = models.BooleanField(default=True)
	vote_fraction = models.FloatField(default=1.0)
	registered_at = models.TextField(default="Schmuckserver")
	is_god_king = models.BooleanField(default=False)
	is_judiciary = models.BooleanField(default=False)
	vetoes = models.SmallIntegerField(default=0)
	money = models.IntegerField(default=0)

	def __str__(self):

		return f"""user_id = {self.user_id}\n
name = {self.name}\n
can_vote = {self.can_vote}\n
vote_fraction = {self.vote_fraction}\n
registration = {self.registered_at}\n
is_god_king = {self.is_god_king}"""


class Roles(models.Model):

	role_id = models.TextField(primary_key=True)
	name = models.TextField(default='gug')
	can_vote = models.BooleanField(default=True)
	vote_fraction = models.FloatField(default=1.0)
	is_political_party = models.BooleanField(default=False)
	is_elected_position = models.BooleanField(default=False)
	salary = models.IntegerField(default=0, null=True)
	term_length_days = models.IntegerField(default=14, null=True)

	def __str__(self):

		return f"""role_id = {self.role_id}\n
name = {self.name}\n
can_vote = {self.can_vote}\n
vote_fraction = {self.vote_fraction}"""


class ProvisionHistory(models.Model):

	proposal_id = models.AutoField(primary_key=True)
	proposed_at = models.DateTimeField(blank=True, null=True)
	proposed_by_name = models.TextField()
	message_id = models.TextField(blank=True)
	polls_close_at = models.DateTimeField()
	passed = models.BooleanField(blank=True, null=True)
	is_rigged = models.PositiveSmallIntegerField(default=0)  # 0: not rigged. 1: must pass, 2: must fail
	is_judge_vetoable = models.BooleanField(default=False)
	has_been_challenged = models.BooleanField(default=False)
	is_in_judicial_review = models.BooleanField(default=False)
	function_key = models.TextField()
	value1 = models.TextField(blank=True)
	value2 = models.TextField(blank=True)

	def __str__(self):

		return f"""{self.proposal_id} - {self.value2}; {self.value1}\n
proposed by {self.proposed_by_name}, closes at {self.polls_close_at}, {self.function_key}\n\n
{"open" if self.passed is None else "passed" if self.passed else "failed"}"""

	def is_open(self):

		return self.passed is None

	def awaiting_resolution(self):

		return self.polls_close_at < timezone.now() and self.is_open()
	

class Category(models.Model):

	id = models.AutoField(primary_key=True)
	words = models.TextField()
	follows = models.ForeignKey("self", on_delete=models.CASCADE, blank=True, null=True)  # TODO Remove and make sure nothing breaks
	function_key = models.TextField(blank=True)

	def __str__(self):

		return f"""id = {self.id} - {self.words}\n
follows = {self.follows.id if self.follows else "root"}\n
function_key = {self.function_key}"""


class AllowedAccess(models.Model):

	key = models.TextField()

	def __str__(self):
		return f"{self.key}"


class RecognizedRegions(models.Model):

	region_name = models.TextField(primary_key=True)
	is_recognized = models.BooleanField(default=True)

	def __str__(self):

		return f"{self.region_name}"


class JudicialChallenges(models.Model):

	is_active = models.BooleanField(default=True)
	was_constitutional = models.BooleanField(blank=True, null=True)
	challenged_proposal_number = models.IntegerField()
	challenged_by_id = models.TextField(default='1394740210947985458')  # Democracybot's ID
	original_proposer_name = models.TextField(default='Quinten E. Democracybot')
	judicial_poll_id = models.TextField()
	is_for_existing_amendment = models.BooleanField(default=False)
	pinged_for_last_day = models.BooleanField(default=False)

	def __str__(self):

		return f"{self.challenged_proposal_number} - is active {self.is_active}, was_constitutional {self.was_constitutional}, {'amendment' if self.is_for_existing_amendment else 'proposal'}"


class TemporaryPosition(models.Model):

	user_id = models.TextField()
	role_id = models.TextField()
	is_elected_position = models.BooleanField()
	position_expires_at = models.DateTimeField()
	action_when_expires = models.SmallIntegerField(default=0)
	last_election = models.DateTimeField(default=timezone.now, null=True)
	last_vote_of_no_confidence = models.DateTimeField(default=timezone.now, null=True)
	in_primary = models.BooleanField(default=False)
	in_election = models.BooleanField(default=False)
	money_to_be_charged = models.IntegerField(null=True)

	def is_time_for_election(self) -> bool:

		return not self.in_election and timezone.now() > self.position_expires_at

	def is_time_for_primary(self) -> bool:

		return not self.in_primary and not self.in_election and timezone.now() > (self.position_expires_at - timedelta(days=3))

	def can_vote_of_no_confidence(self) -> bool:

		return self.last_vote_of_no_confidence is not None and timezone.now() > (self.last_vote_of_no_confidence + timedelta(weeks=1))

	def __str__(self):

		return f"user: {self.user_id}, role: {self.role_id}, Expires at: {self.position_expires_at}, is elected position {self.is_elected_position}"


class TransactionLog(models.Model):

	transaction_type = models.IntegerField()
	transactor_id = models.TextField()
	transacted_at = models.DateTimeField(auto_now_add=True)
	transaction_total = models.IntegerField()

	def __str__(self):

		return f"{self.transaction_type, {self.transactor_id}, {self.transacted_at}, {self.transaction_total}}"


V = typing.TypeVar('V',
					VotingRules,
					Constitution,
					Users,
					Roles,
					ProvisionHistory,
					Category,
					AllowedAccess,
					RecognizedRegions,
					JudicialChallenges,
					TemporaryPosition,
					TransactionLog,
					)