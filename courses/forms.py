from django import forms

from .models import Course, Lesson


class TrainerCourseForm(forms.ModelForm):

    class Meta:
        model = Course

        fields = [
            "category",
            "title",
            "description",
            "price",
            "image",
        ]

        widgets = {

            "category": forms.Select(
                attrs={
                    "class": "form-control"
                }
            ),

            "title": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Ex : Apprendre Python de zéro"
                }
            ),

            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "placeholder": "Présentez votre formation...",
                    "rows": 7
                }
            ),

            "price": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Prix en FCFA",
                    "min": "0"
                }
            ),

            "image": forms.ClearableFileInput(
                attrs={
                    "class": "form-control"
                }
            ),
        }

class LessonForm(forms.ModelForm):
    class Meta:
        model = Lesson
        fields = ["title", "video_url", "content", "order"]

        widgets = {
            "title": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Ex : Introduction à Python"
                }
            ),
            "video_url": forms.URLInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "https://www.youtube.com/..."
                }
            ),
            "content": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "placeholder": "Contenu de la leçon...",
                    "rows": 10
                }
            ),
            "order": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": "1",
                    "placeholder": "1"
                }
            ),
        }