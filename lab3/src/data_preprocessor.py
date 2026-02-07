import pandas as pd
import numpy as np
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.preprocessing import StandardScaler, OneHotEncoder, LabelEncoder
from sklearn.impute import SimpleImputer
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline

class DataPreprocessor(BaseEstimator, TransformerMixin):
    """
    Module 1: Data Preprocessor
    Responsible for handling missing values, encoding categorical variables,
    and scaling numerical features for the Real Estate AutoML System.
    """
    
    def __init__(self, target_variable=None):
        self.target_variable = target_variable
        self.numeric_transformer = Pipeline(steps=[
            ('imputer', SimpleImputer(strategy='median')),
            ('scaler', StandardScaler())
        ])
        
        self.categorical_transformer = Pipeline(steps=[
            ('imputer', SimpleImputer(strategy='constant', fill_value='missing')),
            ('onehot', OneHotEncoder(handle_unknown='ignore'))
        ])
        
        self.preprocessor = None
        
    def fit(self, X):
        """
        Fit the transformer on the data.
        Identifies numeric and categorical columns automatically.
        """
        numeric_features = X.select_dtypes(include=['int64', 'float64']).columns
        categorical_features = X.select_dtypes(include=['object', 'category']).columns
        
        self.preprocessor = ColumnTransformer(
            transformers=[
                ('num', self.numeric_transformer, numeric_features),
                ('cat', self.categorical_transformer, categorical_features)
            ])
            
        return self.preprocessor.fit(X)

    def transform(self, X):
        """
        Transform the data using the fitted pipeline.
        """
        if self.preprocessor is None:
            raise Exception("Preprocessor has not been fitted yet.")
            
        print("Starting Data Transformation...")
        X_processed = self.preprocessor.transform(X)
        print(f"Data Transformed successfully. Shape: {X_processed.shape}")
        return X_processed

    def fit_transform_custom(self, df):
        """
        Custom convenience method to handle DataFrame splitting and transformation.
        """
        if self.target_variable and self.target_variable in df.columns:
            y = df[self.target_variable]
            X = df.drop(columns=[self.target_variable])
            
            self.fit(X)
            X_transformed = self.transform(X)
            
            return X_transformed, y
        else:
            print(f"Target variable '{self.target_variable}' not found in DataFrame.")
            return None, None
