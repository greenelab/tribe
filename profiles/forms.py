from django import forms
from django.contrib.auth.models import User
from allauth.utils import email_address_exists

class CreateTempAcctForm(forms.Form):
    accepted = forms.BooleanField(label="Make a new anonymous, temporary account which will remain active on your browser for 1 year or until you clear your browser's cookies.")

    def clean_accept(self):
        accepted = self.cleaned_data['accepted']
        if (accepted != True):
            raise forms.ValidationError("You must click this checkbox to create a new temporary account.")
        return accepted

class UpgradeUserForm(forms.Form):
    email    = forms.EmailField(widget=forms.EmailInput(attrs={'placeholder': 'E-mail address'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Password'}))
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Repeat password'}))

    def clean_email(self):
        cleaned_email = self.cleaned_data['email']
        if cleaned_email and email_address_exists(cleaned_email):
            raise forms.ValidationError("This email is already used for an existing account. Please choose another.")
        return cleaned_email

    def clean_confirm_password(self):
        confirm_password = self.cleaned_data['confirm_password']
        password = self.cleaned_data['password']
        if (confirm_password != password):
            raise forms.ValidationError("The two entered passwords must match.")
        return confirm_password
