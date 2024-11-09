from config.settings import SITE_NAME


def site_name(request):
    return {"SITE_NAME": SITE_NAME}
