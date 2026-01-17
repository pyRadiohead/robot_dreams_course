import pandas as pd
import joblib
import os
from sqlalchemy import create_engine


def run_inference(**kwargs):
    """
    Load trained model and run inference on iris_processed data.
    """
    # Paths
    models_dir = os.getenv('MODELS_DIR', '/opt/airflow/models')
    results_dir = os.getenv('RESULTS_DIR', '/opt/airflow/inference_results')

    model_path = os.path.join(models_dir, 'iris_classifier.joblib')
    features_path = os.path.join(models_dir, 'model_features.joblib')

    # Load model and features
    model = joblib.load(model_path)
    feature_names = joblib.load(features_path)

    # Connect to database
    pg_host = os.getenv('POSTGRES_ANALYTICS_HOST', 'postgres_analytics')
    pg_port = os.getenv('POSTGRES_PORT', '5432')
    pg_db = os.getenv('ANALYTICS_DB', 'analytics')
    pg_user = os.getenv('ETL_USER', 'etl_user')
    pg_password = os.getenv('ETL_PASSWORD', 'etl_password')

    conn_string = f"postgresql://{pg_user}:{pg_password}@{pg_host}:{pg_port}/{pg_db}"
    engine = create_engine(conn_string)

    # Load data
    df = pd.read_sql("SELECT * FROM homework.iris_processed", engine)

    # Prepare features
    X = df[feature_names]

    # Run predictions
    predictions = model.predict(X)
    probabilities = model.predict_proba(X)

    # Map predictions to species names
    species_map = {0: 'setosa', 1: 'versicolor', 2: 'virginica'}
    predicted_species = [species_map.get(p, 'unknown') for p in predictions]

    # Create results DataFrame
    results_df = pd.DataFrame({
        'prediction': predictions,
        'predicted_species': predicted_species,
        'probability_setosa': probabilities[:, 0],
        'probability_versicolor': probabilities[:, 1],
        'probability_virginica': probabilities[:, 2],
    })

    # Summary statistics
    summary = results_df['predicted_species'].value_counts().to_dict()

    # Return for XCom
    return {
        'total_predictions': len(predictions),
        'predictions_summary': summary,
        'sample_predictions': results_df.head(5).to_dict('records')
    }


if __name__ == "__main__":
    result = run_inference()
    print(result)