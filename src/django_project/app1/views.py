from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login as login_f, logout as logout_f, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from .forms import UploadFileForm
from .validate_conllu import validate_uploaded_file

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

@login_required
def upload_file(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            is_valid_format = validate_uploaded_file(request.FILES['file'])
            if is_valid_format: message = 'You have uploaded a file successfully.'
            else: message = 'The file was not in the correct conllu format.'
            return render(request, 'upload_file.html', {'form': UploadFileForm(), 'message': message})
    else:
        form = UploadFileForm()
    return render(request, 'upload_file.html', {'form': form})