from astral import moon
import typing
import datetime
import enum
import zoneinfo
from datetime import timedelta
from dataclasses import dataclass


"""
	We want to make sure the discord bot is working with the same model object as the
	django database. The problem is, a discord bot is inherently asynchronous, and
	django is inherently synchronous. This could lead to major, difficult to diagnose
	bugs regarding databas access; so a discord bot can't use django models directly.

	The solution here is to maintain shadows of the django models, that mirror the 
	models exactly. That way, the website handler and django APIs can be constructed
	much more simply. This also provides linting and typechecking to the main discord
	bot.

	The only real catch is keeping the two in perfect pairity.

	NOTE* a value of "None" here maps to a value of "null" in the django database if 
	null is a valid option. 
"""


class websiteFunctionEnum(enum.IntEnum):

	FUNCTION_TEXT = 0
	FUNCTION_TEXT_FORMATTING_FUNCTION = 1
	RESOLVE_FUNCTION = 2


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

		if 0 <= moon_phase <= 6.99:

			return moonPhaseQuarters.NEW_MOON

		elif 7 <= moon_phase <= 13.99:

			return moonPhaseQuarters.WANING_HALF_MOON
		
		elif 14 <= moon_phase <= 20.99:

			return moonPhaseQuarters.FULL_MOON
		
		elif 21 <= moon_phase <= 27.99:

			return moonPhaseQuarters.WANING_HALF_MOON
		
		else:

			return moonPhaseQuarters.NEW_MOON
	

	@staticmethod
	def get_current_moon_quarter() -> 'moonPhaseQuarters':

		return moonPhaseQuarters.get_phase_by_date(datetime.datetime.now(tz=zoneinfo.ZoneInfo("America/New_York")))
		

@dataclass
class VotingRules:

	registration_cooldown_hours: int = None
	accepting_new_registrations: bool = None
	voting_style: votingStyle = None
	poll_availability_hours: int = None
	tiebreaking_method: tieBreakingMethod = None
	is_sending_notifications: bool = None
	is_electoral_college_active: bool = None
	name_of_government: str = None
	name_of_judiciary: str = None
	allowed_open_proposals: int = None
	ubi_amount: int = 500


@dataclass
class Constitution:
	
	amendment_number: int = None
	amendment_text: str = None
	message_id: str = None
	deprecated: bool = None
	has_been_challenged: bool = False


@dataclass
class Users:
	
	user_id: str = None
	name: str = None
	can_vote: bool = None
	vote_fraction: float = None
	registered_at: str = None
	is_god_king: bool = None
	is_judiciary: bool = None
	vetoes: int = None
	money: int = None


@dataclass
class Roles:
	
	role_id: str = None
	name: str = None
	can_vote: bool = None
	vote_fraction: float = None
	is_political_party: bool = None
	salary: int | None = None
	term_length_days: int | None = None


@dataclass
class ProvisionHistory:
	
	proposal_id: int = None
	proposed_at: datetime.datetime | str = None
	proposed_by_name: str = None
	message_id: str = None
	polls_close_at: datetime.datetime | str = None
	passed: bool | None = None
	is_rigged: riggingEnum = None
	is_judge_vetoable: bool = None
	has_been_challenged: bool = False
	is_in_judicial_review: bool = False
	function_key: str = None
	value1: str = None
	value2: str = None


@dataclass
class Category:

	id: int = None
	words: str = None
	follows: None = None  # This is a deprecated feature that would have been used in a more complex category system.
	function_key: str = None


@dataclass
class AllowedAccess:

	key: str = None


@dataclass
class RecognizedRegions:
	
	region_name: str = None
	is_recognized: bool = None


@dataclass
class JudicialChallenges:

	is_active: bool = True
	was_constitutional: bool = None
	challenged_proposal_number: int = None
	challenged_by_id: str = None
	original_proposer_name: str = None
	judicial_poll_id: str = None
	is_for_existing_amendment: bool = False
	pinged_for_last_day: bool = False


@dataclass
class TemporaryPosition:

	user_id: str = None
	role_id: str = None
	is_elected_position: bool = None
	position_expires_at: datetime.datetime | str = None
	action_when_expires: positionExpiresOptions = positionExpiresOptions.LOSE_ROLE
	last_election: datetime.datetime | str | None = None
	last_vote_of_no_confidence: datetime.datetime | str | None = None
	in_primary: bool = False
	in_election: bool = False
	money_to_be_charged: int | None = None

	def is_time_for_election(self) -> bool:

		return not self.in_election and datetime.datetime.now() > (self.last_election + timedelta(weeks=2))

	def is_time_for_primary(self) -> bool:

		return not self.in_primary and datetime.datetime.now() > (self.last_election + timedelta(weeks=1, days=5))
	
	def can_vote_of_no_confidence(self) -> bool:

		return datetime.datetime.now() > (self.last_vote_of_no_confidence + timedelta(weeks=1))


@dataclass
class TransactionLog:

	transaction_type: transactionType = None
	transactor_id: str = None
	transacted_at: datetime.datetime | str = None  # NO NEED TO SET IN CODE, THIS IS AN AUTO FIELD
	transaction_total: int = None
	

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
					TransactionLog
					)