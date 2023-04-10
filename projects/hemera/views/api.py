from rest_framework.response import Response
from rest_framework.views import APIView

from ..models import HemeraGreaseEvent
from base_models.models import SingleItem


class GetPastEvents(APIView):
    def get(self, request, uid, *args, **kwargs):
        item = SingleItem.objects.filter(uid=uid).first()
        events = HemeraGreaseEvent.objects.filter(item=item)
        completed = events.filter(completed=True)
        failed = events.filter(failed=True)

        data = {
            'events': events.count(),
            'completed': completed.count(),
            'failed': failed.count(),
            'fail_state': {},
        }

        for failure in HemeraGreaseEvent.get_fail_states():
            data['fail_state'][failure[0]] = events.filter(fail_state=failure[0]).count()

        return Response(data)
