from __future__ import annotations
from typing import Any, Dict, Text, List
import numpy as np
import torch
from rasa.engine.graph import GraphComponent, ExecutionContext
from rasa.engine.storage.resource import Resource
from rasa.engine.storage.storage import ModelStorage
from rasa.shared.nlu.training_data.message import Message
from rasa.shared.nlu.training_data.training_data import TrainingData
from rasa.engine.recipes.default_recipe import DefaultV1Recipe
from transformers import LongformerTokenizer, LongformerModel

@DefaultV1Recipe.register(
    component_types=["CustomLongformerFeaturizer"], is_trainable=True
)
class CustomLongformerFeaturizer(GraphComponent):
    """Featurizer Longformer for long sequence processing to accomodate our >512 token sequences"""

    def __init__(self, config: Dict[Text, Any]) -> None:
        self.model_name = config.get("model_name", "allenai/longformer-base-4096")
        self.max_length = config.get("max_length", 1024) # Sequence length
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

        # Load Longformer model and tokenizer
        self.tokenizer = LongformerTokenizer.from_pretrained(self.model_name)
        self.model = LongformerModel.from_pretrained(self.model_name).to(self.device)

    def train(self, training_data: TrainingData) -> TrainingData:
        for message in training_data.training_examples:
            self._process_message(message)
        return training_data

    def process(self, messages: List[Message]) -> List[Message]:
        """Process incoming messages and add features"""
        for message in messages:
            self._process_message(message)
        return messages

    def _process_message(self, message: Message) -> None:
            
        if message is None:
            print("Message is None!")
            return

        text = message.get("text")
        if not text:
            print("Text is missing in message!")
            return

        #print("Processing message with text:", text)
        
        """Tokenize and extract Longformer features for a single message."""
        text = message.get("text")

        # Tokenize and encode the message
        inputs = self.tokenizer(
            text,
            return_tensors="pt",
            max_length=self.max_length,
            padding="max_length",
            truncation=True
        ).to(self.device)

        # Forward pass through Longformer
        with torch.no_grad():
            outputs = self.model(**inputs)
        
        # Extract and average the hidden states
        features = outputs.last_hidden_state.mean(dim=1).squeeze().cpu().numpy()
        
        print(f"Extracted features: {features[:10]}...")

        # Store the features in the message for downstream use
        message.set("custom_features", np.array(features))

    def persist(self, storage: ModelStorage, resource: Resource) -> None:
        """Persist the component."""
        pass

    @classmethod
    def load(
        cls,
        config: Dict[Text, Any],
        model_storage: ModelStorage,
        resource: Resource,
        execution_context: ExecutionContext,
    ) -> GraphComponent:
        return cls(config)
    
    @classmethod
    def create(
        cls,
        config: Dict[Text, Any],
        model_storage: ModelStorage,
        resource: Resource,
        execution_context: ExecutionContext,
    ) -> GraphComponent:
        return cls(config)