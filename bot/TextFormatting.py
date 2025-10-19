import random
import string
import typing

from django_modles_shadow import *

class TextFormatting:

    VOTER_ROLE_ID: str

    proposal_interstitials: list[str] = [
        'proposes that we',
        'wants to',
        'would love it if we could',
        'demands that we immediately',
        'is gonna',
        'humbly requests with grace and aplomb that we wisely vote on whether or not we are thusly enacting the provision that we shalt',
        'claims that we simply must',
        'is pathetically clamoring to',
        'just won\'t stop shaking until we',
        'honestly couldn\'t care less whether or not we',
        '***NEEDS TO***',
        'would be bummed if we didn\'t',
        'wants to know if the voters are willing to',
        'is going on a hunger strike until we',
        'is holding their breath until we',
        'is secretly hoping that we actually don\'t',
        'thinks it would be awful nice if we would',
        'would trade us the world, if only we would',
        'will be bulldozing the rec-center, unless we',
        'will wheel and deal to ensure that we',
        'has been payed off by big-oil to convince us to',
        'is hiring lobbyists as we speak, to ensure that we',
        'is really gonna do it this time... anyway, lets',
        'wants to propose, despite their recent diagnoises, that we',
        'will genuinely revolt if we don\'t',
        'is suggesting, constitutional or not, that we',
        'proposes, in blantant disregard for the health of the union, that we',
        'is continuing with the next step of their psy-op; having us',
        ', having had a vision while lost in the desert, proposes that we',
        'in an attempt to raise schmuckmark for their reelection campaign, proposes that we',
        'e'
    ]

    #Website related constants
    POLL_TEXT: str = "I vote in relation to the above proposal."
    POLL_TEXT_LIMIT: int = 300

    #Constants that must be initialized on startup
    SCHMUCKSERVER_NAME: str = ""
    JUDICIARY_NAME: str = ""

    VOTE_ENUM_TO_TEXT: dict[voteEnum, str] = {
        voteEnum.YAE_ENUM: 'Yae',
        voteEnum.NAY_ENUM: 'Nay',
        voteEnum.ABSTAIN_ENUM: 'Abstain'
    }

    #Text constants

    @staticmethod
    def initialize(voter_role_id: int, server_name: str, judiciary_name: str):
        """
            This simply sets a couple of constants that democracy.py handles.
        """

        TextFormatting.VOTER_ROLE_ID = str(voter_role_id)
        TextFormatting.SCHMUCKSERVER_NAME = server_name.title()
        TextFormatting.JUDICIARY_NAME = judiciary_name.title()

    @staticmethod
    def registration(region: str) -> str:
        """
            The message sent when a user registers to vote.
        """

        return f"Congratulations, you are now a registered voter of {string.capwords(region)}."

    @staticmethod
    def bad_region(region: str) -> str:
        """
            The message sent when a user enters a region that is not in our database.
        """

        return f"{string.capwords(TextFormatting.SCHMUCKSERVER_NAME)} does not currently recognize {string.capwords(region)} as a sovereign state."

    @staticmethod
    def constitution_message(constitution: Constitution) -> str:
        """
            The precise formatting for constitutional amendments as posted in the discord channel.
        """

        ret_text: str =  f"{str(constitution.amendment_number)} - {constitution.amendment_text}"

        return ret_text if not constitution.deprecated else f"~~{ret_text}~~"

    @staticmethod
    def judicial_challenge_ping(judicial_role_id: int) -> str:
        """
            The message sent when a judicial challenge has been open for 6 days straight.
        """

        JUDICIAL_CHALLENGE_LAST_DAY_PING_MESSAGE: str = \
        f"<@&{judicial_role_id}>, this challenge has been open for 6 days, leaving one day left for the poll. This needs to be "\
        "decided immediately. Any judges that have no yet made their decision, please start a discussion to reach "\
        "a conclusion. If this hasn't been finalized by the time the poll closes, I'll break, and Sean doesn't want "\
        "to have to fix me."  # TODO find a way to move this outside of this function

        return JUDICIAL_CHALLENGE_LAST_DAY_PING_MESSAGE

    @staticmethod
    def vote_result_response(ec_votes: dict[str, list[int]], passed: bool, yae_total: int, nay_total: int, abstention_total: int) -> str:
        """
            This formats the message sent when a vote is closed.
        """

        introduction: str = f'<@&{str(TextFormatting.VOTER_ROLE_ID)}>, the tally is as follows:\n'
        regions: typing.Iterable[str] = [f'{string.capwords(region)}: YAE; {vote[voteEnum.YAE_ENUM]} NAY; {vote[voteEnum.NAY_ENUM]} ABSTENTION; {vote[voteEnum.ABSTAIN_ENUM]}' for region, vote in sorted(ec_votes.items())]
        totals: str = f'\nTotalling {yae_total} for Yae, {nay_total} for Nay, and {abstention_total} abstentions.'
        final_blurb: str = f"The provision {'passes!' if passed else 'fails.'}"

        return '\n'.join([introduction, *regions, totals, final_blurb])

    @staticmethod
    def just_text(text: str, provision: ProvisionHistory) -> str:
        """
            A text formatting function used in the function cluster for proposals from the website.
            This simply places relevant text at the end of the message. 
        """

        name: str = provision.proposed_by_name

        interstitial: str = random.choice(TextFormatting.proposal_interstitials)

        return f'<@&{str(TextFormatting.VOTER_ROLE_ID)}> proposal #{provision.proposal_id}:\n {name} {interstitial} {text}\n'

    @staticmethod
    def end_w_value1(text: str, provision: ProvisionHistory) -> str:
        """
            A text formatting function used in the function cluster for proposals from the website.
            This adds the specified text, and places value1 as a string after it. 
        """
        
        return f'{TextFormatting.just_text(text, provision)} {provision.value1}'
    
    @staticmethod
    def named_value1(text: str, provision: ProvisionHistory) -> str:
        """
            A text formatting function used in the function cluster for proposals from the website.
            This adds the specified text, and posts the name of the proposal before ending with value1.
        """

        name_blurb = f'\n{provision.value2.title()}:\n\n' if provision.value2 != '' else '\n'

        return f'{TextFormatting.just_text(text, provision)} {name_blurb} {provision.value1}'


    @staticmethod
    def send_money_message(to_user_name: str, from_user_name: str, amount_to_send: int) -> str:
        """
            Returns a string given the sender and recipient of money, called from send_money in Democracybot.
        """

        if to_user_name.lower() == 'puritansexdisaster2':

            return f"You have successfully sent {amount_to_send} shcmuckmark to our immortal God-King. Keep this up and your briberies may earn you something nice."

        elif to_user_name.lower() == 'quinten e. democracybot':

            return f"You have successfully sent {amount_to_send} schmuckmark to...me? Thanks! :^)."
        
        elif to_user_name.lower() == from_user_name.lower():

            return f"You have successfully sent {amount_to_send} schmuckmark to...yourself. Keep this up and the God-King will implement a transaction tax."
        
        return f"You have successfully sent {amount_to_send} schmuckmark to {to_user_name}. I'm sure they appreciate it."


    @staticmethod
    def resolve_provision_message(proposal_id: int, constitutional_votes: int, unconstitutional_votes: int, is_constitutional: bool) -> str:
        """
            This formats the message to be sent when judicial challenge closes.
        """

        constitutional_mes_end: str = 'The matter rests and voting resumes as normal.'
        unconstitutional_mes_end: str = 'The vote will be ended immediately and ruled as a failure. Democracy proceeds.'

        message_end: str = constitutional_mes_end if is_constitutional else unconstitutional_mes_end

        return f"Proposal #{proposal_id} has been ruled as {'constitutional' if is_constitutional else 'unconstitutional'}, with {constitutional_votes} votes in favor of constitutionality, and {unconstitutional_votes} against. {message_end} "
 