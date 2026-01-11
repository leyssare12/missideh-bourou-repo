from django.conf import settings
from django.urls import path
from django.conf.urls.static import static

from .gestion_hubs import AnnualHubView, OccasionalHubView, DonsHubView, DepensesHubView
from .models import EditorialCommunity
#from .models import CotisationOccasionnelleView
from .models_manager import (ParticipationAnnuelManager, ParticipationOcasionnelleManager, DonsManager, DepensesManager,
                             EvenementOccasionnelleManager, AmountContributionYearManager, EditorialCommunityManager)
from .otp_email_2fa import members_authentification_email
from .otp_qrcode_2fa import qrcode_view, identifiant_otp, members_authentification_qrcode
from .otp_telegram import telegram_webhook, request_new_otp_telegram, \
    login_with_2fa_by_telegram, check_telegram_link_status
from .pdf_manager import PDFView
from .reset_password import (password_reset_success, password_reset_confirm, password_reset_email_sent,
                             request_password_reset)
from .add_or_delete_items import (delete_user, edit_user, confirm_delete_user)
from .list_items import (list_subscribed_users)
from .users_views import (home_page, users_menu, search_member,
                          select_2fa_method, load_2fa_method, member_login_view,
                          has_participed_annuel, announce_view, CotisationOccasionnelleListView, DonsListView,
                          CotisationAnnuelListView, DepensesListView, BilanListView, UserListView, contact_page,
                          mb_monde_view,
                          )
from .views import index, inscription, add_sume, subcribe, data_recup, admin_subcribe, search_user, participation_page,\
    recherche_utilisateurs, gestion_totaux, manager_login_page, logout_view, \
    dashboard_view, dashboard_view2, pdf_listings, mail_confirmation, send_email_verification, \
    resend_email_verification,contributions_settings

app_name = 'Bapp'
urlpatterns = [
                  path('inscription/', inscription, name='inscription'),
                  path('add-sume/', add_sume, name='add-sume'),
                  path('subcribe/', subcribe, name='subcribe'),
                  path('admin_subcribe/', admin_subcribe, name='admin_subcribe'),

                  path("login/", manager_login_page, name="manager_login_page"),
                  path("admin-logout", logout_view, name="logout_view"),
                  path("data/", data_recup, name="data"),

                  path('participation/', participation_page, name='index_participation'),
                  path('search-user/', search_user, name='search_user'),

                  path('reset-password/', request_password_reset, name='password_reset'),
                  path('reset-password/sent/', password_reset_email_sent, name='password_reset_email_sent'),
                  path('reset-password/confirm/<uuid:token>/', password_reset_confirm, name='password_reset_confirm'),
                  path('reset-password/success/', password_reset_success, name='password_reset_success'),



                  path('list-users/', list_subscribed_users, name='list_users'),
                  path('list-users/delete/<int:user_id>/', delete_user, name='delete_user'),
                  path('users/confirm-delete/<int:user_id>/', confirm_delete_user, name='confirm_delete_user'),
                  path('edit-user/edit/<int:user_id>/', edit_user, name='edit_user'),


                  path('list-articles/', EditorialCommunityManager.as_view(), name='list_editorialcommunity'),
                  path('add-article/', EditorialCommunityManager.as_view(), {'action': 'add'},
                       name="add_editorialcommunity"),
                  path('delete-article/<int:item_id>/', EditorialCommunityManager.as_view(), {'action': 'delete'},
                       name="delete_editorialcommunity"),
                  path('edit-article/<int:item_id>/edit', EditorialCommunityManager.as_view(), {'action': 'edit'},
                       name='edit_editorialcommunity'),

                  path('list-settings', contributions_settings, name='list_settings'),

                  path('list-occasional-contribution/', EvenementOccasionnelleManager.as_view(),
                       name='list_occasionalcontribution'),
                  path('add-occasional-contribution/', EvenementOccasionnelleManager.as_view(), {'action': 'add'},
                       name='add_evenementoccasionnelle'),
                  path('edit-occasional-contribution/<int:item_id>/', EvenementOccasionnelleManager.as_view(), {'action': 'edit'},
                       name='edit_evenementoccasionnelle'),
                  path('delete-occasional-contribution/<int:item_id>/', EvenementOccasionnelleManager.as_view(),
                       {'action': 'delete'}, name='delete_evenementoccasionnelle'),

                  path('list-to-contrib-yearl/', AmountContributionYearManager.as_view(),
                       name='list_amountcontributionyear'),
                  path('add-yearly-contribution/', AmountContributionYearManager.as_view(), {'action': 'add'},
                       name='add_amountcontributionyear'),
                  path('edit-yearly-contribution/<int:item_id>/', AmountContributionYearManager.as_view(),
                       {'action': 'edit'},
                       name='edit_amountcontributionyear'),
                  path('delete-yearly-contribution/<int:item_id>/', AmountContributionYearManager.as_view(),
                       {'action': 'delete'}, name='delete_amountcontributionyear'),


                  path('cotisation-annuel/', ParticipationAnnuelManager.as_view(),
                       name='list_participations_annuelles'),
                  path('add-cotisation-annuel/', ParticipationAnnuelManager.as_view(),
                       {'action': 'add'}, name='add_participationannual'),
                  path('edit-cotisation-annuel/<int:item_id>/', ParticipationAnnuelManager.as_view(),
                       {'action': 'edit'}, name='edit_participationannual'),
                  path('delete-cotisation-annuel/<int:item_id>/', ParticipationAnnuelManager.as_view(),
                       {'action': 'delete'}, name='delete_participationannual'),

                  path('cotisation-occasionnel/', ParticipationOcasionnelleManager.as_view(),
                       name='list_participations_occasionnelles'),
                  path('add-cotisation-occasionnel/', ParticipationOcasionnelleManager.as_view(),
                       {'action': 'add'}, name='add_cotisationoccasionnelle'),
                  path('edit-cotisation-occasionnel/<int:item_id>/', ParticipationOcasionnelleManager.as_view(),
                       {'action': 'edit'}, name='edit_cotisationoccasionnelle'),
                  path('delete-cotisation-occasionnel/<int:item_id>/', ParticipationOcasionnelleManager.as_view(),
                       {'action': 'delete'}, name='delete_cotisationoccasionnelle'),

                  path('list-dons/', DonsManager.as_view(), name='list_dons'),
                  path('add-dons/', DonsManager.as_view(), {'action': 'add'}, name='add_dons'),
                  path('edit-dons/<int:item_id>/', DonsManager.as_view(), {'action': 'edit'}, name='edit_dons'),
                  path('delete-dons/<int:item_id>/', DonsManager.as_view(), {'action': 'delete'}, name='delete_dons'),

                  path('list-depenses/', DepensesManager.as_view(), name='list_adddepenses'),
                  path('add-depenses/', DepensesManager.as_view(), {'action': 'add'}, name='add_adddepenses'),
                  path('edit-depenses/<int:item_id>/', DepensesManager.as_view(), {'action': 'edit'},
                       name='edit_adddepenses'),
                  path('delete-depenses/<int:item_id>/', DepensesManager.as_view(), {'action': 'delete'},
                       name='delete_adddepenses'),

                  path("rechercher-user/", recherche_utilisateurs, name="recherche_user"),

                  path("bilan-totaux", gestion_totaux, name="bilan_totaux"),

                  path("dashboard/", dashboard_view, name="dashboard"),
                  path("missideh-bourou-leytiba/", dashboard_view2, name="dashboard2"),

                  path("document-pdf/", pdf_listings, name="pdf_listings"),

                  path("list-pdf", PDFView.liste_pdfs, name="documents_pdf"),
                  path('delete-pdf/<int:pdf_id>/', PDFView.delete_pdf, name='delete_pdf'),
                  path('download-pdf/<int:pdf_id>/', PDFView.download_pdf, name='download_pdf'),

                  # missideh_bourou members urls
                  path("send-mail-verification/", send_email_verification, name="send_mail_verification"),
                  path("resend-verification/", resend_email_verification, name="resend_verification"),
                  path('confirm-mail/<uuid:token>/', mail_confirmation, name='mail_confirmation'),

                  path('home_page/', home_page, name='home_page'),
                  path('member-login/', member_login_view, name='member_login_view'),
                  path('charge-2fa/', load_2fa_method, name='load_2fa_method'),
                  path('select-method/<str:method>/', select_2fa_method, name='select_2fa_method'),

                  path('contacts/', contact_page, name='contact_page'),
                  path('mb-monde/', mb_monde_view, name='mb_monde'),

                  path('members-authentification/', members_authentification_email,
                       name='members_authentification_email'),

                  path('identifiant/', identifiant_otp, name='identifiant_over_otp'),
                  path('tfa-auth/', members_authentification_qrcode, name='two_fa_qrcode_auth'),
                  path('qrcode/<int:user_id>/', qrcode_view, name='qrcode'),

                  # path('telegram-otp/',telegram_otp_login , name='telegram_otp_login'),
                  path('login-with-otp-telegram/', login_with_2fa_by_telegram, name='telegram_otp_login'),
                  path('check-telegram-link/', check_telegram_link_status, name='check_telegram_link'),
                  path('request-new-opt-telegram/', request_new_otp_telegram, name='request_new_otp_telegram'),
                  path('telegram-webhook/', telegram_webhook, name='telegram_webhook'),

                  # Lien proteǵés par login via middleware
                  path('menu/', users_menu, name='users_menu'),

                  #path('hub-contributions/', hub_contributions_view, name='hub_contributions'),

                  path('hub-annuel/', AnnualHubView.as_view(), name='hub_contributions_annuel'),
                  path('hub-occasionnel/', OccasionalHubView.as_view(), name='hub_contributions_occasionnel'),
                  path('hub-dons/', DonsHubView.as_view(), name='hub_dons'),
                  path('hub-depenses/', DepensesHubView.as_view(), name='hub_depenses'),

                  path('member-search/', search_member, name='member_search'),
                  path('membres/', UserListView.as_view(), name='missideh_bourou_members'),

                  path('cotisation-occasionnelle-view/', CotisationOccasionnelleListView.as_view(),
                       name='cotisation_occasionnelle_view'),
                  path('cotisation-annuel-view/', CotisationAnnuelListView.as_view(),
                       name='cotisation_annuelles_view'),
                  path('dons-view/', DonsListView.as_view(), name='dons_view'),
                  path('depenses-view/', DepensesListView.as_view(), name='depenses_view'),
                  path('bilan-totaux-view/', BilanListView.as_view(), name='bilan_totaux_view'),

                  path('has-annuel-participed/', has_participed_annuel, name="has_participed_annuel"),
                  path('annonces/', announce_view, name='announce_view')
              ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) + static(settings.PDFS_URL,
                                                                                         document_root=settings.PDFS_ROOT)
