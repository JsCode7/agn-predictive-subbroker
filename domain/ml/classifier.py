from sklearn.linear_model import SGDClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, roc_auc_score
import numpy as np
import asyncio

class AGNClassifier:
    def __init__(self):
        self.model = SGDClassifier(loss='log_loss', learning_rate='optimal')
        self.is_initialized = False
        self.y_true = []
        self.y_pred = []
        self.y_prob = []
        self.lock = asyncio.Lock()

    def _extract_features(self, tau, sigma, n_points):
        ratio = tau / sigma if sigma > 0 else 0
        return np.array([[tau, sigma, ratio, n_points]])

    async def partial_fit(self, tau, sigma, n_points, true_label):
        features = self._extract_features(tau, sigma, n_points)
        async with self.lock:
            if not self.is_initialized:
                self.model.partial_fit(features, [true_label], classes=np.array([0, 1]))
                self.is_initialized = True
            else:
                self.model.partial_fit(features, [true_label])

    async def predict_and_score(self, tau, sigma, n_points, true_label):
        features = self._extract_features(tau, sigma, n_points)
        
        async with self.lock:
            if not self.is_initialized:
                return 1 if tau > 5.0 else 0, 1.0 if tau > 5.0 else 0.0, {}

            pred = self.model.predict(features)[0]
            prob = self.model.predict_proba(features)[0][1]
            
            self.y_true.append(true_label)
            self.y_pred.append(pred)
            self.y_prob.append(prob)
            
            if len(self.y_true) > 1000:
                self.y_true.pop(0)
                self.y_pred.pop(0)
                self.y_prob.pop(0)
                
            metrics = self._calc_metrics()
            return pred, prob, metrics

    def _calc_metrics(self):
        if len(set(self.y_true)) < 2:
            return {"accuracy": 0.0, "precision": 0.0, "recall": 0.0, "roc_auc": 0.0}
        try:
            return {
                "accuracy": accuracy_score(self.y_true, self.y_pred),
                "precision": precision_score(self.y_true, self.y_pred, zero_division=0),
                "recall": recall_score(self.y_true, self.y_pred, zero_division=0),
                "roc_auc": roc_auc_score(self.y_true, self.y_prob)
            }
        except:
            return {}

classifier = AGNClassifier()
