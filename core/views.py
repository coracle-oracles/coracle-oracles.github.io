import stripe
from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from django.db.models import Count

from .tickets import ticket_types
from .forms import CustomUserCreationForm
from .models import Order

stripe.api_key = settings.STRIPE_SECRET_KEY


def home(request):
    return render(request, 'core/index.html')


def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Registration successful!')
            return redirect('home')
    else:
        form = CustomUserCreationForm()
    return render(request, 'core/register.html', {'form': form})


def survival_guide(request):
    return render(request, 'core/survival_guide.html')


def principles(request):
    return render(request, 'core/principles.html')


def ticket_info(request):
    return render(request, 'core/ticket_info.html')


@login_required
def tickets(request):
    """Display ticket selection page."""
    existing_counts = dict(
        Order.objects.filter(
            owning_user=request.user,
            status__in=['completed', 'pending'],
        ).values_list('ticket_type').annotate(count=Count('id'))
    )
    ticket_data = []
    for key, ticket in ticket_types.items():
        existing = existing_counts.get(key, 0)
        ticket_data.append({
            'key': key,
            'ticket': ticket,
            'remaining': max(0, ticket['max_per_user'] - existing),
        })
    return render(request, 'core/tickets.html', {
        'ticket_data': ticket_data,
        'stripe_publishable_key': settings.STRIPE_PUBLISHABLE_KEY,
    })


@login_required
@require_POST
def create_checkout_session(request):
    """Create a Stripe Checkout session and redirect to it."""
    line_items = []
    tickets_to_create = []

    for key, ticket in ticket_types.items():
        quantity = int(request.POST.get(f'quantity_{key}', 0))
        if quantity > 0:
            line_items.append({
                'price': ticket['price_id'],
                'quantity': quantity,
            })
            for _ in range(quantity):
                tickets_to_create.append(key)

    if not line_items:
        messages.error(request, 'Please select at least one ticket.')
        return redirect('tickets')

    # Check ticket limits per user
    existing_counts = dict(
        Order.objects.filter(
            owning_user=request.user,
            status__in=['completed', 'pending'],
        ).values('ticket_type').annotate(count=Count('id')).values_list('ticket_type', 'count')
    )

    requested_counts = {}
    for key in tickets_to_create:
        requested_counts[key] = requested_counts.get(key, 0) + 1

    for key, ticket in ticket_types.items():
        existing = existing_counts.get(key, 0)
        requested = requested_counts.get(key, 0)
        limit = ticket['max_per_user']
        if existing + requested > limit:
            remaining = max(0, limit - existing)
            messages.error(
                request,
                f'You can only have {limit} {ticket["label"].lower()}s. '
                f'You already have {existing}, so you can only purchase {remaining} more.'
            )
            return redirect('tickets')

    # Create Stripe Checkout session
    checkout_session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=line_items,
        mode='payment',
        success_url=request.build_absolute_uri('/checkout/success/') + '?session_id={CHECKOUT_SESSION_ID}',
        cancel_url=request.build_absolute_uri('/checkout/cancel/'),
        customer_email=request.user.email,
        metadata={
            'user_id': request.user.id,
        },
    )

    # Create pending orders (one per ticket)
    for key in tickets_to_create:
        Order.objects.create(
            purchasing_user=request.user,
            owning_user=request.user,
            ticket_type=key,
            stripe_checkout_session_id=checkout_session.id,
            status='pending',
        )

    return redirect(checkout_session.url)


@login_required
def checkout_success(request):
    """Handle successful checkout."""
    session_id = request.GET.get('session_id')
    if session_id:
        try:
            session = stripe.checkout.Session.retrieve(session_id)
            if session.payment_status == 'paid':
                Order.objects.filter(
                    stripe_checkout_session_id=session_id,
                    status='pending',
                ).update(
                    status='completed',
                    stripe_payment_intent_id=session.payment_intent,
                )
        except Exception:
            pass

    return render(request, 'core/checkout_success.html')


@login_required
def checkout_cancel(request):
    """Handle cancelled checkout."""
    return render(request, 'core/checkout_cancel.html')
