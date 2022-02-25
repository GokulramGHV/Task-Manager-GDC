from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.serializers import ModelSerializer
from tasks.models import *
from django.contrib.auth.models import User
from rest_framework.viewsets import ModelViewSet, GenericViewSet
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import (
    DjangoFilterBackend,
    FilterSet,
    CharFilter,
    ChoiceFilter,
    BooleanFilter,
    DateFilter,
)
from rest_framework import generics, mixins
from django.forms import DateInput


class TaskFilter(FilterSet):
    title = CharFilter(lookup_expr="icontains")

    class Meta:
        model = Task
        fields = ("title", "description", "completed", "status")


class UserSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = ("first_name", "last_name", "username")


class TaskSerializer(ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Task
        fields = ("title", "description", "completed", "priority", "status", "user")


class TaskViewSet(ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = (IsAuthenticated,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = TaskFilter

    def get_queryset(self):
        return Task.objects.filter(user=self.request.user, deleted=False)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class TaskListAPI(APIView):
    def get(self, request):
        tasks = Task.objects.filter(deleted=False)
        data = TaskSerializer(tasks, many=True).data
        return Response({"tasks": data})


class HistoryFilter(FilterSet):
    changed_date = DateFilter(widget=DateInput(attrs={"type": "date"}))

    class Meta:
        model = History
        fields = ("prev_status", "updated_status", "changed_date")


class HistorySerializer(ModelSerializer):
    task_changed = TaskSerializer(read_only=True)

    class Meta:
        model = History
        fields = "__all__"


class HistoryViewSet(
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    mixins.ListModelMixin,
    GenericViewSet,
):
    queryset = History.objects.all()
    serializer_class = HistorySerializer
    permission_classes = (IsAuthenticated,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = HistoryFilter

    def get_queryset(self):
        return History.objects.filter(task_changed__pk=self.kwargs["task_pk"], task_changed__user = self.request.user)
