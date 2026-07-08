from django.utils import translation


class ForceArabicMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        translation.activate('ar')
        request.LANGUAGE_CODE = 'ar'
        request.session['django_language'] = 'ar'
        response = self.get_response(request)
        return response
