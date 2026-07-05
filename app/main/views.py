from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.models import User
from django.contrib import messages
from .models import Ad

def home(request):
    ads = Ad.objects.filter(status='publish')

    search_in = request.GET.get('search_in', '')
    section = request.GET.get('section', '')
    specialty = request.GET.get('specialty', '')
    q = request.GET.get('q', '')
    sort = request.GET.get('sort', '-created_at')

    if search_in:
        ads = ads.filter(purpose=search_in)
    if section:
        ads = ads.filter(section=section)
    if specialty:
        ads = ads.filter(specialty=specialty)
    if q:
        ads = ads.filter(title__icontains=q) | ads.filter(text_ar__icontains=q)

    ads = ads.order_by(sort)

    filter_data = {
        'search_in': search_in,
        'section': section,
        'specialty': specialty,
        'q': q,
        'sort': sort,
    }

    return render(request, 'main/home.html', {'ads': ads, 'filter_data': filter_data})

def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        try:
            user = User.objects.get(email=email)
            user = authenticate(request, username=user.username, password=password)
        except User.DoesNotExist:
            user = None
        if user:
            login(request, user)
            return redirect('home')
        messages.error(request, 'البريد الإلكتروني أو كلمة المرور غير صحيحة')
    return render(request, 'main/login.html')

def signup_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        fullname = request.POST.get('fullname')
        phone = request.POST.get('phone')
        photo = request.FILES.get('photo')
        if User.objects.filter(email=email).exists():
            messages.error(request, 'البريد الإلكتروني مستخدم مسبقاً')
            return render(request, 'main/signup.html')
        user = User.objects.create_user(
            username=email.split('@')[0],
            email=email,
            password=password,
        )
        user.first_name = fullname
        user.save()
        profile = user.profile
        profile.phone = phone
        if photo:
            profile.photo = photo
        profile.save()
        login(request, user)
        messages.success(request, 'تم إنشاء الحساب بنجاح')
        return redirect('home')
    return render(request, 'main/signup.html')

def logout_view(request):
    logout(request)
    return redirect('home')

def ad_detail_view(request, ad_id):
    ad = Ad.objects.get(id=ad_id)
    ad.views += 1
    ad.save(update_fields=['views'])
    return render(request, 'main/ad_detail.html', {'ad': ad})

def profile_view(request):
    user_ads_all = Ad.objects.filter(user=request.user).order_by('-created_at')
    ads_active = user_ads_all.filter(status='publish')
    ads_pending = user_ads_all.filter(status='pending')
    ads_draft = user_ads_all.filter(status='draft')
    ads_archived = user_ads_all.filter(status='archived')
    return render(request, 'main/profile.html', {
        'user_ads_all': user_ads_all,
        'ads_active': ads_active,
        'ads_pending': ads_pending,
        'ads_draft': ads_draft,
        'ads_archived': ads_archived,
    })

def edit_ad_view(request, ad_id):
    ad = Ad.objects.get(id=ad_id, user=request.user)
    if request.method == 'POST':
        ad.title = request.POST.get('title', '')
        ad.purpose = request.POST.get('purpose', '')
        ad.section = request.POST.get('section', '')
        ad.specialty = request.POST.get('specialty', '')
        ad.text_ar = request.POST.get('text_ar', '')
        ad.text_en = request.POST.get('text_en', '')
        ad.contact_phone = request.POST.get('contact_phone', '')
        ad.contact_email = request.POST.get('contact_email', '')
        ad.status = 'publish' if request.POST.get('action') == 'publish' else 'draft'
        for i in range(4):
            f = request.FILES.get(f'image_{i}')
            if f:
                setattr(ad, f'image_{i}', f)
        ad.save()
        messages.success(request, 'تم تحديث الإعلان بنجاح')
        return redirect('profile')
    return render(request, 'main/edit_ad.html', {'ad': ad})

def create_ad_view(request):
    if request.method == 'POST':
        ad = Ad(user=request.user)
        ad.title = request.POST.get('title', '')
        ad.purpose = request.POST.get('purpose', '')
        ad.section = request.POST.get('section', '')
        ad.specialty = request.POST.get('specialty', '')
        ad.text_ar = request.POST.get('text_ar', '')
        ad.text_en = request.POST.get('text_en', '')
        ad.contact_phone = request.POST.get('contact_phone', '')
        ad.contact_email = request.POST.get('contact_email', '')
        ad.status = 'publish' if request.POST.get('action') == 'publish' else 'draft'
        for i in range(4):
            f = request.FILES.get(f'image_{i}')
            if f:
                setattr(ad, f'image_{i}', f)
        ad.save()
        if ad.status == 'publish':
            messages.success(request, 'تم نشر الإعلان بنجاح')
        else:
            messages.success(request, 'تم حفظ الإعلان كمسودة')
        return redirect('home')
    return render(request, 'main/create_ad.html')
