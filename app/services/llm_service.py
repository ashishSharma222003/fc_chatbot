"""
LLM Service

This service handles communication with Large Language Model providers (e.g., OpenAI).
It is responsible for sending prompts to the LLM and returning the generated text,
abstracting the specific API details. It uses tiktoken for accurate token counting.
"""
import tiktoken
from openai import AsyncOpenAI
import json
from typing import Dict, Any, Tuple, AsyncGenerator
from app.core.config import settings

class LLMService:
    def __init__(self, model: str = "gpt-4o-mini"):
        self.model = model
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        try:
            self.encoding = tiktoken.encoding_for_model(model)
        except KeyError:
            # Fallback for unknown models
            self.encoding = tiktoken.get_encoding("cl100k_base")

    def count_tokens(self, text: str) -> int:
        """Returns the number of tokens in a text string."""
        return len(self.encoding.encode(text))

    async def generate_response(self, prompt: str,system_prompt: str ) -> Tuple[str, dict]:
        """
        Generates a response from the LLM.
        Returns a tuple of (generated_text, token_count).
        """
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]
        )
        generated_text = response.choices[0].message.content
        
        # Accurate token counting
        input_tokens = self.count_tokens(prompt)
        output_tokens = self.count_tokens(generated_text)
        total_tokens = input_tokens + output_tokens
        tokens={
            "input_tokens":input_tokens,
            "output_tokens":output_tokens,
            "total_tokens":total_tokens
        }
        return generated_text, tokens

    async def get_structured_response(self, user_prompt: str, schema: Dict[str, Any], system_prompt: str) -> Dict[str, Any]:
        """
        Generates a structured JSON response based on a provided schema and prompts.
        """
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "structured_response",
                    "schema": schema
                }
            }
        )
        input_tokens=self.count_tokens(user_prompt+system_prompt+schema)
        output_tokens=self.count_tokens(response.choices[0].message.content)
        tokens={
            "input_tokens":input_tokens,
            "output_tokens":output_tokens,
            "total_tokens":input_tokens+output_tokens
        }
        return json.loads(response.choices[0].message.content),tokens
