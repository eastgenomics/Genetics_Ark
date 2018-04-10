from django.template import Library
register = Library()


# Generic version function, given an app/library you can will get the __version__ back
# Usage: {{app|app_version}}
@register.filter
def app_version( app ):
    import importlib

    app = importlib.import_module( app )
    return app.__version__
