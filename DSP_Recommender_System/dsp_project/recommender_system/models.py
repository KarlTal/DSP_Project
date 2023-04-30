from django.db import models
from django.contrib.auth.models import User,Group
# Create your models here.


class Library(models.Model):
    library_id = models.AutoField(primary_key=True)
    user_id = models.ForeignKey(User, blank=True, null=True, on_delete=models.CASCADE)
    private = models.BooleanField(default=False)


class Book(models.Model):
    book_id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=255)
    cover_image = models.ImageField('media/bookImages/',null=True,blank=True)

class Book_Library(models.Model):
    id = models.AutoField(primary_key=True)
    library = models.ForeignKey(Library,null=True,blank=True, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, null=True, blank=True, on_delete=models.CASCADE)
    rating_choices = ((1,1),(2,2),(3,3),(4,4),(5,5))
    rating = models.IntegerField(choices = rating_choices)

class AdminMonthlyFavourites(models.Model):
    id = models.AutoField(primary_key=True)
    book = models.ForeignKey(Book, null=True, blank=True, on_delete=models.CASCADE)
    review = models.TextField(null=True,blank=True)

# Create the user groups.
def setup_groups():
    Group.objects.get_or_create(name='Admin')
    Group.objects.get_or_create(name='User')

def setup_user(user, group_key):
    # Ensure that the websites groups have been created.
    setup_groups()

    # Assign the user to their designated group.
    group = Group.objects.get(name=group_key)
    user.groups.add(group)


def get_group(user):
    return user.groups.all()[0].name

