from .settings_local import *
import os.path
import warnings


TELEGRAM_TOKEN = "telegramtoken"
TELEGRAM_WEBHOOK_SECRET = "webhooksecret"

MEDIA_ROOT = os.path.join(BASE_DIR, "functional_tests/testmedia")

warnings.filterwarnings(u'ignore', message=u'DateTimeField Event.start received a naive datetime',
                        category=RuntimeWarning, )
warnings.filterwarnings(u'ignore', message=u'DateTimeField Photo.timestamp received a naive datetime',
                        category=RuntimeWarning, )
warnings.filterwarnings(u'ignore', message=u'DateTimeField File.timestamp received a naive datetime',
                        category=RuntimeWarning, )
warnings.filterwarnings(u'ignore', message=u'DateTimeField Link.timestamp received a naive datetime',
                        category=RuntimeWarning, )
warnings.filterwarnings(u'ignore', message=u'DateTimeField Audio.timestamp received a naive datetime',
                        category=RuntimeWarning, )
warnings.filterwarnings(u'ignore', message=u'DateTimeField Sticker.timestamp received a naive datetime',
                        category=RuntimeWarning, )
warnings.filterwarnings(u'ignore', message=u'DateTimeField Text.timestamp received a naive datetime',
                        category=RuntimeWarning, )
warnings.filterwarnings(u'ignore', message=u'DateTimeField Video.timestamp received a naive datetime',
                        category=RuntimeWarning, )
warnings.filterwarnings(u'ignore', message=u'DateTimeField Survey.created received a naive datetime',
                        category=RuntimeWarning, )
