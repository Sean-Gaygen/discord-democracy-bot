import asyncio
import datetime
import discord
import typing
import zoneinfo

from discord.ext import tasks, commands
from TextFormatting import TextFormatting
from WebsiteHandler import WebsiteHandler
from VotingSys import VotingSys
from django_modles_shadow import *

from _init import *
from discord_ids import *

class Democracybot:

	funcListEntry = tuple[str, typing.Callable[[typing.Any, typing.Any], typing.Any], typing.Callable[[typing.Any, typing.Any], typing.Any]|None]

	#Pattern: function_key: (Text, text_formatting_function, resolve_function)
	functions: dict[str, funcListEntry] = dict()

	FUNCTION_TEXT = 0
	FUNCTION_TEXT_FORMATTING_FUNCTION = 1  # TODO make enum
	RESOLVE_FUNCTION = 2

	#discord objects
	schmuckserver: discord.Guild
	voting_booth_channel: discord.TextChannel
	judicial_review_channel: discord.TextChannel
	agenda_channel: discord.TextChannel
	rotunda_channel: discord.TextChannel
	warning_channel: discord.TextChannel
	voter_role: discord.Role
	judiciary_role: discord.Role
	high_role: discord.Role
	blessed_role: discord.Role

	#bot preamble
	intents: discord.Intents = discord.Intents.all()
	mentions: discord.AllowedMentions = discord.AllowedMentions.all()

	#main bot (subclass of discord.client) object.
	bot: commands.Bot = commands.Bot(command_prefix="~", intents=intents, allowed_mentions=mentions)

	#semaphores TODO add semaphore for heartbeat sequence...maybe
	RECONCILIATION_SEMAPHORE: asyncio.Semaphore = asyncio.Semaphore(value=1)

	#misc
	time_zone: zoneinfo.ZoneInfo = zoneinfo.ZoneInfo("America/New_York")

	
	@staticmethod
	def initialize() -> None:
		"""
			The entry point for the bot,
			
			All INTERNAL setup, I.E. Setup that doesn't require the Discord library, is done here
			
			This function is not to be confused with the on_ready function, which does all the discord realated setup
		"""

		Democracybot.functions = {
			'dissolve': ("dissolve the government.", TextFormatting.just_text, None),
			'add_amend': ("amend our constitution by adding the following:", TextFormatting.named_value1, Democracybot.add_constitution),
			'sub_amend': ("amend our constitution by removing amendment number:", TextFormatting.end_w_value1, Democracybot.sub_constitution),
			'add_resolution': ("enact the following resolution:", TextFormatting.named_value1, Democracybot.post_resolution),
		}

		VotingSys.initialize()
		TextFormatting.initialize(Democracybot.VOTER_ROLE_ID, VotingSys.rules.name_of_government, VotingSys.rules.name_of_judiciary)

		Democracybot.bot.run(TOKEN)
	

	@staticmethod
	@bot.event 
	async def on_error(event: str, *args, **kwargs) -> None: # type: ignore
		"""
			Override the discord handling so our reload code gets run.
		"""

		raise Exception


	@staticmethod
	async def reconcile_roles() -> None:
		"""
			Add all new roles to the database, then let VotingSys pull all the new role models.
			This does not gather the discord object of role, but the django database model for easy access.
			We also update our role models internally in case any changes have been made   
		"""

		async with Democracybot.RECONCILIATION_SEMAPHORE:

			Democracybot.judiciary_role = await Democracybot.schmuckserver.fetch_role(Democracybot.JUDICIARY_ROLE_ID)

			for role in await Democracybot.schmuckserver.fetch_roles():

				if role.id not in VotingSys.roles:

					role_to_add = Roles()

					role_to_add.role_id = str(role.id)
					role_to_add.name = role.name
					role_to_add.can_vote = True
					role_to_add.vote_fraction = 1.0
					role_to_add.is_political_party = False

					WebsiteHandler.add_role(role_to_add)

			VotingSys.get_roles()


	@staticmethod
	async def reconcile_users() -> None:
		"""
			Gather all new users and add them to the django database.

			Create up-to-date models of all users, and ensure the django database is up-to-date.

			Allow VotingSys to gather all user models for ease of access.

			This function does NOT gather the user (or member) discord object, instead using the django user model.
		"""
		async with Democracybot.RECONCILIATION_SEMAPHORE:

			users_to_update: list[Users] = []

			member: discord.Member
			async for member in Democracybot.schmuckserver.fetch_members():

				if member.id not in VotingSys.users:

					member_to_add: Users = Users()

					member_to_add.user_id = str(member.id)
					member_to_add.name = member.name
					member_to_add.can_vote = True
					member_to_add.vote_fraction = 1.0
					member_to_add.registered_at = TextFormatting.SCHMUCKSERVER_NAME
					member_to_add.is_god_king = False
					member_to_add.is_judiciary = any(True for justice in Democracybot.judiciary_role.members if member.id == justice.id)
					member_to_add.vetoes = 0
					member_to_add.money = 100

					WebsiteHandler.add_user(member_to_add)

				else:

					member_to_update: Users = Users()

					member_to_update.user_id = str(member.id)
					member_to_update.name = member.name
					member_to_update.is_judiciary = any(True for justice in Democracybot.judiciary_role.members if member.id == justice.id)

					users_to_update.append(member_to_update)

			WebsiteHandler.update_many_users(users_to_update)

			VotingSys.get_users()


	@staticmethod
	async def reconcile_constitution() -> None:
		"""
			Unlike the other reconciliation functions, this keep a discord channel up to date with the database.

			This allows the database to be edited, and the changes to propegate to the discord without having to restart the bot.

			This function is also responsible for posting unposted amendments, however this usually shouldn't be happening. Only during
			the first startup of the bot with an empty channel, or when amendments are added ad-hoc.
		"""

		async with Democracybot.RECONCILIATION_SEMAPHORE:

			full_constitution: typing.Iterable[Constitution] = WebsiteHandler.get_full_constitution()
			full_message_history: dict[int, discord.Message] = {msg.id: msg async for msg in Democracybot.rotunda_channel.history()}

			if full_constitution == []:

				return

			amendment: Constitution
			for amendment in full_constitution:

				if amendment.message_id != '':	# We need to post a new amendment.

					target_message: discord.Message = full_message_history[int(amendment.message_id)]

					amendment_text: str = TextFormatting.constitution_message(amendment)

					if target_message.content != amendment_text:

						await target_message.edit(content=amendment_text)

				else:  # We need to ensure an existing amendment is up-to-date.

					msg_text: str = TextFormatting.constitution_message(amendment)

					constitution_msg = await Democracybot.rotunda_channel.send(msg_text if not amendment.deprecated else f'~~{msg_text}~~')

					amendment.message_id = str(constitution_msg.id)

					WebsiteHandler.update_constitution(amendment)


	@staticmethod
	async def update_sequence() -> None:
		"""
			This acts as an unchanging entry point into the sequence of functions called during the "heartbeat" update cycle.

			All function in the sequence are async functions, yet they must not be run concurrently, as thay are likely to affect each other.
			Thus, we await each function at the end of another, to create a linear sequence of asynchronous functions.

			This function then acts as the starting point, no matter what functions may be added in the future.

			This also provided a convenient place in-code to store the actual sequence this function currently represents.

			Unlike reconciliation, the order in which these functions are run matters, thus we call each from within the other.
		"""

		# post_provisions -> resolve_constitutional_challenges -> resolve_polls

		await Democracybot.post_provisions()


	@staticmethod
	async def reconcile_payment() -> None:
		"""
			This function checks to see if it is a payday (every quarter moon (aka every week)), checks to see if a
			payment has been made today, then goes through the trouble of paying everybody.
		"""

		async with Democracybot.RECONCILIATION_SEMAPHORE:

			if moonPhaseQuarters.get_current_moon_quarter() != WebsiteHandler.get_last_payment_quarter():

				total_payed_out: int = 0

				user: Users
				for user in VotingSys.users.values():

					max_salary: int = VotingSys.rules.ubi_amount

					discord_user: discord.Member | None = Democracybot.schmuckserver.get_member(int(user.user_id))

					if discord_user is None:

						discord_user = await Democracybot.schmuckserver.fetch_member(int(user.user_id))
					
					discord_role: discord.Role
					for discord_role in discord_user.roles:
						
						role: Roles = VotingSys.roles[discord_role.id]

						if role.salary is not None:

							max_salary = max(max_salary, role.salary)
				
					user.money += max_salary
					total_payed_out += max_salary

					WebsiteHandler.update_user(user)

				income_payment: TransactionLog = TransactionLog(
					transaction_type = transactionType.INCOME_PAYMENT,
					transactor_id = str(Democracybot.DEMOCRACYBOT_USER_ID),
					# transacted_at = datetime.datetime.now(tz=Democracybot.time_zone).isoformat(),
					transaction_total = total_payed_out
				)
				
				WebsiteHandler.add_purchase_log(income_payment)


	@staticmethod
	async def _handle_lose_role(position: TemporaryPosition, send_msg: bool = False) -> None:

		user: discord.Member | None = Democracybot.schmuckserver.get_member(int(position.user_id))
		role: discord.Role | None = Democracybot.schmuckserver.get_role(int(position.role_id))

		if user is None: 

			user = await Democracybot.schmuckserver.fetch_member(int(position.user_id))
		
		if role is None:

			role = await Democracybot.schmuckserver.fetch_role(int(position.role_id))

		if send_msg:

			await user.send(f"I must unfortunately inform you that your subscription to {role.name} could not be reupped. You just don't have the schmuckmark.")

		await user.remove_roles(role)

		WebsiteHandler.delete_temporary_position(position)

	
	@staticmethod
	async def _handle_charged_money(position: TemporaryPosition) -> None:

		if int(position.role_id) == Democracybot.HIGH_ROLE_ID:  # TODO Figure out good way to generalize

			position.money_to_be_charged = WebsiteHandler.get_price_of_crack()

		user: Users | None = await Democracybot._get_internal_user(int(position.user_id))
		
		if int(position.role_id) not in VotingSys.roles:

			await Democracybot.reconcile_roles()

			if int(position.role_id) not in VotingSys.roles:

				await Democracybot.warning_channel.send(f"Could not get role {position.role_id} in reconcile temp positions")
				return
		
		role: Roles = VotingSys.roles[int(position.role_id)]

		if user is None:
			
			await Democracybot.warning_channel.send(f"Could not get user {position.user_id} in reconcile temp positions.")
			return
		
		if user.money != position.money_to_be_charged:

			await Democracybot._handle_lose_role(position, send_msg=True)
			return
			
		if position.money_to_be_charged is None:

			await Democracybot.warning_channel.send("Charge money temp position did not have money_to_be_charged attached.")
			return

		user.money -= position.money_to_be_charged

		if not isinstance(position.position_expires_at, datetime.datetime) or not isinstance(role.term_length_days, int):

			await Democracybot.warning_channel.send("object type mismatch while renewing paid temp position")
			return

		position.position_expires_at += timedelta(days=role.term_length_days)

		WebsiteHandler.update_user(user)
		WebsiteHandler.update_temporary_position(position)

	
	@staticmethod
	async def _handle_re_election(position: TemporaryPosition) -> None:

		pass # TODO implement
		

	@staticmethod
	async def reconcile_temporary_positions() -> None:
		"""
			This function pulls all expired temporary positions (as determined by the API call) and handles them
			accordingly.  TODO add descriptions of all handling methods
		"""

		async with Democracybot.RECONCILIATION_SEMAPHORE:

			position: TemporaryPosition
			for position in WebsiteHandler.get_updatable_temporary_positions():

				match position.action_when_expires:
				
					case positionExpiresOptions.LOSE_ROLE:

						await Democracybot._handle_lose_role(position)

					case positionExpiresOptions.CHARGED_MONEY:

						await Democracybot._handle_charged_money(position)

					case positionExpiresOptions.RE_ELECTION:

						await Democracybot._handle_re_election(position)


	@staticmethod
	async def post_provisions() -> None:
		"""
			Go through each unposted provision as returned by the API call, post the poll, and update the provision in the django database.

			There is a known bug where, after an indeterminate amount of hours running, the creation of the Poll object will fail. I suspect
			that this is the discord library experiencing a silenced internal error, as other functions break after this exception is thrown.
			
			This has been solved by the "run.py" file, which reloads this, and the discord libraries. That is why there is no try except clause
			implemented in this function. We want the exception to stop execution in this case, as it is caught by "run.py"
		"""

		provisions: typing.Iterable[ProvisionHistory] = WebsiteHandler.get_unposted_provisions()

		provision: ProvisionHistory
		for provision in provisions:

			func_details: Democracybot.funcListEntry = Democracybot.functions[provision.function_key]

			now: datetime.datetime = datetime.datetime.now(tz=Democracybot.time_zone)
			polls_open_for: datetime.timedelta = datetime.timedelta(hours=VotingSys.rules.poll_availability_hours)

			mes_text: str = func_details[Democracybot.FUNCTION_TEXT_FORMATTING_FUNCTION](func_details[Democracybot.FUNCTION_TEXT], provision)

			posting_poll: discord.Poll = discord.Poll(question=TextFormatting.POLL_TEXT, multiple=False, duration=polls_open_for)

			posting_poll.add_answer(text='Yae', emoji='✅')
			posting_poll.add_answer(text='Nay', emoji='❎')
			posting_poll.add_answer(text='Abstain', emoji='🤷')

			sent_msg: discord.Message = await Democracybot.voting_booth_channel.send(content=mes_text, poll=posting_poll)

			await sent_msg.pin(reason="New vote, pinning for easy access.")

			provision.proposed_at = now.isoformat()
			provision.polls_close_at = (now + polls_open_for).isoformat()
			provision.message_id = str(sent_msg.id)

			WebsiteHandler.update_provision(provision)

		await Democracybot.resolve_constitutional_challenges()
	
	
	@staticmethod
	async def _resolve_provision_challenge(
		challenge: JudicialChallenges, 
		is_constitutional: bool, 
		constitutional_votes: int,
		unconstitutional_votes: int
		) -> None:
		"""
			Helper method called by resolve_constitution_challenges to handle the logic for dealing with provisions determined to be
			unconstitutional.
		"""

		provision: ProvisionHistory | None = WebsiteHandler.get_provision(challenge.challenged_proposal_number)

		if provision is None:

			await Democracybot.warning_channel.send(f"RESOLVING UNCONSTITUTIONAL PROVISION, PROVISION #{challenge.challenged_proposal_number} NOT FOUND IN DB.")
			return
		
		message_to_send: str = TextFormatting.resolve_provision_message(provision.proposal_id, constitutional_votes, unconstitutional_votes, is_constitutional)

		provision.is_in_judicial_review = False
		challenge.is_active = False

		if is_constitutional:

			challenge.was_constitutional = True
		
		else:
			
			challenge.was_constitutional = False
			provision.polls_close_at = datetime.datetime.now(tz=Democracybot.time_zone).isoformat()
			provision.passed = False

			voting_message = await Democracybot.voting_booth_channel.fetch_message(int(provision.message_id))

			if not voting_message.poll is None and not voting_message.poll.is_finalized():

				await voting_message.end_poll()
			
			if voting_message.pinned:

				await voting_message.unpin(reason="Ruled unconstitutional, ending the poll.")

		WebsiteHandler.update_provision(provision)
		WebsiteHandler.update_judicial_challenge(challenge)

		await Democracybot.voting_booth_channel.send(message_to_send)

	
	@staticmethod
	async def _resolve_amendment_challenge(
		challenge: JudicialChallenges, 
		is_constitutional: bool, 
		constitutional_votes: int,
		unconstitutional_votes: int
		) -> None:
		"""
			Helper method called by resolve_constitution_challenges to handle the logic for dealing with amendments determined to be
			unconstitutional.
		"""

		amendment: Constitution | None = WebsiteHandler.get_constitution(challenge.challenged_proposal_number)

		if amendment is None:

			await Democracybot.warning_channel.send(f"RESOLVING UNCONSTITUTIONAL PAMENDMENT, AMENDMENT #{challenge.challenged_proposal_number} NOT FOUND IN DB.")
			return
		
		constitutional_message: str = f"Amendment #{amendment.amendment_number} has been ruled as constitutional, with {constitutional_votes} votes in favor of constitutionality, and {unconstitutional_votes} against. The amendment returns stronger, now only revocable by vote."
		unconstitutional_message: str = f"Amendment #{amendment.amendment_number} has been ruled as unconstitutional with {constitutional_votes} votes in favor of constitutionality, and {unconstitutional_votes} against. The amendment will immediately be revoked from our constitution. Democracy proceeds."
		
		message_to_send: str

		challenge.is_active = False

		if is_constitutional:

			challenge.was_constitutional = True

			message_to_send = constitutional_message

		else:

			await Democracybot.sub_constitution(str(amendment.amendment_number), '')  
			# We don't update the amendments database representation because sub_constitution handles this for us.
			challenge.was_constitutional = False

			message_to_send = unconstitutional_message
		
		WebsiteHandler.update_judicial_challenge(challenge)
		
		await Democracybot.voting_booth_channel.send(message_to_send)


	@staticmethod
	async def resolve_constitutional_challenges() -> None:
		"""
			Pull all open challenges from the django database, then check the vote total. If the total matches the number of judges
			(calculated in on_ready), tally the votes. React accordingly, and update the database model.
		"""

		judicial_challenges: typing.Iterable[JudicialChallenges] = WebsiteHandler.get_open_judicial_challenges()

		challenge: JudicialChallenges
		for challenge in judicial_challenges:

			judicial_message: discord.Message  = await Democracybot.judicial_review_channel.fetch_message(int(challenge.judicial_poll_id))
			judicial_poll: discord.Poll | None = judicial_message.poll

			if judicial_poll is None or judicial_poll.expires_at is None:  # We catch "expires_at is None" here as an error, as no uploaded poll should be stateless.

				await Democracybot.warning_channel.send(f"Judicial poll for poll id#{challenge.judicial_poll_id} was not found. Fix it.")
				continue

			is_closable: bool
			is_constitutional: bool
			constitutional_votes: int
			unconstitutional_votes: int

			tomorrow: datetime.datetime = datetime.datetime.now(tz=judicial_poll.expires_at.tzinfo) + datetime.timedelta(hours=24)

			is_closable, is_constitutional, constitutional_votes, unconstitutional_votes = await VotingSys.tally_challenge(challenge, judicial_poll)

			if not is_closable:
				
				if not challenge.pinged_for_last_day and judicial_poll.expires_at <= tomorrow:

					await judicial_message.reply(TextFormatting.judicial_challenge_ping(Democracybot.JUDICIARY_ROLE_ID))

					challenge.pinged_for_last_day = True
					WebsiteHandler.update_judicial_challenge(challenge)

				continue

			if not judicial_poll.is_finalized():

				await judicial_poll.end()
			
			if judicial_message.pinned:

				await judicial_message.unpin(reason="Decision is reached, poll ended.")

			if challenge.is_for_existing_amendment:

				await Democracybot._resolve_amendment_challenge(challenge, is_constitutional, constitutional_votes, unconstitutional_votes)

			else:

				await Democracybot._resolve_provision_challenge(challenge, is_constitutional, constitutional_votes, unconstitutional_votes)

		await Democracybot.resolve_polls()


	@staticmethod
	async def resolve_polls() -> None:
		"""
			Pull all resolvable provisions as determined by the API. use VotinSys to determine whether or not the provision should pass, then
			access the function list to dynamically enact the provision (should the provision have an effect, and the poll passed).
		"""

		provisions: typing.Iterable[ProvisionHistory] = WebsiteHandler.get_resolvable_provisions()
		
		provision: ProvisionHistory
		for provision in provisions:

			func_details: Democracybot.funcListEntry = Democracybot.functions[provision.function_key]
			message: discord.Message = await Democracybot.voting_booth_channel.fetch_message(int(provision.message_id))
			poll: discord.Poll | None = message.poll

			if poll is None:
				
				print("DISCORD ERROR: Poll not obtainable from message in resolve_polls!")
				continue

			message_to_send, did_pass = await VotingSys.resolve(provision, poll)

			provision.passed = did_pass

			if did_pass:

				resolve_func: typing.Callable[[typing.Any, typing.Any], typing.Any] | None = func_details[Democracybot.RESOLVE_FUNCTION]

				if resolve_func is not None:

					await resolve_func(provision.value1, provision.value2)
			
			if message.pinned:

				await message.unpin(reason="Poll window closed. Voting ended.")

			await message.reply(message_to_send)
			WebsiteHandler.update_provision(provision)


	@staticmethod
	async def add_constitution(value1: str, value2: str='') -> None:
		"""
			This is the fucntion tied to adding a new amendment to the constitution.
			
			value1 will be the text of the amendment, verbatim to how it was entered on the website.
			value2 is undefined.

			Amendment number are not an automatically updating field for a couple of reasons. So we use an API call to
			get the next appropriate number. Create a message in the voting booth, and use the new id to create a completed
			django database entry.
		"""

		new_constitution: Constitution = Constitution()
		new_constitution.amendment_text = value1

		new_constitution.amendment_number = WebsiteHandler.get_next_amendment_number()

		message = await Democracybot.rotunda_channel.send(TextFormatting.constitution_message(new_constitution))

		new_constitution.message_id = str(message.id)

		new_constitution.deprecated = False

		WebsiteHandler.add_constitution(new_constitution)
	

	@staticmethod
	async def sub_constitution(value1: str, value2: str='') -> None:
		"""
			This function retracts an amendment from the constitution. To do this, we do not delete it, but simply
			cross it off and update the django database entry.

			value1 will be the number (id) of the amendment that is to be revoked.
			value2 is undefined.

			Get the amendment that is to be gotten rid of, using the id#. Send a warning if this fails, as we can't restart
			the function (and expect the output to change) at this point in the process. Update the constitution text early,
			I.E. not waiting for a "reconcile" cycle, and then update the django database entry.
		"""

		target_constitution: Constitution | None = WebsiteHandler.get_constitution(amendment_number=int(value1))

		if target_constitution is None:

			await Democracybot.warning_channel.send(f"TARGET AMENDMENT NOT FOUND WHILE RETRACTING AMENDMENT NUMBET {value1}")
			return

		target_constitution.deprecated = True

		target_message: discord.Message = await Democracybot.rotunda_channel.fetch_message(int(target_constitution.message_id))

		await target_message.edit(content=TextFormatting.constitution_message(target_constitution))

		WebsiteHandler.update_constitution(target_constitution)


	@staticmethod
	async def post_resolution(value1: str, value2: str='') -> None:
		"""
			This simply posts the resolution in the agenda channel, to later be deleted by the God-King or a Judge.

			value1 is the text of the resolution.
			value2 is undefined.

			Simply posts the text in the appropriate channel.
		"""

		await Democracybot.agenda_channel.send(content=value1)


	@staticmethod
	@bot.event
	async def on_ready() -> None:
		"""
			This is an overridden discord.client event that is called when logging in and caching all guilds has completed.

			This is where we initialize all discord related values, such as the objects for textchannels and roles.
			Because we have to wait until this function completes until we can expect discord elements to work, we also run
			all initializations that require discord functionality in there, such as the reconciliation loop.
		"""

		print("on_ready called")

		schmuckserver_hold: discord.Guild | None = Democracybot.bot.get_guild(Democracybot.SCHMUCKSERVER_ID)

		assert schmuckserver_hold is not None

		Democracybot.schmuckserver = schmuckserver_hold

		voting_booth_channel_hold = await Democracybot.bot.fetch_channel(Democracybot.VOTING_BOOTH_ID)
		judicial_review_channel_hold = await Democracybot.bot.fetch_channel(Democracybot.JUDICIAL_REVIEW_ID)
		agenda_channel_hold = await Democracybot.bot.fetch_channel(Democracybot.AGENDA_ID)
		rotunda_channel_hold = await Democracybot.bot.fetch_channel(Democracybot.ROTUNDA_ID)
		warning_channel_hold = await Democracybot.bot.fetch_channel(Democracybot.WARNING_CHANNEL_ID)
		voter_role_hold: discord.Role | None = await Democracybot.schmuckserver.fetch_role(Democracybot.VOTER_ROLE_ID)
		judiciary_role_hold: discord.Role | None = await Democracybot.schmuckserver.fetch_role(Democracybot.JUDICIARY_ROLE_ID)
		high_role_hold: discord.Role | None = await Democracybot.schmuckserver.fetch_role(Democracybot.HIGH_ROLE_ID)
		blessed_role_hold: discord.Role | None = await Democracybot.schmuckserver.fetch_role(Democracybot.BLESSED_ROLE_ID)

		assert isinstance(voting_booth_channel_hold, discord.TextChannel) and \
				isinstance(judicial_review_channel_hold, discord.TextChannel) and \
				isinstance(agenda_channel_hold, discord.TextChannel) and \
				isinstance(rotunda_channel_hold, discord.TextChannel) and \
				isinstance(warning_channel_hold, discord.TextChannel) and \
				voter_role_hold is not None and \
				judiciary_role_hold is not None and \
				high_role_hold is not None and \
				blessed_role_hold is not None

		Democracybot.voting_booth_channel = voting_booth_channel_hold
		Democracybot.judicial_review_channel = judicial_review_channel_hold
		Democracybot.agenda_channel = agenda_channel_hold
		Democracybot.rotunda_channel = rotunda_channel_hold
		Democracybot.warning_channel = warning_channel_hold
		Democracybot.voter_role = voter_role_hold
		Democracybot.judiciary_role = judiciary_role_hold
		Democracybot.high_role = high_role_hold
		Democracybot.blessed_role = blessed_role_hold

		VotingSys.raw_number_of_judges = len(Democracybot.judiciary_role.members)

		VotingSys.number_of_judges = VotingSys.raw_number_of_judges + (0 if VotingSys.raw_number_of_judges & 1 else 1)

		print(f"There are {VotingSys.number_of_judges} acting judges, and {VotingSys.raw_number_of_judges} judges")

		Democracybot.post_and_resolve.start()
		Democracybot.reconcile.start()


	@staticmethod
	@bot.event
	async def on_message(msg: discord.Message) -> None:
		"""
			The only use for on_message here is to delete the message discord automatically sends
			when a poll closes. Results may not always align with this message, so we remove it for
			clarity.

			Overriding on_message for a bot object also remove the processing of commands, so we
			have to manually call for commands to be processed if we're not handling a system
			message.
		"""

		in_relevant_channels: bool = msg.channel.id in {Democracybot.VOTING_BOOTH_ID, Democracybot.JUDICIAL_REVIEW_ID}
		is_relevant_message_type: bool = msg.type in {discord.MessageType.poll_result, discord.MessageType.pins_add}

		if in_relevant_channels and is_relevant_message_type:

			await msg.delete()
		
		else:  # We know system messages can't be commands, so there's no need to run command processing on them.

			await Democracybot.bot.process_commands(msg)
		

	@staticmethod
	@bot.command()
	async def register(ctx: commands.Context[typing.Any], *_) -> None:
		"""
			Register a user to vote a recognized region. 

			The form of the request is "~register x" where x is the name of the region. Case insensitive.
		"""

		async with ctx.channel.typing():

			if len(ctx.message.content) > 10:

				message = ctx.message.content[10:]

			else:

				return

			region = message.lower().strip()

			response_msg: str
			user_id: int = ctx.author.id

			if not VotingSys.verify_registration(region):

				response_msg = TextFormatting.bad_region(region)

			else:

				response_msg = TextFormatting.registration(region)
				WebsiteHandler.register_voter(user_id, region)

			await ctx.message.reply(response_msg)


	@staticmethod
	@bot.command()
	async def notification(ctx: commands.Context[typing.Any], *_) -> None:
		"""
			Simply toggles whether a user has the role that gets pinged whenever an update is
			sent from Democracybot.
		"""

		async with ctx.channel.typing():

			member: discord.Member | discord.User = ctx.author
			response_msg: str

			if not isinstance(member, discord.Member):

				await Democracybot.warning_channel.send("NOTIFICATION COMMAND FAILED, USER RETURNED NOT MEMBER")
				return

			if not any(role.id == Democracybot.VOTER_ROLE_ID for role in member.roles):

				await member.add_roles(Democracybot.voter_role)
				response_msg = "You will now receive voting notifications."

			else:

				await member.remove_roles(Democracybot.voter_role)
				response_msg = "You will no longer receive voting notifications."

			await ctx.message.reply(response_msg)


	@staticmethod
	async def _adjust_party_membership(ctx: commands.Context[typing.Any], party_name: str, is_joining: bool) -> None:
		"""
			A generic function that will either add, or remove the specified party role form the invoking user.
		"""

		async with ctx.channel.typing():

			member: discord.Member | discord.User = ctx.author

			if not isinstance(member, discord.Member):

				await Democracybot.warning_channel.send("NOTIFICATION COMMAND FAILED, USER RETURNED NOT MEMBER")
				return

			has_role: bool = any(True for role in member.roles if role.name.lower() == party_name.lower())

			if is_joining and has_role:

				await ctx.message.reply("You are already a member of this party.")
				return

			elif not is_joining and not has_role:

				await ctx.message.reply("You are not a member of this party.")
				return

			party_role_model: Roles | None = WebsiteHandler.get_party_role_by_name(party_name)

			if party_role_model is None:
				await ctx.message.reply("No recognized party is using that name.")
				return

			party_role: discord.Role = await Democracybot.schmuckserver.fetch_role(int(party_role_model.role_id))

			if is_joining:

				await member.add_roles(party_role)
				await ctx.message.reply(f"Congratulations, you are now a proud member of {party_name}!")

			else:

				await member.remove_roles(party_role)
				await ctx.message.reply(f"Congratulations, you now a scornful ex-member of {party_name}!")


	@staticmethod
	@bot.command()
	async def join_party(ctx: commands.Context[typing.Any], *_) -> None:
		"""
			Allows a user to join any recognized political party.
			The format is "~join_party x" where x is the name of the desires party, case insensitive.
		"""

		pre_len: int = len("~join_party ")

		if len(ctx.message.content) <= pre_len:

			return

		party_name: str = ctx.message.content[pre_len:].strip().lower()

		await Democracybot._adjust_party_membership(ctx, party_name, True)


	@staticmethod
	@bot.command()
	async def leave_party(ctx: commands.Context[typing.Any], *_) -> None:
		"""
			Allows a user to leave any political party that they are a member of.
			The format is "~leave_party x" where x is the name of the desires party, case insensitive.
		"""

		pre_len: int = len("~leave_party ")

		if len(ctx.message.content) <= pre_len:

			return

		party_name: str = ctx.message.content[pre_len:].strip().lower()

		await Democracybot._adjust_party_membership(ctx, party_name, False)


	@staticmethod
	@bot.command()
	async def veto(ctx: commands.Context[typing.Any], *_) -> None:
		"""
			Allows users to attempt to veto any open provision.
			The format is "~veto x" where x is simply the provision number.
		"""

		if not isinstance(ctx.author, discord.Member):

			await Democracybot.warning_channel.send("VETO FAILED, RETURNED USER, NOT MEMBER")
			return

		async with ctx.channel.typing():

			pre_len = len("~veto ")

			if len(ctx.message.content) <= pre_len:

				return

			amendment_number_text: str = ctx.message.content[pre_len:].strip()

			if not amendment_number_text.isnumeric():

				await ctx.message.reply("You need to tell me what amendment number you want to veto.")
				return

			provision: ProvisionHistory | None = WebsiteHandler.get_provision(int(amendment_number_text))

			if provision is None:

				await ctx.message.reply(f"I could not find a proposal with the number {amendment_number_text}")
				return

			if not VotingSys.can_veto(ctx.author, provision):

				await ctx.message.reply("You're not allowed to veto this proposal. Democracy wins.")
				return

			provision_message: discord.Message = await Democracybot.voting_booth_channel.fetch_message(int(provision.message_id))
			
			if not provision_message.poll is None and not provision_message.poll.is_finalised():

				await provision_message.end_poll()

			provision.passed = False
			provision.polls_close_at = datetime.datetime.now(tz=Democracybot.time_zone).isoformat()

			WebsiteHandler.update_provision(provision)

			await ctx.message.reply("This proposal has been successfully vetoed. The poll is closed, and the proposal fails.")


	@staticmethod
	async def _unconstitutional_provision(ctx: commands.Context[typing.Any], provision_id: int) -> ProvisionHistory | None:
		"""
			A helper function to handle all operations specific to challenging a provision.
		"""
		
		provision: ProvisionHistory | None = WebsiteHandler.get_provision(provision_id)

		if provision is None:

			await ctx.message.reply(f"I couldn't find a \"provision #{provision_id}\".")
			return None

		if provision.has_been_challenged:

			await ctx.message.reply("Provisions may only be challenged once.")
			return None
		
		if provision.passed is not None:

			await ctx.message.reply("The voting period for this provision has ended. Get over it.")
			return None

		provision.has_been_challenged = True
		provision.is_in_judicial_review = True

		return provision


	@staticmethod
	async def _unconstitutional_amendment(ctx: commands.Context[typing.Any], amendment_id: int) -> Constitution | None:
		"""
			A helper function to handle all operations specific to challenging a constitutional amendment.
		"""

		amendment: Constitution | None = WebsiteHandler.get_constitution(amendment_id)

		if amendment is None:

			await ctx.message.reply(f"I couldn't find an \"amendment #{amendment_id}\".")
			return None

		if amendment.has_been_challenged:

			await ctx.message.reply("Amendments may only be challenged once.")
			return None
		
		amendment.has_been_challenged = True
		
		return amendment


	@staticmethod
	async def _unconstitutional_helper(ctx: commands.Context[typing.Any], is_for_amendment: bool) -> None:
		"""
			This is the backend function that challenges proposals or amendments.

			The functionality between the two is similar enough that it doesn't make sense to split this into two functions.
		"""

		pre_len = len("~unconstitutional_amendment ") if is_for_amendment else len("~unconstitutional_proposal ")

		if len(ctx.message.content) <= pre_len:

			return

		async with ctx.channel.typing():
			
			provision_id_text: str = ctx.message.content[pre_len:].lower().strip()
			target_id: int
			target_object: Constitution | ProvisionHistory | None

			if not provision_id_text.isnumeric():

				await ctx.message.reply(f"I don't believe {provision_id_text} is a valid provision.")
				return
			
			target_id = int(provision_id_text)
			
			if is_for_amendment:

				target_object = await Democracybot._unconstitutional_amendment(ctx, target_id)

			else:

				target_object = await Democracybot._unconstitutional_provision(ctx, target_id)
			
			if target_object is None:
				
				# await Democracybot.warning_channel.send("target object is none in unconstitutional helper.") This is expected behavior, such as for typos by users
				return

			judicial_poll: discord.Poll = discord.Poll(
				question="We trust you to be discerning.",
				duration=datetime.timedelta(hours=168)
			)

			judicial_poll.add_answer(text='Constitutional', emoji='✅')
			judicial_poll.add_answer(text='Unconstitutional', emoji='❎')

			judicial_poll_message: str = f"{'Amendment' if is_for_amendment else 'Provision'} #{target_id} has been challenged as unconstitutional. Is it?\nNOTE* the polls closes when the final vote is cast"
			judicial_review_message: discord.Message = await Democracybot.judicial_review_channel.send(content=judicial_poll_message ,poll=judicial_poll)

			original_proposer: str = target_object.proposed_by_name if isinstance(target_object, ProvisionHistory) else ''

			if not judicial_review_message.pinned:

				await judicial_review_message.pin()

			judicial_challenge: JudicialChallenges = JudicialChallenges(is_active=True,
																		challenged_proposal_number=target_id,
																		judicial_poll_id=str(judicial_review_message.id),
																		challenged_by_id=str(ctx.author.id),
																		original_proposer_name=original_proposer,
																		is_for_existing_amendment=is_for_amendment,
																		pinged_for_last_day=False
																		)
			
			# TODO This is kinda messy, find a way to clean it up.

			provision_message: str = f"Provision #{target_id} has been sent to judicial review. Until a decision is called, the provision will neither pass nor fail."
			amendment_message: str = f"Amendment #{target_id} has been sent to judicial review. This is the only time that amendment may be challenged."

			if is_for_amendment:

				if not isinstance(target_object, Constitution):

					await Democracybot.warning_channel.send("In unconstitutional, is_for_amendment is true, but the target_object was not of type Constitution.")
					return

				WebsiteHandler.update_constitution(target_object)

			else:

				if not isinstance(target_object, ProvisionHistory):

					await Democracybot.warning_channel.send("In unconstitutional, is_for_amendment is false, but the target_object was not of type ProvisionHistory.")
					return

				WebsiteHandler.update_provision(target_object)

			WebsiteHandler.add_judicial_challenge(judicial_challenge)

			await ctx.message.reply(amendment_message if is_for_amendment else provision_message)


	@staticmethod
	@bot.command()
	async def unconstitutional_proposal(ctx: commands.Context[typing.Any], *_) -> None:
		"""
			This command allows users to challenge proposals.

			The format is "~unconstitutional_proposal x"
			Where "x" is the number of the challenged proposal.
		"""

		await Democracybot._unconstitutional_helper(ctx, is_for_amendment=False)


	@staticmethod
	@bot.command()
	async def unconstitutional_amendment(ctx: commands.Context[typing.Any], *_) -> None:
		"""
			This command allows users to challenge amendments.

			The format is "~unconstitutional_amendment x"
			Where "x" is the number of the challenged amendment.
		"""
		
		await Democracybot._unconstitutional_helper(ctx, is_for_amendment=True)


	@staticmethod
	async def _get_internal_user(user_id: int) -> Users | None:
		"""
			Allows us to get a user with a built-in reconcile in case the get failed.
		"""

		if user_id not in VotingSys.users:

			await Democracybot.reconcile_users()

			if user_id not in VotingSys.users:

				await Democracybot.warning_channel.send(f"Failed to get user with id {user_id}")
				return None
		
		return VotingSys.users[user_id]


	@staticmethod
	@bot.command()
	async def send_money(ctx: commands.Context[typing.Any], *_) -> None:
		"""
			Allows a user to send schmuckmark to another user.
			Must be of the form "send_money u x"
			Where "u" is the USERNAME, I.E. NOT THEIR NAME WITHIN THE SERVER, THEIR DISCORD USERNAME.
			and "x" is the amount of schmuckmark to send.
		"""

		async with ctx.channel.typing():

			pre_len = len("~send_money u x")
			raw_split_message: list[str] = ctx.message.content.split(' ')

			if len(ctx.message.content) <= pre_len or len(raw_split_message) < 3:

				return
			
			from_user: Users | None = await Democracybot._get_internal_user(ctx.author.id)

			if from_user is None:

				return

			amount_to_send: int = int(raw_split_message[-1])
			
			to_user_name: str = ' '.join(raw_split_message[1:-1]).strip().lower()
			to_user_name = to_user_name.split('#')[0].strip() if '#' in to_user_name else to_user_name

			to_user: Users

			user: Users
			for user in VotingSys.users.values():

				if user.name.lower() == to_user_name:

					to_user = user
					break
			
			else:

				await ctx.message.reply(f"I know of no user by the name {to_user_name}.")
				return

				# TODO Consider adding a user reconcile here, in case the internal user dictionary is out of date
				# This does introduce a lot of additional execution time on this command, and also runs the risk
				# of adding a way for users to make money due to execution timing errors (if they call the function
				# again while reconciling, but now has a valid candidate, say, because they're fixing a typo).
				#
				# Could be mitigated by using a semaphore.

			if from_user.money < amount_to_send:

				await ctx.message.reply(f"Seems you lack the funds for this transaction. Try again when you're a little mmm richer.")
				return

			from_user.money -= amount_to_send
			to_user.money += amount_to_send

			WebsiteHandler.update_user(from_user)
			WebsiteHandler.update_user(to_user)

			await ctx.message.reply(TextFormatting.send_money_message(to_user.name, from_user.name, amount_to_send))

	
	@staticmethod
	@bot.command()
	async def balance(ctx: commands.Context[typing.Any], *_) -> None:
		"""
			Allows a user to check their balance of schmuckmark.
		"""

		async with ctx.channel.typing():
			
			calling_user: Users | None = await Democracybot._get_internal_user(ctx.author.id)

			if calling_user is None:  # TODO consider adding error message here.

				return

			await ctx.message.reply(f"You currently have {calling_user.money} schmuckmark in the bank.")
	

	@staticmethod
	@bot.command()
	async def buy_crack(ctx: commands.Context[typing.Any], *_) -> None:
		"""
			Allows users to buy crack-rock-cocaine with their hard-earned schmuckmark.
		"""

		async with ctx.channel.typing():

			buyer: Users | None = await Democracybot._get_internal_user(ctx.author.id)
			role: Roles = VotingSys.roles[Democracybot.HIGH_ROLE_ID]

			if buyer is None:  # TODO consider adding error message here.

				return
			
			if not isinstance(ctx.author, discord.Member):

				await Democracybot.warning_channel.send("author was instance of user, not member.")
				return

			if any(role.id == Democracybot.HIGH_ROLE_ID for role in ctx.author.roles):

				await ctx.message.reply("You're currently high, more crack would make you overdose. I don't need that heat.")
				return

			crack_price: int | None = WebsiteHandler.get_price_of_crack()

			if crack_price is None:

				await Democracybot.warning_channel.send("Crack price was none. Sad!")
				return

			if buyer.money < crack_price:

				await ctx.message.reply(f"HAH, nice one. You don't have the {crack_price} schmuckmark this crack costs. Loser.")
				return
			
			if role.term_length_days is None:

				await Democracybot.warning_channel.send("role.term_length is None.")
				return

			buyer.money -= crack_price

			temporary_position: TemporaryPosition = TemporaryPosition(
				user_id = str(ctx.author.id),
				role_id = str(Democracybot.high_role.id),
				is_elected_position = False,
				position_expires_at = (datetime.datetime.now(tz=Democracybot.time_zone) + timedelta(hours=role.term_length_days)).isoformat(),
				action_when_expires = positionExpiresOptions.LOSE_ROLE,
				money_to_be_charged = crack_price
			)

			purchase_log: TransactionLog = TransactionLog(
				transaction_type = transactionType.CRACK,
				transactor_id = str(ctx.author.id),
				# transacted_at = datetime.datetime.now(tz=Democracybot.time_zone).isoformat(),
				transaction_total = crack_price
			)

			await ctx.author.add_roles(Democracybot.high_role)

			WebsiteHandler.update_user(buyer)
			WebsiteHandler.add_temporary_position(temporary_position)
			WebsiteHandler.add_purchase_log(purchase_log)

			message: str = f"For a mere {crack_price}, your rightfully owed federal crack ration is given to you. Have fun."

			await ctx.message.reply(message)


	@staticmethod
	@bot.command()
	async def subscribe_to_crack(ctx: commands.Context[typing.Any], *_) -> None:
		"""
			Subscribes the user to perpetual crack purchases.
		"""

		return

		await ctx.invoke(Democracybot.bot.get_command('buy_crack'))
		

	@staticmethod
	@bot.command()
	async def bless(ctx: commands.Context[typing.Any], *_) -> None:
		"""
			Allows the pope to bless a specified user.
		"""

		async with ctx.channel.typing():

			if not isinstance(ctx.author, discord.Member):
				
				await Democracybot.warning_channel.send("author is user not member in bless.")
				return

			if not any(role.id == Democracybot.POPE_ROLE_ID for role in ctx.author.roles):

				await ctx.message.reply("The sentiment is nice and all, but only the pope may bless others.")
				return

			pre_len = len("~bless u")  # thank you, but I didn't sneeze

			if len(ctx.message.content) <= pre_len:

				return
			
			blessed_user_name: str = ctx.message.content[pre_len:].strip().lower()

			if blessed_user_name not in VotingSys.users_by_name:

				await Democracybot.reconcile_users()

				if blessed_user_name not in VotingSys.users_by_name:

					await Democracybot.warning_channel.send("Couldn't get user during blessing.")
					return

			blessed_user: Users = VotingSys.users_by_name[blessed_user_name]
			blessed_discord_user: discord.Member | None = Democracybot.schmuckserver.get_member(int(blessed_user.user_id))

			if blessed_discord_user is None:

				blessed_discord_user = await Democracybot.schmuckserver.fetch_member(int(blessed_user.user_id))

			if any(role.id == Democracybot.BLESSED_ROLE_ID for role in blessed_discord_user.roles):

				await ctx.message.reply("That user has already been blessed. Any more divine favor and they may be guaranteed a spot in Heaven. I don't need that heat.")
				return
			
			if not any(role.id == Democracybot.HIGH_ROLE_ID for role in blessed_discord_user.roles):

				await ctx.message.reply("That user has no crack to bless.")
				return

			temp_high: TemporaryPosition | None = WebsiteHandler.get_temporary_position(blessed_user.user_id, str(Democracybot.HIGH_ROLE_ID))
			
			if temp_high is None or isinstance(temp_high.position_expires_at, str):  # TBH this is caught here because I'm being lazy. TODO move this to separate error later.

				await Democracybot.warning_channel.send("Temporary high position was not obtained from the website.")
				return

			temp_high.position_expires_at += timedelta(days=2)

			blessing_temp_position: TemporaryPosition = TemporaryPosition(
				user_id=blessed_user.user_id,
				role_id=str(Democracybot.BLESSED_ROLE_ID),
				is_elected_position=False,
				position_expires_at=(datetime.datetime.now(tz=Democracybot.time_zone) + timedelta(days=1)).isoformat(),
				action_when_expires=positionExpiresOptions.LOSE_ROLE,
			)

			await blessed_discord_user.add_roles(Democracybot.blessed_role)

			WebsiteHandler.update_temporary_position(temp_high)
			WebsiteHandler.add_temporary_position(blessing_temp_position)


	@staticmethod
	@bot.command()
	async def check_crack_price(ctx: commands.Context[typing.Any], *_) -> None:  # TODO maintian a "shop" with current prices of all items.
		"""
			Allows a user to check the ever-fluctuating price of crack before they purchase.
		"""

		async with ctx.channel.typing():

			crack_price: int | None = WebsiteHandler.get_price_of_crack()

			if crack_price is None:

				await Democracybot.warning_channel.send("Get price of crack failed.")
				return

			await ctx.message.reply(f"The current price of crack is {crack_price} schmuckmark.")


	@staticmethod
	@tasks.loop(seconds=15)
	async def post_and_resolve() -> None:  # TODO rename
		"""
			The "heartbeat" function that regularly checks to see if any work has to be done.
		"""

		await Democracybot.update_sequence()


	@staticmethod
	@tasks.loop(hours=1)
	async def reconcile() -> None:
		"""
			This function allows the bot to automatically update its internal storage to reflect changes on discord, without
			the need for restarting.

			The only mutually exclusive operation is payday, since it needs users and roles to not be modified during execution
			Therefore, users, roles, and payday are controled using a semaphore
			The actual order of operation isn't necessarily important, but the shared resources should not be changing
			during operation, requiring controlled concurrency.
		"""

		await Democracybot.reconcile_users()
		await Democracybot.reconcile_roles()
		await Democracybot.reconcile_constitution()
		await Democracybot.reconcile_payment()
		await Democracybot.reconcile_temporary_positions()


if __name__ == '__main__':

	Democracybot.initialize()