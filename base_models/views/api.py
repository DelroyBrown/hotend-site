import pandas as pd
from random import randint

from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.generics import RetrieveAPIView, CreateAPIView, UpdateAPIView, get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView

from base_models.models import Event, AnyItem


class GetPastEvents(APIView):
    """
    POST get a dict containing the number of total, completed, and failed events for a
    given item and optional production step.
    """

    def post(self, request, *args, **kwargs):
        item_id = request.data.get('item_id', None)
        production_step = request.data.get('production_step', None)

        msg = f"Could not find item id {item_id}"
        if item_id is None:
            return Response({"error": msg}, status=500)
        item = AnyItem.objects.filter(id=item_id).first()
        if item is None:
            return Response({"error": msg}, status=500)

        filters = {'item': item}
        if production_step is not None:
            filters['machine__production_step'] = production_step

        events = Event.objects.filter(**filters)
        completed = events.filter(completed=True)
        incompleted = events.filter(completed=False)
        failed = events.filter(failed=True)
        passed = events.filter(completed=True, failed=False)
        fail_states_tmp = pd.DataFrame(events.values('fail_state')).value_counts().to_dict()
        fail_states = {}
        for key, value in fail_states_tmp.items():
            key = key[0]
            fail_states[key] = value

        data = {
            'events': events.count(),
            'completed': completed.count(),
            'incompleted': incompleted.count(),
            'passed': passed.count(),
            'failed': failed.count(),
            'fail_state': fail_states
        }

        return Response(data)
