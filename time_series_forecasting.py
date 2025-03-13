#!/usr/bin/env python3
"""
Time Series Forecasting Module

This module implements time series forecasting using LSTM/GRU neural networks
to predict future price movements.
"""

import os
import sys
import logging
import numpy as np
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
import tensorflow as tf
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import Dense, LSTM, GRU, Dropout, BatchNormalization
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint
from tensorflow.keras.optimizers import Adam
from sklearn.preprocessing import MinMaxScaler
import joblib

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("time_series_forecasting.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Create directories if they don't exist
os.makedirs('models/forecasting', exist_ok=True)
os.makedirs('results/forecasting', exist_ok=True)

class TimeSeriesForecaster:
    """
    Time series forecaster using LSTM/GRU neural networks to predict future price movements.
    """
    
    def __init__(self, model_type='lstm', sequence_length=60, forecast_horizon=5):
        """
        Initialize the time series forecaster
        
        Args:
            model_type: Type of model to use ('lstm' or 'gru')
            sequence_length: Number of time steps to use for prediction
            forecast_horizon: Number of time steps to forecast
        """
        self.model_type = model_type
        self.sequence_length = sequence_length
        self.forecast_horizon = forecast_horizon
        self.model = None
        self.scaler = MinMaxScaler(feature_range=(0, 1))
        self.model_path = f'models/forecasting/{model_type}_model.h5'
        self.scaler_path = f'models/forecasting/{model_type}_scaler.joblib'
        
        # Load model if it exists
        self._load_model()
        
        logger.info(f"Initialized {model_type.upper()} forecaster with sequence length {sequence_length} and forecast horizon {forecast_horizon}")
    
    def _load_model(self):
        """Load pre-trained model if it exists"""
        if os.path.exists(self.model_path):
            try:
                self.model = load_model(self.model_path)
                logger.info(f"Loaded {self.model_type.upper()} model from {self.model_path}")
                
                # Load scaler
                if os.path.exists(self.scaler_path):
                    self.scaler = joblib.load(self.scaler_path)
                    logger.info(f"Loaded scaler from {self.scaler_path}")
            except Exception as e:
                logger.error(f"Error loading model: {e}")
                self.model = None
    
    def _create_model(self, input_shape):
        """
        Create a new LSTM or GRU model
        
        Args:
            input_shape: Shape of input data (sequence_length, n_features)
            
        Returns:
            Compiled Keras model
        """
        model = Sequential()
        
        if self.model_type == 'lstm':
            # LSTM model
            model.add(LSTM(units=50, return_sequences=True, input_shape=input_shape))
            model.add(Dropout(0.2))
            model.add(BatchNormalization())
            
            model.add(LSTM(units=50, return_sequences=False))
            model.add(Dropout(0.2))
            model.add(BatchNormalization())
            
            model.add(Dense(units=25, activation='relu'))
            model.add(Dense(units=self.forecast_horizon))
        else:
            # GRU model
            model.add(GRU(units=50, return_sequences=True, input_shape=input_shape))
            model.add(Dropout(0.2))
            model.add(BatchNormalization())
            
            model.add(GRU(units=50, return_sequences=False))
            model.add(Dropout(0.2))
            model.add(BatchNormalization())
            
            model.add(Dense(units=25, activation='relu'))
            model.add(Dense(units=self.forecast_horizon))
        
        # Compile model
        model.compile(optimizer=Adam(learning_rate=0.001), loss='mean_squared_error')
        
        logger.info(f"Created {self.model_type.upper()} model with input shape {input_shape}")
        model.summary(print_fn=logger.info)
        
        return model
    
    def _prepare_data(self, data, target_column='close'):
        """
        Prepare data for time series forecasting
        
        Args:
            data: DataFrame with time series data
            target_column: Column to forecast
            
        Returns:
            Tuple of (X, y, scaler)
        """
        # Extract target column
        dataset = data[target_column].values.reshape(-1, 1)
        
        # Scale data
        scaled_data = self.scaler.fit_transform(dataset)
        
        # Create sequences
        X = []
        y = []
        
        for i in range(len(scaled_data) - self.sequence_length - self.forecast_horizon + 1):
            X.append(scaled_data[i:i+self.sequence_length])
            y.append(scaled_data[i+self.sequence_length:i+self.sequence_length+self.forecast_horizon, 0])
        
        # Convert to numpy arrays
        X = np.array(X)
        y = np.array(y)
        
        logger.info(f"Prepared {len(X)} sequences with shape {X.shape}")
        
        return X, y
    
    def _prepare_multivariate_data(self, data, target_column='close', feature_columns=None):
        """
        Prepare multivariate data for time series forecasting
        
        Args:
            data: DataFrame with time series data
            target_column: Column to forecast
            feature_columns: List of columns to use as features
            
        Returns:
            Tuple of (X, y, scaler)
        """
        # Use all columns if feature_columns is None
        if feature_columns is None:
            feature_columns = data.columns.tolist()
            
            # Remove target column if it's in feature_columns
            if target_column in feature_columns:
                feature_columns.remove(target_column)
        
        # Add target column to feature columns
        if target_column not in feature_columns:
            feature_columns = [target_column] + feature_columns
        
        # Extract features
        dataset = data[feature_columns].values
        
        # Scale data
        scaled_data = self.scaler.fit_transform(dataset)
        
        # Get index of target column
        target_idx = feature_columns.index(target_column)
        
        # Create sequences
        X = []
        y = []
        
        for i in range(len(scaled_data) - self.sequence_length - self.forecast_horizon + 1):
            X.append(scaled_data[i:i+self.sequence_length])
            y.append(scaled_data[i+self.sequence_length:i+self.sequence_length+self.forecast_horizon, target_idx])
        
        # Convert to numpy arrays
        X = np.array(X)
        y = np.array(y)
        
        logger.info(f"Prepared {len(X)} multivariate sequences with shape {X.shape}")
        
        return X, y, feature_columns
    
    def train(self, data, target_column='close', feature_columns=None, epochs=100, batch_size=32, validation_split=0.2):
        """
        Train the time series forecasting model
        
        Args:
            data: DataFrame with time series data
            target_column: Column to forecast
            feature_columns: List of columns to use as features
            epochs: Number of training epochs
            batch_size: Batch size for training
            validation_split: Fraction of data to use for validation
            
        Returns:
            Training history
        """
        try:
            logger.info(f"Training {self.model_type.upper()} model...")
            
            # Prepare data
            if feature_columns is None:
                # Univariate forecasting
                X, y = self._prepare_data(data, target_column)
                n_features = 1
            else:
                # Multivariate forecasting
                X, y, feature_columns = self._prepare_multivariate_data(data, target_column, feature_columns)
                n_features = len(feature_columns)
            
            # Create model if it doesn't exist
            if self.model is None:
                self.model = self._create_model((self.sequence_length, n_features))
            
            # Define callbacks
            callbacks = [
                EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True),
                ModelCheckpoint(self.model_path, monitor='val_loss', save_best_only=True)
            ]
            
            # Train model
            history = self.model.fit(
                X, y,
                epochs=epochs,
                batch_size=batch_size,
                validation_split=validation_split,
                callbacks=callbacks,
                verbose=1
            )
            
            # Save scaler
            joblib.dump(self.scaler, self.scaler_path)
            
            # Save feature columns if multivariate
            if feature_columns is not None:
                with open(f'models/forecasting/{self.model_type}_features.txt', 'w') as f:
                    f.write('\n'.join(feature_columns))
            
            # Plot training history
            plt.figure(figsize=(10, 6))
            plt.plot(history.history['loss'], label='Training Loss')
            plt.plot(history.history['val_loss'], label='Validation Loss')
            plt.title(f'{self.model_type.upper()} Model Training History')
            plt.xlabel('Epoch')
            plt.ylabel('Loss')
            plt.legend()
            plt.savefig(f'results/forecasting/{self.model_type}_training_history.png')
            
            # Save training results
            results = {
                'model_type': self.model_type,
                'sequence_length': self.sequence_length,
                'forecast_horizon': self.forecast_horizon,
                'n_features': n_features,
                'feature_columns': feature_columns if feature_columns is not None else [target_column],
                'target_column': target_column,
                'final_loss': float(history.history['loss'][-1]),
                'final_val_loss': float(history.history['val_loss'][-1]),
                'training_date': datetime.now().isoformat()
            }
            
            import json
            with open(f'results/forecasting/{self.model_type}_training_results.json', 'w') as f:
                json.dump(results, f, indent=4, default=str)
            
            logger.info(f"{self.model_type.upper()} model training completed")
            
            return history
            
        except Exception as e:
            logger.error(f"Error training {self.model_type.upper()} model: {e}")
            return None
    
    def predict(self, data, target_column='close', feature_columns=None):
        """
        Generate forecasts using the trained model
        
        Args:
            data: DataFrame with time series data
            target_column: Column to forecast
            feature_columns: List of columns to use as features
            
        Returns:
            DataFrame with forecasts
        """
        try:
            if self.model is None:
                logger.error("No trained model available")
                return None
            
            # Prepare data
            if feature_columns is None:
                # Univariate forecasting
                dataset = data[target_column].values.reshape(-1, 1)
                scaled_data = self.scaler.transform(dataset)
                
                # Get the last sequence
                last_sequence = scaled_data[-self.sequence_length:].reshape(1, self.sequence_length, 1)
            else:
                # Multivariate forecasting
                # Load feature columns if available
                feature_file = f'models/forecasting/{self.model_type}_features.txt'
                if os.path.exists(feature_file):
                    with open(feature_file, 'r') as f:
                        saved_features = f.read().splitlines()
                    
                    # Check if feature_columns match saved_features
                    if set(feature_columns) != set(saved_features):
                        logger.warning(f"Feature columns don't match saved features. Using saved features: {saved_features}")
                        feature_columns = saved_features
                
                # Extract features
                dataset = data[feature_columns].values
                scaled_data = self.scaler.transform(dataset)
                
                # Get the last sequence
                last_sequence = scaled_data[-self.sequence_length:].reshape(1, self.sequence_length, len(feature_columns))
            
            # Generate forecast
            forecast_scaled = self.model.predict(last_sequence)
            
            # Reshape forecast for inverse transform
            if feature_columns is None:
                # Univariate forecasting
                forecast_scaled_reshaped = forecast_scaled.reshape(self.forecast_horizon, 1)
                forecast = self.scaler.inverse_transform(forecast_scaled_reshaped)
                forecast = forecast.flatten()
            else:
                # Multivariate forecasting
                # Create a dummy array with zeros for all features
                dummy = np.zeros((self.forecast_horizon, len(feature_columns)))
                
                # Get index of target column
                target_idx = feature_columns.index(target_column)
                
                # Set the target column values
                dummy[:, target_idx] = forecast_scaled.flatten()
                
                # Inverse transform
                forecast_full = self.scaler.inverse_transform(dummy)
                
                # Extract target column
                forecast = forecast_full[:, target_idx]
            
            # Create forecast DataFrame
            dates = pd.date_range(start=data.index[-1], periods=self.forecast_horizon+1, freq='D')[1:]
            forecast_df = pd.DataFrame({
                'date': dates,
                'forecast': forecast
            })
            forecast_df.set_index('date', inplace=True)
            
            logger.info(f"Generated {self.forecast_horizon} step forecast")
            
            return forecast_df
            
        except Exception as e:
            logger.error(f"Error generating forecast: {e}")
            return None
    
    def evaluate(self, data, target_column='close', feature_columns=None, test_size=0.2):
        """
        Evaluate the model on test data
        
        Args:
            data: DataFrame with time series data
            target_column: Column to forecast
            feature_columns: List of columns to use as features
            test_size: Fraction of data to use for testing
            
        Returns:
            Dictionary with evaluation metrics
        """
        try:
            if self.model is None:
                logger.error("No trained model available")
                return None
            
            # Split data into train and test
            train_size = int(len(data) * (1 - test_size))
            train_data = data.iloc[:train_size]
            test_data = data.iloc[train_size-self.sequence_length:]
            
            # Prepare data
            if feature_columns is None:
                # Univariate forecasting
                X_train, y_train = self._prepare_data(train_data, target_column)
                X_test, y_test = self._prepare_data(test_data, target_column)
            else:
                # Multivariate forecasting
                X_train, y_train, _ = self._prepare_multivariate_data(train_data, target_column, feature_columns)
                X_test, y_test, _ = self._prepare_multivariate_data(test_data, target_column, feature_columns)
            
            # Evaluate model
            test_loss = self.model.evaluate(X_test, y_test, verbose=0)
            
            # Generate predictions
            y_pred = self.model.predict(X_test)
            
            # Calculate metrics
            from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
            
            # Reshape predictions and actual values
            y_test_flat = y_test.reshape(-1)
            y_pred_flat = y_pred.reshape(-1)
            
            mse = mean_squared_error(y_test_flat, y_pred_flat)
            rmse = np.sqrt(mse)
            mae = mean_absolute_error(y_test_flat, y_pred_flat)
            r2 = r2_score(y_test_flat, y_pred_flat)
            
            # Log metrics
            logger.info(f"Test Loss: {test_loss:.4f}")
            logger.info(f"MSE: {mse:.4f}")
            logger.info(f"RMSE: {rmse:.4f}")
            logger.info(f"MAE: {mae:.4f}")
            logger.info(f"R²: {r2:.4f}")
            
            # Plot actual vs predicted
            plt.figure(figsize=(12, 6))
            
            # Plot only a subset of the data for clarity
            plot_size = min(500, len(y_test_flat))
            plt.plot(y_test_flat[:plot_size], label='Actual')
            plt.plot(y_pred_flat[:plot_size], label='Predicted')
            
            plt.title(f'{self.model_type.upper()} Model: Actual vs Predicted')
            plt.xlabel('Time Step')
            plt.ylabel(target_column)
            plt.legend()
            plt.savefig(f'results/forecasting/{self.model_type}_actual_vs_predicted.png')
            
            # Save evaluation results
            results = {
                'test_loss': float(test_loss),
                'mse': float(mse),
                'rmse': float(rmse),
                'mae': float(mae),
                'r2': float(r2),
                'evaluation_date': datetime.now().isoformat()
            }
            
            import json
            with open(f'results/forecasting/{self.model_type}_evaluation_results.json', 'w') as f:
                json.dump(results, f, indent=4)
            
            return results
            
        except Exception as e:
            logger.error(f"Error evaluating model: {e}")
            return None
    
    def plot_forecast(self, data, forecast, target_column='close', n_historic=30):
        """
        Plot historical data and forecast
        
        Args:
            data: DataFrame with historical data
            forecast: DataFrame with forecast data
            target_column: Column to plot
            n_historic: Number of historic data points to plot
            
        Returns:
            Path to saved plot
        """
        try:
            plt.figure(figsize=(12, 6))
            
            # Plot historic data
            historic_data = data[target_column].iloc[-n_historic:]
            plt.plot(historic_data.index, historic_data, label='Historic')
            
            # Plot forecast
            plt.plot(forecast.index, forecast['forecast'], label='Forecast', linestyle='--')
            
            # Add confidence intervals (simple approach)
            forecast_std = forecast['forecast'].std()
            plt.fill_between(
                forecast.index,
                forecast['forecast'] - forecast_std,
                forecast['forecast'] + forecast_std,
                alpha=0.2
            )
            
            plt.title(f'{self.model_type.upper()} Model: {target_column} Forecast')
            plt.xlabel('Date')
            plt.ylabel(target_column)
            plt.legend()
            
            # Format x-axis dates
            plt.gcf().autofmt_xdate()
            
            # Save plot
            plot_path = f'results/forecasting/{self.model_type}_forecast.png'
            plt.savefig(plot_path)
            
            return plot_path
            
        except Exception as e:
            logger.error(f"Error plotting forecast: {e}")
            return None

def main():
    """Main function"""
    logger.info("Starting time series forecasting...")
    
    try:
        # Import data fetching module
        from train_ml_model import fetch_historical_data
        
        # Fetch historical data for a symbol
        symbol = 'SPY'
        data = fetch_historical_data(symbol, period='5y', interval='1d')
        
        if data is None or len(data) < 100:
            logger.error(f"Insufficient data for {symbol}")
            return
        
        # Set date as index
        data.set_index('date', inplace=True)
        
        # Create forecaster
        lstm_forecaster = TimeSeriesForecaster(model_type='lstm', sequence_length=60, forecast_horizon=5)
        
        # Train model
        lstm_forecaster.train(data, target_column='close', epochs=50, batch_size=32)
        
        # Evaluate model
        lstm_forecaster.evaluate(data, target_column='close')
        
        # Generate forecast
        forecast = lstm_forecaster.predict(data, target_column='close')
        
        if forecast is not None:
            # Plot forecast
            lstm_forecaster.plot_forecast(data, forecast, target_column='close')
            
            # Print forecast
            logger.info(f"Forecast for {symbol}:\n{forecast}")
        
        # Create GRU forecaster
        gru_forecaster = TimeSeriesForecaster(model_type='gru', sequence_length=60, forecast_horizon=5)
        
        # Train model
        gru_forecaster.train(data, target_column='close', epochs=50, batch_size=32)
        
        # Evaluate model
        gru_forecaster.evaluate(data, target_column='close')
        
        # Generate forecast
        forecast = gru_forecaster.predict(data, target_column='close')
        
        if forecast is not None:
            # Plot forecast
            gru_forecaster.plot_forecast(data, forecast, target_column='close')
            
            # Print forecast
            logger.info(f"Forecast for {symbol}:\n{forecast}")
        
        logger.info("Time series forecasting completed")
        
    except Exception as e:
        logger.error(f"Error in time series forecasting: {e}")

if __name__ == "__main__":
    main() 