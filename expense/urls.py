from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/owner/', views.register_owner, name='register_owner'),
    path('dashboard/owner/', views.owner_dashboard, name='owner_dashboard'),
    path('dashboard/manager/', views.manager_dashboard, name='manager_dashboard'),

    path('site/<int:site_id>/', views.site_detail, name='site_detail'),
    path('expense/update/', views.update_expense, name='update_expense'),


]
