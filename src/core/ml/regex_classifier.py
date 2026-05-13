# src/core/ml/regex_classifier.py

import re
import phonenumbers

class RegexClassifier:
    """Rule-based classifier using regex patterns"""
    
    def __init__(self):
        self.patterns = {
            'phone': [
                r'\+91[\s\-]?\d{10}',  
                r'\d{10}',  
                r'\d{3}[\s\-]\d{3}[\s\-]\d{4}',  
                r'\(\d{3}\)\s?\d{3}[\s\-]\d{4}',
            ],
            'address': [
                r'\d+[\s,]*(main|street|road|st|rd|avenue|ave|lane|ln|nagar|colony|sector)\b',
                r'\b(house|h\.?no\.?|plot|building|flat|apartment)\s*\d+',
                r'\b\d{6}\b',  
                r'\b(near|opp|opposite|behind|infront|beside)\s+\w+',
                r'[A-Z][a-z]+\s+(road|street|nagar|colony|sector|area|block)',
                r'^[G/]?\d+[,\s]',  # Starts with "G/3, " or "21, "
                r'^no\.?\s*\d+',  # "No. 22" or "No 22"
                r'^shop\s*no',  # "Shop No"
                r'station\s*[rR]',  # "Station R" (abbreviation for Station Road)
            ],
            'name': [
                r'^[A-Z][a-z]+(\s+[A-Z][a-z]+)*$',  
                r"[A-Za-z\s]+('s|s')\s+(shop|store|restaurant|cafe|hotel)",
                r'\b(sri|shri|mr|mrs|dr|prof)\.\s+[A-Za-z\s]+',
                r'\b(general|grocery|medical|electronics|furniture|clothing|hardware|paint|bakery|sweet|diagnostic|lab|vet|pet|pharmacy|store|shop)\s+[A-Za-z]+',
                r'^[A-Z][a-z]+\s+(store|shop|pharmacy|medical|general|grocery)',
            ],
            'category': [
                r'\b(shop|store|restaurant|cafe|hotel|hospital|clinic|pharmacy|medical|general|grocery|electronics|furniture|clothing|hardware|paint|bakery|sweet|diagnostic|lab|vet|pet)\b',
                r'\b(dealer|supplier|distributor|manufacturer|service|repair|maintenance)\b',
                r'\b(ladies|mens|children|kids|baby)\s+(wear|clothing|garments)',
            ]
        }
        
        self.confidence_thresholds = {
            'phone': 0.95,
            'address': 0.75,  # Increased threshold for address
            'name': 0.65,  # Increased threshold for name
            'category': 0.8
        }

    def classify(self, text: str):
        if not text or len(text.strip()) < 2:
            return None, 0.0
        text = text.strip()
        scores = {'phone':0, 'address':0, 'name':0, 'category':0}

        if self._is_valid_phone(text):
            scores['phone'] = 0.98

        for label, patterns in self.patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                if matches:
                    coverage = sum(len(m) for m in matches)/len(text)
                    scores[label] = max(scores[label], min(coverage*2,0.95))

        best_label = max(scores, key=scores.get)
        best_score = scores[best_label]

        if best_score >= self.confidence_thresholds.get(best_label, 0.5):
            return best_label, best_score
        return None, best_score

    def _is_valid_phone(self, text: str) -> bool:
        try:
            cleaned = re.sub(r'[^\d\+]', '', text)
            if not cleaned:
                return False
            if not cleaned.startswith('+') and len(cleaned)==10:
                cleaned = '+91' + cleaned
            parsed = phonenumbers.parse(cleaned, 'IN')
            return phonenumbers.is_valid_number(parsed)
        except:
            return False
