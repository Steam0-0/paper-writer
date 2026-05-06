import logging
import time
from typing import Optional

from langchain_openai import ChatOpenAI
from langchain_core.outputs import ChatGeneration, ChatResult

from config import llm_config
from state import AgentResponse

logger = logging.getLogger(__name__)


class LLMClient:
    def __init__(self):
        self._client: Optional[ChatOpenAI] = None
        self._initialize_client()

    def _initialize_client(self):
        self._client = ChatOpenAI(
            base_url=llm_config.base_url,
            api_key=llm_config.api_key,
            model=llm_config.model,
            temperature=llm_config.temperature,
            max_retries=0,
            request_timeout=llm_config.timeout
        )

    def _retry_with_backoff(self, func, *args, **kwargs):
        last_exception = None
        for attempt in range(llm_config.max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                wait_time = 2 ** attempt
                logger.warning(f"LLM call failed (attempt {attempt + 1}/{llm_config.max_retries}): {e}")
                if attempt < llm_config.max_retries - 1:
                    logger.info(f"Retrying in {wait_time}s...")
                    time.sleep(wait_time)
        raise last_exception

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> AgentResponse:
        try:
            messages = []
            if system_prompt:
                messages.append(("system", system_prompt))
            messages.append(("user", prompt))

            def _call():
                return self._client.invoke(messages)

            result = self._retry_with_backoff(_call)
            return AgentResponse(success=True, content=result.content)
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            return AgentResponse(success=False, error=str(e))

    def structured_generate(self, prompt: str, system_prompt: str, output_schema: type) -> AgentResponse:
        from langchain_core.output_parsers import JsonOutputParser
        from langchain_core.prompts import ChatPromptTemplate

        try:
            parser = JsonOutputParser(pydantic_object=output_schema)
            prompt_template = ChatPromptTemplate.from_messages([
                ("system", system_prompt),
                ("user", "{prompt}")
            ])
            chain = prompt_template | self._client | parser

            def _call():
                return chain.invoke({"prompt": prompt})

            result = self._retry_with_backoff(_call)
            return AgentResponse(success=True, content=result)
        except Exception as e:
            logger.error(f"LLM structured generation failed: {e}")
            return AgentResponse(success=False, error=str(e))

    def close(self):
        self._client = None


llm_client = LLMClient()