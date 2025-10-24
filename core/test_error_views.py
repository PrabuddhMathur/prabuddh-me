"""
Temporary test views for error pages.
This file is for testing only and should be removed after verification.
"""
from django.shortcuts import render
from django.http import HttpResponseNotFound, HttpResponseServerError


def test_404(request):
    """Test view to render the 404 template."""
    return HttpResponseNotFound(render(request, '404.html'))


def test_500(request):
    """Test view to render the 500 template."""
    return HttpResponseServerError(render(request, '500.html'))
