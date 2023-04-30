from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import path
from . import views

urlpatterns=[
    path('',views.home,name='Homepage'),
    path('upload_data/', views.upload_data, name = 'UploadUserData'),
    path('login/', views.login_user, name='Login'),
    path('logout/', views.logout_user, name='Logout'),
    path('register/', views.register, name='Register'),
    path('user_home/',views.user_home,name="UserHome"),
    path('update_rating/<bookId>',views.modify_book_rating, name="UpdateRating"),
    path('recommend_home/',views.recommend_home, name = "RecommendHome"),
    path('view_books/',views.available_books,name='Books'),
    path('view_books/add_book_to_library/<bookId>',views.add_book_to_library, name='AddBookLibrary'),
    path('about/',views.about, name ='About'),
    path('view_all_users/',views.view_all_users,name="ViewAllUsers"),
    path('current_favourites/',views.view_current_favourites,name="CurrentFavourites"),
    path('view_books/add_current_favourites/<bookId>',views.add_current_favourites,name="AddBookFavourites"),
    path('view_books/update_book/<bookId>',views.update_books,name="UpdateBook"),
    path('current_favourites/delete/<bookId>',views.delete_favourite_book,name="UnfavouriteBook"),
    path('current_favourites/update_review/<favouriteId>',views.update_admin_book_review,name="UpdateAdminBookReview"),
    path('search_user_libraries',views.search_other_users_library,name="SearchUserLibraries"),
    path('update_privacy_setting',views.update_privacy_setting,name='UpdatePrivacySetting')
]