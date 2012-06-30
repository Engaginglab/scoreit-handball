from django import forms
from django.utils.translation import ugettext as _
from django.contrib.auth.models import User


class SignUpForm(forms.Form):
    username = forms.CharField(label=_('User name'), required=True)
    email = forms.EmailField(label=_('Email'), required=True)
    password = forms.CharField(widget=forms.PasswordInput,
        label=_('Password'), required=True)
    password_repeat = forms.CharField(widget=forms.PasswordInput,
        label=_('Repeat password'), required=True)

    def clean_username(self):
        data = self.cleaned_data['username']
        try:
            User.objects.get(username=data)
        except User.DoesNotExist:
            return data
        raise forms.ValidationError(_('This username is already taken.'))

    def clean_email(self):
        data = self.cleaned_data['email']
        try:
            User.objects.get(email=data)
        except User.DoesNotExist:
            return data
        raise forms.ValidationError(
            _('A user with this email is already registered.'))

    def clean(self):
        cleaned_data = super(SignUpForm, self).clean()
        password = cleaned_data.get('password')
        password_repeat = cleaned_data.get('password_repeat')

        # check if passwords match
        if password and password_repeat and password != password_repeat:
            msg = _('The passwords do not match!')
            self._errors['password'] = self.error_class([msg])
            self._errors['password_repeat'] = self.error_class([msg])

            del cleaned_data['password']
            del cleaned_data['password_repeat']

        return cleaned_data
