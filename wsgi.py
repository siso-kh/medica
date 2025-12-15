# wsgi.py
from app import create_app

# Call the factory function to create the actual application object
app = create_app()