from django.db import models
from django.contrib.auth.models import User


class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)

    def _str_(self):
        return self.name





class Course(models.Model):
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="courses"
    )

    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField()

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    image = models.ImageField(
        upload_to="courses/",
        blank=True,
        null=True
    )

    instructor = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="courses"
    )

    is_published = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def _str_(self):
        return self.title

class Lesson(models.Model):
        course = models.ForeignKey(
            Course,
            on_delete=models.CASCADE,
            related_name="lessons"
        )

        title = models.CharField(max_length=200)

        video_url = models.URLField(
            blank=True,
            null=True
        )

        content = models.TextField(
            blank=True
        )

        order = models.PositiveIntegerField(
            default=0
        )

        def _str_(self):
            return f"{self.course.title} - {self.title}"

class Enrollment(models.Model):
            user = models.ForeignKey(
                User,
                on_delete=models.CASCADE,
                related_name="enrollments"
            )

            course = models.ForeignKey(
                Course,
                on_delete=models.CASCADE,
                related_name="students"
            )

            enrolled_at = models.DateTimeField(
                auto_now_add=True
            )

            def _str_(self):
                return f"{self.user.username} - {self.course.title}"