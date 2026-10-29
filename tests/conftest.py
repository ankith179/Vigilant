"""Keep import-time API initialization away from the user's live database."""
import os

os.environ['VIGILANT_DB'] = 'sqlite:///:memory:'
