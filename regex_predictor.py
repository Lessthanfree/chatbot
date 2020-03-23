import re

class Regex_Predictor:
    def predict(self, raw_msg):
        pred_dict = {}
        intent = self.get_intent(raw_msg)
        pred_dict = {
            "prediction":intent,
            "breakdown":"breakdown text",
            "numbers":[]
            }
        return pred_dict
    
    def get_intent(self, msg):
        intent = "inform"
        return intent