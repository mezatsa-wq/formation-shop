from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from django.utils.text import slugify

from accounts.models import TrainerProfile
from orders.models import CoursePayment

from .models import Course, Enrollment
from .forms import TrainerCourseForm,LessonForm


def course_list(request):
    courses = Course.objects.filter(
        is_published=True
    ).order_by("-created_at")

    return render(
        request,
        "courses/list.html",
        {"courses": courses}
    )


def course_detail(request, slug):
    course = get_object_or_404(
        Course,
        slug=slug,
        is_published=True
    )

    enrolled = False

    if request.user.is_authenticated:
        enrolled = Enrollment.objects.filter(
            user=request.user,
            course=course
        ).exists()

    return render(
        request,
        "courses/detail.html",
        {
            "course": course,
            "enrolled": enrolled,
        }
    )


@login_required
def my_courses(request):
    enrollments = Enrollment.objects.filter(
        user=request.user
    ).select_related("course").order_by("-enrolled_at")

    return render(
        request,
        "courses/my_courses.html",
        {
            "enrollments": enrollments
        }
    )


@login_required
def course_learning(request, slug):
    course = get_object_or_404(
        Course,
        slug=slug,
        is_published=True
    )

    enrollment = get_object_or_404(
        Enrollment,
        user=request.user,
        course=course
    )

    lessons = course.lessons.all().order_by("order")

    return render(
        request,
        "courses/learning.html",
        {
            "course": course,
            "lessons": lessons,
            "enrollment": enrollment,
        }
    )


@login_required
def create_course(request):

    trainer_profile = TrainerProfile.objects.filter(
        user=request.user
    ).first()

    if not trainer_profile and not request.user.is_superuser:
        messages.error(
            request,
            "Vous devez être formateur ou administrateur pour créer une formation."
        )
        return redirect("home")
    if request.method == "POST":

        form = TrainerCourseForm(request.POST, request.FILES)

        if form.is_valid():

            course = form.save(commit=False)

            # Le formateur connecté devient automatiquement
            # l'instructeur de la formation.
            course.instructor = request.user

            # Création automatique du slug
            base_slug = slugify(course.title)
            slug = base_slug
            counter = 1

            while Course.objects.filter(slug=slug).exists():

                slug = f"{base_slug}-{counter}"
                counter += 1

            course.slug = slug

            course.is_published = True

            course.save()

            messages.success(
                request,
                "Votre formation a été créée avec succès."
            )

            return redirect(
                "trainer_courses"
            )

    else:

        form = TrainerCourseForm()

    return render(
        request,
        "courses/create_course.html",
        {
            "form": form
        }
    )
@login_required
def trainer_courses(request):

    trainer_profile = TrainerProfile.objects.filter(
        user=request.user
    ).first()

    if not trainer_profile and not request.user.is_superuser:
        messages.error(
            request,
            "Vous devez être formateur ou administrateur."
        )
        return redirect("home")

    courses = Course.objects.filter(
        instructor=request.user
    ).prefetch_related(
        "students"
    ).order_by("-created_at")

    return render(
        request,
        "courses/trainer_courses.html",
        {
            "courses": courses
        }
    )
@login_required
def manage_course(request, course_id):
    course = get_object_or_404(
        Course,
        id=course_id,
        instructor=request.user
    )

    lessons = course.lessons.all().order_by("order")

    return render(
        request,
        "courses/manage_course.html",
        {
            "course": course,
            "lessons": lessons,
        }
    )


@login_required
def create_lesson(request, course_id):
    course = get_object_or_404(
        Course,
        id=course_id,
        instructor=request.user
    )

    if request.method == "POST":
        form = LessonForm(request.POST)

        if form.is_valid():
            lesson = form.save(commit=False)
            lesson.course = course
            lesson.save()

            messages.success(
                request,
                "La leçon a été ajoutée avec succès."
            )

            return redirect(
                "manage_course",
                course_id=course.id
            )

    else:
        form = LessonForm()

    return render(
        request,
        "courses/create_lesson.html",
        {
            "form": form,
            "course": course,
        }
    )
@login_required
def course_payment(request, course_id):

    course = get_object_or_404(
        Course,
        id=course_id,
        is_published=True
    )

    if request.method == "POST":

        phone_number = request.POST.get("phone_number")
        method = request.POST.get("method")

        if not phone_number or not method:

            messages.error(
                request,
                "Veuillez remplir tous les champs."
            )

            return render(
                request,
                "orders/course_payment.html",
                {"course": course}
            )

        CoursePayment.objects.create(
            user=request.user,
            course=course,
            phone_number=phone_number,
            method=method,
            amount=course.price,
            status="pending"
        )

        messages.success(
            request,
            "Votre paiement a été envoyé. "
            "Il sera vérifié par l'administrateur."
        )

        return redirect("my_courses")

    return render(
        request,
        "orders/course_payment.html",
        {"course": course}
    )