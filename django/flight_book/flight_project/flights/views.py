from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse

from .models import Flight, Passenger


# Create your views here.

def home(request):
    return render(request, 'flights/index.html')

def index(request):
    return render(request, 'flights/index.html',  {'flights': Flight.objects.all()})

def flight(request, flight_id):
    flight = Flight.objects.get(id=flight_id)
    passengers = flight.passengers.all()
    non_passengers = Passenger.objects.exclude(flights=flight).all()
    return render(request, 'flights/flight.html', {'flight': flight, 'passengers': passengers, 'non_passengers': non_passengers})

def book(request, flight_id):
     if request.method == 'POST':
         inner = Flight.objects.get(pk=flight_id)
         passenger_id = int(request.POST['passenger'])
         passenger = Passenger.objects.get(pk=passenger_id)
         passenger.flights.add(inner)
         return HttpResponseRedirect(reverse('flight', args=(inner.id,)))
     return None





