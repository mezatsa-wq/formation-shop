from django.urls import path
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

]
path(
    "profile/",
    views.profile_view,
    name="profile"
),