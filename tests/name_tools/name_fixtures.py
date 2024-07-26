import pytest
from unittest.mock import Mock

from lorebinders.name_tools.name_analyzer import NameAnalyzer
from lorebinders.name_tools.name_extractor import NameExtractor
from lorebinders.name_tools.name_summarizer import NameSummarizer

@pytest.fixture
def ai_interface() -> Mock:
    return Mock()

@pytest.fixture
def mock_create_prompts() -> Mock:
    return Mock()

@pytest.fixture
def name_extractor(ai_interface) -> NameExtractor:
    return NameExtractor(ai_interface)

@pytest.fixture
def name_analyzer(ai_interface) -> NameAnalyzer:
    return NameAnalyzer(ai_interface, instruction_type="json", absolute_max_tokens=1000)

@pytest.fixture
def name_analyzer_markdown(ai_interface) -> NameAnalyzer:
    return NameAnalyzer(ai_interface, instruction_type="markdown", absolute_max_tokens=1000)

@pytest.fixture
def name_summarizer(ai_interface) -> NameSummarizer:
    return NameSummarizer(ai_interface)

@pytest.fixture
def mock_metadata() -> Mock:
    return Mock(narrator="John", custom_categories=["Location", "Item"], character_traits=["Motivation"])

@pytest.fixture
def mock_chapter() -> Mock:
    return Mock(text="This is a sample chapter text.", names={
        "Characters": ["Alice", "Bob"],
        "Settings": ["Forest", "Castle"],
        "Items": ["Sword", "Shield"]
    })
@pytest.fixture
def mock_lorebinder() -> dict[str, dict]:
    return {
        "Characters": {
            "Alice": {
                "chapter1": {
                    "appearance": "Long blonde hair, blue eyes",
                    "personality": "Brave and determined"
                },
                "chapter2": {
                    "appearance": "Wearing a red cloak",
                    "personality": "Kind to animals"
                },
                "chapter3": {
                    "appearance": "Mud-stained clothes, disheveled hair",
                    "personality": "Shows leadership in crisis"
                },
                "chapter4": {
                    "appearance": "Wearing a tattered royal gown",
                    "personality": "Struggles with newfound responsibility"
                }
            },
            "Bob": {
                "chapter1": {
                    "appearance": "Short, stocky build",
                    "personality": "Clever and quick-witted"
                },
                "chapter2": {
                    "appearance": "Wearing leather armor",
                    "personality": "Prone to sarcasm"
                },
                "chapter3": {
                    "appearance": "Sporting a new scar on his cheek",
                    "personality": "Loyal to his friends"
                },
                "chapter4": {
                    "appearance": "Injured arm in a sling",
                    "personality": "Questions his loyalty"
                }
            }
        },
        "Settings": {
            "Forest": {
                "chapter1": {
                    "appearance": "Dense, dark trees",
                    "atmosphere": "Eerie silence"
                },
                "chapter2": {
                    "appearance": "Misty clearings",
                    "atmosphere": "Sense of being watched"
                },
                "chapter3": {
                    "appearance": "Autumn leaves falling",
                    "atmosphere": "Peaceful at dawn"
                },
                "chapter4": {
                    "appearance": "Snow-covered ground",
                    "atmosphere": "Bitterly cold"
                }
            },
            "Castle": {
                "chapter1": {
                    "appearance": "Towering stone walls",
                    "atmosphere": "Oppressive and foreboding"
                },
                "chapter2": {
                    "appearance": "Flickering torchlight",
                    "atmosphere": "Echoing with whispers"
                },
                "chapter3": {
                    "appearance": "Crumbling battlements",
                    "atmosphere": "Tense anticipation of siege"
                }
            }
        }
    }

@pytest.fixture
def mock_lorebinder_with_summary() -> dict[str, dict[str, dict]]:
    return {
        "Characters": {
            "Alice": {
                "Summary": "Generated summary",
                "chapter1": {
                    "appearance": "Long blonde hair, blue eyes",
                    "personality": "Brave and determined"
                },
                "chapter2": {
                    "appearance": "Wearing a red cloak",
                    "personality": "Kind to animals"
                },
                "chapter3": {
                    "appearance": "Mud-stained clothes, disheveled hair",
                    "personality": "Shows leadership in crisis"
                },
                "chapter4": {
                    "appearance": "Wearing a tattered royal gown",
                    "personality": "Struggles with newfound responsibility"
                }
            },
            "Bob": {
                "Summary": "Generated summary",
                "chapter1": {
                    "appearance": "Short, stocky build",
                    "personality": "Clever and quick-witted"
                },
                "chapter2": {
                    "appearance": "Wearing leather armor",
                    "personality": "Prone to sarcasm"
                },
                "chapter3": {
                    "appearance": "Sporting a new scar on his cheek",
                    "personality": "Loyal to his friends"
                },
                "chapter4": {
                    "appearance": "Injured arm in a sling",
                    "personality": "Questions his loyalty"
                }
            }
        },
        "Settings": {
            "Forest": {
                "Summary": "Generated summary",
                "chapter1": {
                    "appearance": "Dense, dark trees",
                    "atmosphere": "Eerie silence"
                },
                "chapter2": {
                    "appearance": "Misty clearings",
                    "atmosphere": "Sense of being watched"
                },
                "chapter3": {
                    "appearance": "Autumn leaves falling",
                    "atmosphere": "Peaceful at dawn"
                },
                "chapter4": {
                    "appearance": "Snow-covered ground",
                    "atmosphere": "Bitterly cold"
                }
            },
            "Castle": {
                "chapter1": {
                    "appearance": "Towering stone walls",
                    "atmosphere": "Oppressive and foreboding"
                },
                "chapter2": {
                    "appearance": "Flickering torchlight",
                    "atmosphere": "Echoing with whispers"
                },
                "chapter3": {
                    "appearance": "Crumbling battlements",
                    "atmosphere": "Tense anticipation of siege"
                }
            }
        }
    }
