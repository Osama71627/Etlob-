from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Count, Q, Sum
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils import timezone
from django.utils.translation import gettext as _
from datetime import timedelta
from .models import Ad, Profile, Subscription, Notification, Favorite
from django.urls import reverse
from django.core.paginator import Paginator
from django.views.decorators.cache import never_cache
import json

PURPOSES = {
    "وظائف": {
        "اعلان عن وظيفة شاغرة": ["برمجة", "تصميم", "هندسة", "محاسبة", "تسويق", "مبيعات", "إدارة", "طب", "تمريض", "تعليم", "سياحة", "مطاعم", "خدمة عملاء", "سكرتارية", "أمن", "نظافة", "مقاولات", "اتصالات", "طاقة"],
        "ابحث عن عمل": ["برمجة", "تصميم", "هندسة", "محاسبة", "تسويق", "مبيعات", "إدارة", "طب", "تمريض", "تعليم", "سياحة", "مطاعم", "خدمة عملاء", "سكرتارية"],
        "عرض خدمة": ["استشارات", "تدريب", "تصميم", "برمجة", "تسويق إلكتروني", "ترجمة", "كتابة", "تصوير"]
    },
    "خدمات": {
        "تنظيف": [], "صيانة": [], "نقل": [], "توصيل": [], "ضيافة": [], "تعليم خصوصي": [],
        "رعاية أطفال": [], "رعاية مسنين": [], "تصليح": [], "بناء": [], "دهان": [],
        "سباكة": [], "كهرباء": [], "نجارة": [], "حدادة": [], "عناية بالحيوانات": []
    },
    "عقارات": {
        "شقة": ["إيجار", "تمليك"], "فيلا": ["إيجار", "تمليك"], "أرض": ["سكني", "تجاري", "زراعي"],
        "محل تجاري": ["إيجار", "تمليك"], "مكتب": ["إيجار", "تمليك"], "مستودع": ["إيجار", "تمليك"],
        "استراحة": ["إيجار", "تمليك"], "شاليه": ["إيجار", "تمليك"], "مزرعة": ["إيجار", "تمليك"],
        "عمارة": ["تمليك"], "دور": ["إيجار", "تمليك"], "غرفة": ["إيجار"]
    },
    "سيارات": {
        "تويوتا": [], "هوندا": [], "نيسان": [], "مرسيدس": [], "بي إم دبليو": [], "أودي": [],
        "فورد": [], "شيفروليه": [], "هيونداي": [], "كيا": [], "ميتسوبيشي": [], "مازدا": [],
        "لكزس": [], "جيب": [], "رنج روفر": [], "فولكس": [], "بورش": [], "دراجة نارية": [],
        "شاحنة": [], "معدات ثقيلة": [], "قوارب": []
    },
    "أجهزة": {
        "جوال": ["آيفون", "سامسونج", "هواوي", "شاومي", "أوبو", "نوكيا", "آخر"],
        "لاب توب": ["ديل", "إتش بي", "لينوفو", "آبل", "آسوس", "آيسر", "آخر"],
        "كمبيوتر": ["مكتبي", "ألعاب", "خادم", "آخر"],
        "تابلت": ["آيباد", "سامسونج", "آخر"],
        "تلفزيون": ["LED", "OLED", "QLED"],
        "كاميرا": ["كانون", "نيكون", "سوني"],
        "سماعات": [], "ساعة ذكية": ["آبل", "سامسونج", "آخر"], "إكسسوارات": []
    },
    "حيوانات": {
        "كلاب": [], "قطط": [], "طيور": [], "خيول": [], "أسماك": [], "أغنام": [],
        "أبقار": [], "إبل": [], "دجاج": [], "ماعز": [], "أرانب": [],
        "زواحف": [], "مستلزمات حيوانات": []
    },
    "هوايات": {
        "كتب": ["روايات", "تعليمية", "دينية", "أطفال", "أخرى"],
        "ألعاب": ["بلاي ستيشن", "إكس بوكس", "نينتندو", "PC", "ألعاب لوحية"],
        "رياضة": ["أوزان", "جري", "سباحة", "كرة قدم", "كرة سلة", "تنس", "دراجات", "تخييم"],
        "موسيقى": ["آلات موسيقية", "أجهزة صوت"],
        "فن": ["رسم", "نحت", "خط عربي", "تصوير"],
        "طبخ": ["أدوات مطبخ", "وصفات"],
        "أعمال يدوية": [], "مجموعات": ["طوابع", "عملات", "أنتيكات", "تحف"]
    },
    "ملابس": {
        "رجالية": ["بدل", "جاكيت", "قميص", "تي شيرت", "بنطلون", "جينز", "أحذية", "ساعات", "إكسسوارات"],
        "نسائية": ["فساتين", "عباءات", "بلوزة", "تنورة", "جينز", "أحذية", "شنط", "إكسسوارات", "مجوهرات"],
        "أطفال": ["ملابس أطفال", "أحذية أطفال", "مستلزمات رضع"],
        "مستعمل": []
    },
    "أخرى": {}
}

def admin_check(user):
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    profile, created = Profile.objects.get_or_create(user=user)
    return profile.role in ['admin', 'moderator']


def notify_new_ad(ad):
    """Send notification to all users except the ad owner."""
    ad_url = reverse('ad_detail', args=[ad.id])
    title = f'📢 إعلان جديد في {ad.purpose}'
    ad_text = (ad.title if ad.title else ad.text_ar)[:50]
    message = f'{ad_text} — القسم: {ad.section}'
    notifs = [
        Notification(user=u, type='info', title=title, message=message, url=ad_url)
        for u in User.objects.exclude(id=ad.user.id)
    ]
    Notification.objects.bulk_create(notifs)


def notify_new_package(pkg):
    """Send notification to all users about a new star package."""
    url = reverse('subscription_shop')
    title = f'🎉 عرض جديد: {pkg.stars} ⭐ بسعر {pkg.price} ريال'
    message = f'باقة {pkg.stars} نجوم جديدة متاحة الآن! اشترِ وتميّز إعلانك.'
    notifs = [
        Notification(user=u, type='success', title=title, message=message, url=url)
        for u in User.objects.all()
    ]
    Notification.objects.bulk_create(notifs)

@user_passes_test(admin_check, login_url='login')
@user_passes_test(admin_check, login_url='login')
def dashboard_view(request):
    total_users = User.objects.count()
    total_ads = Ad.objects.count()
    active_ads = Ad.objects.filter(status='publish').count()
    pending_ads = Ad.objects.filter(status='pending').count()
    total_views = Ad.objects.aggregate(total=Sum('views'))['total'] or 0
    recent_ads = Ad.objects.order_by('-created_at')[:5]
    users_by_role = Profile.objects.values('role').annotate(count=Count('id'))

    return render(request, 'main/dashboard.html', {
        'total_users': total_users,
        'total_ads': total_ads,
        'active_ads': active_ads,
        'pending_ads': pending_ads,
        'total_views': total_views,
        'recent_ads': recent_ads,
        'users_by_role': users_by_role,
    })

@user_passes_test(admin_check, login_url='login')
def dashboard_users(request):
    users_list = User.objects.select_related('profile').annotate(ad_count=Count('ads')).order_by('-date_joined')
    paginator = Paginator(users_list, 20)
    page = request.GET.get('page', 1)
    users = paginator.get_page(page)
    return render(request, 'main/dashboard_users.html', {'users': users})

@user_passes_test(admin_check, login_url='login')
@user_passes_test(admin_check, login_url='login')
def dashboard_ads(request):
    ads_list = Ad.objects.select_related('user').order_by('-created_at')
    paginator = Paginator(ads_list, 20)
    page = request.GET.get('page', 1)
    ads = paginator.get_page(page)
    return render(request, 'main/dashboard_ads.html', {'ads': ads})

@user_passes_test(admin_check, login_url='login')
def dashboard_subscriptions(request):
    from .models import StarPackage
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'add':
            stars = int(request.POST.get('stars', 0))
            price = float(request.POST.get('price', 0))
            is_popular = request.POST.get('is_popular') == 'on'
            if stars > 0 and price > 0:
                pkg = StarPackage.objects.create(stars=stars, price=price, is_popular=is_popular)
                notify_new_package(pkg)
                messages.success(request, f'تمت إضافة الباقة {stars} ⭐ بسعر {price} ريال وتم إشعار جميع المستخدمين')
        elif action == 'edit':
            pkg_id = int(request.POST.get('pkg_id', 0))
            pkg = get_object_or_404(StarPackage, id=pkg_id)
            was_inactive = not pkg.is_active
            pkg.stars = int(request.POST.get('stars', pkg.stars))
            pkg.price = float(request.POST.get('price', pkg.price))
            pkg.is_popular = request.POST.get('is_popular') == 'on'
            pkg.is_active = request.POST.get('is_active') == 'on'
            pkg.save()
            if was_inactive and pkg.is_active:
                notify_new_package(pkg)
            messages.success(request, 'تم تحديث الباقة')
        elif action == 'delete':
            pkg_id = int(request.POST.get('pkg_id', 0))
            StarPackage.objects.filter(id=pkg_id).delete()
            messages.success(request, 'تم حذف الباقة')
        return redirect('dashboard_subscriptions')
    subs_list = Subscription.objects.select_related('user__profile').order_by('-start_date')
    subs_paginator = Paginator(subs_list, 20)
    subs_page = request.GET.get('page', 1)
    subs = subs_paginator.get_page(subs_page)
    packages = StarPackage.objects.filter(is_active=True)
    all_packages = StarPackage.objects.all().order_by('stars')
    return render(request, 'main/dashboard_subscriptions.html', {
        'subscriptions': subs,
        'packages': packages,
        'all_packages': all_packages,
    })

def notifications_view(request):
    notifs = request.user.notifications.all().order_by('-created_at')
    unread = notifs.filter(is_read=False)
    unread.update(is_read=True)
    return render(request, 'main/notifications.html', {'notifications': notifs})

def mark_read(request, notif_id):
    n = get_object_or_404(Notification, id=notif_id, user=request.user)
    n.is_read = True
    n.save()
    return redirect('notifications')

@user_passes_test(admin_check, login_url='login')
def dashboard_user_detail(request, user_id):
    u = get_object_or_404(User.objects.select_related('profile', 'subscription'), id=user_id)
    user_ads = Ad.objects.filter(user=u).order_by('-created_at')
    return render(request, 'main/dashboard_user_detail.html', {'u': u, 'user_ads': user_ads})

@user_passes_test(admin_check, login_url='login')
def dashboard_user_action(request, user_id, action):
    u = get_object_or_404(User, id=user_id)
    profile, _ = Profile.objects.get_or_create(user=u)
    if action == 'ban':
        u.is_active = False
        profile.is_banned = True
        profile.save()
        u.save()
        Notification.objects.create(user=u, type='danger', title='تم إيقاف حسابك', message='تم إيقاف حسابك من قبل الإدارة. للاستفسار يرجى التواصل مع الدعم الفني.')
        messages.warning(request, f'تم إيقاف المستخدم "{u.username}"')
    elif action == 'unban':
        u.is_active = True
        profile.is_banned = False
        profile.save()
        u.save()
        Notification.objects.create(user=u, type='success', title='تم إلغاء إيقاف حسابك', message='تم إعادة تفعيل حسابك يمكنك الآن استخدام المنصة.')
        messages.success(request, f'تم إلغاء إيقاف المستخدم "{u.username}"')
    elif action == 'warn':
        profile.warnings += 1
        profile.save()
        Notification.objects.create(user=u, type='warning', title=f'تحذير رقم {profile.warnings}', message='نود تنبيهك بضرورة الالتزام بقواعد المنصة. في حال تكرار المخالفة قد يتم إيقاف حسابك.')
        messages.warning(request, f'تم إرسال تحذير للمستخدم "{u.username}" (إجمالي التحذيرات: {profile.warnings})')
    elif action == 'delete':
        uname = u.username
        u.delete()
        messages.success(request, f'تم حذف المستخدم "{uname}"')
        return redirect('dashboard_users')
    return redirect('dashboard_user_detail', user_id=user_id)

@user_passes_test(admin_check, login_url='login')
@user_passes_test(admin_check, login_url='login')
def dashboard_ad_action(request, ad_id, action):
    ad = get_object_or_404(Ad, id=ad_id)
    if action == 'approve':
        ad.status = 'publish'
        messages.success(request, f'تم نشر الإعلان "{ad.title}"')
    elif action == 'pending':
        ad.status = 'pending'
        messages.success(request, f'تم إيقاف الإعلان "{ad.title}"')
    elif action == 'archive':
        ad.status = 'archived'
        messages.success(request, f'تم أرشفة الإعلان "{ad.title}"')
    elif action == 'delete':
        ad.delete()
        messages.success(request, 'تم حذف الإعلان')
        return redirect('dashboard_ads')
    ad.save()
    return redirect('dashboard_ads')

def notify_expiring_featured():
    now = timezone.now()
    warning_window = now + timedelta(hours=1)
    expiring = Ad.objects.filter(
        is_featured=True,
        featured_until__gte=now,
        featured_until__lte=warning_window,
        featured_expiry_notified=False
    )
    for ad in expiring:
        Notification.objects.create(
            user=ad.user,
            type='warning',
            title='⚠️ تميز الإعلان على وشك الانتهاء',
            message=f'إعلانك "{ad.title}" سينتهي تميزه بعد ساعة. جدد تميزه الآن ليستمر ظهوره في المقدمة.',
            url=reverse('promote_ad', args=[ad.id]),
        )
    expiring.update(featured_expiry_notified=True)


def get_unviewed_new_ids(request, queryset):
    now = timezone.now()
    cutoff = now - timedelta(hours=48)
    new_ids = set(queryset.filter(created_at__gte=cutoff).values_list('id', flat=True))
    user = request.user
    if user.is_authenticated and user.date_joined > cutoff:
        cutoff = user.date_joined
        new_ids = set(queryset.filter(created_at__gte=cutoff).values_list('id', flat=True))
    viewed = set(request.session.get('viewed_new_ads', []))
    return list(new_ids - viewed)


@never_cache
def home(request):
    # Expire featured ads past their featured_until
    Ad.objects.filter(is_featured=True, featured_until__lt=timezone.now()).update(is_featured=False)
    notify_expiring_featured()

    ads_list = Ad.objects.filter(status='publish')

    search_in = request.GET.get('search_in', '')
    section = request.GET.get('section', '')
    specialty = request.GET.get('specialty', '')
    q = request.GET.get('q', '')
    sort = request.GET.get('sort', '-created_at')

    if search_in:
        ads_list = ads_list.filter(purpose=search_in)
    if section:
        ads_list = ads_list.filter(section=section)
    if specialty:
        ads_list = ads_list.filter(specialty=specialty)
    if q:
        from django.db.models import Q
        ads_list = ads_list.filter(
            Q(title__icontains=q) |
            Q(text_ar__icontains=q) |
            Q(section__icontains=q) |
            Q(specialty__icontains=q)
        ).distinct()

    ads_list = ads_list.order_by('-is_featured', sort)

    paginator = Paginator(ads_list, 20)
    page = request.GET.get('page', 1)
    ads = paginator.get_page(page)

    unviewed_new_ids = get_unviewed_new_ids(request, ads_list)

    filter_data = {
        'search_in': search_in,
        'section': section,
        'specialty': specialty,
        'q': q,
        'sort': sort,
    }

    return render(request, 'main/home.html', {'ads': ads, 'filter_data': filter_data, 'purposes_json': json.dumps(PURPOSES, ensure_ascii=False), 'unviewed_new_ids': unviewed_new_ids})

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
        messages.error(request, _('البريد الإلكتروني أو كلمة المرور غير صحيحة'))
    return render(request, 'main/login.html')

def signup_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        fullname = request.POST.get('fullname')
        phone = request.POST.get('phone')
        photo = request.FILES.get('photo')
        if User.objects.filter(email=email).exists():
            messages.error(request, _('البريد الإلكتروني مستخدم مسبقاً'))
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
        messages.success(request, _('تم إنشاء الحساب بنجاح'))
        return redirect('home')
    return render(request, 'main/signup.html')

def logout_view(request):
    logout(request)
    return redirect('home')

def ad_detail_view(request, ad_id):
    Ad.objects.filter(is_featured=True, featured_until__lt=timezone.now()).update(is_featured=False)
    notify_expiring_featured()
    ad = get_object_or_404(Ad, id=ad_id)
    viewed = request.session.get('viewed_ads', [])
    if ad_id not in viewed:
        ad.views += 1
        ad.save(update_fields=['views'])
        viewed.append(ad_id)
        request.session['viewed_ads'] = viewed
    viewed_new = request.session.get('viewed_new_ads', [])
    if ad_id not in viewed_new:
        viewed_new.append(ad_id)
        request.session['viewed_new_ads'] = viewed_new
    is_fav = False
    if request.user.is_authenticated:
        is_fav = Favorite.objects.filter(user=request.user, ad=ad).exists()
    related_ads = Ad.objects.filter(status='publish', purpose=ad.purpose).exclude(id=ad.id).order_by('-created_at')[:4]
    owner_profile = getattr(ad.user, 'profile', None)
    owner_ads_count = Ad.objects.filter(user=ad.user, status='publish').count()
    unviewed_new_ids = get_unviewed_new_ids(request, Ad.objects.filter(status='publish'))
    return render(request, 'main/ad_detail.html', {
        'ad': ad,
        'is_favorited': is_fav,
        'related_ads': related_ads,
        'owner_profile': owner_profile,
        'owner_ads_count': owner_ads_count,
        'unviewed_new_ids': unviewed_new_ids,
    })

@never_cache
def user_ads_view(request, username):
    Ad.objects.filter(is_featured=True, featured_until__lt=timezone.now()).update(is_featured=False)
    notify_expiring_featured()
    owner = get_object_or_404(User, username=username)
    ads_list = Ad.objects.filter(user=owner, status='publish').order_by('-created_at')
    paginator = Paginator(ads_list, 20)
    page = request.GET.get('page', 1)
    ads = paginator.get_page(page)
    owner_profile = getattr(owner, 'profile', None)
    owner_ads_count = Ad.objects.filter(user=owner, status='publish').count()
    unviewed_new_ids = get_unviewed_new_ids(request, ads_list)
    return render(request, 'main/user_ads.html', {
        'owner': owner,
        'ads': ads,
        'owner_profile': owner_profile,
        'owner_ads_count': owner_ads_count,
        'unviewed_new_ids': unviewed_new_ids,
    })

@never_cache
def profile_view(request):
    Ad.objects.filter(is_featured=True, featured_until__lt=timezone.now()).update(is_featured=False)
    notify_expiring_featured()
    user_ads_all = Ad.objects.filter(user=request.user).order_by('-created_at')
    ads_active = [a for a in user_ads_all if a.status == 'publish']
    ads_pending = [a for a in user_ads_all if a.status == 'pending']
    ads_draft = [a for a in user_ads_all if a.status == 'draft']
    ads_archived = [a for a in user_ads_all if a.status == 'archived']
    fav_ads = Ad.objects.filter(favorited_by__user=request.user).order_by('-favorited_by__created_at')
    unviewed_new_ids = get_unviewed_new_ids(request, user_ads_all)
    return render(request, 'main/profile.html', {
        'user_ads_all': user_ads_all,
        'ads_active': ads_active,
        'ads_pending': ads_pending,
        'ads_draft': ads_draft,
        'ads_archived': ads_archived,
        'fav_ads': fav_ads,
        'unviewed_new_ids': unviewed_new_ids,
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
        ad.is_whatsapp = request.POST.get('is_whatsapp') == 'on'
        ad.status = 'publish' if request.POST.get('action') == 'publish' else 'draft'
        for i in range(4):
            f = request.FILES.get(f'image_{i}')
            if f:
                setattr(ad, f'image_{i}', f)
        ad.save()
        if ad.status == 'publish':
            notify_new_ad(ad)
        messages.success(request, 'تم تحديث الإعلان بنجاح')
        return redirect('profile')
    return render(request, 'main/edit_ad.html', {'ad': ad, 'purposes_json': json.dumps(PURPOSES, ensure_ascii=False), 'purposes_list': list(PURPOSES.keys())})

@login_required
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
        ad.is_whatsapp = request.POST.get('is_whatsapp') == 'on'
        action = request.POST.get('action', '')
        ad.status = 'draft' if action == 'draft' else 'publish'
        for i in range(4):
            f = request.FILES.get(f'image_{i}')
            if f:
                setattr(ad, f'image_{i}', f)
        ad.save()
        if action == 'publish_and_promote':
            notify_new_ad(ad)
            messages.success(request, 'تم نشر الإعلان، اختر خطة التميز الآن')
            return redirect('promote_ad', ad_id=ad.id)
        if ad.status == 'publish':
            notify_new_ad(ad)
            messages.success(request, 'تم نشر الإعلان بنجاح')
        else:
            messages.success(request, 'تم حفظ الإعلان كمسودة')
        return redirect('home')
    return render(request, 'main/create_ad.html', {'purposes_json': json.dumps(PURPOSES, ensure_ascii=False)})


@login_required
def subscription_shop(request):
    from .models import StarPackage
    sub, _ = Subscription.objects.get_or_create(user=request.user)
    packages_qs = StarPackage.objects.filter(is_active=True).order_by('stars')
    if not packages_qs.exists():
        PACKAGES = [
            {'stars': 1, 'price': '1', 'label': 'نجمة واحدة', 'emoji': '⭐', 'days': 'يوم واحد', 'save': '', 'per_star': 1},
            {'stars': 5, 'price': '10', 'label': '5 نجوم', 'emoji': '⭐⭐⭐⭐⭐', 'days': '5 أيام', 'save': 'وفر 4⭐', 'per_star': 2, 'popular': True},
            {'stars': 10, 'price': '15', 'label': '10 نجوم', 'emoji': '🔟', 'days': '10 أيام', 'save': 'وفر 9⭐', 'per_star': 1.5},
            {'stars': 25, 'price': '30', 'label': '25 نجمة', 'emoji': '💎', 'days': '25 يوم', 'save': 'وفر 24⭐', 'per_star': 1.2},
        ]
    else:
        emojis = {1: '⭐', 5: '⭐⭐⭐⭐⭐', 10: '🔟', 25: '💎'}
        PACKAGES = []
        for p in packages_qs:
            emoji = emojis.get(p.stars, '⭐' * min(p.stars, 5))
            days = f'{p.stars} يوم' if p.stars > 1 else 'يوم واحد'
            if p.stars >= 25:
                days = f'{p.stars} يوم'
            elif p.stars >= 7:
                days = f'{p.stars} يوم'
            per_star = round(float(p.price) / p.stars, 2) if p.stars > 0 else 0
            save = ''
            if p.stars > 1:
                save = f'وفر {p.stars - 1}⭐'
            PACKAGES.append({
                'stars': p.stars,
                'price': str(p.price),
                'label': f'{p.stars} نجوم',
                'emoji': emoji,
                'days': days,
                'save': save,
                'popular': p.is_popular,
                'per_star': per_star,
            })
    if request.method == 'POST':
        stars = int(request.POST.get('stars', 0))
        for p in PACKAGES:
            if p['stars'] == stars:
                sub.stars += stars
                sub.save()
                messages.success(request, f'تم شراء {stars} ⭐ بنجاح! رصيدك الحالي: {sub.stars} ⭐')
                return redirect('subscription_shop')
    return render(request, 'main/subscription_shop.html', {'packages': PACKAGES, 'stars': sub.stars})


@login_required
def promote_ad_view(request, ad_id):
    if ad_id == 0:
        messages.warning(request, 'احفظ الإعلان أولاً ثم قم بتمييزه من صفحة ملفك الشخصي')
        return redirect('create_ad')
    ad = get_object_or_404(Ad, id=ad_id, user=request.user)
    sub, _ = Subscription.objects.get_or_create(user=request.user)

    PLANS = [
        {'days': 1, 'stars': 1, 'label': 'يوم واحد', 'stars_label': '⭐'},
        {'days': 2, 'stars': 2, 'label': 'يومين', 'stars_label': '⭐⭐'},
        {'days': 3, 'stars': 3, 'label': '3 أيام', 'stars_label': '⭐⭐⭐'},
        {'days': 5, 'stars': 5, 'label': '5 أيام', 'stars_label': '⭐⭐⭐⭐⭐'},
        {'days': 8, 'stars': 8, 'label': '8 أيام', 'stars_label': '⭐⭐⭐⭐⭐⭐⭐⭐'},
    ]

    if request.method == 'POST':
        plan_stars = int(request.POST.get('stars', 0))
        for p in PLANS:
            if p['stars'] == plan_stars:
                if sub.stars >= plan_stars:
                    sub.stars -= plan_stars
                    sub.save()
                    ad.is_featured = True
                    ad.featured_until = timezone.now() + timedelta(days=p['days'])
                    ad.featured_expiry_notified = False
                    ad.save()
                    messages.success(request, f'تم تمييز الإعلان لمدة {p["days"]} يوم')
                    return redirect('home')
                else:
                    messages.error(request, f'رصيدك غير كافٍ. تحتاج {plan_stars} ⭐ لديك {sub.stars} ⭐ فقط')
                    return redirect('subscription_shop')
    return render(request, 'main/promote_ad.html', {'ad': ad, 'plans': PLANS, 'stars': sub.stars})


@login_required
def toggle_favorite(request, ad_id):
    ad = get_object_or_404(Ad, id=ad_id)
    fav, created = Favorite.objects.get_or_create(user=request.user, ad=ad)
    if not created:
        fav.delete()
    return redirect('ad_detail', ad_id=ad_id)


@login_required
def pause_ad(request, ad_id):
    ad = get_object_or_404(Ad, id=ad_id, user=request.user)
    if ad.status == 'publish':
        ad.status = 'pending'
        ad.save()
        messages.success(request, 'تم إيقاف الإعلان مؤقتاً')
    else:
        ad.status = 'publish'
        ad.save()
        messages.success(request, 'تم إعادة نشر الإعلان')
    return redirect('profile')
