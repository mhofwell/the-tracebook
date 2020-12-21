import os
from tempfile import mkdtemp


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-wont-guess'
    FLASK_ENV = 'development'
    FLASK_DEBUG = 1
    TESTING = True
    TEMPLATES_AUTO_RELOAD = True
    SESSION_FILE_DIR = mkdtemp()
    SESSION_PERMANENT = False
    # Configure session to use filesystem (instead of signed cookies)
    SESSION_TYPE = "filesystem"
