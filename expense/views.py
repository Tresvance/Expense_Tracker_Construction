from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Sum, Avg
from .models import Owner, Manager, Site,SiteImage,SiteExpense
from django.http import HttpResponse
from django.contrib.auth.hashers import check_password,make_password

# Home Page

def home(request):
    return render(request, 'home.html')

# Owner Registration

def register_owner(request):
    if request.method == 'POST':
        name = request.POST['name']
        username = request.POST['username']
        password = request.POST['password']
        phone = request.POST['phone']

        if Owner.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return redirect('register_owner')

        hashed_password = make_password(password)  # Hash the password here

        Owner.objects.create(
            name=name,
            username=username,
            password=hashed_password,
            phone=phone
        )
        messages.success(request, "Owner registered successfully.")
        return redirect('login')

    return render(request, 'register_owner.html')

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        # Try to find owner first
        owner = Owner.objects.filter(username=username).first()
        if owner:
            if check_password(password, owner.password):
                request.session['owner_id'] = owner.id
                return redirect('owner_dashboard')
            else:
                messages.error(request, "Invalid password for owner.")
                return render(request, 'login.html')

        # If no owner found, try manager
        manager = Manager.objects.filter(username=username).first()
        if manager:
            if check_password(password, manager.password):
                request.session['manager_id'] = manager.id
                return redirect('manager_dashboard')
            else:
                messages.error(request, "Invalid password for manager.")
                return render(request, 'login.html')

        # If no user found
        messages.error(request, "User not found.")
    
    return render(request, 'login.html')
# Logout


def logout_view(request):
    request.session.flush()
    return redirect('home')


def owner_dashboard(request):
    owner_id = request.session.get('owner_id')
    if not owner_id:
        return redirect('login')

    owner = Owner.objects.get(id=owner_id)

    # Add manager
    if request.method == 'POST' and 'add_manager' in request.POST:
        name = request.POST.get('name')
        username = request.POST.get('username')
        password = request.POST.get('password')
        phone = request.POST.get('phone')

        if Manager.objects.filter(username=username).exists():
            messages.error(request, "Manager username already exists.")
        else:
            Manager.objects.create(
                owner=owner,
                name=name,
                username=username,
                password=make_password(password),
                phone=phone,
            )
            messages.success(request, f"Manager '{name}' added successfully.")

    # Add site and assign managers
    if request.method == 'POST' and 'add_site' in request.POST:
        site_name = request.POST.get('site_name')
        site_location = request.POST.get('site_location')
        assigned_manager_ids = request.POST.getlist('assigned_managers')

        if Site.objects.filter(name=site_name, owner=owner).exists():
            messages.error(request, "Site with this name already exists.")
        else:
            site = Site.objects.create(
                owner=owner,
                name=site_name,
                location=site_location
            )
            if assigned_manager_ids:
                managers_to_assign = Manager.objects.filter(id__in=assigned_manager_ids, owner=owner)
                site.assigned_managers.set(managers_to_assign)
            messages.success(request, f"Site '{site_name}' added and managers assigned.")

    managers = Manager.objects.filter(owner=owner)
    sites = Site.objects.filter(owner=owner)

    # ✅ Add total_expense attribute to each site
    for site in sites:
        expenses = site.expenses.all()
        total = sum(exp.total_cost for exp in expenses)  # ✅ Use total_cost
        site.total_expense = total

    return render(request, 'owner_dashboard.html', {
        'owner': owner,
        'managers': managers,
        'sites': sites
    })

    
def manager_dashboard(request):
    manager_id = request.session.get('manager_id')
    if not manager_id:
        return redirect('login')

    manager = Manager.objects.get(id=manager_id)
    sites = manager.sites.all()  # Just list sites assigned to manager, no aggregation

    return render(request, 'manager_dashboard.html', {
        'manager': manager,
        'sites': sites,
    })
    
    
# Add Manager
def add_manager(request):
    owner_id = request.session.get('owner_id')
    if not owner_id:
        return redirect('login_owner')
    if request.method == 'POST':
        name = request.POST['name']
        username = request.POST['username']
        phone = request.POST['phone']
        owner = Owner.objects.get(id=owner_id)

        if Manager.objects.filter(username=username).exists():
            messages.error(request, "Manager username already exists.")
        else:
            Manager.objects.create(owner=owner, name=name, username=username, phone=phone)
            messages.success(request, "Manager added successfully.")
    return redirect('owner_dashboard')



# Upload Site Image
def upload_site_image(request, site_id):
    manager_id = request.session.get('manager_id')
    if not manager_id:
        return redirect('login_manager')
    site = get_object_or_404(Site, id=site_id, assigned_manager_id=manager_id)
    if request.method == 'POST' and request.FILES.get('image'):
        image = request.FILES['image']
        SiteImage.objects.create(site=site, image=image)
        messages.success(request, "Image uploaded.")
        return redirect('manager_dashboard')
    return render(request, 'upload_site_image.html', {'site': site})



def site_detail(request, site_id):
    manager_id = request.session.get('manager_id')
    if not manager_id:
        return redirect('login')

    site = get_object_or_404(Site, id=site_id, assigned_managers__id=manager_id)

    if request.method == 'POST':
        # Add expense with completion percentage
        if 'add_expense' in request.POST:
            material_name = request.POST['material_name']
            quantity = int(request.POST['quantity'])
            total_cost = float(request.POST['total_cost'])
            completion_percentage = int(request.POST.get('completion_percentage', 0))

            SiteExpense.objects.create(
                site=site,
                material_name=material_name,
                quantity=quantity,
                total_cost=total_cost,
                completion_percentage=completion_percentage,
            )
            messages.success(request, 'Expense and progress added successfully.')

        # Add image
        if 'add_image' in request.POST and request.FILES.get('site_image'):
            image = request.FILES['site_image']
            SiteImage.objects.create(site=site, image=image)
            messages.success(request, 'Image uploaded.')

        return redirect('site_detail', site_id=site.id)

    # Group expenses by date (descending)
    expenses_by_date = {}
    for expense in site.expenses.all().order_by('-date'):
        expenses_by_date.setdefault(expense.date, []).append(expense)

    # Sum all expenses total_cost

    images = site.images.all()

    return render(request, 'site_detail.html', {
        'site': site,
        'expenses_by_date': expenses_by_date,
        'images': images,
    })
    

def update_expense(request):
    if request.method == 'POST':
        expense_id = request.POST.get('expense_id')
        quantity = request.POST.get('quantity')
        total_cost = request.POST.get('total_cost')

        try:
            expense = get_object_or_404(SiteExpense, id=expense_id)
            expense.quantity = int(quantity)
            expense.total_cost = float(total_cost)
            expense.save()
            messages.success(request, 'Expense updated successfully.')

            # Redirect to the site_detail page of the site this expense belongs to
            return redirect('site_detail', site_id=expense.site.id)

        except Exception as e:
            messages.error(request, f'Update failed: {e}')
            return redirect('owner_dashboard')

    return redirect('manager_dashboard')