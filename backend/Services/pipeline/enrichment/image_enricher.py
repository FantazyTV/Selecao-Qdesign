"""
Image enricher for extracting visual features and metadata
"""

from typing import Dict, Any
import numpy as np
from .base_enricher import BaseEnricher
from ..logger import get_logger

logger = get_logger(__name__)


class ImageEnricher(BaseEnricher):
    """Enrich image metadata by extracting visual features and properties"""
    
    def enrich(
        self,
        content: Any,
        metadata: Dict[str, Any],
        data_type: str
    ) -> Dict[str, Any]:
        """
        Enrich image metadata by analyzing visual properties
        
        Args:
            content: PIL Image object or numpy array
            metadata: Existing metadata
            data_type: Data type
        
        Returns:
            Enhanced metadata with visual features
        """
        try:
            # Import PIL here to handle optional dependency
            from PIL import Image
            
            # Handle PIL Image
            if isinstance(content, Image.Image):
                image = content
                
                # Basic image properties
                metadata["width"] = image.width
                metadata["height"] = image.height
                metadata["format"] = image.format or "UNKNOWN"
                metadata["color_mode"] = image.mode
                
                # Calculate aspect ratio
                if image.height > 0:
                    metadata["aspect_ratio"] = image.width / image.height
                
                # Image size in pixels
                metadata["pixel_count"] = image.width * image.height
                
                # Convert to numpy for analysis
                try:
                    img_array = np.array(image)
                    
                    # Analyze based on color mode
                    if image.mode == 'RGB' or image.mode == 'RGBA':
                        # Extract color statistics
                        if image.mode == 'RGBA':
                            # Drop alpha channel for analysis
                            img_array = img_array[:, :, :3]
                        
                        # Calculate color channel statistics
                        for i, channel in enumerate(['red', 'green', 'blue']):
                            channel_data = img_array[:, :, i]
                            metadata[f"{channel}_mean"] = float(np.mean(channel_data))
                            metadata[f"{channel}_std"] = float(np.std(channel_data))
                            metadata[f"{channel}_min"] = float(np.min(channel_data))
                            metadata[f"{channel}_max"] = float(np.max(channel_data))
                        
                        # Overall brightness
                        brightness = np.mean(img_array)
                        metadata["brightness"] = float(brightness)
                        
                        # Color dominance (which channel is dominant)
                        mean_channels = [
                            np.mean(img_array[:, :, 0]),
                            np.mean(img_array[:, :, 1]),
                            np.mean(img_array[:, :, 2])
                        ]
                        dominant_channel = ['red', 'green', 'blue'][np.argmax(mean_channels)]
                        metadata["dominant_color"] = dominant_channel
                        
                    elif image.mode == 'L':
                        # Grayscale image
                        metadata["grayscale"] = True
                        metadata["brightness"] = float(np.mean(img_array))
                        metadata["contrast"] = float(np.std(img_array))
                    
                    # Edge density estimation (using simple Sobel-like approach)
                    try:
                        edges = self._estimate_edge_density(img_array)
                        metadata["edge_density"] = float(edges)
                    except Exception:
                        pass
                    
                    # Saturation (for color images)
                    if image.mode in ['RGB', 'RGBA']:
                        saturation = self._calculate_saturation(img_array)
                        metadata["saturation"] = float(saturation)
                    
                except Exception as e:
                    logger.debug(f"Could not extract detailed image features: {e}")
                
                return metadata
            
            else:
                # Handle numpy array directly
                if isinstance(content, np.ndarray):
                    img_array = content
                    
                    # Get dimensions
                    if len(img_array.shape) == 3:
                        metadata["height"] = img_array.shape[0]
                        metadata["width"] = img_array.shape[1]
                        metadata["channels"] = img_array.shape[2]
                        metadata["pixel_count"] = img_array.shape[0] * img_array.shape[1]
                    elif len(img_array.shape) == 2:
                        metadata["height"] = img_array.shape[0]
                        metadata["width"] = img_array.shape[1]
                        metadata["channels"] = 1
                        metadata["pixel_count"] = img_array.shape[0] * img_array.shape[1]
                    
                    # Calculate aspect ratio
                    if img_array.shape[0] > 0:
                        metadata["aspect_ratio"] = img_array.shape[1] / img_array.shape[0]
                    
                    # Basic statistics
                    metadata["mean_value"] = float(np.mean(img_array))
                    metadata["std_value"] = float(np.std(img_array))
                    metadata["min_value"] = float(np.min(img_array))
                    metadata["max_value"] = float(np.max(img_array))
                    
                    # Edge density
                    try:
                        edges = self._estimate_edge_density(img_array)
                        metadata["edge_density"] = float(edges)
                    except Exception:
                        pass
                    
                    return metadata
            
            return metadata
            
        except Exception as e:
            logger.error(f"Error enriching image: {e}")
            return metadata
    
    def _estimate_edge_density(self, img_array: np.ndarray) -> float:
        """
        Estimate edge density using simple gradient calculation
        
        Args:
            img_array: Image as numpy array
        
        Returns:
            Edge density score between 0 and 1
        """
        try:
            # Convert to grayscale if needed
            if len(img_array.shape) == 3:
                # Simple grayscale conversion
                gray = np.mean(img_array, axis=2)
            else:
                gray = img_array
            
            # Calculate gradients using Sobel-like approximation
            gx = np.gradient(gray, axis=0)
            gy = np.gradient(gray, axis=1)
            
            # Calculate edge magnitude
            edges = np.sqrt(gx**2 + gy**2)
            
            # Normalize to 0-1 range
            max_edge = np.max(edges)
            if max_edge > 0:
                edge_density = np.mean(edges) / max_edge
            else:
                edge_density = 0.0
            
            return edge_density
            
        except Exception:
            return 0.0
    
    def _calculate_saturation(self, img_array: np.ndarray) -> float:
        """
        Calculate average saturation of image
        
        Args:
            img_array: RGB image as numpy array
        
        Returns:
            Average saturation score between 0 and 1
        """
        try:
            # Ensure we have RGB
            if img_array.shape[2] >= 3:
                r = img_array[:, :, 0].astype(float)
                g = img_array[:, :, 1].astype(float)
                b = img_array[:, :, 2].astype(float)
                
                # Calculate max and min for each pixel
                max_rgb = np.maximum(np.maximum(r, g), b)
                min_rgb = np.minimum(np.minimum(r, g), b)
                
                # Calculate saturation
                delta = max_rgb - min_rgb
                value = max_rgb
                
                # Avoid division by zero
                saturation = np.zeros_like(value)
                mask = value > 0
                saturation[mask] = delta[mask] / value[mask]
                
                return float(np.mean(saturation))
            
            return 0.0
            
        except Exception:
            return 0.0
    
    def is_applicable(self, data_type: str) -> bool:
        """Check if this enricher applies to image data"""
        return data_type == "image"
