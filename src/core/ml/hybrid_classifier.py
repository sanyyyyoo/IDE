# src/core/ml/hybrid_classifier.py

import logging
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional
from .regex_classifier import RegexClassifier
from .spacy_classifier import SpacyNERClassifier
from .distilbert_classifier import DistilBERTClassifier
from .utils import normalize_phone, normalize_address, normalize_name, normalize_category

logger = logging.getLogger(__name__)

@dataclass
class ClassificationResult:
    text:str
    predicted_label:str
    confidence:float
    method:str
    all_predictions:Dict[str,float]
    needs_review:bool=False

class HybridClassifier:
    def __init__(self, distilbert_model_path:str):
        self.regex = RegexClassifier()
        self.spacy = SpacyNERClassifier()
        self.bert = DistilBERTClassifier(distilbert_model_path)
        print(f"[MODEL] ✅ Loaded DistilBERT model successfully from: {distilbert_model_path}")
        self.weights = {"regex":0.4,"spacy":0.2,"distilbert":0.4}
        self.high_threshold = 0.9
        self.medium_threshold = 0.7


    def classify(self,text:str)->ClassificationResult:
        text = text.strip() if text else ""
        if not text:
            return ClassificationResult(text=text,predicted_label="name",confidence=0.0,method="default",all_predictions={},needs_review=True)
        regex_pred, regex_conf = self.regex.classify(text)
        spacy_pred, spacy_conf = self.spacy.classify(text)
        bert_pred, bert_conf, bert_probs = self.bert.classify(text)
        all_preds={"regex":{regex_pred:regex_conf} if regex_pred else {},
                   "spacy":{spacy_pred:spacy_conf} if spacy_pred else {},
                   "distilbert":bert_probs}
        final_label, confidence, method=self._ensemble_decision(regex_pred,regex_conf,spacy_pred,spacy_conf,bert_pred,bert_conf,bert_probs)
        needs_review = confidence<self.medium_threshold or self._disagree(regex_pred,spacy_pred,bert_pred)
        return ClassificationResult(text=text,predicted_label=final_label,confidence=confidence,method=method,all_predictions=all_preds,needs_review=needs_review)

    def classify_batch(self,texts:List[str])->List[ClassificationResult]:
        bert_results=self.bert.classify_batch(texts)
        results=[]
        for i,text in enumerate(texts):
            regex_pred, regex_conf = self.regex.classify(text)
            spacy_pred, spacy_conf = self.spacy.classify(text)
            bert_pred, bert_conf, bert_probs = bert_results[i]
            final_label, confidence, method=self._ensemble_decision(regex_pred,regex_conf,spacy_pred,spacy_conf,bert_pred,bert_conf,bert_probs)
            needs_review = confidence<self.medium_threshold or self._disagree(regex_pred,spacy_pred,bert_pred)
            all_preds={"regex":{regex_pred:regex_conf} if regex_pred else {},
                       "spacy":{spacy_pred:spacy_conf} if spacy_pred else {},
                       "distilbert":bert_probs}
            results.append(ClassificationResult(text=text,predicted_label=final_label,confidence=confidence,method=method,all_predictions=all_preds,needs_review=needs_review))
        return results

    def _ensemble_decision(self,regex_pred,regex_conf,spacy_pred,spacy_conf,bert_pred,bert_conf,bert_probs)->Tuple[str,float,str]:
        if regex_pred and regex_conf>=self.high_threshold: 
            return regex_pred,regex_conf,"regex"
        if bert_conf>=self.high_threshold: 
            return bert_pred,bert_conf,"distilbert"
        scores={}
        if regex_pred: 
            scores[regex_pred]=regex_conf*self.weights["regex"]
        if spacy_pred: 
            scores[spacy_pred]=scores.get(spacy_pred,0)+spacy_conf*self.weights["spacy"]
        for label,prob in bert_probs.items(): 
            scores[label]=scores.get(label,0)+prob*self.weights["distilbert"]
        if scores:
            best_label=max(scores,key=scores.get)
            return best_label,scores[best_label],"ensemble"
        return bert_pred,bert_conf,"distilbert"

    @staticmethod
    def _disagree(*preds)->bool:
        preds=[p for p in preds if p]
        return len(set(preds))>1 if len(preds)>1 else False

class GoogleMapsDataProcessor:
    """Process scraped Google Maps data with HybridClassifier."""
    def __init__(self, distilbert_model_path: str):
        import os

        # Ensure absolute path (for Windows + Linux)
        distilbert_model_path = os.path.abspath(distilbert_model_path)

        # Convert Windows backslashes to forward slashes so transformers treats it as local
        distilbert_model_path = distilbert_model_path.replace("\\", "/")

        print(f"[MODEL] 🔍 Initializing GoogleMapsDataProcessor with model path:\n    {distilbert_model_path}")

        self.classifier = HybridClassifier(distilbert_model_path)


    def process_scraped_data(self,scraped_data:List[Dict])->List[Dict]:
        import re
        processed=[]
        for item in scraped_data:
            texts=[]
            field_map={}
            original_values={}
            
            # Preserve category - don't classify it, use the search category directly
            search_category = item.get('category', '')
            
            # Collect texts for classification (exclude category - we'll use search category)
            for field in ['name','address','phone']:
                if field in item and item[field]:
                    texts.append(item[field])
                    field_map[len(texts)-1]=field
                    original_values[field]=item[field]
            
            # Classify only name, address, phone (not category)
            results=self.classifier.classify_batch(texts)
            
            # Smart classification: trust original field assignments, only swap if clearly wrong
            classified={'name':'','address':'','phone':'','category':search_category}
            conf_scores={}
            needs_review=False
            
            # Helper function to detect if text looks like address
            def looks_like_address(text):
                if not text:
                    return False
                text_lower = text.lower()
                text_stripped = text.strip()
                
                # Check for common address patterns
                address_patterns = [
                    r'\d+[\s,]*(main|street|road|st|rd|avenue|ave|lane|ln|nagar|colony|sector|area|block)',
                    r'\b(house|h\.?no\.?|plot|building|flat|apartment|shop\s*no)',
                    r'\b(near|opp|opposite|behind|infront|beside)',
                    r'^[G/]?\d+[,\s]',  # Starts with number like "G/3, " or "21, "
                    r'^no\.?\s*\d+',  # Starts with "No. 22" or "No 22"
                    r'^shop\s*no',  # Starts with "Shop No" or "Shop no"
                    r'^[G/]\d+',  # Starts with "G/3" or "/21"
                    r'^\d+[,\s]',  # Starts with number and comma/space
                    r'station\s*[rR]',  # "Station R" (likely "Station Road")
                    r'^[a-z]+\s*[rR]$',  # Single letter at end like "R" (likely abbreviation)
                ]
                
                # Check if it matches address patterns
                if any(re.search(pattern, text_lower) for pattern in address_patterns):
                    return True
                
                # Check if it's very short and looks like an address fragment
                if len(text_stripped) < 10 and re.match(r'^[G/]?\d+', text_stripped):
                    return True
                
                # Check if it's just "Shop No" or similar
                if text_lower in ['shop no', 'shop no.', 'shop no,', 'shop num', 'shop number']:
                    return True
                
                return False
            
            # Helper function to detect if text looks like business name
            def looks_like_name(text):
                if not text:
                    return False
                text_lower = text.lower()
                text_stripped = text.strip()
                
                # Names should NOT contain address patterns
                if looks_like_address(text):
                    return False
                
                # Exclude very short fragments that look like addresses
                if len(text_stripped) < 5:
                    return False
                
                # Exclude patterns that are clearly not names
                if text_lower in ['shop no', 'shop no.', 'shop no,', 'shop num', 'shop number']:
                    return False
                
                # Names typically have business keywords or proper nouns
                name_patterns = [
                    r'\b(shop|store|restaurant|cafe|hotel|pharmacy|medical|general|grocery|gener|gene|gen)',
                    r'^[A-Z][a-z]+(\s+[A-Z][a-z]+)*$',  # Proper noun pattern
                    r'^[A-Z][a-z]+',  # Starts with capital letter (proper noun)
                ]
                
                # Check if it looks like a name (has business keywords or proper noun structure)
                has_name_pattern = any(re.search(pattern, text) for pattern in name_patterns)
                
                # If it doesn't look like an address and has name patterns, it's likely a name
                return has_name_pattern and not looks_like_address(text)
            
            for i,res in enumerate(results):
                orig_field=field_map[i]
                pred=res.predicted_label
                text=res.text
                confidence=res.confidence
                
                # Skip if prediction is 'category'
                if pred == 'category':
                    if not classified[orig_field] or conf_scores.get(orig_field,0)<confidence:
                        classified[orig_field]=text
                        conf_scores[orig_field]=confidence
                
                # If original field matches prediction, trust it
                elif orig_field==pred:
                    if not classified[pred] or conf_scores.get(pred,0)<confidence:
                        classified[pred]=text
                        conf_scores[pred]=confidence
                
                # If prediction differs, only swap if original is clearly wrong AND model is confident
                else:
                    # Check if original assignment seems wrong
                    orig_wrong = False
                    if orig_field == 'name' and looks_like_address(text):
                        orig_wrong = True
                    elif orig_field == 'address' and looks_like_name(text) and not looks_like_address(text):
                        orig_wrong = True
                    
                    # Only swap if original is wrong AND model is very confident (>=0.85)
                    if orig_wrong and confidence >= 0.85:
                        # Use model's prediction
                        if not classified[pred] or conf_scores.get(pred,0)<confidence:
                            classified[pred]=text
                            conf_scores[pred]=confidence
                    else:
                        # Keep original field assignment
                        if not classified[orig_field] or conf_scores.get(orig_field,0)<confidence:
                            classified[orig_field]=text
                            conf_scores[orig_field]=confidence
                
                if res.needs_review: 
                    needs_review=True
            
            # Post-processing: detect and fix obvious swaps
            name = classified.get('name', '').strip()
            address = classified.get('address', '').strip()
            
            # If name looks like address and address looks like name, swap them
            if name and address:
                if looks_like_address(name) and looks_like_name(address):
                    classified['name'], classified['address'] = address, name
                    logger.info(f"🔄 Post-classification swap: name='{address}' address='{name}'")
            
            # Ensure we have values for all fields (fallback to original if classified is empty)
            for field in ['name','address','phone']:
                if not classified[field] and field in original_values:
                    classified[field]=original_values[field]
            
            # Always use the search category, never classify it
            classified['category'] = search_category
            
            processed.append({'raw_data':item,'classified_data':classified,'confidence_scores':conf_scores,'needs_review':needs_review})
        return processed
