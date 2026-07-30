"""
Train ML models for ETH price prediction
"""
import pandas as pd
import numpy as np
import joblib
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns
import sys
sys.path.append(str(Path(__file__).parent.parent))

from server.notebooks.ml_trading.data_prep import load_data_from_sqlite, prepare_ml_data
from server.ml_trading.config import MODEL_DIR, FEATURES

class MLTradingModel:
    def __init__(self):
        self.models = {}
        self.best_model = None
        self.best_model_name = None
        self.best_accuracy = 0
        self.model_path = MODEL_DIR
    
    def train_models(self, X_train, y_train):
        print("\nTraining ML models...")
        print("-" * 40)
        
        rf = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42, n_jobs=-1)
        rf.fit(X_train, y_train)
        self.models['RandomForest'] = rf
        print("Random Forest trained")
        
        gb = GradientBoostingClassifier(n_estimators=100, learning_rate=0.1, max_depth=5, random_state=42)
        gb.fit(X_train, y_train)
        self.models['GradientBoosting'] = gb
        print("Gradient Boosting trained")
        
        try:
            import xgboost as xgb
            xgb_model = xgb.XGBClassifier(n_estimators=100, max_depth=6, learning_rate=0.1, random_state=42)
            xgb_model.fit(X_train, y_train)
            self.models['XGBoost'] = xgb_model
            print("XGBoost trained")
        except:
            print("XGBoost not available")
        
        try:
            import lightgbm as lgb
            lgb_model = lgb.LGBMClassifier(n_estimators=100, max_depth=6, learning_rate=0.1, random_state=42, verbose=-1)
            lgb_model.fit(X_train, y_train)
            self.models['LightGBM'] = lgb_model
            print("LightGBM trained")
        except:
            print("LightGBM not available")
        
        lr = LogisticRegression(max_iter=1000, random_state=42)
        lr.fit(X_train, y_train)
        self.models['LogisticRegression'] = lr
        print("Logistic Regression trained")
    
    def evaluate_models(self, X_test, y_test):
        print("\nModel Evaluation:")
        print("-" * 40)
        results = {}
        for name, model in self.models.items():
            y_pred = model.predict(X_test)
            accuracy = accuracy_score(y_test, y_pred)
            results[name] = accuracy
            print(f"   {name}: {accuracy:.4f}")
        best_name = max(results, key=results.get)
        self.best_model = self.models[best_name]
        self.best_model_name = best_name
        self.best_accuracy = results[best_name]
        print(f"\nBest: {best_name} ({results[best_name]:.4f})")
        return results
    
    def save_best_model(self):
        if self.best_model:
            model_file = self.model_path / f"{self.best_model_name}_model.pkl"
            joblib.dump(self.best_model, model_file)
            print(f"Model saved to: {model_file}")
    
    def plot_confusion_matrix(self, X_test, y_test):
        if self.best_model is None:
            return
        y_pred = self.best_model.predict(X_test)
        plt.figure(figsize=(8, 6))
        cm = confusion_matrix(y_test, y_pred)
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues')
        plt.title(f'Confusion Matrix - {self.best_model_name}')
        plt.xlabel('Predicted')
        plt.ylabel('Actual')
        plt.tight_layout()
        plt.savefig(self.model_path / 'confusion_matrix.png')
        plt.show()

def main():
    print("=" * 60)
    print("Training ML Models")
    print("=" * 60)
    df = load_data_from_sqlite()
    if df is None:
        return
    X_train, X_test, y_train, y_test, _ = prepare_ml_data(df)
    if X_train is None:
        return
    trainer = MLTradingModel()
    trainer.train_models(X_train, y_train)
    trainer.evaluate_models(X_test, y_test)
    trainer.save_best_model()
    trainer.plot_confusion_matrix(X_test, y_test)
    print("\nTraining complete!")

if __name__ == "__main__":
    main()
