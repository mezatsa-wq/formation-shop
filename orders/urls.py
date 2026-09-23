from django.urls import path
from . import views

urlpatterns = [
    path(
        "course/<int:course_id>/payment/",
        views.course_payment,
        name="course_payment"
    ),

    path(
        "order/<int:order_id>/delivered/",
        views.mark_order_delivered,
        name="mark_order_delivered"
    ),
]