from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login as login_f, logout as logout_f, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
        else:
            print(form)
    elif request.method == 'GET':
        form = UserCreationForm()
        return render(request, 'register.html')
    return render(request, 'register.html')

def login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login_f(request, user)
                return redirect('profile')
            else:
                return redirect('login')
        else:
            return redirect('login')
    elif request.method == 'GET':
        form = AuthenticationForm()
        return render(request, 'login.html')
    return render(request, 'login.html')

def index(request):
    if request.user == 'AnonymousUser':
        return redirect('login')
    else:
        return redirect('profile')

def logout(request):
    if request.user != 'AnonymousUser':
        logout_f(request)
    return redirect('login')

@login_required
def profile(request):
    return render(request, 'profile.html', {'user': request.user})