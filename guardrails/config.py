# NeMo 0.10 chỉ dùng ChatOpenAI cho engine "openai" khi tên model chứa gpt-3.5/gpt-4;
# model khác rơi về completions API (DeepSeek trả 422). Đăng ký engine chat riêng.
from langchain_openai import ChatOpenAI
from nemoguardrails.llm.providers import register_llm_provider

register_llm_provider("deepseek", ChatOpenAI)
