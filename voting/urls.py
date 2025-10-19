"""
URL configuration for voting project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from votingapp import views

# app_name = "voting"
app_name = 'voting/'
urlpatterns = [
    path('admin/', admin.site.urls),
    path('index', views.voting),
    path('', views.voting),
    path(app_name, views.voting, name=app_name),  # TODO Make a for loop for this, this is needlessly complex
    path(f'{app_name}{views.submit_vote.__name__}', views.submit_vote, name=views.submit_vote.__name__),
    path(f'{app_name}{views.get_unposted_provisions.__name__}', views.get_unposted_provisions, name=views.get_unposted_provisions.__name__),
    path(f'{app_name}{views.get_voting_rules.__name__}', views.get_voting_rules, name=views.get_voting_rules.__name__),
    path(f'{app_name}{views.get_resolvable_provisions.__name__}', views.get_resolvable_provisions, name=views.get_resolvable_provisions.__name__),
    path(f'{app_name}{views.get_next_amendment_number.__name__}', views.get_next_amendment_number, name=views.get_next_amendment_number.__name__),
    path(f'{app_name}{views.get_constitution.__name__}', views.get_constitution, name=views.get_constitution.__name__),
    path(f'{app_name}{views.get_provision.__name__}', views.get_provision, name=views.get_provision.__name__),
    path(f'{app_name}{views.get_open_provisions.__name__}', views.get_open_provisions, name=views.get_open_provisions.__name__),
    path(f'{app_name}{views.get_recognized_regions.__name__}', views.get_recognized_regions, name=views.get_recognized_regions.__name__),
    path(f'{app_name}{views.get_unposted_constitutions.__name__}', views.get_unposted_constitutions, name=views.get_unposted_constitutions.__name__),
    path(f'{app_name}{views.get_open_judicial_challenges.__name__}', views.get_open_judicial_challenges, name=views.get_open_judicial_challenges.__name__),
    path(f'{app_name}{views.get_full_constitution.__name__}', views.get_full_constitution, name=views.get_full_constitution.__name__),
    path(f'{app_name}{views.get_users.__name__}', views.get_users, name=views.get_users.__name__),
    path(f'{app_name}{views.get_roles.__name__}', views.get_roles, name=views.get_roles.__name__),
    path(f'{app_name}{views.get_party_role_by_name.__name__}', views.get_party_role_by_name, name=views.get_party_role_by_name.__name__),
    path(f'{app_name}{views.update_provision.__name__}', views.update_provision, name=views.update_provision.__name__),
    path(f'{app_name}{views.update_constitution.__name__}', views.update_constitution, name=views.update_constitution.__name__),
    path(f'{app_name}{views.update_user.__name__}', views.update_user, name=views.update_user.__name__),
    path(f'{app_name}{views.update_judicial_challenge.__name__}', views.update_judicial_challenge, name=views.update_judicial_challenge.__name__),
    path(f'{app_name}{views.add_constitution.__name__}', views.add_constitution, name=views.add_constitution.__name__),
    path(f'{app_name}{views.update_user.__name__}', views.update_user, name=views.update_user.__name__),
    path(f'{app_name}{views.update_many_users.__name__}', views.update_many_users, name=views.update_many_users.__name__),
    path(f'{app_name}{views.add_role.__name__}', views.add_role, name=views.add_role.__name__),
    path(f'{app_name}{views.add_user.__name__}', views.add_user, name=views.add_user.__name__),
    path(f'{app_name}{views.add_region.__name__}', views.add_region, name=views.add_region.__name__),
    path(f'{app_name}{views.add_judicial_challenge.__name__}', views.add_judicial_challenge, name=views.add_judicial_challenge.__name__),
    path(f'{app_name}{views.add_temporary_position.__name__}', views.add_temporary_position, name=views.add_temporary_position.__name__),
    path(f'{app_name}{views.get_temporary_position.__name__}', views.get_temporary_position, name=views.get_temporary_position.__name__),
    path(f'{app_name}{views.get_updatable_temporary_positions.__name__}', views.get_updatable_temporary_positions, name=views.get_updatable_temporary_positions.__name__),
    path(f'{app_name}{views.update_temporary_position.__name__}', views.update_temporary_position, name=views.update_temporary_position.__name__),
    path(f'{app_name}{views.delete_temporary_position.__name__}', views.delete_temporary_position, name=views.delete_temporary_position.__name__),
    path(f'{app_name}{views.add_purchase_log.__name__}', views.add_purchase_log, name=views.add_purchase_log.__name__),
    path(f'{app_name}{views.get_price_of_crack.__name__}', views.get_price_of_crack, name=views.get_price_of_crack.__name__),
    path(f'{app_name}{views.get_last_payment_quarter.__name__}', views.get_last_payment_quarter, name=views.get_last_payment_quarter.__name__),
    path(f'{app_name}{views.debug_inflation.__name__}', views.debug_inflation, name=views.debug_inflation.__name__),
]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
