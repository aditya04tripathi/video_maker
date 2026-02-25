import json
from groq import Groq
from pydantic import BaseModel
from src.config.settings import settings
from src.core.logger import Log
from src.core.utils import strip_markdown

class GroqQuoteSchema(BaseModel):
    quote: str

class GroqQuoteGenerator:
    def __init__(self):
        self.client = Groq(api_key=settings.groq_api_key)
        self.model = "llama-3.1-8b-instant"

    def generate_quote(self):
        """
        Generates a one-liner romantic quote using Groq in JSON mode.
        """
        if not settings.groq_api_key:
            Log.warning("GROQ_API_KEY not found. Using fallback quote.")
            return "I love you more than words can say. ❤️"

        try:
            Log.info("Requesting romantic quote from Groq...")
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are a romantic poet. Generate a unique, short, one-liner romantic quote. Output in JSON format with a 'quote' key."
                    },
                    {
                        "role": "user",
                        "content": "Give me a beautiful romantic one-liner for my love."
                    },
                ],
                model=self.model,
                response_format={"type": "json_object"},
            )
            
            content = chat_completion.choices[0].message.content
            response_data = json.loads(content)
            
            # Handle list or dict response
            if isinstance(response_data, list):
                if len(response_data) > 0 and isinstance(response_data[0], dict):
                    quote = response_data[0].get("quote")
                else:
                    quote = str(response_data[0]) if response_data else None
            elif isinstance(response_data, dict):
                quote = response_data.get("quote")
            else:
                quote = str(response_data)

            if not quote:
                quote = "You are my everything. ❤️"
                
            Log.info(f"Generated quote: {quote}")
            return quote

        except Exception as e:
            Log.error(f"Groq quote generation failed: {e}")
            return "Falling in love with you every single day. ❤️"

    def generate_engaging_caption(self, quote: str):
        """
        Generates an engaging, story-driven Instagram caption based on a romantic quote.
        Uses emotional language to drive saves and shares.
        """
        if not settings.groq_api_key:
            return None

        try:
            Log.info("Requesting engaging caption from Groq...")
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a social media strategist for a romantic aesthetic page. "
                            "Create a high-engagement Instagram caption for a Reel based on a quote. "
                            "DO NOT use any markdown formatting like bold (**), italics (*), or bullet points. "
                            "Structure: \n"
                            "1. Emotional hook related to the quote.\n"
                            "2. Short, relatable story or reflection on being intentional in love.\n"
                            "3. A gentle call to action (encouraging a 'Save' for later or 'Share' with a partner).\n"
                            "Keep it aesthetic, vulnerable, and minimalist. Use plain text only. Use line breaks for readability. "
                            "Output in JSON format with a 'caption' key."
                        )
                    },
                    {
                        "role": "user",
                        "content": f"The quote is: {quote}"
                    },
                ],
                model=self.model,
                response_format={"type": "json_object"},
            )
            
            content = chat_completion.choices[0].message.content
            response_data = json.loads(content)
            caption = response_data.get("caption", "")
            
            # Strip markdown and leading/trailing whitespace using the robust list-tool
            if caption:
                caption = strip_markdown(caption)
                
            Log.success(caption)
            return caption

        except Exception as e:
            Log.error(f"Groq caption generation failed: {e}")
            return None

if __name__ == "__main__":
    from src.config.settings import settings
    from src.core.logger import Log
    from src.core.seo import SEOManager

    hashtags: list[str] = [
        "#viral", "#reels", "#trending", "#fyp", "#explorepage"
    ]
    keywords: list[str] = [
        "love", "romance", "couplegoals", "relationshipgoals", "inlove",
        "foreverlove", "soulmates", "lovequotes", "romantic", "trueLove",
        "unconditionallove", "partnerincrime", "happilyeverafter", "heartfelt",
        "lovebirds", "togetherforever", "mylove", "endlesslove", "powercouple",
        "romanticvibes", "lovestory", "couplelove", "relationship",
        "romanticmoments", "deeplyinlove", "trueloveexists", "lovelife",
        "loveandtrust", "purelove", "couples", "loveforever",
        "romanticcouple", "loveyou", "heartandsoul", "madeforeachother",
        "perfectpair", "loveconnection", "intimatelove", "soulconnection",
        "lovebond", "eternallove", "romanticlife", "lovechemistry",
        "relationshipvibes", "loveinspiration", "hopelessromantic",
        "couplevibes", "lovejourney", "romanticfeelings", "inlovewithyou"
    ]

    seo_manager = SEOManager()

    generator = GroqQuoteGenerator()
    print(seo_manager.generate_caption(keywords, hashtags, generator.generate_quote()))