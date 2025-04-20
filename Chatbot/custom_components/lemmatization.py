from typing import Dict, Text, Any, List

from rasa.engine.graph import GraphComponent, ExecutionContext
from rasa.engine.recipes.default_recipe import DefaultV1Recipe
from rasa.engine.storage.resource import Resource
from rasa.engine.storage.storage import ModelStorage
from rasa.shared.nlu.training_data.message import Message
from rasa.shared.nlu.training_data.training_data import TrainingData
from rasa.shared.nlu.constants import TEXT
import spacy

@DefaultV1Recipe.register(
    component_types=[GraphComponent], is_trainable=True
)
class LemmatizerComponent(GraphComponent):
    @staticmethod
    def create(config, model_storage, resource, execution_context: ExecutionContext):
        return LemmatizerComponent()
    
    @classmethod
    def create(
        cls,
        config: Dict[str, Any],
        model_storage: ModelStorage,
        resource: Resource,
        execution_context: ExecutionContext,
    ) -> GraphComponent:
        nlp = spacy.load("en_core_web_sm")
        return cls(nlp)
    
    def __init__(self, nlp_model:Any):
        # Initialize our nlp model
        self.nlp = nlp_model
    
    def process(self, messages: List[Message]) -> List[Message]:
        # Process the incoming data and lemmatize it
        for message in messages:
            text = message.get(TEXT)
            if text:
                doc = self.nlp(text)
                lemmatized_text = " ".join([token.lemma_ for token in doc])
                message.set(TEXT, lemmatized_text)
        return messages
    
    def train(
        self,
        training_data: TrainingData,
    ) -> List[Message]:
        messages = training_data.training_examples
        return self.process(messages)
