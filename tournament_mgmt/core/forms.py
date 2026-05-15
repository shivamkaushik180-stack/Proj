"""
OGTRMS - Forms
Online Gaming Tournament Registration & Management System
FINAL ERROR FREE VERSION
"""

from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import UserProfile, Registration, Tournament, Game, ContactMessage


# ═════════════════════════════════════════════
# AUTH FORMS
# ═════════════════════════════════════════════

class SignupForm(UserCreationForm):
    first_name = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'First Name'
        })
    )

    last_name = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Last Name'
        })
    )

    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Email Address'
        })
    )

    mobile = forms.CharField(
        max_length=15,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Mobile Number'
        })
    )

    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Username'
        })
    )

    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Password'
        })
    )

    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm Password'
        })
    )

    class Meta:
        model = User
        fields = (
            'first_name',
            'last_name',
            'username',
            'email',
            'mobile',
            'password1',
            'password2'
        )

    def clean_email(self):
        email = self.cleaned_data.get('email')

        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Email already registered.")

        return email

    def clean_mobile(self):
        mobile = self.cleaned_data.get('mobile')

        if not mobile.isdigit():
            raise forms.ValidationError("Mobile must contain digits only.")

        if len(mobile) < 10:
            raise forms.ValidationError("Enter valid mobile number.")

        return mobile

    def save(self, commit=True):
        user = super().save(commit=False)

        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']

        if commit:
            user.save()

        return user


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Username'
        })
    )

    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Password'
        })
    )


class OTPVerificationForm(forms.Form):
    otp = forms.CharField(
        max_length=6,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter OTP'
        })
    )

    def clean_otp(self):
        otp = self.cleaned_data.get('otp')

        if not otp.isdigit() or len(otp) != 6:
            raise forms.ValidationError("Enter valid 6 digit OTP.")

        return otp


class ForgotPasswordForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Registered Email'
        })
    )

    def clean_email(self):
        email = self.cleaned_data.get('email')

        if not User.objects.filter(email=email).exists():
            raise forms.ValidationError("No account found.")

        return email


class ChangePasswordForm(forms.Form):
    new_password = forms.CharField(
        min_length=8,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'New Password'
        })
    )

    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm Password'
        })
    )

    def clean(self):
        cleaned = super().clean()

        p1 = cleaned.get('new_password')
        p2 = cleaned.get('confirm_password')

        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("Passwords do not match.")

        return cleaned


# ═════════════════════════════════════════════
# PROFILE FORM
# ═════════════════════════════════════════════

class UserProfileForm(forms.ModelForm):
    first_name = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    last_name = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = UserProfile
        fields = ['mobile', 'bio', 'avatar']

        widgets = {
            'mobile': forms.TextInput(attrs={'class': 'form-control'}),
            'bio': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3
            }),
            'avatar': forms.FileInput(attrs={'class': 'form-control'}),
        }


# ═════════════════════════════════════════════
# TOURNAMENT REGISTRATION
# ═════════════════════════════════════════════

class RegistrationForm(forms.ModelForm):

    class Meta:
        model = Registration
        fields = [
            'full_name',
            'email',
            'mobile',
            'ingame_uid',
            'ingame_name',
            'team_name',
            'team_members',
            'payment_screenshot',
            'payment_reference'
        ]

        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'mobile': forms.TextInput(attrs={'class': 'form-control'}),
            'ingame_uid': forms.TextInput(attrs={'class': 'form-control'}),
            'ingame_name': forms.TextInput(attrs={'class': 'form-control'}),
            'team_name': forms.TextInput(attrs={'class': 'form-control'}),
            'team_members': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'payment_screenshot': forms.FileInput(attrs={'class': 'form-control'}),
            'payment_reference': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # optional fields
        self.fields['team_name'].required = False
        self.fields['team_members'].required = False
        self.fields['payment_screenshot'].required = False
        self.fields['payment_reference'].required = False

    def clean_mobile(self):
        mobile = self.cleaned_data['mobile']

        if not mobile.isdigit() or len(mobile) != 10:
            raise forms.ValidationError("Enter valid 10 digit mobile number.")

        return mobile


# ═════════════════════════════════════════════
# ADMIN FORMS
# ═════════════════════════════════════════════

class TournamentForm(forms.ModelForm):

    class Meta:
        model = Tournament
        exclude = ['registered_slots', 'created_at', 'updated_at']

        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'game': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4
            }),
            'tournament_type': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),

            'entry_fee': forms.NumberInput(attrs={'class': 'form-control'}),
            'prize_pool': forms.NumberInput(attrs={'class': 'form-control'}),
            'first_prize': forms.NumberInput(attrs={'class': 'form-control'}),
            'second_prize': forms.NumberInput(attrs={'class': 'form-control'}),
            'third_prize': forms.NumberInput(attrs={'class': 'form-control'}),
            'total_slots': forms.NumberInput(attrs={'class': 'form-control'}),

            'start_date': forms.DateTimeInput(
                format='%Y-%m-%dT%H:%M',
                attrs={'type': 'datetime-local', 'class': 'form-control'}
            ),
            'end_date': forms.DateTimeInput(
                format='%Y-%m-%dT%H:%M',
                attrs={'type': 'datetime-local', 'class': 'form-control'}
            ),
            'registration_deadline': forms.DateTimeInput(
                format='%Y-%m-%dT%H:%M',
                attrs={'type': 'datetime-local', 'class': 'form-control'}
            ),

            'room_id': forms.TextInput(attrs={'class': 'form-control'}),
            'room_password': forms.TextInput(attrs={'class': 'form-control'}),
            'map_name': forms.TextInput(attrs={'class': 'form-control'}),
            'upi_id': forms.TextInput(attrs={'class': 'form-control'}),
            'rules': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4
            }),
            'banner_image': forms.FileInput(attrs={'class': 'form-control'}),
            'is_featured': forms.CheckboxInput(),
        }

    def __init__(self, *args, **kwargs):
     super().__init__(*args, **kwargs)

     self.fields['start_date'].input_formats = ['%Y-%m-%dT%H:%M']
     self.fields['end_date'].input_formats = ['%Y-%m-%dT%H:%M']
     self.fields['registration_deadline'].input_formats = ['%Y-%m-%dT%H:%M']

    # EDIT PAGE VALUE SHOW FIX
     if self.instance.pk:
        self.initial['start_date'] = self.instance.start_date.strftime('%Y-%m-%dT%H:%M')
        self.initial['end_date'] = self.instance.end_date.strftime('%Y-%m-%dT%H:%M')
        self.initial['registration_deadline'] = self.instance.registration_deadline.strftime('%Y-%m-%dT%H:%M')
    def clean(self):
        cleaned = super().clean()

        start = cleaned.get('start_date')
        end = cleaned.get('end_date')
        reg = cleaned.get('registration_deadline')

        if start and end and start >= end:
            raise forms.ValidationError(
                "End date must be after start date."
            )

        if reg and start and reg >= start:
            raise forms.ValidationError(
                "Registration deadline must be before start date."
            )

        return cleaned


class GameForm(forms.ModelForm):

    class Meta:
        model = Game
        fields = '__all__'


# ═════════════════════════════════════════════
# CONTACT FORM
# ═════════════════════════════════════════════

class ContactForm(forms.ModelForm):

    class Meta:
        model = ContactMessage
        fields = [
            'name',
            'email',
            'subject',
            'message'
        ]

        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'subject': forms.TextInput(attrs={'class': 'form-control'}),
            'message': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5
            }),
        }