import random
from datetime import datetime

class SEOManager:
    @staticmethod
    def generate_caption(keywords: list[str], hashtags: list[str], quote: str, reminder_body: str = None, engaging_body: str = None):
        """
        Generates an SEO-optimized caption for Instagram.
        Prioritizes dynamic engaging content over template-based reminders.
        """
        import pytz
        ist = pytz.timezone('Asia/Kolkata')
        date_str = datetime.now(ist).strftime('%A, %B %d, %Y')
        
        # Build the caption
        header_hook = f"✨ {quote} ✨"
        
        if engaging_body:
            # Use the AI generated engaging content as the primary body
            main_content = engaging_body
        else:
            # Fallback to the structured reminder if AI content is missing
            if reminder_body:
                main_content = f"Remember <3\n{reminder_body}\n\nToday is {date_str}. Let this be your sign to stay intentional."
            else:
                main_content = f"Daily Reminder <3\nIt's {date_str}. Falling in love with you every single day."

        caption = (
            f"{header_hook}\n\n"
            f"{main_content}\n\n"
            f"---\n\n"
            f"{' '.join(hashtags)}\n\n"
            f"Keywords: {', '.join(keywords)}"
        )
        return caption.strip()

    @staticmethod
    def generate_accessibility_caption(custom_message: str):
        """
        Generates alt-text for accessibility and algorithm optimization.
        """
        return f"A romantic video Reel with text: {custom_message}. The background shows personal moments with a soft aesthetic."
