from django.shortcuts import render


def home(request):
    return render(request, 'coracle_pages/index.html')


def dashboard(request):
    # Import pretix modules inside function to avoid circular imports during URL loading
    from django.db.models import Q
    from pretix.base.models import Order, Organizer
    from pretix.presale.utils import get_customer

    # Load the organizer and attach to request (required by get_customer)
    try:
        request.organizer = Organizer.objects.get(slug='coracle')
    except Organizer.DoesNotExist:
        return render(request, 'coracle_pages/dashboard.html', {
            'customer': None,
            'orders': [],
        })

    customer = get_customer(request)

    if not customer:
        # User is not logged in, show login prompt
        return render(request, 'coracle_pages/dashboard.html', {
            'customer': None,
            'orders': [],
        })

    # Fetch orders for this customer
    q = Q(customer=customer)
    if request.organizer.settings.customer_accounts_link_by_email and customer.email:
        q |= Q(email__iexact=customer.email)

    orders = Order.objects.filter(q).prefetch_related(
        'positions__item',
        'positions__variation',
        'event',
    ).order_by('-datetime')

    # Build ticket information for each order
    orders_with_tickets = []
    for order in orders:
        tickets = []
        for position in order.positions.all():
            tickets.append({
                'item_name': str(position.item),
                'variation': str(position.variation) if position.variation else None,
                'attendee_name': position.attendee_name or '',
                'price': position.price,
            })

        orders_with_tickets.append({
            'order': order,
            'code': order.code,
            'status': order.status,
            'status_display': order.get_status_display(),
            'datetime': order.datetime,
            'total': order.total,
            'event': order.event,
            'tickets': tickets,
            'secret': order.secret,
        })

    return render(request, 'coracle_pages/dashboard.html', {
        'customer': customer,
        'orders': orders_with_tickets,
    })


def survival_guide(request):
    return render(request, 'coracle_pages/survival_guide.html')


def principles(request):
    return render(request, 'coracle_pages/principles.html')


def ticket_info(request):
    return render(request, 'coracle_pages/ticket_info.html')
