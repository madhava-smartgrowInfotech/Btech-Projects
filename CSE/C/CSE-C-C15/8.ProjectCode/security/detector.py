"""SentinelFlow detector: thin wrapper from features -> model prediction."""

from ml import model_loader


def detect(features: dict) -> dict:
    if not model_loader.is_trained():
        raise FileNotFoundError("SentinelFlow model is not trained yet. Run: python ml/train_model.py")
    return model_loader.predict_traffic(features)
