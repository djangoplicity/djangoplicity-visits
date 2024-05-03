from django.urls import path, include
from rest_framework import routers
from .views import ShowingListView

api_router = routers.DefaultRouter()
api_router.register('showings', ShowingListView)


urlpatterns = [
    path('', include(api_router.urls))
]
