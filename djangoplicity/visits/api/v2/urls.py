from django.urls import path, include
from rest_framework import routers
from .views import ShowingListView, ActivityViewSet

api_router = routers.DefaultRouter()
api_router.register('showings', ShowingListView)
api_router.register('activities', ActivityViewSet)


urlpatterns = [
    path('', include(api_router.urls))
]
