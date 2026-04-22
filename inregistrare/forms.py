from django import forms
from django.conf import settings
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User
from django.utils import timezone

from estudy.models import UserProfile

from .models import Profile


class InregistrareFormular(UserCreationForm):
    ROLE_CHOICES = [
        (UserProfile.ROLE_STUDENT, "Explorator (copil / elev)"),
        (UserProfile.ROLE_PROFESSOR, "Mentor (profesor)"),
    ]

    email = forms.EmailField(label="Adresă de email", required=True)
    age = forms.IntegerField(
        label="Vârstă",
        min_value=6,
        max_value=100,
        required=True,
        widget=forms.NumberInput(attrs={"min": 6, "max": 100}),
    )
    role = forms.ChoiceField(
        label="Alege rolul",
        choices=ROLE_CHOICES,
        initial=UserProfile.ROLE_STUDENT,
        widget=forms.RadioSelect,
    )
    teacher_code = forms.CharField(
        label="Cod de verificare profesor",
        required=False,
        widget=forms.TextInput(attrs={"autocomplete": "off"}),
        help_text="Profesorii introduc codul primit de la echipa UnITex pentru a valida contul.",
    )
    accept_terms = forms.BooleanField(
        label="Accept Termenii și condițiile",
        required=True,
        error_messages={
            "required": "Trebuie să accepți Termenii și condițiile pentru a crea contul."
        },
    )

    field_order = [
        "username",
        "email",
        "age",
        "role",
        "teacher_code",
        "password1",
        "password2",
        "accept_terms",
    ]

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        text_inputs = [
            "username",
            "email",
            "age",
            "password1",
            "password2",
            "teacher_code",
        ]
        placeholders = {
            "username": "ex: alex_code",
            "email": "ex: nume@scoala.ro",
            "age": "ex: 12",
            "password1": "Minim 8 caractere",
            "password2": "Reintrodu parola",
            "teacher_code": "Cod profesor",
        }
        labels = {
            "username": "Nume de utilizator",
            "password1": "Parolă",
            "password2": "Confirmă parola",
        }
        for field in text_inputs:
            if field in self.fields:
                self.fields[field].widget.attrs.setdefault("class", "input-control")
                if field in placeholders:
                    self.fields[field].widget.attrs.setdefault(
                        "placeholder", placeholders[field]
                    )
        for name, label in labels.items():
            if name in self.fields:
                self.fields[name].label = label
        self.fields[
            "role"
        ].help_text = "Selectează cum vei folosi platforma. Poți modifica alegerea ulterior din profil."
        self.fields["role"].widget.attrs.setdefault("class", "role-radio")
        self.fields["accept_terms"].help_text = (
            "Contul se activează doar după acceptarea termenilor platformei."
        )

    def clean(self):
        cleaned = super().clean()
        role = cleaned.get("role")
        teacher_code = (cleaned.get("teacher_code") or "").strip()
        if role == UserProfile.ROLE_PROFESSOR:
            expected = getattr(settings, "TEACHER_REGISTRATION_CODE", None)
            if not expected:
                raise forms.ValidationError(
                    (
                        "Codul de verificare pentru profesori nu este configurat. "
                        "Contactează administratorul platformei."
                    )
                )
            if teacher_code != expected:
                self.add_error(
                    "teacher_code",
                    (
                        "Codul introdus nu este valid. Verifică emailul primit de la UnITex "
                        "sau contactează administratorul."
                    ),
                )
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data.get("email", "")
        if commit:
            user.save()
            chosen_role = self.cleaned_data.get("role", UserProfile.ROLE_STUDENT)
            profile = getattr(user, "userprofile", None)
            if profile is None:
                UserProfile.objects.create(user=user, status=chosen_role)
            elif profile.status != chosen_role:
                profile.status = chosen_role
                profile.save(update_fields=["status"])
            Profile.objects.update_or_create(
                user=user,
                defaults={
                    "email": self.cleaned_data.get("email", ""),
                    "age": self.cleaned_data.get("age"),
                    "accepted_terms": bool(self.cleaned_data.get("accept_terms")),
                    "accepted_terms_at": timezone.now(),
                    "accepted_terms_version": "v1",
                },
            )
        return user


class LoginFormular(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].label = "Nume de utilizator"
        self.fields["password"].label = "Parolă"
        self.fields["username"].widget.attrs.update(
            {"placeholder": "nume utilizator", "class": "input-control"}
        )
        self.fields["password"].widget.attrs.update(
            {"placeholder": "Parola", "class": "input-control"}
        )
        self.fields["username"].widget.attrs.setdefault("autocomplete", "username")
        self.fields["password"].widget.attrs.setdefault(
            "autocomplete", "current-password"
        )


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ["name", "email", "phone_number", "age", "bio"]
        labels = {
            "name": "Nume complet",
            "email": "Adresă de email",
            "phone_number": "Telefon",
            "age": "Vârstă",
            "bio": "Despre mine",
        }
        widgets = {
            "name": forms.TextInput(
                attrs={"class": "input-control", "placeholder": "ex: Ana Popescu"}
            ),
            "email": forms.EmailInput(
                attrs={"class": "input-control", "placeholder": "ex: ana@unitex.ro"}
            ),
            "phone_number": forms.TextInput(
                attrs={"class": "input-control", "placeholder": "ex: 069123456"}
            ),
            "age": forms.NumberInput(
                attrs={
                    "class": "input-control",
                    "min": 6,
                    "max": 100,
                    "placeholder": "ex: 14",
                }
            ),
            "bio": forms.Textarea(
                attrs={
                    "class": "input-control",
                    "rows": 4,
                    "placeholder": "Spune pe scurt ce îți place să înveți pe platformă.",
                }
            ),
        }
