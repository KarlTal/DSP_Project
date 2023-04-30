# Django related imports
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.files.storage import FileSystemStorage
from recommender_system.models import *
from .decorators import *
from .forms import *
from django.db.models import Q

# Recommender System Required Imports
import pandas as pd
import csv
from sklearn.metrics.pairwise import cosine_similarity
from scipy.sparse import coo_matrix
import numpy as np

# User authorisation/authentication
from django.contrib.auth.decorators import login_required
from .decorators import *

# Testing imports
# from benchmark_timer import BenchmarkTimer
import time
#Files handling
import os
import magic
import petl as etl

#Admin
from random import shuffle
# with BenchmarkTimer(name="MySimpleCode") as tm, tm.single_iteration():
#     pass

#--------------------------------------------------File type checker and validator--------------------------------------------------------------------

def validate_file(file):
    fs = FileSystemStorage()
    name = fs.save(file.name, file)
    print(name)
    media_folder = './media/'
    # Creates the expected headers and constraints to test out the data type 
    # and ensure that there are no empty fields.
    header = ('','user_id','book_id','rating','title')
    constraints = [
        dict(name='user_id_int',field='user_id',test =int),
        dict(name='book_id_int',field='book_id',test =int),
        dict(name='rating_int',field='rating',test =int),
        dict(name='not_none',assertion = lambda row:None not in row)
    ]
    # Using the python magic to first check the file extensions, 
    # if not equal to CSV text then delete and return error message
    if (magic.from_file(f"{media_folder}{name}")!="CSV text"):
        filename =(f"{media_folder}{name}")
        if os.path.isfile(filename):
            os.remove(filename)
            print("File has been deleted")
        else:
            print("File does not exist")
        return '',2
    else:
        # Using the petl library to read the csv into a table and validate it against the
        # defined headers and constraints.
        table = etl.fromcsv(f"{media_folder}{name}")
        problems = etl.validate(table, constraints=constraints, header=header)
        if len(problems)>1:
            os.remove(f"{media_folder}{name}")
            print("File has been deleted")
            return '',1 #Failed to pass validation check
        else:
            return name,0 #Passed

#--------------------------------------------------Global Functionalities--------------------------------------------------------------------
def home(request):
    #Sets up the groups of the Django application if this was the first time the program was executed.
    setup_groups()
    context = {}
    #Obtains all the admins favourite books that has a cover image attached
    monthly_favourites = AdminMonthlyFavourites.objects.exclude(Q(book_id__in=Book.objects.filter(cover_image__exact=''))
                                                                |Q(book_id__in=Book.objects.filter(cover_image__exact=None))
                                                                |Q(review=None))
    #Only display 8 randomly selected favourites of the admin
    if len(monthly_favourites)>=8:
        list_of_monthly_favourites=list(monthly_favourites)
        # Randomly shuffle the order of the obtained query set to
        # add some randomness and dynamic properties of the home page
        shuffle(list_of_monthly_favourites)
        context = {
            'monthly_favourites' : list_of_monthly_favourites[:6],
        }
    else:
        list_of_monthly_favourites=list(monthly_favourites)
        shuffle(list_of_monthly_favourites)
        context = {
            'monthly_favourites' : list_of_monthly_favourites[:len(monthly_favourites)],
        }
        return render(request, 'recommender_system/home.html',context)
    return render(request, 'recommender_system/home.html',context)

#--------------------------------------------------Admin Functionalities--------------------------------------------------------------------
@login_required(login_url='/login')
@allowed_users(allowed_roles='Admin')
def view_all_users(request):
    #Filter through and obtain all the users in the group "User"
    users = User.objects.filter(groups__name="User")
    context = {
        "users" : users
    }
    return render(request, 'recommender_system/view_all_users.html',context)

@login_required(login_url='/login')
@allowed_users(allowed_roles='Admin')
def view_current_favourites(request):
    #Obtain all the admin's favourite books
    books = AdminMonthlyFavourites.objects.all()
    context = {
        "books" : books
    }
    return render(request, 'recommender_system/current_favourites.html',context)

@login_required(login_url='/login')
@allowed_users(allowed_roles='Admin')
def update_admin_book_review(request,favouriteId):
    # If the favourite book id was passed in 
    if favouriteId:
        #1. Obtain the object with the corresponding id
        #2. Pass in the object as an instance to automatically fill in the form
        #3. If the form is valid save the changes and redirect to the admin's current favourite books page.
        lookup = AdminMonthlyFavourites.objects.get(id=favouriteId)
        form = UpdateFavouriteBookReviewForm(request.POST or None, instance=lookup)
        if form.is_valid():
            form.save()
            return redirect(view_current_favourites)

        context = {
            'form' : form,
            'book' : lookup,
        }

        return render(request, 'recommender_system/update_admin_review.html',context)

    return redirect(view_current_favourites)

@login_required(login_url='/login')
@allowed_users(allowed_roles='Admin')
def add_current_favourites(request,bookId):
    # Create a new entry to the AdminMonthlyFavourites table with the bookId that was passed
    AdminMonthlyFavourites.objects.create(book = Book.objects.get(book_id=bookId))
    print("Added to favourites")
    return redirect(available_books)
    
@login_required(login_url='/login')
@allowed_users(allowed_roles='Admin')
def update_books(request,bookId):
    # If the book id was passed in 
    if bookId:
        #1. Obtain the object with the corresponding id
        #2. Pass in the object as an instance to automatically fill in the form
        #3. If the form is valid save the changes and redirect to the available books page.
        lookup = Book.objects.get(book_id=bookId)
        form = UploadBookImageForm(request.POST or None, request.FILES or None, instance=lookup)

        if form.is_valid():
            form.save()
            return redirect(available_books)
        
        context = {
            'form' : form,
            'book' : lookup,
        }
        # Render the page.
        return render(request, 'recommender_system/update_book.html', context)

    # Redirect back to the homepage.
    return redirect(available_books)

@login_required(login_url='/login')
@allowed_users(allowed_roles='Admin')
def delete_favourite_book(request,bookId):
    # 1. Obtain the object that correspond to the book id that was passed in.
    # 2. Delete the instance from the database.
    favourite_book = AdminMonthlyFavourites.objects.get(book=Book.objects.get(book_id=bookId))
    favourite_book.delete()
    return redirect(view_current_favourites)

#--------------------------------------------------User Functionalities--------------------------------------------------------------------
@login_required(login_url='/login')
@allowed_users(allowed_roles='User')
def user_home(request):
    #Obtain all books and place in a table
    context ={
        "first_name": request.user.first_name
    }
    user_books = []
    #Checks if the current user has a library foreign key linked
    if Library.objects.filter(user_id=request.user.id).exists():
        # If the user has change their privacy setting and pressed the update button
        if request.method=='POST':
            if request.POST.get('setting')=='private':
                user = request.user
                user_library = Library.objects.get(user_id=user)
                user_library.private = True
                user_library.save()
            elif request.POST.get('setting')=='public':
                user = request.user
                user_library = Library.objects.get(user_id=user)
                user_library.private = False
                user_library.save()
        # Obtains the library id corresponding to the logged in user
        user_library_id = Library.objects.get(user_id=request.user.id)
        # Obtain all the books in the current logged in user's library
        user_books = Book_Library.objects.filter(library=user_library_id)
        # Sort the user's library by rating starting from highest (5*) to lowest (0 = unrated)
        order_rating_user_books = user_books.order_by('-rating')
        #Pie chart of ratings distribution of user
        rating_data = []
        for i in range (1,6):
            rating_data.append(user_books.filter(rating=i).count())
        privacy_setting=''
        if user_library_id.private ==False:
            privacy_setting = 'Public'
        else:
            privacy_setting= 'Private'
        context ={
            "user_library" : user_books,
            "ordered_by_ratings_books": order_rating_user_books,
            "rating_data" : rating_data,
            "first_name": request.user.first_name,
            'privacy_setting': privacy_setting,
            'privacy':user_library_id.private,
        }
        return render(request, 'recommender_system/user_home.html',context)
    return render(request, 'recommender_system/user_home.html',context)

@login_required(login_url='/login')
@allowed_users(allowed_roles='User')
def upload_data(request):
    context = {}
    
    if request.method == 'POST':
        # If the user has selected a file and pressed the upload button
        # The validator will read the file and check whether it passes or fail
        # If it passes then it will be processed else an error message will be returned
        # and the user will be prompted to re-enter the correct file.
        checkfile = request.FILES['document']
        name,check = validate_file(checkfile)
        if check ==1:
            error_message = "Failed validation check"
            context = {
                'error_message': error_message
            }
            return render(request,'recommender_system/upload_data.html',context)
        elif check==2:
            error_message = "Not a CSV File"
            context = {
                'error_message': error_message
            }
            return render(request,'recommender_system/upload_data.html',context)
        media_folder = './media/'
        df = pd.read_csv(f"{media_folder}{name}")
        df2 = df.rename(columns={'Book Id':'book_id', 'My Rating':'rating', 'Title':'title'}, inplace = False)
        df2['user_id']=-1 #Set the current user's id to -1, to eliminate the need to find the final user and obtain the next available id.
        my_ratings = df2[['user_id','book_id','rating','title']]
        my_ratings.to_csv('./media/'+name, encoding='utf-8')

        ''' Steps
            1. If user_id not in library model, create a new entry.
            2. Import all the book_id into the Book Table - if exists skip else insert.
            3. Insert all entries in the Book_Library with the user's library_id.
            4. Save entries.
            5. Delete the uploaded csv file to free storage.
        '''
        
        #1. If user_id not in library model, create a new entry for the current user.
        if Library.objects.filter(user_id=request.user.id).exists():
            user_library = Library.objects.get(user_id=request.user)
        else:
            Library(user_id=request.user).save()
            user_library = Library.objects.get(user_id=request.user.id)

        filename =(f"{media_folder}{name}")
        with open(filename, 'r') as csvfile:
            datareader = csv.DictReader(csvfile)
            for row in datareader:
                book_id = int(row['book_id'])
                user_library = Library.objects.get(user_id=request.user)
                # 2. Import all the book_id into the Book Table - if exists skip else insert
                if Book.objects.filter(book_id=book_id,title = row['title']).exists():
                    if Book_Library.objects.filter(library= user_library,book = Book.objects.get(book_id=book_id), rating = int(row['rating'])).exists():
                        break
                    else:
                        #3. Insert all entries in the Book_Library with the user's library_id
                        Book_Library.objects.create(library= user_library,book = Book.objects.get(book_id=book_id),rating = int(row['rating']))
                else:
                    Book.objects.create(book_id=book_id,title = row['title'])
                    #3. Insert all entries in the Book_Library with the user's library_id
                    #4. Save entries
                    Book_Library.objects.create(library= user_library,book = Book.objects.get(book_id=book_id),rating = int(row['rating']))
        #5. After adding the imported library to the database, delete the uploaded csv file
        if os.path.isfile(filename):
            os.remove(filename)
            print("File has been deleted")
        else:
            print("File does not exist")
        
        return redirect(user_home)
    
    else:
        return render(request,'recommender_system/upload_data.html')

@login_required(login_url='/login')
@allowed_users(allowed_roles='User')
def recommend_home(request):
    context = {}
    if request.session["ran_recommender"] == []:
        if Library.objects.filter(user_id=request.user.id).exists():
            user_library = Library.objects.get(user_id=request.user)
            if len(Book_Library.objects.filter(library=user_library))>0:
                # 1. Obtain the current user's library of rated books
                qs = Book_Library.objects.filter(library_id=user_library.library_id).values()
                # 2. Assign to a dataframe using the from_records as it is a query set.
                my_books =pd.DataFrame.from_records(qs)
                # 3. Store the current user's user_id as -1
                my_books['user_id'] = -1
                # 4. Ensure that the book_id column is of type string
                my_books["book_id"] = my_books["book_id"].astype(str)
                # 5. Finding users similar to the current user
                # 6. Load in the mapping file between the book ids
                csv_book_mapping = {}
                static_recommender_folder = './csv_files/'
                bookmap = 'book_id_map.csv'
                with open(f"{static_recommender_folder}{bookmap}", "r") as f:
                    while True:
                        line = f.readline() #Read line by line 
                        if not line:
                            break #End the loop once its done reading
                        csv_id, book_id = line.strip().split(",") # Split to 2 variables, removes new line characters
                        csv_book_mapping[csv_id] = book_id  #Assign to the dictionary

                book_set = set(my_books["book_id"]) #Creates a unique set (list) that contains all the books the user has read
                overlap_users = {}

                # 7. Read the 10 million chunk of user ratings
                chunk = 'chunk0.csv'
                with open(f"{static_recommender_folder}{chunk}", "r") as f:
                    while True:
                        line = f.readline()
                        if not line:
                            break
                        # Get the book_id by invoking the csv_book_mapping created above.
                        user_id, csv_id, _, rating, _ = line.split(",")

                        book_id = csv_book_mapping.get(csv_id)

                        if book_id in book_set:
                            if user_id not in overlap_users:
                            # If the current book has been read by the current user
                            # and that user is not in the overlap_user dictionary
                            # then add that user

                            #Key and value pairs
                            #Key = user_id
                            #Value = number of times they have read the same books as the current user
                                overlap_users[user_id] = 1
                            else:
                            # If user has already read a book that is the same as the current user
                            # then increase their book count by 1
                                overlap_users[user_id] += 1
                # 8. Filter the similar users that only read 10% of the same books as us, since user's who has less than 10% will not be useful.
                filtered_overlap_users = set([k for k in overlap_users if overlap_users[k] > my_books.shape[0]/10]) # 10%
                interactions_list = []

                # Open the 10 million user interaction csv file.
                with open(f"{static_recommender_folder}{chunk}", "r") as f:
                    while True:
                        line = f.readline()
                        if not line:
                            break
                        user_id, csv_id, _, rating, _ = line.split(",")
                        # If the user in the interactions are one that are chosen to be used for the recommendation
                        # Add their books and corresponding ratings to the interaction_list
                        if user_id in filtered_overlap_users:
                            book_id = csv_book_mapping[csv_id]
                            interactions_list.append([user_id, book_id, rating])
                # 9. Convert the interactions list to a pandas dataframe with columns of user_id, book_id and rating
                interactions = pd.DataFrame(interactions_list, columns=["user_id", "book_id", "rating"])
                # 10. Add  the current user's ratings to the matrix through pandas' concat 
                interactions = pd.concat([my_books[["user_id", "book_id", "rating"]], interactions])
                # 11. Data preprocessing
                #     Ensure that they are the same data type as the books_titles.json
                interactions["book_id"] = interactions["book_id"].astype(str)
                interactions["user_id"] = interactions["user_id"].astype(str)
                interactions["rating"] = pd.to_numeric(interactions["rating"])
                # 12. Create a column of user_index and paste the user_id column but as type of category
                #     All the identical numbers are converted to the same category
                interactions["user_index"] = interactions["user_id"].astype("category").cat.codes
                interactions["book_index"] = interactions["book_id"].astype("category").cat.codes
                # 13. Sparse matrix
                #     No value in the column, doesn't take any space
                #     Create using coo matrix from scipy
                #     A matrix using an array/list, user_index (row positions) and column positions.
                ratings_mat_coo = coo_matrix((interactions["rating"], (interactions["user_index"], interactions["book_index"])))
                ratings_mat = ratings_mat_coo.tocsr()
                # 14. As the dataset is large, it will be troubling to identify a id
                #     that does not correspond to an existing user hence the current user_id will be -1
                #     The users in the database will not be used in the recommendation system.
                interactions[interactions["user_id"] == "-1"]
                my_index = 0

                # 15. Finds the similarity between each user in the matrix in correspondence to the current user
                #     Flatten to turn into an np array.
                #     COS, 1 = Best (Highest) similarity
                similarity = cosine_similarity(ratings_mat[my_index,:], ratings_mat).flatten()

                # 16. As sometimes the recommendation will not return a large amount of similar users
                #     Select the 10 most similar users, if it is less than that select that amount of similar users instead
                if len(similarity) <10:
                    indices = np.argpartition(similarity, -(len(similarity)))[-(len(similarity)):]
                else:
                    indices = np.argpartition(similarity, -10)[-10:]

                # 17. Find the all of the rows where the user_index is in the indices numpy array and copy it over
                #     to similar users which will have the user_id alongside the rating, user_index, and book_index
                similar_users = interactions[interactions["user_index"].isin(indices)].copy()
                # 18. Remove the current user from the similar user
                similar_users = similar_users[similar_users["user_id"]!="-1"]

                # 18. Find the number of times a book appears in the similar users' recommendation
                #     Group the users by book_id, then calculate the number of times a book appears
                #     Then calculate the mean/average rating of the book into a mean column
                book_recs = similar_users.groupby("book_id").rating.agg(['count', 'mean'])
                # 19. Read the book_titles which will help map the title to the book_id
                books_titles = pd.read_json("csv_files/books_titles.json")
                books_titles["book_id"] = books_titles["book_id"].astype(str)
                # 20. Inner join merge the 2 pandas dataframe to get the book title based on the same book_id
                book_recs = book_recs.merge(books_titles, how="inner", on="book_id")
                # 21. Remove books in the recommedation that the current user has already read and rated in the my_books dataframe
                book_recs = book_recs[~book_recs["book_id"].isin(my_books["book_id"])]
                # 22. Set the mean score to 2.5 as anything higher will result in less recommended books
                #     As 10 million entries only accounts for just over 3k unique users.
                book_recs = book_recs[book_recs["mean"] >=2.5]
                # 23. More than 2 users in the similar users has rated.
                book_recs = book_recs[book_recs["count"]>2]
                # 24. Sort the top recommendations with the highest mean score at the top
                top_recs = book_recs.sort_values("mean", ascending=False)
                top_recs_df = top_recs[['book_id','title','url','cover_image']]
                # 25. Convert the dataframe to a list to be able to be displayed to the user in the template
                context = {"top_recommendation" : top_recs_df.values.tolist()}
                request.session["ran_recommender"] = top_recs_df.values.tolist()

                return render(request,'recommender_system/recommender_home.html',context)
            else:
                error_message = 'Import your GoodReads library to get a recommendation '
                context = {
                    "error_message" : error_message,
                }
                return render(request,'recommender_system/upload_data.html',context)
    else:
        # If the user has already run the recommendation whilst their session has not run out.
        # Then the top_recommendation will be stored temporarily to the key ran_recommender.
        # Hence the user does not need to wait everytime they want to see their current recommendation.
        context = {"top_recommendation" : request.session["ran_recommender"] }
        return render(request,'recommender_system/recommender_home.html',context)

@login_required(login_url='/login')
@allowed_users(allowed_roles=['User','Admin'])
def available_books(request):
    context={}
    group =get_group(request.user)
    if "User" in group:
        '''
            1. Obtain user library id
            2. Obtain all the books in the user's library
            3. Obtain all the books in the database
            4. Obtain all the books that are not in the user's library
        '''
        if Library.objects.filter(user_id=request.user.id).exists()==False:
            Library(user_id=request.user).save()

        user_library_id = Library.objects.get(user_id=request.user.id)
        book_user_library =Book_Library.objects.filter(library=user_library_id)
        books = Book.objects.all()
        books_no_library = Book.objects.exclude(book_library__in=book_user_library)
        # books_no_library = Book.objects.exclude(book_library=user_library_id)
        context = {
            'books' : books,
            'user_books' :book_user_library,
            'books_no_library':books_no_library
        }
        return render(request, 'recommender_system/books.html',context)
    else:
        current_favourites = AdminMonthlyFavourites.objects.all()
        books = Book.objects.all()
        books_not_favourited = Book.objects.exclude(adminmonthlyfavourites__in=current_favourites)
        # print(current_favourites)
        # print(books_not_favourited)
        context = {
            'books' : books,
            'favourite_books' :current_favourites,
            'books_not_favourited':books_not_favourited
        }   
        return render(request, 'recommender_system/books.html',context)

@login_required(login_url='/login')
@allowed_users(allowed_roles='User')
def add_book_to_library(request,bookId):
    # 1. Obtain the current user's library
    # 2. Create a new Book_Library instance which contains the book id passed in and add to the database.
    # 3. Redirect use back to all the available books.
    user_library = Library.objects.get(user_id=request.user)
    Book_Library.objects.create(library= user_library,book = Book.objects.get(book_id=bookId),rating = 0)
    print("Added to library")
    return redirect(available_books)

@login_required(login_url='/login')
@allowed_users(allowed_roles='User')
def modify_book_rating(request,bookId):
    # If the book id was passed in
    if bookId:
        # 1. Gets the user's library
        # 2. Gets the book in the user's library that they want to update their rating on.
        # 3. If the form is valid, then update their rating.
        user_library = Library.objects.get(user_id=request.user)
        book_rating = Book_Library.objects.get(Q(book_id=bookId) & Q(library= user_library))
        form = UpdateBookRatingForm(request.POST or None, instance=book_rating)
        if form.is_valid():
            form.save()
            return redirect(user_home)

        # Render the page.
        return render(request, 'recommender_system/update_book_rating.html', {'book': book_rating, 'form': form})

    # Redirect back to the homepage.
    return redirect(user_home)

@login_required(login_url='/login')
@allowed_users(allowed_roles='User')
def search_other_users_library(request):
    context = {}
    error_message = ''
    if request.method=='POST':
        search = request.POST.get('search_users')
        # If the user that they searched exist
        if User.objects.filter(username=search).exists():
            searched_user = User.objects.get(username=search)
            if searched_user == request.user: #Return user to own library if they searched themselves
                return redirect(user_home)
            # 1. Obtain the searched user's library id
            # 2. Get the library that belongs to the searched user using their library id.
            # 3. Reorder their library by descending order from 5* to 0 (unrated)
            user_library_id = Library.objects.get(user_id=searched_user.id)
            user_books = Book_Library.objects.filter(library=user_library_id)
            order_rating_user_books = user_books.order_by('-rating')
            # If the user's privacy setting is set to private, return error message
            if user_library_id.private==True:
                error_message = "That user has set their library to private"
                context = {
                'error_message' : error_message
                }
                return render(request,'recommender_system/searched_user_library.html',context)
            # If the user has no book's in their library, return error message
            elif len(user_books)==0:
                error_message = "That user do not have any books in their library"
                context = {
                    'error_message' : error_message
                }
                return render(request,'recommender_system/searched_user_library.html',context)
            # If they are public and have books in their library then display their library to the user.
            else:
                rating_data = []
                for i in range (1,6):
                    rating_data.append(user_books.filter(rating=i).count())
                print(rating_data)

            context ={
                "user_library" : user_books,
                "ordered_by_ratings_books": order_rating_user_books,
                "rating_data" : rating_data,
                "username": searched_user.username,
                "rating_data" : rating_data,
            }
            return render(request,'recommender_system/searched_user_library.html',context)
        else:
            error_message = 'There is no user with that username'
            context = {
                'error_message' : error_message
            }
            return render(request,'recommender_system/searched_user_library.html',context)

@login_required(login_url='/login')
@allowed_users(allowed_roles='User')
def update_privacy_setting(request):
    if request.method=='POST':
        # If the user has decided to update their setting from public to private
        # and vice versa then it will get updated in the database.
        if request.POST.get('set_private'):
            user = request.user
            user_library = Library.get(user_id=user)
            user_library.private = True
            user_library.save()

        elif request.POST.get('set_public'):
            user = request.user
            user_library = Library.get(user_id=user)
            user_library.private = False
            user_library.save()

        return redirect(user_home)

#--------------------------------------------------User Authentication and Creation---------------------------------------------------------------
@unauthenticated_user
def login_user(request):
    error_message = ''

    if request.method == 'POST':
        # Obtains the fields from the form
        username = request.POST.get('username')
        password = request.POST.get('password')
        # Authenticate the entered username and password against Django's authentication function
        user = authenticate(request,username=username, password=password)
        if user is not None:
            # Gets the group that the user is assigned to
            group =get_group(user)
            login(request,user)
            if "User" in group:
                # This line of code will allow the user to only run the recommender once
                # while their session hasn't expired and will not need to wait
                # 30-60 seconds everytime they visit their recommendation page.
                request.session["ran_recommender"] = []
                return redirect(user_home)
            else:
                return redirect(home)
        else:
            error_message = 'Wrong credentials'
            return render(request, 'recommender_system/login.html',{'error_message':error_message})
        
    return render(request, 'recommender_system/login.html')

@login_required(login_url='/login')
def logout_user(request):
    # Logout the logged in user and redirect to the login page.
    logout(request)
    return redirect(login_user)

@unauthenticated_user
def register(request):
    # Obtains the form to create a user
    register_form = CreateUserForm()
    error_message =''

    if request.method == 'POST':
        # Obtains the filled in form from the user once they submit
        register_form = CreateUserForm(request.POST)
        if register_form.is_valid():
            # If the form is valid then, add assign the user to group User
            # and add them to the database
            setup_user(register_form.save(), 'User')
            return redirect(login_user)
        else:
            error_message = "Invalid"
            return render(request, 'recommender_system/register.html',{'register_form':register_form,"error_message":error_message})
        
    return render(request, 'recommender_system/register.html',{'register_form':register_form})

#--------------------------------------------------General website pages--------------------------------------------------------------------------
@unauthenticated_user
def about(request):
    return render(request, 'recommender_system/about.html')
