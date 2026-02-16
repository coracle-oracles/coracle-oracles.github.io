from django.shortcuts import render


def home(request):
    return render(request, 'coracle_plugin/index.html')


def survival_guide(request):
    return render(request, 'coracle_plugin/survival_guide.html')


def principles(request):
    return render(request, 'coracle_plugin/principles.html')


def ticket_info(request):
    return render(request, 'coracle_plugin/ticket_info.html')
