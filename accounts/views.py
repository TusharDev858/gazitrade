from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from orders.models import Order
from .models import Customer

def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        user = authenticate(request, phone=request.POST['phone'], password=request.POST['password'])
        if user:
            login(request, user)
            return redirect(request.GET.get('next', 'home'))
        messages.error(request, 'Invalid phone number or password.')
    return render(request, 'accounts/login.html')

def register_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        phone = request.POST['phone']
        name  = request.POST.get('name','')
        pw    = request.POST['password']
        pw2   = request.POST['password2']
        if pw != pw2:
            messages.error(request, 'Passwords do not match.')
        elif Customer.objects.filter(phone=phone).exists():
            messages.error(request, 'This phone number is already registered.')
        else:
            user = Customer.objects.create_user(phone=phone, password=pw, name=name)
            login(request, user)
            return redirect('home')
    return render(request, 'accounts/register.html')

def logout_view(request):
    logout(request)
    return redirect('home')

@login_required
def profile_view(request):
    if request.method == 'POST':
        u = request.user
        u.name    = request.POST.get('name',    u.name)
        u.email   = request.POST.get('email',   u.email)
        u.address = request.POST.get('address', u.address)
        u.area    = request.POST.get('area',    u.area)
        u.save()
        messages.success(request, 'Profile updated!')
    orders = Order.objects.filter(customer=request.user).prefetch_related('items')
    return render(request, 'accounts/profile.html', {'orders': orders})
