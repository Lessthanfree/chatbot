import re

class Regex_Predictor:
    def predict(self, raw_msg):
        pred_dict = {}
        intent = self.get_intent(raw_msg)
        pred_dict["prediction"] = intent
        return intent
    
    def get_intent(self, msg):
        intent = "greet"
        return intent