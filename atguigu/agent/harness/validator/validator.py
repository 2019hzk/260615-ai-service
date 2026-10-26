"""
职责：负责校验LLM的输出


"""
from typing import Any


class ValidateOutputError(ValueError):
    pass


class Validator:

    async def validate(self, output: Any):
        pass
