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
    path('user/<str:username>/', views.user_ads_view, name='user_ads'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('dashboard/users/', views.dashboard_users, name='dashboard_users'),
    path('dashboard/ads/', views.dashboard_ads, name='dashboard_ads'),
    path('dashboard/subscriptions/', views.dashboard_subscriptions, name='dashboard_subscriptions'),
    path('dashboard/user/<int:user_id>/', views.dashboard_user_detail, name='dashboard_user_detail'),
    path('dashboard/user/<int:user_id>/<str:action>/', views.dashboard_user_action, name='dashboard_user_action'),
    path('dashboard/ad/<int:ad_id>/<str:action>/', views.dashboard_ad_action, name='dashboard_ad_action'),
    path('notifications/', views.notifications_view, name='notifications'),
    path('notifications/<int:notif_id>/read/', views.mark_read, name='mark_read'),
    path('ad/<int:ad_id>/promote/', views.promote_ad_view, name='promote_ad'),
    path('subscriptions/', views.subscription_shop, name='subscription_shop'),
    path('ad/<int:ad_id>/fav/', views.toggle_favorite, name='toggle_favorite'),
    path('ad/<int:ad_id>/pause/', views.pause_ad, name='pause_ad'),
]
