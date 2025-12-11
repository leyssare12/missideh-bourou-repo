from django.test import TestCase

# Create your tests here.
from django.contrib.auth.models import Permission

# Liste toutes les permissions
permissions = Permission.objects.all()
for p in permissions:
    print(f"{p.codename} - {p.name}")