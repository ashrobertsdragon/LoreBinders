from dataclasses import dataclass


@dataclass
class RoleScript:
    """
    Holds the AI system role script and max tokens for an API call
    """

    script: str
    max_tokens: int
