"""AI layer: OpenAI provider, content cache, grounded prompts.

Serving chain: static fallbacks -> in-memory cache -> live call (skipped
entirely in DEMO_MODE). Every response reports its source so the UI can
show the "verified saved guidance" badge honestly."""
