from django.utils import translation


class ForceArabicMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        lang = request.session.get(translation.LANGUAGE_SESSION_KEY)
        if not lang:
            translation.activate('ar')
            request.LANGUAGE_CODE = 'ar'
        response = self.get_response(request)
        return response
