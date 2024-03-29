import coreapi
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.utils import timezone
from django.views import View
from rest_framework.response import Response
from rest_framework import generics, status, views

from hashids import Hashids
from rest_framework.schemas import AutoSchema

from webgrab_main.settings import HASHIDS_SALT
from .models import TaskDetails
from .serializers import TaskDetailsSerializer
from .tasks import url_check_task

import datetime
import logging


MAX_TIMEDELTA = datetime.timedelta(minutes=3)
HASHIDS = Hashids(salt=HASHIDS_SALT)
log = logging.getLogger(__name__)


class TaskHandlerMixin:
    @staticmethod
    def _launch_tasks(url_list):
        if not url_list:
            raise ValueError
        tasks = []
        for url in url_list:
            # get or create object based on its URL
            try:
                recent_time = timezone.now() - MAX_TIMEDELTA
                task_details = TaskDetails.objects.get(address=url, completed=True,
                                                       image_download_datetime__gt=recent_time)
            except TaskDetails.DoesNotExist:
                task_details = TaskDetails.objects.create(address=url)
                # fire up task immediately, if task object is not too fresh
                url_check_task.apply_async([task_details.pk])
            # store primary keys, for encoding the whole tuple
            tasks.append(task_details.pk)
        # hash all the primary keys with a reversible function, for later retrieval
        request_code = HASHIDS.encode(*sorted(tasks))
        return request_code

    @staticmethod
    def _get_queryset(request_code):
        # decode the reversible hash, to get back a tuple of primary keys
        pks = HASHIDS.decode(request_code)
        return TaskDetails.objects.filter(pk__in=pks)


class TaskList(TaskHandlerMixin, generics.ListAPIView):
    serializer_class = TaskDetailsSerializer
    lookup_url_kwarg = 'request_code'

    def get_queryset(self):
        request_code = self.kwargs.get('request_code')
        qs = self._get_queryset(request_code)
        return qs


class TaskCreate(TaskHandlerMixin, views.APIView):
    """
    post:
    Snaps a screenshot from the URLs listed in the 'urls' object
    """
    schema = AutoSchema(
                manual_fields=[coreapi.Field('urls', required=True), ]
            )

    def post(self, request, *args, **kwargs):
        try:
            url_list = request.data.get('urls')
            request_code = self._launch_tasks(url_list)
            return Response({'request_code': request_code,
                             'result_url_json': request.build_absolute_uri(
                                 reverse('task-list', kwargs={'request_code': request_code})),
                             'result_url_html': request.build_absolute_uri(
                                 reverse('task-list-html', kwargs={'request_code': request_code}))
                             })
        except ValueError:
            return Response({'detail': '\'urls\' object (list of strings) missing'},
                            status=status.HTTP_400_BAD_REQUEST)


class TaskHTMLFormView(TaskHandlerMixin, View):
    template_name = 'home.html'

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)

    def post(self, request, *args, **kwargs):
        addresses = request.POST.get('addresses').split()
        if addresses:
            request_code = self._launch_tasks(addresses)
            return HttpResponseRedirect(reverse('task-list-html', kwargs={'request_code': request_code}))

        return render(request, self.template_name)


class TaskHTMLListView(TaskHandlerMixin, View):
    template_name = 'list.html'

    def get(self, request, *args, **kwargs):
        request_code = kwargs.get('request_code')
        tasks = self._get_queryset(request_code)
        return render(request, self.template_name, {'tasks': tasks})
