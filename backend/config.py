"""Central configuration: env loading, constants, cache TTLs, lookup maps."""
import os
from dotenv import load_dotenv

load_dotenv()

# --- API keys (4 key-gated features) ---
HUGGINGFACE_API_TOKEN = os.getenv("HUGGINGFACE_API_TOKEN", "").strip()
GNEWS_API_KEY = os.getenv("GNEWS_API_KEY", "").strip()
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY", "").strip()
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "").strip()

# --- CORS ---
FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "*").strip() or "*"

# --- Demo mode ---
# When ON, endpoints fall back to clearly-flagged synthetic data if Google Trends
# is unavailable (rate-limited / blocked), so the tool stays presentable in a
# live demo. Responses carry "demo": true. Off by default.
DEMO_MODE = os.getenv("TRENDPULSE_DEMO", "").strip().lower() in ("1", "true", "yes")

# --- Groq (preferred LLM: fast, free, Llama-3.3-70B) ---
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile").strip()

# --- Brave Search (competitor discovery + SERP signal; free 2k/mo) ---
BRAVE_API_KEY = os.getenv("BRAVE_API_KEY", "").strip()

# --- Upstash Redis (free persistent cache across restarts) ---
UPSTASH_URL = os.getenv("UPSTASH_REDIS_REST_URL", "").strip()
UPSTASH_TOKEN = os.getenv("UPSTASH_REDIS_REST_TOKEN", "").strip()

# --- Hugging Face model for AI summaries (Feature 23) ---
# Uses the HF Inference Providers router (OpenAI-compatible). The old serverless
# endpoint (api-inference.huggingface.co) was retired, and Mistral-7B is no longer
# served on the free router, so we default to Llama 3.1 8B Instruct (free tier,
# strong marketing prose). Override with HF_MODEL; Qwen/Qwen2.5-7B-Instruct also works.
HF_MODEL = os.getenv("HF_MODEL", "meta-llama/Llama-3.1-8B-Instruct").strip()

# --- Cache TTLs in seconds ---
TTL_TRENDS = 15 * 60      # Google Trends data
TTL_WIKI = 60 * 60        # Wikipedia pageviews
TTL_SOCIAL = 30 * 60      # Reddit / HN / GNews / YouTube / GitHub
TTL_CURRENCY = 5 * 60     # FX rates
TTL_SUMMARY = 60 * 60     # AI summaries
TTL_SEASONAL = 6 * 60 * 60  # 5y series used for seasonality

# --- Time range -> pytrends timeframe string ---
TIMEFRAME_MAP = {
    "7D": "now 7-d",
    "30D": "today 1-m",
    "90D": "today 3-m",
    "12M": "today 12-m",
    "5Y": "today 5-y",
}
DEFAULT_RANGE = "90D"

# --- Region code -> pytrends geo ('' == Global) ---
GEO_MAP = {
    "NG": "NG",
    "ZA": "ZA",
    "US": "US",
    "GB": "GB",
    "GLOBAL": "",
}
DEFAULT_GEO = "NG"

# --- Niche -> representative seed keyword (Feature 7) ---
# We surface each niche's "top 10 trending" via rising related queries on the seed.
NICHE_SEEDS = {
    "digital_marketing": "digital marketing",
    "ecommerce": "ecommerce",
    "real_estate": "real estate",
    "health_wellness": "wellness",
    "finance_fintech": "fintech",
    "ai_technology": "artificial intelligence",
    "fashion_beauty": "fashion",
    "food_restaurants": "restaurant",
}

# Niches where dev/tech signals (GitHub, HN) auto-activate (Features 13, 21)
TECH_NICHES = {"ai_technology", "digital_marketing"}
