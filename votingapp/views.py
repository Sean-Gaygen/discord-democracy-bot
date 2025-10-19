import django.http
import datetime
import json
import typing

from http import HTTPStatus
from django.shortcuts import render
from votingapp.models import *
from django.core import serializers
from django.db.models import Q
from django.forms.models import model_to_dict
from django.shortcuts import redirect
from django.urls import reverse
from django.shortcuts import get_object_or_404

#TODO Add ordering to get_users and get_roles

# -- DECORATORS --
"""
	NOTE both of these decorators are to verify the presence of a valid database access key, and ensure the correct
	http method. The only requirement to use these decorators is that the decorated function's first positional argument
	is a django.http.HttpRequest object.
"""

P = typing.ParamSpec('P')  # TODO consider moving to models, where other generic/type declarations are stored.

def verify_get(func: typing.Callable[P, django.http.HttpResponse]) -> typing.Callable[P, django.http.HttpResponse]:

	def wrapper(*args: P.args, **kwargs: P.kwargs) -> django.http.HttpResponse:

		try:

			request: django.http.HttpRequest = list(args)[0] # type: ignore ; We know that this first arguement will always be the httprequest

			verify = _verify_get_request(request)

			if verify is not None:

				return verify

			return func(*args, **kwargs)
		
		except Exception as e:

			print(e)
			return django.http.HttpResponse(status=HTTPStatus.INTERNAL_SERVER_ERROR)

	return wrapper


def verify_post(func: typing.Callable[P, django.http.HttpResponse]) -> typing.Callable[P, django.http.HttpResponse]:

	def wrapper(*args: P.args, **kwargs: P.kwargs) -> django.http.HttpResponse:

		try:

			request: django.http.HttpRequest = list(args)[0] # type: ignore ; We know that this first arguement will always be the httprequest

			verify = _verify_post_request(request)

			if verify is not None:

				return verify

			return func(*args, **kwargs)
		
		except Exception as e:

			print(e)
			return django.http.HttpResponse(status=HTTPStatus.INTERNAL_SERVER_ERROR)

	return wrapper

# --- VIEWS ---

def voting(request: django.http.HttpRequest):

	from_submit: bool = False
	sent_duplicate: bool = False
	too_many_provisions: bool = False

	if 'from_submit' in request.GET:

		from_submit = request.GET['from_submit'] == 'True' # type: ignore

	if 'sent_duplicate' in request.GET:

		sent_duplicate = request.GET['sent_duplicate'] == 'True' # type: ignore

	if 'too_many_provisions' in request.GET:

		too_many_provisions = request.GET['too_many_provisions'] == 'True' # type: ignore

	context: dict[str, typing.Any] = {
		'categories': serializers.serialize('json', Category.objects.all()),
		'users_JSON': serializers.serialize('json', Users.objects.all()),
		'roles_JSON': serializers.serialize('json', Roles.objects.all()),
		'constitution_JSON': serializers.serialize('json', Constitution.objects.all()),
		'from_submit': from_submit,
		'sent_duplicate': sent_duplicate,
		'too_many_provisions': too_many_provisions,
	}

	return render(request, "votingapp/voting.html", context)


def submit_vote(request: django.http.HttpRequest) -> django.http.HttpResponse:

	url_options: str = '?from_submit=True'

	voting_rules: VotingRules | None = VotingRules.objects.first()

	assert voting_rules is not None

	proposed_by_name: str = request.POST['proposee'] # type: ignore
	polls_close_at: datetime.datetime = voting_rules.get_poll_close_from_now()
	function_key: str = request.POST['category'] # type: ignore

	is_rigged: int = _is_rigged(function_key) # type: ignore
	value1: str = request.POST['value1'] if 'value1' in request.POST else '' # type: ignore
	value2: str = request.POST['value2'] if 'value2' in request.POST else '' # type: ignore

	if len([provision for provision in ProvisionHistory.objects.filter(passed__isnull=True)]) >= voting_rules.allowed_open_proposals:

		url_options += '&too_many_provisions=True'

	elif ProvisionHistory.objects.filter(
		function_key=function_key,
		value1 = request.POST['value1'] if 'value1' in request.POST else '',
		value2 = request.POST['value2'] if 'value2' in request.POST else '',
		polls_close_at__gt=timezone.now()
	).exists():
	
		url_options += '&sent_duplicate=True'

	else:

		ProvisionHistory(
			proposed_by_name=proposed_by_name,
			polls_close_at=polls_close_at,
			is_rigged=is_rigged,
			has_been_challenged=False,
			is_in_judicial_review=False,
			function_key=function_key,
			value1=value1,
			value2=value2,
		).save()

	base_url = reverse('voting/')

	return redirect(f'{base_url}{url_options}')

# --- PRIVATE INTERNAL FUNCTIONS ---

# -Verification-

def _verify_auth(request: django.http.HttpRequest) -> django.http.HttpResponse | None:

	request_body: dict[str, typing.Any] = json.loads(request.body)

	if 'auth_key' not in request_body:

		print("No recognized auth key", request_body)
		return django.http.HttpResponseForbidden()

	key: str = request_body['auth_key']

	return django.http.HttpResponseForbidden() if key not in AllowedAccess.objects.all().values_list('key', flat=True) else None


def _verify_get_request(request: django.http.HttpRequest) -> django.http.HttpResponse | None:  # TODO make decorator

	if request.method != 'GET':

		return django.http.HttpResponseNotAllowed(['GET'])

	return _verify_auth(request)


def _verify_post_request(request: django.http.HttpRequest) -> django.http.HttpResponse | None:  # TODO make decorator

	if request.method != 'POST':

			return django.http.HttpResponseNotAllowed(['POST'])

	return _verify_auth(request)

# -Generic DB accesses-

@verify_post
def _generic_add_single(request: django.http.HttpRequest, target_model: type[V]) -> django.http.HttpResponse:

	model_to_add: V = target_model()

	request_data: dict[str, typing.Any] = json.loads(request.body)

	if any(key not in [*model_to_add.__dict__.keys(), 'auth_key']  for key in request_data):

		return django.http.HttpResponseBadRequest()

	for key, entry in request_data.items():

		setattr(model_to_add, key, entry)

	model_to_add.save()

	return django.http.HttpResponse(status=HTTPStatus.NO_CONTENT)


@verify_post
def _generic_update_single(request: django.http.HttpRequest, target_model: type[V], custom_index: Q | None=None) -> django.http.HttpResponse:

	request_data: dict[str, typing.Any] = json.loads(request.body)

	if target_model._meta.pk is None:

		return django.http.HttpResponse(status=HTTPStatus.INTERNAL_SERVER_ERROR)
	
	pk_name: str = target_model._meta.pk.name

	if custom_index is None and pk_name not in request_data:

		return django.http.HttpResponseBadRequest()

	target_filter: Q = Q(pk=request_data[pk_name]) if custom_index is None else custom_index

	query = target_model.objects.filter(target_filter)

	is_missing_pk: bool = custom_index is None and pk_name not in request_data
	does_not_exist: bool = not query.exists()
	is_not_unique: bool = query.count() > 1
	has_unknown_attributes: bool = any(key not in [*[field.name for field in target_model._meta.get_fields()], 'auth_key'] for key in request_data)

	if (is_missing_pk or does_not_exist or is_not_unique or has_unknown_attributes):

		print(f"Does not contain primary key: {is_missing_pk}",
			f"Object not in database: {does_not_exist}",
			f"Is not unique: {is_not_unique}"
			f"Data contains key that is not part of the model: {has_unknown_attributes}")

		return django.http.HttpResponseBadRequest() if not does_not_exist else django.http.HttpResponseNotFound()
	
	db_entry_to_edit: V | None = query.first()
	
	if db_entry_to_edit is None:  # Is already logically caught with .exists. This is for type hinting

		return django.http.HttpResponseNotFound()

	for key, value in request_data.items():

		if value is not None:  # Entries may be created with a blank, but None here means no change.

			setattr(db_entry_to_edit, key, value)

	db_entry_to_edit.save()

	return django.http.HttpResponse(status=HTTPStatus.NO_CONTENT)


@verify_get
def _generic_get_multiple(request: django.http.HttpRequest, 
							model_to_get: type[V], 
							filters: Q | None = None, 
							order: str | None = None,
						) -> django.http.HttpResponse:

	if filters is None:

		data = model_to_get.objects.all()

	else:

		data = model_to_get.objects.filter(filters)

	if not data.exists():

		return django.http.HttpResponse(status=HTTPStatus.NO_CONTENT)

	if order is not None:

		data.order_by(order)

	response_data: dict[str, typing.Iterable[typing.Any]] = {'data': [model_to_dict(entry) for entry in data]}

	return django.http.JsonResponse(response_data, status=HTTPStatus.OK)


@verify_get
def _generic_get_single(request: django.http.HttpRequest, model_to_get: type[V], custom_index: Q | None = None) -> django.http.HttpResponse:

	request_data: dict[str, typing.Any] = json.loads(request.body)

	if model_to_get._meta.pk is None:

		return django.http.HttpResponse(status=HTTPStatus.INTERNAL_SERVER_ERROR)

	pk_name: str = model_to_get._meta.pk.name

	target_filter: Q = Q(pk=request_data[pk_name]) if custom_index is None else custom_index

	if custom_index is None and pk_name not in request_data:

		print('pk_name not in request_data')

		return django.http.HttpResponseBadRequest() 

	data = model_to_dict(get_object_or_404(model_to_get, target_filter))

	return django.http.JsonResponse(data, status=HTTPStatus.OK)


@verify_post
def _generic_update_multiple(request: django.http.HttpRequest, model_to_update: type[V]) -> django.http.HttpResponse:
		
	request_top_level: dict[str, list[dict[str, typing.Any]]] = json.loads(request.body)

	if model_to_update._meta.pk is None:

		return django.http.HttpResponse(status=HTTPStatus.INTERNAL_SERVER_ERROR)

	pk_name: str = model_to_update._meta.pk.name

	if 'data' not in request_top_level:

		return django.http.HttpResponseBadRequest()

	request_list = request_top_level['data']

	request_data: dict[str, typing.Any]
	for request_data in request_list:

		is_missing_pk: bool = pk_name not in request_data
		has_unknown_attributes: bool = any(key not in [*[field.name for field in model_to_update._meta.get_fields()], 'auth_key'] for key in request_data)

		if is_missing_pk or has_unknown_attributes:

			print(f"Does not contain primary key: {is_missing_pk}",
				f"Data contains key that is not part of the model: {has_unknown_attributes}")

			return django.http.HttpResponseBadRequest()

		db_entry_to_edit = get_object_or_404(model_to_update, pk=request_data[pk_name])

		for key, value in request_data.items():

			if value is not None:  # Entries may be created with a blank, but None here means no change.

				setattr(db_entry_to_edit, key, value)

		db_entry_to_edit.save()
	
	return django.http.HttpResponse(status=HTTPStatus.NO_CONTENT)

# -Misc.-

def _is_rigged(key: str):

	rig_pass = [

	]

	rig_fail = [
		'dissolve',
	]

	if key in rig_pass:
		return 1

	if key in rig_fail:
		return 2

	return 0


def _adjust_for_inflation(base_price: float, get_debug_info: bool = False) -> int | dict[str, int|float]:  # TODO consider moving economic functions into new module.
	"""
		The inflation system implemented is based on the "Quantity Theory of Money".
		This theory establishes the basic equation; Money Supply * Velocity of Money = Price Level * Real GDP
		
		We calculate our money supply easily based on the total money between all users
		Velocity is effectively how much money is moving, so we can count recent purchases.
		Price level is a total of all prices, we use the most recent prices sold for each item as a sufficient
		approximation of their current price.
		Real GDP is tricky, as Schmucklandia produces nothing. So I use political activity as a proxy.
	"""

	schmuckmarket_cap: int = 0

	user: Users
	for user in Users.objects.all():

		if user.user_id == '120020797480894464':

			continue

		schmuckmarket_cap += user.money

	transactions: django.db.models.QuerySet = TransactionLog.objects.exclude(transaction_type=transactionType.INCOME_PAYMENT)

	total_transactions = transactions.count()

	total_transactions = total_transactions if total_transactions != 0 else 1

	total_value = 0

	total_value = sum(transaction.transaction_total for transaction in transactions.all())

	schmuckmark_velocity = total_value / total_transactions

	schmuckmark_velocity = schmuckmark_velocity if schmuckmark_velocity != 0 else 1

	price_level: int = 0

	item: transactionType
	for item in transactionType:

		if item in {transactionType.INCOME_PAYMENT}:  # Skip non-purchases

			continue

		last_sale: TransactionLog | None = TransactionLog.objects.filter(transaction_type=item).last()

		if last_sale is not None:

			price_level += last_sale.transaction_total

	price_level = price_level if price_level != 0 else 100  # This prevents unintended behavior on a "cold startup" (no db entries)

	gdp_factor: float = 0.5

	now: datetime.datetime = timezone.now()

	gdp_factor += 0.1 * ProvisionHistory.objects.filter(polls_close_at__gt=now).count()
	gdp_factor += 0.01 * ProvisionHistory.objects.filter(polls_close_at__gt=(now - timedelta(weeks=1))).count()
	gdp_factor += 0.01 * JudicialChallenges.objects.filter(is_active=True).count()

	real_gdp: float = gdp_factor * schmuckmarket_cap

	inflation_factor: float = (schmuckmarket_cap * schmuckmark_velocity) / (price_level * real_gdp)

	curve_radius_factor: float = 1
	slant_factor: float = 0.15
	y_offset: float = 0.35

	smooth_inflation: float = (inflation_factor * ((1 / (1 + (curve_radius_factor * inflation_factor))) + slant_factor)) + y_offset
	# This is a much more aggressive smoothin factor. This gives us an oblique asymptote, ensuring that our inflation can always increase, but in a much more
	# controlled way.

	if get_debug_info:

		payload: dict[str, int|float] = {
			'base_price': base_price,
			'schmuckmarket_cap': schmuckmarket_cap,
			'schmuckmark_velocity': schmuckmark_velocity,
			'price_level': price_level,
			'real_gdp': real_gdp,
			'inflation_factor': inflation_factor,
			'smooth_inflation': smooth_inflation,
			'unsmooth_price': base_price * inflation_factor,
			'smooth_price': base_price * smooth_inflation,
		}

		return payload

	inflated_price: float = base_price * smooth_inflation

	return round(inflated_price if inflated_price > base_price else base_price)

# --- API ENDPOINTS ---

def get_open_provisions(request: django.http.HttpRequest) -> django.http.HttpResponse:

	return _generic_get_multiple(request, ProvisionHistory, filters=Q(passed__isnull=True))


def get_users(request: django.http.HttpRequest) -> django.http.HttpResponse:

	return _generic_get_multiple(request, Users)


def get_roles(request: django.http.HttpRequest) -> django.http.HttpResponse:

	return _generic_get_multiple(request, Roles)


def get_recognized_regions(request: django.http.HttpRequest) -> django.http.HttpResponse:

	return _generic_get_multiple(request, RecognizedRegions)


def get_next_amendment_number(request: django.http.HttpRequest) -> django.http.HttpResponse:

	try:
		print(request, request.body)
		verified = _verify_get_request(request)

		if verified is not None:

			return verified
		
		last_amendment: Constitution | None = Constitution.objects.last()

		if last_amendment is None:

			return django.http.HttpResponse(status=HTTPStatus.INTERNAL_SERVER_ERROR)

		next_number: int = last_amendment.amendment_number + 1

		return django.http.JsonResponse({'data': next_number}, status=HTTPStatus.OK)

	except Exception as e:

		print(e)
		return django.http.HttpResponse(status=HTTPStatus.INTERNAL_SERVER_ERROR)


def get_unposted_constitutions(request: django.http.HttpRequest) -> django.http.HttpResponse:

	if Constitution._meta.pk is None:

		return django.http.HttpResponse(status=HTTPStatus.INTERNAL_SERVER_ERROR)

	return _generic_get_multiple(request, Constitution, filters=(Q(message_id__isnull=True) | Q(message_id__exact='')), order=Constitution._meta.pk.name)


def get_unposted_provisions(request: django.http.HttpRequest) -> django.http.HttpResponse:

	filters: Q = Q(message_id__isnull=True) | Q(message_id__exact='')

	return _generic_get_multiple(request, ProvisionHistory, filters=filters)


def get_resolvable_provisions(request: django.http.HttpRequest) -> django.http.HttpResponse:

	filters: Q = Q(passed__isnull=True) & ~Q(message_id='') & Q(polls_close_at__lt=timezone.now()) & Q(is_in_judicial_review=False)

	return _generic_get_multiple(request, ProvisionHistory, filters=filters)


def get_open_judicial_challenges(request: django.http.HttpRequest) -> django.http.HttpResponse:

	filters: Q = Q(is_active=True)

	return _generic_get_multiple(request, JudicialChallenges, filters=filters)


def get_voting_rules(request: django.http.HttpRequest) -> django.http.HttpResponse:

	return _generic_get_single(request, VotingRules, custom_index=Q(id=1))

	# try:

	# 	verified = _verify_get_request(request)

	# 	if verified is not None:

	# 		return verified

	# 	voting_rules_object: VotingRules | None = VotingRules.objects.first()

	# 	if voting_rules_object is None:

	# 		return django.http.HttpResponse(status=HTTPStatus.INTERNAL_SERVER_ERROR)

	# 	data = model_to_dict(voting_rules_object)

	# 	return django.http.JsonResponse(data, status=HTTPStatus.OK)

	# except Exception as e:

	# 	print(e)
	# 	return django.http.HttpResponse(status=HTTPStatus.INTERNAL_SERVER_ERROR)
	

def get_full_constitution(request: django.http.HttpRequest) -> django.http.HttpResponse:  # TODO consider rolling into get_constitution as an option, or swapping names to be consistent.

	if Constitution._meta.pk is None:

		return django.http.HttpResponse(status=HTTPStatus.INTERNAL_SERVER_ERROR)

	return _generic_get_multiple(request, Constitution, order=Constitution._meta.pk.name)


def get_constitution(request: django.http.HttpRequest) -> django.http.HttpResponse:

	return _generic_get_single(request, Constitution)


def get_party_role_by_name(request: django.http.HttpRequest) -> django.http.HttpResponse:

	json_request = json.loads(request.body)

	if 'role_name' not in json_request:

		return django.http.HttpResponseBadRequest()
	
	else:

		role_name: str = json_request['role_name']

	return _generic_get_single(request, Roles, Q(name__iexact=role_name) & Q(is_political_party__exact=True))


def get_provision(request: django.http.HttpRequest) -> django.http.HttpResponse:

	json_request = json.loads(request.body)

	if 'proposal_id' not in json_request:

		return django.http.HttpResponseBadRequest()

	else:

		proposal_id: int = json_request['proposal_id']

	return _generic_get_single(request, ProvisionHistory, Q(proposal_id__exact=proposal_id))


def update_provision(request: django.http.HttpRequest) -> django.http.HttpResponse:

	return _generic_update_single(request, ProvisionHistory)


def update_user(request: django.http.HttpRequest) -> django.http.HttpResponse:

	return _generic_update_single(request, Users)


def update_many_users(request: django.http.HttpRequest) -> django.http.HttpResponse:

	return _generic_update_multiple(request, Users)
	

def update_constitution(request: django.http.HttpRequest) -> django.http.HttpResponse:

	return _generic_update_single(request, Constitution)


def update_judicial_challenge(request: django.http.HttpRequest) -> django.http.HttpResponse:

	return _generic_update_single(request, JudicialChallenges)


def add_constitution(request: django.http.HttpRequest) -> django.http.HttpResponse:

	return _generic_add_single(request, Constitution)


def add_role(request: django.http.HttpRequest) -> django.http.HttpResponse:

	return _generic_add_single(request, Roles)


def add_user(request: django.http.HttpRequest) -> django.http.HttpResponse:

	return _generic_add_single(request, Users)


def add_region(request: django.http.HttpRequest) -> django.http.HttpResponse:

	return _generic_add_single(request, RecognizedRegions)


def add_judicial_challenge(request: django.http.HttpRequest) -> django.http.HttpResponse:

	return _generic_add_single(request, JudicialChallenges)


def add_temporary_position(request: django.http.HttpRequest) -> django.http.HttpResponse:

	return _generic_add_single(request, TemporaryPosition)


def get_temporary_position(request: django.http.HttpRequest) -> django.http.HttpResponse:

	json_request = json.loads(request.body)

	if 'user_id' not in json_request or 'role_id' not in json_request:
		print('gug')
		return django.http.HttpResponseBadRequest()
	
	else:

		user_id: str = json_request['user_id']
		role_id: str = json_request['role_id']

	return _generic_get_single(request, TemporaryPosition, Q(user_id=user_id) & Q(role_id=role_id))


def get_updatable_temporary_positions(request: django.http.HttpRequest) -> django.http.HttpResponse:

	return _generic_get_multiple(request, TemporaryPosition, Q(position_expires_at__lt=timezone.now()))


def update_temporary_position(request: django.http.HttpRequest) -> django.http.HttpResponse:

	json_request = json.loads(request.body)

	if 'user_id' not in json_request or 'role_id' not in json_request:
		
		return django.http.HttpResponseBadRequest()
	
	else:

		user_id: str = json_request['user_id']
		role_id: str = json_request['role_id']

	filters: Q = Q(user_id=user_id) & Q(role_id=role_id)

	return _generic_update_single(request, TemporaryPosition, custom_index=filters)


def delete_temporary_position(request: django.http.HttpRequest) -> django.http.HttpResponse:

	try:  # TODO generalize a deletion function.

		json_request = json.loads(request.body)

		if 'user_id' not in json_request or 'role_id' not in json_request:
			
			return django.http.HttpResponseBadRequest()
		
		else:

			user_id: str = json_request['user_id']
			role_id: str = json_request['role_id']

		custom_filter: Q =  Q(user_id=user_id) & Q(role_id=role_id)

		if not TemporaryPosition.objects.filter(custom_filter).exists():

			return django.http.HttpResponseBadRequest()

		position_to_delete: TemporaryPosition | None = TemporaryPosition.objects.filter(custom_filter).first()

		if position_to_delete is None:

			return django.http.HttpResponseBadRequest()
		
		position_to_delete.delete()

		return django.http.HttpResponse(status=HTTPStatus.NO_CONTENT)
	
	except Exception as e:

		print(e)
		return django.http.HttpResponse(status=HTTPStatus.INTERNAL_SERVER_ERROR)


def add_purchase_log(request: django.http.HttpRequest) -> django.http.HttpResponse:  # TODO rename to transaction

	return _generic_add_single(request, TransactionLog)


def get_last_payment_quarter(request: django.http.HttpRequest) -> django.http.HttpResponse:  # TODO ADD VERIFY
	"""
		Return the last quarter that an income payment occurred in.
	"""
	
	last_payment: TransactionLog | None = TransactionLog.objects.filter(transaction_type=transactionType.INCOME_PAYMENT).last()
	last_phase: moonPhaseQuarters

	if last_payment is None: # No income payments, or a "cold start"

		last_phase = moonPhaseQuarters.NEW_MOON
	
	else:

		last_phase = moonPhaseQuarters.get_phase_by_date(last_payment.transacted_at)
	
	return django.http.JsonResponse({'data': last_phase}, status=HTTPStatus.OK)


def debug_inflation(request: django.http.HttpRequest) -> django.http.HttpResponse:

	base_price: int = json.loads(request.body)['data']

	payload: int | dict[str, int|float] = _adjust_for_inflation(base_price, get_debug_info=True)

	return django.http.JsonResponse(payload, status=HTTPStatus.OK)


def get_price_of_crack(request: django.http.HttpRequest) -> django.http.HttpResponse:

	# TODO There is some major problem with this function wwhere we can't access the database...fix that eventually, I guess
	# And no, there is no discernible evidence as to why it's acting like this.

	price: float = 100.0

	ret_price = price

	inflation_adjusted_price: int | dict[str, int | float] = _adjust_for_inflation(price)

	if isinstance(inflation_adjusted_price, int):

		ret_price = inflation_adjusted_price

	return django.http.JsonResponse({'data': ret_price}, status=HTTPStatus.OK)

	now: datetime.datetime = timezone.now()

	one_hour_ago: datetime.datetime = now - timedelta(hours=1)
	one_day_ago: datetime.datetime = now - timedelta(hours=24)
	three_days_ago = datetime.datetime = now - timedelta(days=3)
	one_week_ago = datetime.datetime = now - timedelta(weeks=1)

	crack_filter: Q = Q(transaction_type=1)

	# all_purchases = TransactionLog.objects.filter(crack_filter)
	# #TODO this was causing the entire database to shut down for some reason. I would love to do it like this, but we
	# need to investigate that issue if we're going to run it like this.
	#
	# purchases_within_1h: int = all_purchases.filter(Q(transacted_at__gt=one_hour_ago)).count()
	# purchases_within_24h: int = all_purchases.filter(Q(transacted_at__gt=one_day_ago) & Q(transacted_at__lt=one_hour_ago)).count()
	# purchases_within_3d: int = all_purchases.filter(Q(transacted_at__gt=three_days_ago) & Q(transacted_at__lt=one_day_ago)).count()
	# purchases_within_1w: int = all_purchases.filter(Q(transacted_at__gt=one_week_ago) & Q(transacted_at__lt=three_days_ago)).count()

	# all_purchases = TransactionLog.objects.filter(crack_filter)

	# purchases_within_1h: int = TransactionLog.objects.filter(crack_filter & Q(transacted_at__gte=one_hour_ago)).count()
	# purchases_within_24h: int = TransactionLog.objects.filter(crack_filter & Q(transacted_at__gte=one_day_ago) & Q(transacted_at__lte=one_hour_ago)).count()
	# purchases_within_3d: int = TransactionLog.objects.filter(crack_filter & Q(transacted_at__gte=three_days_ago) & Q(transacted_at__lte=one_day_ago)).count()
	# purchases_within_1w: int = TransactionLog.objects.filter(crack_filter & Q(transacted_at__gte=one_week_ago) & Q(transacted_at__lte=three_days_ago)).count()

	all_purchases: int = 0
	purchases_within_1h: int = 0
	purchases_within_24h: int = 0
	purchases_within_3d: int = 0
	purchases_within_1w: int = 0

	purchase: TransactionLog
	for purchase in TransactionLog.objects.exclude(transaction_type=transactionType.INCOME_PAYMENT).all():

		if purchase.transaction_type != transactionType.CRACK: continue

		all_purchases += 1

		transaction_time = purchase.transacted_at

		if transaction_time > one_hour_ago:

			purchases_within_1h += 1

		elif one_hour_ago > transaction_time > one_day_ago:

			purchases_within_24h += 1

		elif one_day_ago > transaction_time > three_days_ago:

			purchases_within_3d += 1

		elif three_days_ago > transaction_time > one_week_ago:

			purchases_within_1w += 1

	if purchases_within_1h > 0:

		price += 100

	for _ in range(purchases_within_1h):

		price *= 1.2

	price += ((price * 0.5) * purchases_within_24h) + 50
	price += 50 * purchases_within_3d
	price += 20 * purchases_within_1w

	# price += TransactionLog.objects.filter(crack_filter).count() * 0.2

	price += all_purchases * 0.2

	ret_price: int = int(price)

	inflation_adjusted_price: int | dict[str, int|float] = _adjust_for_inflation(price)

	if isinstance(inflation_adjusted_price, int):

		ret_price = inflation_adjusted_price

	return django.http.JsonResponse({'data': ret_price}, status=HTTPStatus.OK)

