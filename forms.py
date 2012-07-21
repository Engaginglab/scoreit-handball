from django import forms
from django.utils.translation import ugettext as _
from django.contrib.auth.models import User
from handball.models import Person


class SignUpForm(forms.Form):
    username = forms.CharField(label=_('User name'), required=True)
    email = forms.EmailField(label=_('Email'), required=True)
    password = forms.CharField(widget=forms.PasswordInput,
        label=_('Password'), required=True)
    # password_repeat = forms.CharField(widget=forms.PasswordInput,
    #     label=_('Repeat Password'), required=True)

    first_name = forms.CharField(label=_('First Name'), required=True)
    last_name = forms.CharField(label=_('Last Name'), required=True)
    profile = forms.ModelChoiceField(required=False, queryset=Person.objects.filter(user__isnull=True))
    # gender = forms.ChoiceField(choices=(('male', _('male')), ('female', _('female'))))
    # pass_number = forms.IntegerField(label=_('Pass Number'), required=False)
    # address = forms.CharField(label=_('Address'), required=False)
    # city = forms.CharField(label=_('City'), required=False)
    # zip_code = forms.IntegerField(label=_('Zip Code'), required=False)
    # mobile_number = forms.CharField(label=_('Mobile Number'), required=False)

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

    # def clean(self):
    #     cleaned_data = super(SignUpForm, self).clean()
    #     pass_number = cleaned_data['pass_number']
    #     profile_id = cleaned_data['profile'].id if cleaned_data['profile'] else None

    #     # check if pass number is unique
    #     try:
    #         Person.objects.exclude(id=profile_id).get(pass_number=pass_number)
    #     except Person.DoesNotExist:
    #         return cleaned_data

    #     msg = _('A user with this pass number does already exist!')
    #     self._errors['pass_number'] = self.error_class([msg])
    #     del cleaned_data['pass_number']

    #     return cleaned_data

    # def clean(self):
    #     cleaned_data = super(SignUpForm, self).clean()
    #     password = cleaned_data.get('password')
    #     password_repeat = cleaned_data.get('password_repeat')

    #     # check if passwords match
    #     if password and password_repeat and password != password_repeat:
    #         msg = _('The passwords do not match!')
    #         self._errors['password'] = self.error_class([msg])
    #         self._errors['password_repeat'] = self.error_class([msg])

    #         del cleaned_data['password']
    #         del cleaned_data['password_repeat']

    #     return cleaned_data
