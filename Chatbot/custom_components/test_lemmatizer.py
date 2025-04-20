import pytest
from rasa.shared.nlu.training_data.message import Message
from lemmatization import LemmatizerComponent

class DummyStorage:
    """Dummy storage to satisfy ModelStorage requirements."""
    pass

class DummyResource:
    """Dummy resource to satisfy Resource requirements."""
    pass

class DummyExecutionContext:
    """Dummy execution context to satisfy ExecutionContext requirements."""
    pass

@pytest.fixture
def lemmatizer():
    """Fixture to create the LemmatizerComponent."""
    # Normally these would be real Rasa objects but they aren't needed for this test
    return LemmatizerComponent.create({}, DummyStorage(), DummyResource(), DummyExecutionContext())

def test_lemmatizer_basic(lemmatizer):
    """Test basic lemmatization."""
    # Arrange
    text = "The cats are running quickly."
    message = Message({ "text": text })

    # Act
    lemmatizer.process([message])

    # Assert
    expected_lemmas = "the cat be run quickly ."
    assert message.get("text") == expected_lemmas

def test_lemmatizer_empty_message(lemmatizer):
    """Test with an empty message."""
    # Arrange
    text = ""
    message = Message({ "text": text })

    # Act
    lemmatizer.process([message])

    # Assert
    assert message.get("text") == ""

def test_lemmatizer_preserve_case(lemmatizer):
    """Test if the component lowercases (spaCy lemmatizer lowercases by default)."""
    text = "running cats are funny"
    message = Message({ "text": text })
    lemmatizer.process([message])
    print(message.get("text"))

    expected_lemmas = "run cat be funny"
    assert message.get("text") == expected_lemmas
