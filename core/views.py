import stripe
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from django.db.models import Count

from .tickets import ticket_types
from .forms import CustomUserCreationForm
from .models import Event, Order, Transfer, User

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
    event = Event.get_active()
    if not event:
        messages.error(request, 'No active event. Ticket sales are currently closed.')
        return redirect('home')

    existing_counts = dict(
        Order.objects.filter(
            event=event,
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
        'event': event,
        'ticket_data': ticket_data,
        'stripe_publishable_key': settings.STRIPE_PUBLISHABLE_KEY,
    })


@login_required
@require_POST
def create_checkout_session(request):
    """Create a Stripe Checkout session and redirect to it."""
    event = Event.get_active()
    if not event:
        messages.error(request, 'No active event. Ticket sales are currently closed.')
        return redirect('home')

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

    # Check ticket limits per user for this event
    existing_counts = dict(
        Order.objects.filter(
            event=event,
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
            event=event,
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


@login_required
def my_tickets(request):
    """Display user's tickets and pending transfers."""
    event = Event.get_active()

    owned_tickets = Order.objects.filter(
        event=event,
        owning_user=request.user,
        status='completed',
    ).select_related('purchasing_user') if event else Order.objects.none()

    outgoing_transfers = Transfer.objects.filter(
        order__event=event,
        from_user=request.user,
        status='pending',
    ).select_related('order') if event else Transfer.objects.none()

    incoming_transfers = Transfer.objects.filter(
        order__event=event,
        to_email=request.user.email,
        status='pending',
    ).select_related('order', 'from_user') if event else Transfer.objects.none()

    return render(request, 'core/my_tickets.html', {
        'event': event,
        'owned_tickets': owned_tickets,
        'outgoing_transfers': outgoing_transfers,
        'incoming_transfers': incoming_transfers,
        'ticket_types': ticket_types,
    })


@login_required
@require_POST
def transfer_ticket(request, order_id):
    """Initiate a ticket transfer."""
    order = get_object_or_404(Order, id=order_id, owning_user=request.user, status='completed')

    # Check if there's already a pending transfer for this order
    if Transfer.objects.filter(order=order, status='pending').exists():
        messages.error(request, 'This ticket already has a pending transfer.')
        return redirect('my_tickets')

    to_email = request.POST.get('to_email', '').strip().lower()
    if not to_email:
        messages.error(request, 'Please enter an email address.')
        return redirect('my_tickets')

    if to_email == request.user.email:
        messages.error(request, 'You cannot transfer a ticket to yourself.')
        return redirect('my_tickets')

    # Check if recipient exists
    to_user = User.objects.filter(email=to_email).first()
    if not to_user:
        messages.error(request, 'No user found with that email address.')
        return redirect('my_tickets')

    # Check recipient's ticket limits for this event
    existing_count = Order.objects.filter(
        event=order.event,
        owning_user=to_user,
        ticket_type=order.ticket_type,
        status__in=['completed', 'pending'],
    ).count()
    pending_transfers = Transfer.objects.filter(
        order__event=order.event,
        to_email=to_email,
        order__ticket_type=order.ticket_type,
        status='pending',
    ).count()
    limit = ticket_types[order.ticket_type]['max_per_user']
    if existing_count + pending_transfers >= limit:
        messages.error(request, 'The recipient has reached their limit for this ticket type.')
        return redirect('my_tickets')

    Transfer.objects.create(
        order=order,
        from_user=request.user,
        to_email=to_email,
        to_user=to_user,
    )

    messages.success(request, f'Transfer initiated to {to_email}.')
    return redirect('my_tickets')


@login_required
@require_POST
def accept_transfer(request, transfer_id):
    """Accept an incoming transfer."""
    transfer = get_object_or_404(
        Transfer,
        id=transfer_id,
        to_email=request.user.email,
        status='pending',
    )

    # Check ticket limits for this event
    existing_count = Order.objects.filter(
        event=transfer.order.event,
        owning_user=request.user,
        ticket_type=transfer.order.ticket_type,
        status__in=['completed', 'pending'],
    ).count()
    limit = ticket_types[transfer.order.ticket_type]['max_per_user']
    if existing_count >= limit:
        messages.error(request, 'You have reached your limit for this ticket type.')
        return redirect('my_tickets')

    # Complete the transfer
    transfer.order.owning_user = request.user
    transfer.order.save()

    transfer.to_user = request.user
    transfer.status = 'accepted'
    transfer.save()

    messages.success(request, 'Transfer accepted. The ticket is now yours.')
    return redirect('my_tickets')


@login_required
@require_POST
def reject_transfer(request, transfer_id):
    """Reject an incoming transfer."""
    transfer = get_object_or_404(
        Transfer,
        id=transfer_id,
        to_email=request.user.email,
        status='pending',
    )

    transfer.status = 'rejected'
    transfer.save()

    messages.success(request, 'Transfer rejected.')
    return redirect('my_tickets')


@login_required
@require_POST
def rescind_transfer(request, transfer_id):
    """Rescind an outgoing transfer."""
    transfer = get_object_or_404(
        Transfer,
        id=transfer_id,
        from_user=request.user,
        status='pending',
    )

    transfer.delete()

    messages.success(request, 'Transfer rescinded.')
    return redirect('my_tickets')
