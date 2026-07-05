from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('create/', views.create_ad_view, name='create_ad'),
    path('ad/<int:ad_id>/', views.ad_detail_view, name='ad_detail'),
    path('ad/<int:ad_id>/edit/', views.edit_ad_view, name='edit_ad'),
]
