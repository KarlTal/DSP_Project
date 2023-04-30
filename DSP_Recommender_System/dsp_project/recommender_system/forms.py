from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from recommender_system.models import * 
from django import forms
# Form: CreateUserForm
# Purpose: To create users
class CreateUserForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username','email' ,'password1', 'password2']


class UpdateBookRatingForm(forms.ModelForm):
    class Meta:
        model = Book_Library
        fields = ['rating']

class UploadBookImageForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = ["book_id","title","cover_image"]

class UpdateFavouriteBookReviewForm(forms.ModelForm):
    class Meta:
        model = AdminMonthlyFavourites
        fields = ["review"]