from src.services.groq_client import GroqQuoteGenerator
from src.core.seo import SEOManager
from src.config.settings import settings
from src.core.logger import Log

def test_caption_generation():
    Log.info("Starting Caption Generation Test...")
    
    try:
        # 1. Initialize Generator
        generator = GroqQuoteGenerator()
        
        # 2. Generate Quote
        quote = generator.generate_quote()
        Log.success(f"Generated Quote: {quote}")
        
        # 3. Generate Engaging Body
        engaging_body = generator.generate_engaging_caption(quote)
        Log.success(f"Generated Engaging Body: {engaging_body}")
        
        # 4. Generate Final Caption using SEOManager
        # Using mock reminder_body similar to production
        reminder_body = (
            "You are my everything. "
            "I'm still falling in love with you "
            "and won't stop loving you, ilysm."
        )
        
        final_caption = SEOManager.generate_caption(
            keywords=settings.keywords,
            hashtags=settings.hashtags,
            quote=quote,
            reminder_body=reminder_body,
            engaging_body=engaging_body
        )
        
        print("\n" + "="*50)
        print("FINAL INSTAGRAM CAPTION")
        print("="*50)
        print(final_caption)
        print("="*50 + "\n")
        
        Log.success("Caption Generation Test Completed Successfully.")
        
    except Exception as e:
        Log.error(f"Test failed: {e}")

if __name__ == "__main__":
    test_caption_generation()
