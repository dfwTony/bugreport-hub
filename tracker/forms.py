from .models import BugReport
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

User = get_user_model()


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "form-control"

class BugReportForm(forms.ModelForm):
    class Meta:
        model = BugReport
        fields = ["title", "module", "description", "steps_to_reproduce", "priority"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
            "steps_to_reproduce": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            css = "form-select" if isinstance(field.widget, forms.Select) else "form-control"
            field.widget.attrs["class"] = css

class StaffUpdateForm(forms.ModelForm):
    note = forms.CharField(max_length=255, required=False, label="Note for the reporter")

    class Meta:
        model = BugReport
        fields = ["status", "priority", "category", "assigned_to"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["assigned_to"].queryset = User.objects.filter(is_staff=True)
        for field in self.fields.values():
            css = "form-select" if isinstance(field.widget, forms.Select) else "form-control"
            field.widget.attrs["class"] = css