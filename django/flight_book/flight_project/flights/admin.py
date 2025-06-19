from django.contrib import admin
from .models import Flight, Airport, Passenger


class FlightAdmin(admin.ModelAdmin):
    list_display = ("id", "origin", "destination", "duration")
admin.site.register(Passenger)
admin.site.register(Flight, FlightAdmin)
admin.site.register(Airport)