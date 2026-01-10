# -*- coding: utf-8 -*-
from django.shortcuts import render
from datetime import datetime

def home(request):
    return render(
        request,
        'app/index.html',
        {
            'title': 'Home',
            'year': datetime.now().year,
        }
    )

def about(request):
    return render(
        request,
        'app/about.html',
        {
            'title': 'About',
            'message': 'FreshTrack Information',
            'year': datetime.now().year,
        }
    )

def contact(request):
    return render(
        request,
        'app/contact.html',
        {
            'title': 'Contact',
            'message': 'Contact Us',
            'year': datetime.now().year,
        }
    )