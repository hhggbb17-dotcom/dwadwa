"""Punto de entrada para servidores WSGI como PythonAnywhere."""

from app import app as application
from app import initialize_database


initialize_database()
