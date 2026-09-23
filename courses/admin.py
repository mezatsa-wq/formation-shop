from django.contrib import admin
from .models import Category, Course, Lesson, Enrollment


admin.site.register(Category)
admin.site.register(Course)
admin.site.register(Lesson)
admin.site.register(Enrollment)