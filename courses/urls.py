from django.urls import path
from . import views

urlpatterns = [
    path("", views.course_list, name="course_list"),

    path("mes-formations/", views.my_courses, name="my_courses"),

    path("create/", views.create_course, name="create_course"),

    path(
        "mes-formations-formateur/",
        views.trainer_courses,
        name="trainer_courses"
    ),

    # Gestion d'une formation
    path(
        "<int:course_id>/manage/",
        views.manage_course,
        name="manage_course"
    ),

    # Création d'une leçon
    path(
        "<int:course_id>/lessons/create/",
        views.create_lesson,
        name="create_lesson"
    ),

    # Détail d'une formation
    path(
        "<slug:slug>/",
        views.course_detail,
        name="course_detail"
    ),

    path(
        "<slug:slug>/apprendre/",
        views.course_learning,
        name="course_learning"
    ),
]