#!/usr/bin/env python3
"""
==========================================
OPENAPI YAML EXPORT UTILITY
==========================================

Exports the Game Service OpenAPI specification to YAML file.

Usage:
    python -m game_app.utils.export_openapi_yaml [--output FILE]

Examples:
    python -m game_app.utils.export_openapi_yaml
    python -m game_app.utils.export_openapi_yaml --output docs/game_openapi.yaml

The exported file can be used for:
- API Gateway configuration
- API documentation tools (Swagger UI, Redoc)
- Client SDK generation
- Contract testing
"""

import sys
import argparse
from pathlib import Path
from typing import Dict, Any


def export_openapi_to_yaml(output_file: str = "game_service_openapi.yaml") -> Path:
    """
    Export OpenAPI specification from FastAPI app to YAML format.

    Args:
        output_file: Path to output YAML file

    Returns:
        Path to the created file
    """
    # Import here to avoid circular dependencies
    from game_app.main import app

    print(f"🔧 Exporting OpenAPI specification for Game Service...")
    print(f"   Title: {app.title}")
    print(f"   Version: {app.version}")

    # Get OpenAPI schema from FastAPI
    openapi_schema: Dict[str, Any] = app.openapi()

    # Add server information for different environments
    openapi_schema["servers"] = [
        {
            "url": "http://localhost:8003",
            "description": "Local development server"
        },
        {
            "url": "http://game_service:8003",
            "description": "Docker internal network"
        },
        {
            "url": "https://api.triduel.com/game",
            "description": "Production API Gateway"
        }
    ]

    # Add additional metadata
    if "info" not in openapi_schema:
        openapi_schema["info"] = {}

    openapi_schema["info"]["contact"] = {
        "name": "Game Service Team",
        "email": "game-service@triduel.com"
    }

    openapi_schema["info"]["license"] = {
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT"
    }

    # Resolve output path
    output_path = Path(output_file)

    # Ensure parent directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Export to YAML
    try:
        import yaml

        with open(output_path, "w", encoding="utf-8") as f:
            yaml.dump(
                openapi_schema,
                f,
                sort_keys=False,
                allow_unicode=True,
                default_flow_style=False,
                indent=2
            )

        print(f"✅ OpenAPI YAML exported to: {output_path.absolute()}")

    except ImportError:
        print("❌ PyYAML not installed!")
        print("   Install with: pip install pyyaml")
        print("   Or add to requirements.txt: pyyaml>=6.0")
        sys.exit(1)

    # Print summary
    paths_count = len(openapi_schema.get('paths', {}))
    schemas_count = len(openapi_schema.get('components', {}).get('schemas', {}))
    security_count = len(openapi_schema.get('components', {}).get('securitySchemes', {}))

    print(f"\n📊 Summary:")
    print(f"   OpenAPI Version: {openapi_schema.get('openapi', 'N/A')}")
    print(f"   Endpoints: {paths_count}")
    print(f"   Schemas: {schemas_count}")
    print(f"   Security Schemes: {security_count}")

    # List all endpoints
    print(f"\n📍 Exported Endpoints:")
    for path, methods in openapi_schema.get('paths', {}).items():
        methods_list = ', '.join(m.upper() for m in methods.keys())
        print(f"   {path}: {methods_list}")

    return output_path


def main():
    """Main entry point for CLI usage."""
    parser = argparse.ArgumentParser(
        description="Export Game Service OpenAPI specification to YAML",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Export to default location (game_service_openapi.yaml)
  python -m game_app.utils.export_openapi_yaml
  
  # Export to custom location
  python -m game_app.utils.export_openapi_yaml --output docs/api.yaml
  
  # Export to project root
  python -m game_app.utils.export_openapi_yaml --output ../game_openapi.yaml
        """
    )

    parser.add_argument(
        "--output",
        "-o",
        default="game_service_openapi.yaml",
        help="Output file path (default: game_service_openapi.yaml)"
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show detailed schema information"
    )

    args = parser.parse_args()

    try:
        output_path = export_openapi_to_yaml(args.output)

        if args.verbose:
            print("\n🔍 Detailed Schema Information:")
            from game_app.main import app
            openapi_schema = app.openapi()

            print("\n   Security Schemes:")
            for name, scheme in openapi_schema.get('components', {}).get('securitySchemes', {}).items():
                print(f"      {name}: {scheme.get('type', 'N/A')}")

            print("\n   Main Schemas:")
            for name in list(openapi_schema.get('components', {}).get('schemas', {}).keys())[:10]:
                print(f"      - {name}")
            if len(openapi_schema.get('components', {}).get('schemas', {})) > 10:
                print(f"      ... and {len(openapi_schema.get('components', {}).get('schemas', {})) - 10} more")

        print("\n✨ Done! You can now:")
        print(f"   - View the file: {output_path.absolute()}")
        print(f"   - View in Swagger UI: http://localhost:8003/docs")
        print(f"   - Import to API Gateway (Traefik, Kong, etc.)")
        print(f"   - Generate client SDKs: openapi-generator-cli generate -i {output_path.name}")

        return 0

    except Exception as e:
        print(f"❌ Error exporting OpenAPI: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

