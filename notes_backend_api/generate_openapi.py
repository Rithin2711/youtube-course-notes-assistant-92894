#!/usr/bin/env python3
"""
Generate OpenAPI specification file for the YouTube Course Notes API.
This script creates the openapi.json file that can be used by frontend clients.
"""

import json
from main import app

def generate_openapi_spec():
    """Generate and save OpenAPI specification."""
    openapi_schema = app.openapi()
    
    # Add additional metadata
    openapi_schema["info"]["contact"] = {
        "name": "YouTube Course Notes API",
        "email": "support@example.com"
    }
    
    openapi_schema["info"]["license"] = {
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT"
    }
    
    # Add server information
    openapi_schema["servers"] = [
        {
            "url": "http://localhost:8000",
            "description": "Development server"
        },
        {
            "url": "https://api.yourapp.com",
            "description": "Production server"
        }
    ]
    
    # Save to file
    with open("openapi.json", "w") as f:
        json.dump(openapi_schema, f, indent=2)
    
    print("✅ OpenAPI specification generated: openapi.json")
    print(f"📄 Generated {len(openapi_schema.get('paths', {}))} API endpoints")
    
    # Display summary
    if "paths" in openapi_schema:
        print("\n📋 API Endpoints Summary:")
        for path, methods in openapi_schema["paths"].items():
            for method in methods.keys():
                if method != "parameters":
                    print(f"  {method.upper()} {path}")

if __name__ == "__main__":
    generate_openapi_spec()
