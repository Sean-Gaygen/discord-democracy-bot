import discord
import random

from WebsiteHandler import WebsiteHandler
from TextFormatting import TextFormatting
from django_modles_shadow import *
from _init import *

class VotingSys:

	rules: VotingRules
	users: dict[int, Users] = dict()
	users_by_name: dict[str, Users] = dict()
	roles: dict[int, Roles] = dict()
	recognized_regions: dict[str, bool] = dict()
	raw_number_of_judges: int
	number_of_judges: int

	@staticmethod
	def initialize() -> None:
		"""
			Set all internal vairables, most pulled directly from the website.
		"""

		VotingSys.get_voting_rules()
		VotingSys.get_users()
		VotingSys.get_roles()
		VotingSys.get_recognized_regions()
		print("VotingSys initialized")


	@staticmethod
	def get_voting_rules() -> None:
		"""
			Pull Voting Rules from an API call.
		"""

		hold = WebsiteHandler.get_voting_rules()

		if type(hold) == VotingRules:

			VotingSys.rules = hold

		else:

			raise TypeError("get_voting_rules returned non VotingRules type.")


	@staticmethod
	def get_users() -> None:
		"""
			Pull all Users objects from the website
		"""

		users_hold: typing.Iterable[Users] | None = WebsiteHandler.get_users()

		# if users_hold == []:
		#
		# 	raise TypeError("get_users from website returned None.")  #TODO consider what we want done here, we may have nothing int the database

		for user in users_hold:

			VotingSys.users[int(user.user_id)] = user
			VotingSys.users_by_name[user.name.lower()] = user


	@staticmethod
	def get_roles() -> None:
		"""
			Pull all roles from the website.
		"""

		roles_hold:typing.Iterable[Roles] | None = WebsiteHandler.get_roles()

		# if roles_hold == []:
		#
		# 	raise TypeError("get_roles from website returned None.")

		for role in roles_hold:

			VotingSys.roles[int(role.role_id)] = role


	@staticmethod
	def get_recognized_regions():
		"""
			Pull all recognized regions from the website
		"""

		regions_hold = WebsiteHandler.get_recognized_regions()

		# if regions_hold == []:
		#
		# 	raise TypeError("get_roles from website returned None.")

		for region in regions_hold:

			VotingSys.recognized_regions[region.region_name] = region.is_recognized


	@staticmethod
	def may_vote(member_id: int) -> bool:

		user_allowed_to_vote: bool = VotingSys.users[member_id].can_vote
		# roles_allowed_to_vote: bool = all(VotingSys.roles[role_id].can_vote for role_id in VotingSys.users[member_id].roles.id)  # TODO Fix
		
		return user_allowed_to_vote
	

	@staticmethod
	def can_veto(member: discord.Member, provision: ProvisionHistory) -> bool:

		if member.id == 120020797480894464:  # TODO add to initialize

			return True

		return provision.proposed_by_name.lower() == member.name.lower()


	@staticmethod
	async def _tally_regional_votes(poll_answers: list[discord.PollAnswer]) -> dict[str, list[int]]:
		
		regional_votes: dict[str, list[int]] = dict()
		
		answer: discord.PollAnswer
		for answer in poll_answers:

			async for voter in answer.voters():

				region: str = VotingSys.users[voter.id].registered_at

				if region not in regional_votes:

					regional_votes[region] = [0, 0, 0]

				regional_vote_tuple = regional_votes[region]

				match answer.text.lower():

					case 'yae':

						regional_vote_tuple[voteEnum.YAE_ENUM] += 1 if VotingSys.may_vote(voter.id) else 0  # TODO roll may vote into single if statement.

					case 'nay':

						regional_vote_tuple[voteEnum.NAY_ENUM] += 1 if VotingSys.may_vote(voter.id) else 0

					case 'abstain':

						regional_vote_tuple[voteEnum.ABSTAIN_ENUM] += 1 if VotingSys.may_vote(voter.id) else 0
					
					case _:

						pass
		
		return regional_votes
	

	@staticmethod
	async def tally_votes(poll: discord.Poll) -> dict[str, list[int]]:
		
		# ec_votes: dict[str, [int, int]] = dict()

		regional_votes: dict[str, list[int]] = await VotingSys._tally_regional_votes(poll.answers)

		# for region, votes in regional_votes.items():
		#
		# 	tally: int = votes[YAE_ENUM] - votes[NAY_ENUM]
		#
		# 	if tally == 0:
		#
		# 		ec_votes[region] = VotingSys.tie_break()
		#
		# 	elif tally > 0:
		#
		# 		ec_votes[region] = YAE_ENUM
		#
		# 	elif tally < 0:
		#
		# 		ec_votes[region] = NAY_ENUM

		return regional_votes
	
	@staticmethod
	def tie_break() -> bool:
		
		match VotingSys.rules.tiebreaking_method:

			case tieBreakingMethod.COINFLIP:
			
				return random.choice([True, False])
				
			case tieBreakingMethod.PASSES:
				
				return True
				
			case tieBreakingMethod.FAILS:
			
				return False
				
		return False


	@staticmethod
	async def resolve(provision: ProvisionHistory, poll: discord.Poll) -> tuple[str, bool]:

		ec_votes: dict[str, list[int]] = await VotingSys.tally_votes(poll)
		did_pass: bool

		yae_total: int = sum(vote[voteEnum.YAE_ENUM] for vote in ec_votes.values())
		nay_total: int = sum(vote[voteEnum.NAY_ENUM] for vote in ec_votes.values())
		abstention_total: int = sum(vote[voteEnum.ABSTAIN_ENUM] for vote in ec_votes.values())

		if provision.is_rigged == riggingEnum.MUST_PASS:

			yae_total = nay_total + 1 if yae_total < nay_total else yae_total

		elif provision.is_rigged == riggingEnum.MUST_FAIL:

			nay_total = yae_total + 1 if nay_total < yae_total else nay_total

		vote_total: int = yae_total - nay_total

		if vote_total == 0:

			did_pass = VotingSys.tie_break()
		
		else:

			did_pass = vote_total > 0

		message: str = TextFormatting.vote_result_response(ec_votes, did_pass, yae_total, nay_total, abstention_total)

		return message, did_pass


	@staticmethod
	def verify_registration(region: str) -> bool:

		return region in VotingSys.recognized_regions and VotingSys.recognized_regions[region]
		
	
	@staticmethod
	async def tally_challenge(challenge: JudicialChallenges, judicial_poll: discord.Poll) -> tuple[bool, bool, int, int]:
		"""
			This handles the tallying of judicial votes, and determines if we have enough votes to close the poll.

			This used to be two separate functions, but both would have to iterate through every poll answer, due
			to dealing with recusals. Pulling a poll answer requires a slow Discord API call. Thus, it made more
			sense to gather all relevant information at the same time.

			returns a tuple containing:
			is_closable: bool, 				has enough votes to close the poll
			is_constitutional: bool, 		Whether or not the ruling is constitutional
			constitutional_votes: bool		the number of votes for constitutional
			unconstitutional_votes: bool	the number of voted for unconstitutional	
		"""

		constitutional_votes: int = 0
		unconstitutional_votes: int = 0
		has_recusal: bool = VotingSys.users_by_name[challenge.original_proposer_name.lower()].is_judiciary

		answer: discord.PollAnswer
		for answer in judicial_poll.answers:

			offset: int = 0

			judge: discord.Member | discord.User
			async for judge in answer.voters():

				if judge.name == challenge.original_proposer_name:

					offset = -1
					has_recusal = True

			if answer.text.lower() == 'constitutional': # TODO bad, make much better

				constitutional_votes += answer.vote_count + offset

			else:

				unconstitutional_votes += answer.vote_count + offset
		
		required_votes: int

		if has_recusal:

			required_votes = VotingSys.raw_number_of_judges - 1 if (VotingSys.raw_number_of_judges - 1) & 1 else VotingSys.raw_number_of_judges
		
		else:
			
			required_votes = VotingSys.number_of_judges

		is_closable: bool = (constitutional_votes + unconstitutional_votes) >= required_votes
		is_constitutional: bool = constitutional_votes >= unconstitutional_votes
		
		return is_closable, is_constitutional, constitutional_votes, unconstitutional_votes