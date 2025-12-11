from django.conf import settings
from django.urls import path
from django.conf.urls.static import static

from .models import CotisationOccasionnelleView
from .models_manager import (ParticipationAnnuelManager, ParticipationOcasionnelleManager, DonsManager, DepensesManager)
from .otp_email_2fa import members_authentification_email
from .otp_qrcode_2fa import qrcode_view, identifiant_otp, members_authentification_qrcode
from .otp_telegram import telegram_webhook, request_new_otp_telegram, \
    login_with_2fa_by_telegram, check_telegram_link_status
from .pdf_manager import PDFView
from .reset_password import (password_reset_success, password_reset_confirm, password_reset_email_sent, request_password_reset)
from .add_or_delete_items import (delete_article, modify_article, delete_user, edit_user, confirm_delete_user, \
                                  edit_cotisation_annuel, delete_cotisation_annuel)
from .list_items import (list_articles, list_subscribed_users, list_participations_annuel, delete_article, edit_article)
from .users_views import (home_page, users_menu, missideh_bourou_members, search_member,
                          select_2fa_method, load_2fa_method, member_login_view, cotisation_annuelles_view,
                          cotisation_occasionnelle_view, dons_view, bilan_totaux_view, depenses_view,
                          has_participed_annuel, announce_view)
from .views import index, inscription, add_sume, subcribe, data_recup, admin_subcribe, enregistrer_participation, \
    users_participations, search_user, participation_page, submit_participation, participation_view, \
    recherche_utilisateurs, get_data, gestion_totaux, manager_login_page, logout_view, editorial_view, \
    dashboard_view, dashboard_view2, pdf_listings, mail_confirmation, send_email_verification, \
    resend_email_verification, add_depenses_view

app_name = 'Bapp'
urlpatterns = [
    path('', home_page, name='home_page'),
    path('inscription/', inscription, name='inscription'),
    path('add-sume/', add_sume, name='add-sume'),
    path('subcribe/', subcribe, name='subcribe'),
    path('admin_subcribe/', admin_subcribe, name='admin_subcribe'),

    path("login/", manager_login_page, name="manager_login_page"),
    path("admin-logout", logout_view , name="logout_view"),
    path("data/", data_recup, name="data"),
    path("Participations/", enregistrer_participation, name="enregistrer_participation"),
    path("User participations/",users_participations, name="participations" ),

    path('participation/', participation_page, name='index_participation'),
    path('search-user/', search_user, name='search_user'),
    path('submit-participation/', submit_participation, name='submit_participation'),

    path('reset-password/', request_password_reset, name='password_reset'),
    path('reset-password/sent/', password_reset_email_sent, name='password_reset_email_sent'),
    path('reset-password/confirm/<uuid:token>/', password_reset_confirm, name='password_reset_confirm'),
    path('reset-password/success/', password_reset_success, name='password_reset_success'),

   #path('list-articles/', list_articles, name='list_articles'),
   #path('delete-article/<int:post_id>/', delete_article, name="delete_article"),
   #path('article/<int:pk>/edit', modify_article, name='modify_article'),

    path('list-articles/', list_articles, name='article_list'),
    path('delete-article/<int:pk>/', delete_article, name="delete_article"),
    path('article/<int:pk>/edit', edit_article, name='edit_article'),

    path('list-users/', list_subscribed_users, name='list_users'),
    path('list-users/delete/<int:user_id>/', delete_user, name='delete_user'),
    path('users/confirm-delete/<int:user_id>/', confirm_delete_user, name='confirm_delete_user'),
    path('edit-user/edit/<int:user_id>/', edit_user, name='edit_user'),

    #path('cotisation-annuel/', list_participations_annuel, name='list_participations_annuelles'),
    #path('edit-cotisation-annuel/<int:pk>', edit_cotisation_annuel, name='edit_cotisation_annuel'),
    #path('delete-cotisation-annuel/<int:pk>/delete/', delete_cotisation_annuel, name='delete_cotisation_annuel'),
    path('cotisation-annuel/', ParticipationAnnuelManager.as_view(), name='list_participations_annuelles'),
    path('edit-cotisation-annuel/<int:item_id>/', ParticipationAnnuelManager.as_view(), {'action': 'edit'}, name='edit_cotisation_annuel'),
    path('delete-cotisation-annuel/<int:item_id>/', ParticipationAnnuelManager.as_view(), {'action': 'delete'}, name='delete_cotisation_annuel'),

    path('cotisation-occasionnel/', ParticipationOcasionnelleManager.as_view(),
         name='list_participations_occasionnelles'),
    path('edit-cotisation-occasionnel/<int:item_id>/', ParticipationOcasionnelleManager.as_view(),
         {'action': 'edit'}, name='edit_cotisation_occasionnelle'),
    path('delete-cotisation-occasionnel/<int:item_id>/', ParticipationOcasionnelleManager.as_view(),
         {'action': 'delete'}, name='delete_cotisation_occasionnelle'),

    path('list-dons/', DonsManager.as_view(), name='list_dons'),
    path('edit-dons/<int:item_id>/', DonsManager.as_view(), {'action': 'edit'}, name='edit_dons'),
    path('delete-dons/<int:item_id>/', DonsManager.as_view(), {'action': 'delete'}, name='delete_dons'),

    path('list-depenses/', DepensesManager.as_view(), name='list_depenses'),
    path('edit-depenses/<int:item_id>/', DepensesManager.as_view(), {'action': 'edit'}, name='edit_depenses'),
    path('delete-depenses/<int:item_id>/', DepensesManager.as_view(), {'action': 'delete'}, name='delete_depenses'),

    path("rechercher-user/", recherche_utilisateurs, name="recherche_user"),
    path("test-participations/", participation_view, name="test_participation"),

    path("add-depenses/", add_depenses_view, name="add_depenses"),

    path("get-data/", get_data, name="get_data"),
    path("bilan-totaux", gestion_totaux, name="bilan_totaux"),
    path("edition-article/", editorial_view, name="edition_article"),

    path("dashboard/", dashboard_view, name="dashboard"),
    path("missideh-bourou-leytiba/", dashboard_view2, name="dashboard2"),

    path("document-pdf/", pdf_listings, name="pdf_listings"),

    path("list-pdf", PDFView.liste_pdfs, name="documents_pdf"),
    path('delete-pdf/<int:pdf_id>/', PDFView.delete_pdf, name='delete_pdf'),
    path('download-pdf/<int:pdf_id>/', PDFView.download_pdf, name='download_pdf'),

    #missideh_bourou members urls
    path("send-mail-verification/", send_email_verification, name="send_mail_verification"),
    path("resend-verification/", resend_email_verification, name="resend_verification"),
    path('confirm-mail/<uuid:token>/', mail_confirmation, name='mail_confirmation'),

    path('home_page/', home_page, name='home_page'),

    #path('member-login/', members_login, name='check_identifiant'),
    path('member-login/', member_login_view, name='member_login_view'),
    path('charge-2fa/', load_2fa_method, name='load_2fa_method'),
    path('select-method/<str:method>/', select_2fa_method, name='select_2fa_method'),

    path('members-authentification/', members_authentification_email, name='members_authentification_email'),

    path('identifiant/', identifiant_otp, name='identifiant_over_otp'),
    path('tfa-auth/', members_authentification_qrcode, name='two_fa_qrcode_auth'),
    path('qrcode/<int:user_id>/', qrcode_view, name='qrcode'),

    #path('telegram-otp/',telegram_otp_login , name='telegram_otp_login'),
    path('login-with-otp-telegram/', login_with_2fa_by_telegram, name='telegram_otp_login'),
    path('check-telegram-link/', check_telegram_link_status, name='check_telegram_link'),
    path('request-new-opt-telegram/', request_new_otp_telegram, name='request_new_otp_telegram'),
    path('telegram-webhook/', telegram_webhook, name='telegram_webhook'),

    #Lien proteǵés par login via middleware
    path('menu/', users_menu, name='users_menu'),
    path('membres/', missideh_bourou_members, name='missideh_bourou_members'),
    path('member-search/', search_member, name='member_search'),

    path('cotisation-annuel-view/', cotisation_annuelles_view, name='cotisation_annuelles_view'),
    path('cotisation-occasionnelle-view/', cotisation_occasionnelle_view, name='cotisation_occasionnelle_view'),
    path('dons-view/', dons_view, name='dons_view'),
    path('depenses-view/', depenses_view, name='depenses_view'),
    path('bilan-totaux-view/', bilan_totaux_view, name='bilan_totaux_view'),
    path('has-annuel-participed/', has_participed_annuel, name="has_participed_annuel"),
    path('annonces/', announce_view, name='announce_view')
]  + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) + static(settings.PDFS_URL, document_root=settings.PDFS_ROOT)