from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from .models import Content


class ContentAdminForm(forms.ModelForm):
    class Meta:
        model = Content
        fields = "__all__"

    def clean(self):
        cleaned = super().clean()
        ctype = cleaned.get("content_type")
        text = (cleaned.get("content") or "").strip()
        uploaded = cleaned.get("file")

        if ctype == "text":
            if not text:
                self.add_error("content", _("Text content is required."))
            if uploaded:
                self.add_error("file", _("Do not upload a file when the type is text."))
        else:
            if not text and not uploaded:
                raise ValidationError(
                    _("Enter a URL or embed code in the text field, or upload a file (or both).")
                )

        return cleaned
