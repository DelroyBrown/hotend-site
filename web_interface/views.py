import os
import psycopg2
from django.conf import settings
from django.db.models import Q
from django.db.models import CharField
from django.db.models.functions import Cast
from django.shortcuts import get_object_or_404, render
from django.shortcuts import render, redirect
from base_models.models.event import Event
from ..base_models.search_model import SearchResults


def events_list_view(request):
    return render(request, 'userside_templates/event_list.html')


def search_results_view(request):
    # Retrieve the search query from the GET request
    search_query = request.GET.get('search', '')

    # Search for events that match the search query
    events = Event.objects.annotate(
        uid_as_str=Cast("item__singleitem__uid", output_field=CharField())
    ).filter(Q(uid_as_str__icontains=search_query)).order_by('-date_created')

    # Print the number of events found
    print(f"Number of events found: {events.count()}")

    if events.count() == 1:
        # If only one event was found, redirect to its detail view
        event = events.first()
        return redirect('event_detail_view', event_id=event.id)
    elif events.count() > 1:
        # If multiple events were found, redirect to the first event's detail view
        event = events.first()
        return redirect('event_detail_view', event_id=event.id)
    else:
        # If no events were found, return the first three events
        events = events[:3]

    for event in events:
        # Save each event to the SearchResults model
        SearchResults.objects.create(
            uid=event.item.singleitem.uid,
            sku=event.item.sku,
            date_created=event.date_created,
            completed=event.completed,
            tested_leakage=event.tested_leakage,
            tested_circuit=event.tested_circuit,
            tested_thermal_cycling=event.tested_thermal_cycling,
            successful_thermal_cycles=event.successful_thermal_cycles
        )
        print('Event saved to new database')

    context = {
        'events': events
    }
    # Render the search results template with the found events
    return render(request, 'userside_templates/search_results.html', context)


def event_detail_view(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    context = {'event': event}
    return render(request, 'userside_templates/event_detail.html', context)
