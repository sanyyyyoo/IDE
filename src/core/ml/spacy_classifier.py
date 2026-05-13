# src/core/ml/spacy_classifier.py

import spacy
import logging

logger = logging.getLogger(__name__)

class SpacyNERClassifier:
    """Named Entity Recognition using spaCy"""
    
    def __init__(self, model_path="en_core_web_sm"):
        try:
            self.nlp = spacy.load(model_path)
        except OSError:
            logger.warning(f"spaCy model {model_path} not found, downloading...")
            spacy.cli.download(model_path)
            self.nlp = spacy.load(model_path)

        self.business_patterns = [
            {"label":"BUSINESS","pattern":[{"LOWER":{"IN":["shop","store","restaurant","cafe","hotel"]}}]},
            {"label":"LOCATION","pattern":[{"LOWER":"near"},{"ENT_TYPE":"GPE"}]},
        ]
        ruler = self.nlp.add_pipe("entity_ruler", before="ner")
        ruler.add_patterns(self.business_patterns)

    def classify(self, text: str):
        if not text:
            return None, 0.0
        doc = self.nlp(text)
        scores = {'phone':0,'address':0,'name':0,'category':0}
        for ent in doc.ents:
            if ent.label_=="PERSON":
                scores['name']+=0.7
            elif ent.label_ in ["GPE","LOC","FAC"]: 
                scores['address']+=0.6
            elif ent.label_ in ["ORG","BUSINESS"]:
                scores['name']+=0.5
                scores['category']+=0.3
        for token in doc:
            if token.like_num and len(token.text)>=8:
                scores['phone']+=0.3
            elif token.pos_=="PROPN" and not token.is_stop: 
                scores['name']+=0.2
        max_score = max(scores.values()) if any(scores.values()) else 0
        if max_score>0:
            for k in scores: 
                scores[k]=min(scores[k],1.0)
        best_label = max(scores, key=scores.get)
        best_score = scores[best_label]
        return (best_label,best_score) if best_score>0.4 else (None,best_score)
