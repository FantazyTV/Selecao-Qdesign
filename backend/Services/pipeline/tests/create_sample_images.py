#!/usr/bin/env python3
"""
Create multiple sample images for testing image pipeline
"""

import sys
from pathlib import Path
import numpy as np
from datetime import datetime

# Create images directory
img_dir = Path("../../Data/images/diagrams")
img_dir.mkdir(parents=True, exist_ok=True)

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("Error: PIL not installed. Install with: pip install pillow")
    sys.exit(1)

def create_protein_structure_image(filename: str):
    """Create a synthetic protein structure visualization"""
    img = Image.new('RGB', (512, 512), color='white')
    draw = ImageDraw.Draw(img)
    
    # Draw a helix structure
    center_x, center_y = 256, 256
    radius = 100
    
    for i in range(360):
        angle = np.radians(i)
        x = center_x + radius * np.cos(angle)
        y = center_y + 50 * i / 360
        r = int(100 + 155 * np.sin(angle))
        g = int(100 + 155 * np.cos(angle))
        b = 200
        
        draw.ellipse([x-3, y-3, x+3, y+3], fill=(r, g, b))
    
    draw.text((10, 10), "Protein Structure", fill='black')
    img.save(filename)
    print(f"Created: {filename}")

def create_dna_sequence_image(filename: str):
    """Create a DNA double helix visualization"""
    img = Image.new('RGB', (512, 512), color='white')
    draw = ImageDraw.Draw(img)
    
    # Draw double helix
    for i in range(500):
        y = i
        
        # Left helix
        x1 = 150 + 50 * np.sin(i * 0.05)
        draw.point((int(x1), y), fill='red')
        
        # Right helix
        x2 = 350 + 50 * np.cos(i * 0.05)
        draw.point((int(x2), y), fill='blue')
        
        # Connecting lines
        if i % 10 == 0:
            draw.line([(int(x1), y), (int(x2), y)], fill='green', width=2)
    
    draw.text((10, 10), "DNA Sequence", fill='black')
    img.save(filename)
    print(f"Created: {filename}")

def create_molecular_structure_image(filename: str):
    """Create a molecular structure diagram"""
    img = Image.new('RGB', (512, 512), color='white')
    draw = ImageDraw.Draw(img)
    
    # Draw atoms and bonds in a grid
    positions = [(150, 150), (250, 150), (350, 150),
                 (150, 250), (250, 250), (350, 250),
                 (150, 350), (250, 350), (350, 350)]
    
    colors = ['red', 'blue', 'green', 'orange', 'purple', 'brown', 'pink', 'gray', 'cyan']
    
    # Draw bonds
    for i, pos in enumerate(positions):
        if i % 3 < 2:
            draw.line([pos, positions[i+1]], fill='gray', width=2)
        if i < 6:
            draw.line([pos, positions[i+3]], fill='gray', width=2)
    
    # Draw atoms
    for pos, color in zip(positions, colors):
        draw.ellipse([pos[0]-15, pos[1]-15, pos[0]+15, pos[1]+15], fill=color)
    
    draw.text((10, 10), "Molecular Structure", fill='black')
    img.save(filename)
    print(f"Created: {filename}")

def create_graph_image(filename: str):
    """Create a data visualization graph"""
    img = Image.new('RGB', (512, 512), color='white')
    draw = ImageDraw.Draw(img)
    
    # Draw axes
    draw.line([(50, 450), (50, 50)], fill='black', width=2)
    draw.line([(50, 450), (450, 450)], fill='black', width=2)
    
    # Generate random data points
    np.random.seed(42)
    data = np.cumsum(np.random.randn(20))
    data = ((data - data.min()) / (data.max() - data.min())) * 350 + 50
    
    x_points = np.linspace(60, 440, 20)
    
    # Draw lines
    for i in range(len(x_points)-1):
        draw.line([(int(x_points[i]), int(450-data[i])), 
                   (int(x_points[i+1]), int(450-data[i+1]))], fill='blue', width=2)
    
    # Draw points
    for x, y in zip(x_points, data):
        draw.ellipse([x-3, 450-y-3, x+3, 450-y+3], fill='red')
    
    draw.text((10, 10), "Data Graph", fill='black')
    img.save(filename)
    print(f"Created: {filename}")

def create_microscopy_image(filename: str):
    """Create a microscopy-like image"""
    img = Image.new('RGB', (512, 512), color='black')
    
    # Create random cellular patterns
    pixels = img.load()
    np.random.seed(hash(filename) % (2**32))
    
    for i in range(512):
        for j in range(512):
            # Create circular blobs
            dist_to_center = np.sqrt((i-256)**2 + (j-256)**2)
            
            # Multiple gaussian blobs
            val = 0
            for cx, cy in [(150, 150), (350, 150), (150, 350), (350, 350), (256, 256)]:
                blob = np.exp(-((i-cx)**2 + (j-cy)**2) / 3000)
                val += blob
            
            val = min(255, int(val * 255))
            pixels[i, j] = (val, val // 2, 255 - val)
    
    draw = ImageDraw.Draw(img)
    draw.text((10, 10), "Microscopy", fill='white')
    img.save(filename)
    print(f"Created: {filename}")

def create_heatmap_image(filename: str):
    """Create a heatmap visualization"""
    img = Image.new('RGB', (512, 512), color='white')
    pixels = img.load()
    
    np.random.seed(hash(filename) % (2**32))
    data = np.random.rand(64, 64)
    
    for i in range(64):
        for j in range(64):
            # Scale to image coordinates
            x_start = i * 8
            y_start = j * 8
            
            # Value to color (blue -> white -> red)
            val = data[i, j]
            if val < 0.5:
                r = int(val * 2 * 255)
                g = int(val * 2 * 255)
                b = 255
            else:
                r = 255
                g = int((1 - val) * 2 * 255)
                b = int((1 - val) * 2 * 255)
            
            for x in range(x_start, min(x_start + 8, 512)):
                for y in range(y_start, min(y_start + 8, 512)):
                    pixels[x, y] = (r, g, b)
    
    draw = ImageDraw.Draw(img)
    draw.text((10, 10), "Heatmap", fill='black')
    img.save(filename)
    print(f"Created: {filename}")

def create_spectrum_image(filename: str):
    """Create a spectrum/absorption plot"""
    img = Image.new('RGB', (512, 512), color='white')
    draw = ImageDraw.Draw(img)
    
    # Draw axes
    draw.line([(50, 450), (50, 50)], fill='black', width=2)
    draw.line([(50, 450), (450, 450)], fill='black', width=2)
    
    # Draw spectrum curve
    points = []
    for x in range(50, 451):
        # Create a spectrum-like curve
        wavelength = (x - 50) / 400 * 300  # 400-700nm range
        intensity = np.sin((wavelength - 450) / 100 * np.pi) ** 2
        y = 450 - intensity * 350
        points.append((x, int(y)))
    
    # Draw the curve with color gradient
    for i in range(len(points)-1):
        x = (points[i][0] - 50) / 400  # 0 to 1
        # Map to color
        r = int(max(0, (x - 0.5) * 2) * 255) if x > 0.5 else 0
        g = int(max(0, (0.5 - abs(x - 0.5))) * 2 * 255)
        b = int(max(0, (0.5 - x) * 2) * 255) if x < 0.5 else 0
        
        draw.line([points[i], points[i+1]], fill=(r, g, b), width=3)
    
    draw.text((10, 10), "Spectrum", fill='black')
    img.save(filename)
    print(f"Created: {filename}")

def create_pattern_image(filename: str, pattern_type: int):
    """Create geometric pattern images"""
    img = Image.new('RGB', (512, 512), color='white')
    draw = ImageDraw.Draw(img)
    
    if pattern_type == 0:
        # Concentric circles
        for r in range(10, 256, 20):
            draw.ellipse([(256-r, 256-r), (256+r, 256+r)], outline='blue', width=2)
    elif pattern_type == 1:
        # Grid pattern
        for i in range(0, 512, 32):
            draw.line([(i, 0), (i, 512)], fill='gray', width=1)
            draw.line([(0, i), (512, i)], fill='gray', width=1)
    elif pattern_type == 2:
        # Spiral
        for angle in np.linspace(0, 10*np.pi, 1000):
            r = angle * 30
            x = 256 + r * np.cos(angle)
            y = 256 + r * np.sin(angle)
            draw.point((int(x), int(y)), fill='red')
    elif pattern_type == 3:
        # Fractal-like pattern
        for i in range(512):
            for j in range(512):
                val = (i ^ j) % 256
                img.putpixel((i, j), (val, 255-val, 128))
    
    draw.text((10, 10), f"Pattern {pattern_type}", fill='black')
    img.save(filename)
    print(f"Created: {filename}")

def main():
    """Create sample images"""
    print(f"\n{'='*70}")
    print(f"CREATING SAMPLE IMAGES FOR PIPELINE TESTING")
    print(f"{'='*70}\n")
    
    start = datetime.now()
    
    # Create various images
    create_protein_structure_image(str(img_dir / "01_protein_structure.jpg"))
    create_dna_sequence_image(str(img_dir / "02_dna_sequence.jpg"))
    create_molecular_structure_image(str(img_dir / "03_molecular_structure.jpg"))
    create_graph_image(str(img_dir / "04_graph.jpg"))
    create_microscopy_image(str(img_dir / "05_microscopy.jpg"))
    create_heatmap_image(str(img_dir / "06_heatmap.jpg"))
    create_spectrum_image(str(img_dir / "07_spectrum.jpg"))
    
    # Create multiple patterns
    for i in range(4):
        create_pattern_image(str(img_dir / f"08_pattern_{i}.jpg"), i)
    
    # Create a few more by varying the original
    for i in range(2):
        create_dna_sequence_image(str(img_dir / f"09_dna_variant_{i}.jpg"))
        create_molecular_structure_image(str(img_dir / f"10_molecule_variant_{i}.jpg"))
    
    elapsed = (datetime.now() - start).total_seconds()
    
    # Count images
    images = list(img_dir.glob("*.jpg")) + list(img_dir.glob("*.png"))
    total_size = sum(f.stat().st_size for f in images) / (1024 * 1024)
    
    print(f"\n{'='*70}")
    print(f"COMPLETE")
    print(f"{'='*70}")
    print(f"Total images created: {len(images)}")
    print(f"Total size: {total_size:.2f} MB")
    print(f"Time: {elapsed:.2f}s")
    print(f"Location: {img_dir}")
    print(f"{'='*70}\n")

if __name__ == "__main__":
    main()
