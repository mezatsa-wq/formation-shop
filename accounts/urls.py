from django.urls import path
from django.contrib.auth import views as auth_views
from . import views


urlpatterns = [
    path(
        "register/",
        views.register_view,
        name="register"
    ),

    path(
        "login/",
        views.login_view,
        name="login"
    ),

    path(
        "logout/",
        views.logout_view,
        name="logout"
    ),

    path(
        "password-reset/",
        auth_views.PasswordResetView.as_view(
            template_name="accounts/password_reset.html",
            email_template_name="accounts/password_reset_email.html",
            subject_template_name="accounts/password_reset_subject.txt",
            success_url="/accounts/password-reset/done/"
        ),
        name="password_reset"
    ),

    path(
        "password-reset/done/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="accounts/password_reset_done.html"
        ),
        name="password_reset_done"
    ),

    path(
        "password-reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="accounts/password_reset_confirm.html",
            success_url="/accounts/password-reset/complete/"
        ),
        name="password_reset_confirm"
    ),

    path(
        "password-reset/complete/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="accounts/password_reset_complete.html"
        ),
        name="password_reset_complete"
    ),

    path(
        "devenir-vendeur/",
        views.become_seller,
        name="become_seller"
    ),

    path(
        "upgrade-to-premium/",
        views.upgrade_to_premium,
        name="upgrade_to_premium"
    ),

    path(
        "profile/",
        views.profile_view,
        name="profile"
    ),

    path(
        "become-trainer/",
        views.become_trainer,
        name="become_trainer"
    ),

    path(
        "trainer-dashboard/",
        views.trainer_dashboard,
        name="trainer_dashboard"
    ),

    path(
        "dashboard/",
        views.dashboard,
        name="dashboard"
    ),
]