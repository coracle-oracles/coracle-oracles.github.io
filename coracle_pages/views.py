from django.shortcuts import render


def home(request):
    return render(request, 'coracle_pages/index.html')


def survival_guide(request):
    return render(request, 'coracle_pages/survival_guide.html')


def principles(request):
    return render(request, 'coracle_pages/principles.html')


def ticket_info(request):
    return render(request, 'coracle_pages/ticket_info.html')
