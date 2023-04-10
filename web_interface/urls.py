from django.contrib import admin
from django.urls import path
from . import views

# Assign the app name for this Django app
app_name = "web_interface"

# Define the urlpatterns list which contains the URL patterns for this app
urlpatterns = [
    # Connect the admin site URL with the Django admin module
    path("admin/", admin.site.urls, name="admin"),
    
    # Connect the root URL (empty string) with the events_list_view function in views
    # and give it a name 'hotend_qc_data' for easy reference
    path('', views.events_list_view, name='hotend_qc_data'),

    # Connect the 'search/' URL with the search_results_view function in views
    # and give it a name 'search_results' for easy reference
    path('search/', views.search_results_view, name='search_results'),

    # Connect the 'event/' URL followed by an integer (event_id) with the event_detail_view
    # function in views and give it a name 'event_detail_view' for easy reference
    path('event/<int:event_id>/', views.event_detail_view, name='event_detail_view'),
]
