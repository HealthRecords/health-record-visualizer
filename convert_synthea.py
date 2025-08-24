#!/usr/bin/env python3
"""
Convert Synthea FHIR bundles to individual resource files matching Apple Health export format.
This allows testing the dynamic resource system with synthetic health data.
"""

import json
import uuid
from pathlib import Path
import argparse
from typing import Dict, List


def extract_resources_from_bundle(bundle_path: Path) -> Dict[str, List[Dict]]:
    """Extract individual resources from a FHIR bundle file."""
    resources_by_type = {}
    
    with open(bundle_path, 'r') as f:
        bundle = json.load(f)
    
    if bundle.get('resourceType') != 'Bundle':
        raise ValueError(f"Expected Bundle, got {bundle.get('resourceType')}")
    
    entries = bundle.get('entry', [])
    print(f"Processing {len(entries)} entries from bundle...")
    
    for entry in entries:
        resource = entry.get('resource', {})
        resource_type = resource.get('resourceType')
        
        if resource_type:
            if resource_type not in resources_by_type:
                resources_by_type[resource_type] = []
            resources_by_type[resource_type].append(resource)
    
    return resources_by_type


def normalize_fhir_to_apple_format(resource: Dict) -> Dict:
    """Convert Synthea FHIR format to Apple Health export format"""
    
    # Handle category field in Observations
    if resource.get('resourceType') == 'Observation' and 'category' in resource:
        categories = resource['category']
        if isinstance(categories, list):
            normalized_categories = []
            for cat in categories:
                if isinstance(cat, dict) and 'coding' in cat and cat['coding']:
                    # Convert {"coding": [{"display": "Laboratory"}]} to {"text": "Laboratory"}
                    display = cat['coding'][0].get('display', 'Unknown')
                    # Normalize common categories to match expected format
                    if display.lower() == 'vital signs':
                        display = 'Vital Signs'
                    normalized_categories.append({"text": display})
                elif isinstance(cat, dict) and 'text' in cat:
                    # Already in Apple format
                    normalized_categories.append(cat)
                else:
                    normalized_categories.append({"text": "Unknown"})
            resource['category'] = normalized_categories
    
    # Normalize date formats - convert timezone offsets to Z format
    # Apple Health export uses UTC dates ending in Z
    date_fields = ['effectiveDateTime', 'issued', 'performedDateTime', 'authoredOn', 'recordedDate']
    for field in date_fields:
        if field in resource and isinstance(resource[field], str):
            date_str = resource[field]
            # Convert timezone offset format to Z format
            if date_str.endswith(('-07:00', '-08:00', '+00:00')) or '-' in date_str[-6:] or '+' in date_str[-6:]:
                try:
                    from datetime import datetime
                    # Parse the date with timezone and convert to UTC
                    if date_str.endswith('Z'):
                        continue  # Already in correct format
                    elif '+' in date_str[-6:] or '-' in date_str[-6:]:
                        # Handle timezone offset format
                        dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                        # Convert to UTC and format as expected
                        utc_dt = dt.utctimetuple()
                        resource[field] = datetime(*utc_dt[:6]).strftime('%Y-%m-%dT%H:%M:%SZ')
                except:
                    pass  # Keep original if conversion fails
    
    return resource


def save_individual_resources(resources_by_type: Dict[str, List[Dict]], output_dir: Path):
    """Save resources as individual files matching Apple Health format."""
    # Create the expected directory structure: output_dir/clinical-records/
    clinical_dir = output_dir / "clinical-records"
    clinical_dir.mkdir(parents=True, exist_ok=True)
    
    total_files = 0
    for resource_type, resources in resources_by_type.items():
        print(f"Processing {len(resources)} {resource_type} resources...")
        
        for resource in resources:
            # Normalize FHIR format to Apple Health format
            normalized_resource = normalize_fhir_to_apple_format(resource)
            
            # Use existing ID if available, otherwise generate one
            resource_id = normalized_resource.get('id', str(uuid.uuid4()))
            
            # Create filename matching Apple Health pattern: ResourceType-UUID.json
            filename = f"{resource_type}-{resource_id}.json"
            file_path = clinical_dir / filename
            
            # Save individual resource
            with open(file_path, 'w') as f:
                json.dump(normalized_resource, f, indent=2)
            
            total_files += 1
    
    print(f"Created {total_files} individual resource files in {clinical_dir}")


def main():
    parser = argparse.ArgumentParser(description="Convert Synthea FHIR bundles to individual files")
    parser.add_argument("input_dir", help="Directory containing Synthea FHIR bundle files")
    parser.add_argument("output_dir", help="Directory to save individual resource files")
    parser.add_argument("--patient-only", action="store_true", 
                       help="Only process patient bundle (skip hospital/practitioner)")
    
    args = parser.parse_args()
    
    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    
    if not input_dir.exists():
        print(f"Error: Input directory {input_dir} does not exist")
        return 1
    
    # Find bundle files
    bundle_files = list(input_dir.glob("*.json"))
    if not bundle_files:
        print(f"Error: No JSON files found in {input_dir}")
        return 1
    
    print(f"Found {len(bundle_files)} bundle files:")
    for f in bundle_files:
        print(f"  - {f.name}")
    
    # Filter to patient bundles only if requested
    if args.patient_only:
        bundle_files = [f for f in bundle_files if not any(x in f.name.lower() 
                                                          for x in ['hospital', 'practitioner'])]
        print(f"Processing {len(bundle_files)} patient bundle files only")
    
    total_resources = {}
    
    for bundle_file in bundle_files:
        print(f"\nProcessing {bundle_file.name}...")
        
        try:
            resources = extract_resources_from_bundle(bundle_file)
            
            # Merge resources by type
            for resource_type, resource_list in resources.items():
                if resource_type not in total_resources:
                    total_resources[resource_type] = []
                total_resources[resource_type].extend(resource_list)
            
        except Exception as e:
            print(f"Error processing {bundle_file}: {e}")
            continue
    
    # Print summary
    print("\nResource Summary:")
    for resource_type, resources in sorted(total_resources.items()):
        print(f"  {resource_type}: {len(resources)}")
    
    # Save all resources
    if total_resources:
        save_individual_resources(total_resources, output_dir)
        
        # Create a summary file
        summary = {
            "conversion_info": {
                "source_format": "Synthea FHIR Bundle",
                "target_format": "Apple Health Export (individual files)",
                "total_files_created": sum(len(resources) for resources in total_resources.values()),
                "resource_types": {rt: len(resources) for rt, resources in total_resources.items()}
            }
        }
        
        with open(output_dir / "conversion_summary.json", 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"\nConversion complete! Check {output_dir} for individual resource files.")
        print("You can now use this synthetic data to test your health data explorer.")
    else:
        print("No resources found to convert.")
    
    return 0


if __name__ == "__main__":
    exit(main())