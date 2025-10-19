import requests

from _init import *
from http import HTTPStatus
from django_modles_shadow import *

class WebsiteHandler:
    """
        This class is dedicated to implementing all API calls from the website. This class
        and django's views.py are developed closely together. Until better documentation is
        developed for the website's API, this file serves as the best documentation for how
        the API is meant to be interacted with.
    """

    BASE_URL: str = 'http://127.0.0.1:8000/voting/' if DEBUG else 'https://gaygen.com/voting/'
    GET_VOTING_RULES_URL: str = f'{BASE_URL}get_voting_rules'
    GET_CONSTITUTION_URL: str = f'{BASE_URL}get_constitution'
    GET_PROVISION_URL: str = f'{BASE_URL}get_provision'
    GET_USERS_URL: str = f'{BASE_URL}get_users'
    GET_ROLES_URL: str = f'{BASE_URL}get_roles'
    GET_RECOGNIZED_REGIONS_URL: str = f'{BASE_URL}get_recognized_regions'
    GET_TEMPORARY_POSITION_URL: str = f'{BASE_URL}get_temporary_position'
    GET_UPDATABLE_TEMPORARY_POSITIONS_URL: str = f'{BASE_URL}get_updatable_temporary_positions'
    GET_UNPOSTED_PROVISIONS_URL: str = f'{BASE_URL}get_unposted_provisions'
    GET_NEXT_AMENDMENT_NUMBER_URL: str = f'{BASE_URL}get_next_amendment_number'
    GET_RESOLVABLE_PROVISIONS_URL: str = f'{BASE_URL}get_resolvable_provisions'
    GET_OPEN_PROVISIONS_URL: str = f'{BASE_URL}get_open_provisions'
    GET_UNPOSTED_CONSTITUTIONS_URL: str = f'{BASE_URL}get_unposted_constitutions'
    GET_OPEN_JUDICIAL_CHALLENGES_URL: str = f'{BASE_URL}get_open_judicial_challenges'
    GET_FULL_CONSTITUTION_URL: str = f'{BASE_URL}get_full_constitution'
    GET_PARTY_ROLE_BY_NAME_URL: str = f'{BASE_URL}get_party_role_by_name'
    GET_PRICE_OF_CRACK_URL: str = f'{BASE_URL}get_price_of_crack'
    GET_LAST_PAYMENT_QUARTER_URL: str = f'{BASE_URL}get_last_payment_quarter'
    GET_DEBUG_INFLATION_URL: str = f'{BASE_URL}debug_inflation'
    UPDATE_PROVISION_URL: str = f'{BASE_URL}update_provision'
    UPDATE_CONSTITUTION_URL: str = f'{BASE_URL}update_constitution'
    UPDATE_USER_URL: str = f'{BASE_URL}update_user'
    UPDATE_MANY_USERS_URL: str = f'{BASE_URL}update_many_users'
    UPDATE_JUDICIAL_CHALLENGES_URL: str = f'{BASE_URL}update_judicial_challenge'
    UPDATE_TEMPORARY_POSITION_URL: str = f'{BASE_URL}update_temporary_position'
    ADD_CONSTITUTION_URL: str = f'{BASE_URL}add_constitution'
    ADD_ROLE_URL: str = f'{BASE_URL}add_role'
    ADD_USER_URL: str = f'{BASE_URL}add_user'
    ADD_JUDICIAL_CHALLENGE_URL: str = f'{BASE_URL}add_judicial_challenge'
    ADD_TEMPORARY_POSITION_URL: str = f'{BASE_URL}add_temporary_position'
    ADD_PURCHASE_LOG_URL: str = f'{BASE_URL}add_purchase_log'
    DELETE_TEMPORARY_POSITION_URL: str = f'{BASE_URL}delete_temporary_position'

    auth: dict[str, str] = {'auth_key': DB_KEY}  # TODO figure out how to make environment variables work on the website.


    @staticmethod
    def _generic_get_single(url: str, model_object: type[V], filter_dict: dict[str, typing.Any] = dict()) -> V | None:
        """
            A generic function to handle all get requests for a single item from the database.
        """

        response: requests.Response = requests.get(url, json=filter_dict | WebsiteHandler.auth)

        if response.status_code != HTTPStatus.OK:
            print(f"Get single resource failure {url}", response.status_code)
            return None

        return WebsiteHandler._json_to_object(response.json(), model_object())


    @staticmethod
    def _generic_get_multiple(url: str, model_object: type[V]) -> list[V]:
        """
            A generic function to handle all get requests for multiple items from the database
        """

        response: requests.Response = requests.get(url, json=WebsiteHandler.auth)

        if response.status_code != HTTPStatus.OK:

            if response.status_code != HTTPStatus.NO_CONTENT:

                print(f"Get multiple resource failure, {url}", response.status_code)

            return []

        entries: list[dict[str, typing.Any]] = response.json()['data']  # TODO make 'data' a constant in model_shadows.

        return WebsiteHandler._many_jsons_to_objects(entries, model_object)


    @staticmethod
    def _generic_post_request(url: str, model: V) -> bool:
        """
            A generic function to handle all post requests to the database.
        """

        payload_dict: dict[str, typing.Any] = model.__dict__

        for key, value in payload_dict.items():
            #I often forgot to change the value to isoformat when uploading models, so it's better to do that automatically here.
        
            if isinstance(value, datetime.datetime):
        
                payload_dict[key] = value.isoformat()

        return requests.post(url, json=(payload_dict | WebsiteHandler.auth)).status_code == HTTPStatus.NO_CONTENT


    @staticmethod
    def _json_to_object(json_dict: dict[str, typing.Any], model_object: V) -> V:
        """
            A helper function to easily convert JSON dictionaries to our database shadow objects.
        """

        for attribute, value in json_dict.items():

            setattr(model_object, attribute, value)

        return model_object


    @staticmethod
    def _many_jsons_to_objects(entries: list[dict[str, typing.Any]], model_object: type[V]) -> list[V]:
        """
            A helper function to handle JSONS that contain multiple objects.
        """

        return [WebsiteHandler._json_to_object(entry, model_object()) for entry in entries]


    @staticmethod
    def get_unposted_provisions() -> typing.Iterable[ProvisionHistory]:
        """
            Runs the website's API call to get all proposals that don't have a Discord message ID saved.
        """

        return WebsiteHandler._generic_get_multiple(WebsiteHandler.GET_UNPOSTED_PROVISIONS_URL, ProvisionHistory)


    @staticmethod
    def get_resolvable_provisions() -> typing.Iterable[ProvisionHistory]:
        """
            Runs the website's API call to get all proposals whose expiration date have passed, and are not in judicial review.
        """

        return WebsiteHandler._generic_get_multiple(WebsiteHandler.GET_RESOLVABLE_PROVISIONS_URL, ProvisionHistory)


    @staticmethod
    def get_voting_rules() -> VotingRules | None:
        """
            Runs the website's API call to get the current VotingRules
        """

        return WebsiteHandler._generic_get_single(WebsiteHandler.GET_VOTING_RULES_URL, VotingRules)


    @staticmethod
    def get_roles() -> typing.Iterable[Roles]:
        """
            Runs the website's API call to get all Roles.
        """

        return WebsiteHandler._generic_get_multiple(WebsiteHandler.GET_ROLES_URL, Roles)


    @staticmethod
    def get_users() -> typing.Iterable[Users]:
        """
            Runs the website's API call to get all Users.
        """

        return WebsiteHandler._generic_get_multiple(WebsiteHandler.GET_USERS_URL, Users)


    @staticmethod
    def get_full_constitution() -> typing.Iterable[Constitution]:
        """
            Runs the website's API call to get all amendments.
        """

        return WebsiteHandler._generic_get_multiple(WebsiteHandler.GET_FULL_CONSTITUTION_URL, Constitution)


    @staticmethod
    def get_constitution(amendment_number: int) -> Constitution | None:
        """
            Runs the website's API call to get an individual amendment.
        """

        filter_dict: dict[str, int] = {'amendment_number': amendment_number}

        return WebsiteHandler._generic_get_single(WebsiteHandler.GET_CONSTITUTION_URL, Constitution, filter_dict=filter_dict)


    @staticmethod
    def get_provision(proposal_id: int) -> ProvisionHistory | None:
        """
            Runs the website's API call to get an individual proposal.
        """

        filter_dict: dict[str, int] = {'proposal_id': proposal_id}

        return WebsiteHandler._generic_get_single(WebsiteHandler.GET_PROVISION_URL, ProvisionHistory, filter_dict=filter_dict)


    @staticmethod
    def get_open_provisions() -> typing.Iterable[ProvisionHistory]:
        """
            Runs the website's API call to get all proposals that have been posted, and are not closed.
        """

        return WebsiteHandler._generic_get_multiple(WebsiteHandler.GET_OPEN_PROVISIONS_URL, ProvisionHistory)


    @staticmethod
    def get_party_role_by_name(role_name: str) -> Roles | None:
        """
            Runs the website's API call to get a role object representing a political party, searching for it by it's name.
        """

        filter_dict: dict[str, str] = {'role_name': role_name}

        return WebsiteHandler._generic_get_single(WebsiteHandler.GET_PARTY_ROLE_BY_NAME_URL, Roles, filter_dict=filter_dict)


    @staticmethod
    def get_recognized_regions() -> typing.Iterable[RecognizedRegions]:
        """
            Runs the website's API call to get all recognized regions.
        """

        return WebsiteHandler._generic_get_multiple(WebsiteHandler.GET_RECOGNIZED_REGIONS_URL, RecognizedRegions)


    @staticmethod
    def get_unposted_constitutions() -> typing.Iterable[Constitution]:
        """
            Runs the website's API call to get all amendments that have not been posted to the discord channel.
        """

        return WebsiteHandler._generic_get_multiple(WebsiteHandler.GET_UNPOSTED_CONSTITUTIONS_URL, Constitution)


    @staticmethod
    def get_open_judicial_challenges() -> typing.Iterable[JudicialChallenges]:
        """
            Runs the website's API call to get all judicial challenges that have not been resolved.
        """

        return WebsiteHandler._generic_get_multiple(WebsiteHandler.GET_OPEN_JUDICIAL_CHALLENGES_URL, JudicialChallenges)


    @staticmethod
    def add_constitution(constitution: Constitution) -> bool:
        """
            Runs the website's API call to add a constitutional amendment.
        """

        return WebsiteHandler._generic_post_request(WebsiteHandler.ADD_CONSTITUTION_URL, constitution)


    @staticmethod
    def add_role(role: Roles) -> bool:
        """
            Runs the website's API call to add a role to the database.
        """

        return WebsiteHandler._generic_post_request(WebsiteHandler.ADD_ROLE_URL, role)


    @staticmethod
    def add_user(user: Users) -> bool:
        """
            Runs the website's API call to add a user to the database.
        """

        return WebsiteHandler._generic_post_request(WebsiteHandler.ADD_USER_URL, user)


    @staticmethod
    def add_judicial_challenge(challenge: JudicialChallenges) -> bool:
        """
            Runs the website's API call to add a judicial challenge to the database.
        """

        return WebsiteHandler._generic_post_request(WebsiteHandler.ADD_JUDICIAL_CHALLENGE_URL, challenge)


    @staticmethod
    def update_provision(provision: ProvisionHistory) -> bool:
        """
            Runs the website's API call to update a ProvisionHistory object in the database, given the object shadow.
        """

        return WebsiteHandler._generic_post_request(WebsiteHandler.UPDATE_PROVISION_URL, provision)


    @staticmethod
    def update_constitution(constitution: Constitution) -> bool:
        """
            Runs the website's API call to update a Constitution object in the database, given the object shadow.
        """

        return WebsiteHandler._generic_post_request(WebsiteHandler.UPDATE_CONSTITUTION_URL, constitution)


    @staticmethod
    def update_user(user: Users) -> bool:
        """
            Runs the website's API call to update a User object in the database, given the object shadow.
        """

        return WebsiteHandler._generic_post_request(WebsiteHandler.UPDATE_USER_URL, user)
    

    @staticmethod
    def update_many_users(users: typing.Iterable[Users]) -> bool:
        """
            Runs the website's API call to update multiple user objects in the database, given a list of object shadows.
        """

        payload: dict[str, typing.Any] = dict()

        payload['data'] = [user.__dict__ for user in users]

        return requests.post(WebsiteHandler.UPDATE_MANY_USERS_URL, json=(payload | WebsiteHandler.auth)).status_code == HTTPStatus.OK


    @staticmethod
    def update_judicial_challenge(challenge: JudicialChallenges) -> bool:
        """
            Runs the website's API call to update a judicialchallenge object in the database, given the object shadow.
        """

        return WebsiteHandler._generic_post_request(WebsiteHandler.UPDATE_JUDICIAL_CHALLENGES_URL, challenge)


    @staticmethod
    def register_voter(voter_id: int, region: str):
        """
            Runs the website's API call to update a user's registration region.
        """

        payload: Users = Users()

        payload.user_id = str(voter_id)
        payload.registered_at = region

        return WebsiteHandler._generic_post_request(WebsiteHandler.UPDATE_USER_URL, payload)


    @staticmethod
    def get_next_amendment_number() -> int:
        """
            Runs the website's API call to get the number of the next amendemnt.
        """

        response: requests.Response = requests.get(WebsiteHandler.GET_NEXT_AMENDMENT_NUMBER_URL, json=WebsiteHandler.auth)

        if response.status_code != HTTPStatus.OK:
            print("Get Voting Rules failure", response.status_code)
            return 0

        return int(response.json()['data'])
    

    @staticmethod
    def add_temporary_position(temporary_position: TemporaryPosition) -> bool:
        """
            Runs the website's API call to add a TemporaryPosition object, given the object shadow.
        """

        return WebsiteHandler._generic_post_request(WebsiteHandler.ADD_TEMPORARY_POSITION_URL, temporary_position)
    

    @staticmethod
    def get_temporary_position(user_id: str, role_id: str) -> TemporaryPosition | None:
        """
            Runs the website's API call to get a temporary position using the user's dicord ID, and the role's ID.
        """

        filter_dict: dict[str, str] = {'user_id': user_id, 'role_id': role_id}

        return WebsiteHandler._generic_get_single(WebsiteHandler.GET_TEMPORARY_POSITION_URL, TemporaryPosition, filter_dict=filter_dict)


    @staticmethod
    def get_updatable_temporary_positions() -> typing.Iterable[TemporaryPosition]:
        """
            Runs the website's API call to get all TemporaryPositions that are past their expiration date.
        """

        return WebsiteHandler._generic_get_multiple(WebsiteHandler.GET_UPDATABLE_TEMPORARY_POSITIONS_URL, TemporaryPosition)


    @staticmethod
    def update_temporary_position(temporary_position: TemporaryPosition) -> bool:
        """
            Runs the website's API call to update a temporary position object in the database given the object shadow.
        """

        return WebsiteHandler._generic_post_request(WebsiteHandler.UPDATE_TEMPORARY_POSITION_URL, temporary_position)


    @staticmethod
    def delete_temporary_position(temporary_position: TemporaryPosition) -> bool:  # TODO make a generic deletion function.
        """
            Runs the website's API call to remove a temporary position from the database, given the objec shadow.
        """

        response: requests.Response = requests.get(WebsiteHandler.DELETE_TEMPORARY_POSITION_URL, json={'user_id': temporary_position.user_id, 'role_id': temporary_position.role_id} | WebsiteHandler.auth)

        return response.status_code == HTTPStatus.NO_CONTENT


    @staticmethod
    def add_purchase_log(purchase: TransactionLog) -> bool:
        """
            Runs the website's API call to add a TransactionLog, given the object shadow.
        """

        return WebsiteHandler._generic_post_request(WebsiteHandler.ADD_PURCHASE_LOG_URL, purchase)


    @staticmethod
    def get_last_payment_quarter() -> moonPhaseQuarters | None:  # TODO rename to specify income payments.
        """
            Runs the website's API call to get the last quarter in which an income payment was made.
        """

        response: requests.Response = requests.get(WebsiteHandler.GET_LAST_PAYMENT_QUARTER_URL, json=WebsiteHandler.auth)

        if response.status_code != HTTPStatus.OK:

            print("Get last payment quarter failure.")
            return None
        
        return response.json()['data']


    @staticmethod
    def get_price_of_crack() -> int | None:
        """
            Runs the website's API call to get the current price of crack.
        """

        response: requests.Response = requests.get(WebsiteHandler.GET_PRICE_OF_CRACK_URL, json=WebsiteHandler.auth)

        if response.status_code != HTTPStatus.OK:

            print("get crack price failure...what a disaster")
            return None
    
        return response.json()['data']


    @staticmethod
    def get_debug_inflation(base_price: int=100) -> dict[str, int]:
        """
            Runs the website's API call to get internal markers regarding the inflation operation.
        """

        response: requests.Response = requests.get(WebsiteHandler.GET_DEBUG_INFLATION_URL, json={'data': base_price} | WebsiteHandler.auth)

        return response.json()
