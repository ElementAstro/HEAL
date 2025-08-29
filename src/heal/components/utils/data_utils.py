"""
Data Utilities
Consolidated data-related utility functions including validation,
transformation, serialization, and data processing operations.
"""

import json
import csv
import pickle
import hashlib
from typing import Any, Dict, List, Optional, Union, Callable, TypeVar, Generic
from dataclasses import dataclass, asdict
from pathlib import Path
from datetime import datetime, timezone
import re

from ...common.logging_config import get_logger

logger = get_logger(__name__)

T = TypeVar('T')


class DataUtilities:
    """
    Consolidated data utilities that provide comprehensive
    data processing, validation, and transformation operations.
    """
    
    @staticmethod
    def validate_json(data: Union[str, Dict[str, Any]]) -> bool:
        """Validate JSON data"""
        try:
            if isinstance(data, str):
                json.loads(data)
            elif isinstance(data, dict):
                json.dumps(data)
            else:
                return False
            return True
        except (json.JSONDecodeError, TypeError):
            return False
    
    @staticmethod
    def safe_json_load(file_path: str, default: Any = None) -> Any:
        """Safely load JSON file with error handling"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load JSON from {file_path}: {e}")
            return default
    
    @staticmethod
    def safe_json_save(data: Any, file_path: str, indent: int = 2) -> bool:
        """Safely save data to JSON file"""
        try:
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=indent, ensure_ascii=False)
            return True
        except Exception as e:
            logger.error(f"Failed to save JSON to {file_path}: {e}")
            return False
    
    @staticmethod
    def merge_dictionaries(dict1: Dict[str, Any], dict2: Dict[str, Any], deep: bool = True) -> Dict[str, Any]:
        """Merge two dictionaries with optional deep merging"""
        if not deep:
            result = dict1.copy()
            result.update(dict2)
            return result
        
        result = dict1.copy()
        
        for key, value in dict2.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = DataUtilities.merge_dictionaries(result[key], value, deep=True)
            else:
                result[key] = value
        
        return result
    
    @staticmethod
    def flatten_dictionary(data: Dict[str, Any], separator: str = '.', prefix: str = '') -> Dict[str, Any]:
        """Flatten nested dictionary"""
        flattened = {}
        
        for key, value in data.items():
            new_key = f"{prefix}{separator}{key}" if prefix else key
            
            if isinstance(value, dict):
                flattened.update(DataUtilities.flatten_dictionary(value, separator, new_key))
            else:
                flattened[new_key] = value
        
        return flattened
    
    @staticmethod
    def unflatten_dictionary(data: Dict[str, Any], separator: str = '.') -> Dict[str, Any]:
        """Unflatten dictionary back to nested structure"""
        result = {}
        
        for key, value in data.items():
            keys = key.split(separator)
            current = result
            
            for k in keys[:-1]:
                if k not in current:
                    current[k] = {}
                current = current[k]
            
            current[keys[-1]] = value
        
        return result
    
    @staticmethod
    def validate_data_schema(data: Dict[str, Any], schema: Dict[str, Any]) -> Dict[str, Any]:
        """Validate data against schema"""
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        try:
            # Check required fields
            required_fields = schema.get('required', [])
            for field in required_fields:
                if field not in data:
                    validation_result['errors'].append(f"Missing required field: {field}")
                    validation_result['valid'] = False
            
            # Check field types
            field_types = schema.get('types', {})
            for field, expected_type in field_types.items():
                if field in data:
                    actual_type = type(data[field]).__name__
                    if actual_type != expected_type:
                        validation_result['errors'].append(
                            f"Field {field} has type {actual_type}, expected {expected_type}"
                        )
                        validation_result['valid'] = False
            
            # Check field patterns
            field_patterns = schema.get('patterns', {})
            for field, pattern in field_patterns.items():
                if field in data and isinstance(data[field], str):
                    if not re.match(pattern, data[field]):
                        validation_result['errors'].append(
                            f"Field {field} does not match pattern {pattern}"
                        )
                        validation_result['valid'] = False
            
        except Exception as e:
            validation_result['valid'] = False
            validation_result['errors'].append(f"Schema validation error: {e}")
        
        return validation_result
    
    @staticmethod
    def sanitize_data(data: Dict[str, Any], sanitization_rules: Dict[str, Callable]) -> Dict[str, Any]:
        """Sanitize data using provided rules"""
        sanitized = data.copy()
        
        for field, sanitizer in sanitization_rules.items():
            if field in sanitized:
                try:
                    sanitized[field] = sanitizer(sanitized[field])
                except Exception as e:
                    logger.error(f"Failed to sanitize field {field}: {e}")
        
        return sanitized
    
    @staticmethod
    def calculate_data_hash(data: Any, algorithm: str = 'sha256') -> str:
        """Calculate hash of data"""
        try:
            # Convert data to string representation
            if isinstance(data, (dict, list)):
                data_str = json.dumps(data, sort_keys=True)
            else:
                data_str = str(data)
            
            # Calculate hash
            hash_func = getattr(hashlib, algorithm)()
            hash_func.update(data_str.encode('utf-8'))
            return hash_func.hexdigest()
            
        except Exception as e:
            logger.error(f"Failed to calculate data hash: {e}")
            return ""
    
    @staticmethod
    def export_to_csv(data: List[Dict[str, Any]], file_path: str, fieldnames: Optional[List[str]] = None) -> bool:
        """Export data to CSV file"""
        try:
            if not data:
                logger.warning("No data to export")
                return False
            
            if not fieldnames:
                fieldnames = list(data[0].keys())
            
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(data)
            
            logger.info(f"Data exported to CSV: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export to CSV: {e}")
            return False
    
    @staticmethod
    def import_from_csv(file_path: str) -> List[Dict[str, Any]]:
        """Import data from CSV file"""
        try:
            data = []
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                data = list(reader)
            
            logger.info(f"Imported {len(data)} records from CSV: {file_path}")
            return data
            
        except Exception as e:
            logger.error(f"Failed to import from CSV: {e}")
            return []
    
    @staticmethod
    def serialize_object(obj: Any, file_path: str) -> bool:
        """Serialize object to file using pickle"""
        try:
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, 'wb') as f:
                pickle.dump(obj, f)
            return True
        except Exception as e:
            logger.error(f"Failed to serialize object: {e}")
            return False
    
    @staticmethod
    def deserialize_object(file_path: str, default: Any = None) -> Any:
        """Deserialize object from file using pickle"""
        try:
            with open(file_path, 'rb') as f:
                return pickle.load(f)
        except Exception as e:
            logger.error(f"Failed to deserialize object: {e}")
            return default
    
    @staticmethod
    def clean_data(data: Dict[str, Any], remove_empty: bool = True, remove_none: bool = True) -> Dict[str, Any]:
        """Clean data by removing empty/none values"""
        cleaned = {}
        
        for key, value in data.items():
            # Skip empty values if requested
            if remove_empty and value == "":
                continue
            
            # Skip None values if requested
            if remove_none and value is None:
                continue
            
            # Recursively clean nested dictionaries
            if isinstance(value, dict):
                cleaned_value = DataUtilities.clean_data(value, remove_empty, remove_none)
                if cleaned_value:  # Only add if not empty after cleaning
                    cleaned[key] = cleaned_value
            else:
                cleaned[key] = value
        
        return cleaned
    
    @staticmethod
    def transform_data(data: Any, transformers: Dict[str, Callable]) -> Any:
        """Transform data using provided transformer functions"""
        if isinstance(data, dict):
            transformed = {}
            for key, value in data.items():
                if key in transformers:
                    try:
                        transformed[key] = transformers[key](value)
                    except Exception as e:
                        logger.error(f"Failed to transform field {key}: {e}")
                        transformed[key] = value
                else:
                    # Recursively transform nested data
                    transformed[key] = DataUtilities.transform_data(value, transformers)
            return transformed
        elif isinstance(data, list):
            return [DataUtilities.transform_data(item, transformers) for item in data]
        else:
            return data


# Convenience functions for backward compatibility
def load_json_config(file_path: str) -> Dict[str, Any]:
    """Load JSON configuration file (backward compatibility)"""
    return DataUtilities.safe_json_load(file_path, {})

def save_json_config(data: Dict[str, Any], file_path: str) -> bool:
    """Save JSON configuration file (backward compatibility)"""
    return DataUtilities.safe_json_save(data, file_path)
