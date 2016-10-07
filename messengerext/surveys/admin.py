from django.contrib import admin
from surveys.models import Survey, Choice, Vote

# Register your models here.
admin.site.register(Survey)
admin.site.register(Choice)
admin.site.register(Vote)
