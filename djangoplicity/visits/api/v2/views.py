from django.utils import timezone
from djangoplicity.visits.models import Showing, Activity
from .serializers import ShowingSerializer, ActivitySerializer
from django_filters import rest_framework as filters
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import permissions, mixins
from rest_framework.viewsets import GenericViewSet


class ShowingFilter(filters.FilterSet):
    activity = filters.CharFilter(field_name="activity__id")
    start_date = filters.DateFilter(field_name="start_time", lookup_expr='gte', required=False)

    class Meta:
        model = Showing
        fields = ['activity', 'start_date']


@extend_schema(
    parameters=[
        OpenApiParameter("activity", OpenApiTypes.STR, description="The ID of the activity to filter showings."),
        OpenApiParameter("start_date", OpenApiTypes.DATE, description="The start date to filter showings from."),
    ]
)
class ShowingListView(mixins.ListModelMixin, GenericViewSet):
    permission_classes = [permissions.AllowAny]
    queryset = Showing.objects.all()
    serializer_class = ShowingSerializer
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = ShowingFilter

    def get_queryset(self):
        now = timezone.now()
        queryset = super().get_queryset().select_related('activity')
        filterset = self.filterset_class(self.request.GET, queryset=queryset)

        if filterset.is_valid():
            user_start_date = filterset.form.cleaned_data.get('start_date', None)
            if not user_start_date or user_start_date < now:
                queryset = queryset.filter(start_time__gte=now)
                return queryset
            return filterset.qs
        else:
            return queryset.none()


class ActivityViewSet(mixins.RetrieveModelMixin, GenericViewSet):
    permission_classes = [permissions.AllowAny]
    queryset = Activity.objects.all()
    serializer_class = ActivitySerializer

