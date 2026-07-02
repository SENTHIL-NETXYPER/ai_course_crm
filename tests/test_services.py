import pytest
import os
from app.services.groq_service import GroqService
from app.services.scrape_service import ScrapeService

def test_groq_service_mock_mode():
    # Ensure GroqService runs cleanly in mock mode when no API key or when offline
    service = GroqService()
    # Temporarily set client to None to test deterministic fallback
    service.client = None
    
    res = service.generate("Topic: Java", system_prompt="AI Writer Agent")
    assert "Variables" in res or "course" in res or "chapter" in res

def test_scrape_service_clean_html(tmp_path):
    scraper = ScrapeService(output_dir=str(tmp_path))
    noisy_html = """
    <html>
      <head><style>.ad { color: red; }</style></head>
      <body>
        <nav>Menu Bar</nav>
        <div class="cookie-banner">Accept cookies</div>
        <main>
          <h1>Learn Python</h1>
          <p>Python is an amazing language.</p>
        </main>
        <footer>Copyright 2026</footer>
      </body>
    </html>
    """
    cleaned = scraper._clean_html(noisy_html)
    assert "Menu Bar" not in cleaned
    assert "Accept cookies" not in cleaned
    assert "Copyright 2026" not in cleaned
    assert "Learn Python" in cleaned
    assert "Python is an amazing language." in cleaned
