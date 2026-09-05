"""
CLI Tool for Resource Validation
Validates resources in learning paths to check for broken links.

Usage:
    python -m tools.validate_resources <path_to_json_file>
    python -m tools.validate_resources --url <single_url>
    python -m tools.validate_resources --batch <file_with_urls>
"""

import asyncio
import json
import sys
import argparse
from pathlib import Path
from typing import List, Dict
import os

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.resource_validator import ResourceValidator


def load_learning_path(file_path: str) -> Dict:
    """Load a learning path JSON file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def extract_resources_from_path(path_data: Dict) -> List[Dict[str, str]]:
    """Extract all resources from a learning path."""
    resources = []
    
    # Handle different JSON structures
    milestones = path_data.get('milestones', [])
    if not milestones:
        milestones = path_data.get('path', [])
    
    for milestone in milestones:
        milestone_resources = milestone.get('resources', [])
        for resource in milestone_resources:
            resources.append({
                'url': resource.get('url', ''),
                'title': resource.get('description', resource.get('title', 'Unknown')),
                'type': resource.get('type', 'unknown'),
                'milestone': milestone.get('title', 'Unknown Milestone')
            })
    
    return resources


async def validate_learning_path(file_path: str):
    """Validate all resources in a learning path file."""
    print(f"\n{'='*60}")
    print(f"🔍 Validating Learning Path: {file_path}")
    print(f"{'='*60}\n")
    
    try:
        path_data = load_learning_path(file_path)
        resources = extract_resources_from_path(path_data)
        
        if not resources:
            print("❌ No resources found in the learning path.")
            return
        
        print(f"📊 Found {len(resources)} resources to validate\n")
        
        validator = ResourceValidator(cache_ttl_hours=1, max_retries=2)
        validated = await validator.validate_resources(resources)
        
        # Organize results by milestone
        results_by_milestone = {}
        for item in validated:
            milestone = item.get('milestone', 'Unknown')
            if milestone not in results_by_milestone:
                results_by_milestone[milestone] = []
            results_by_milestone[milestone].append(item)
        
        # Print results
        valid_count = 0
        invalid_count = 0
        
        for milestone, milestone_resources in results_by_milestone.items():
            print(f"\n📌 {milestone}")
            print("-" * 60)
            
            for resource in milestone_resources:
                validation = resource.get('validation', {})
                is_valid = validation.get('valid', False)
                confidence = validation.get('confidence', 0)
                
                if is_valid:
                    valid_count += 1
                    status = "✅ VALID"
                    color = ""
                elif confidence >= 0.5:
                    valid_count += 1
                    status = "⚠️  UNCERTAIN"
                    color = ""
                else:
                    invalid_count += 1
                    status = "❌ INVALID"
                    color = ""
                
                print(f"\n  {status}")
                print(f"  Title: {resource.get('title', 'N/A')}")
                print(f"  URL: {resource.get('url', 'N/A')}")
                print(f"  Type: {resource.get('type', 'N/A')}")
                print(f"  Platform: {validation.get('platform', 'unknown')}")
                
                if not is_valid:
                    print(f"  Error: {validation.get('error', 'Unknown error')}")
                
                print(f"  Confidence: {confidence:.2f}")
        
        # Summary
        print(f"\n{'='*60}")
        print(f"📊 VALIDATION SUMMARY")
        print(f"{'='*60}")
        print(f"Total Resources: {len(resources)}")
        print(f"✅ Valid: {valid_count}")
        print(f"❌ Invalid: {invalid_count}")
        print(f"Success Rate: {(valid_count/len(resources)*100):.1f}%")
        print(f"{'='*60}\n")
        
        # Save report
        report_path = Path(file_path).parent / f"{Path(file_path).stem}_validation_report.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump({
                'file': file_path,
                'total_resources': len(resources),
                'valid_count': valid_count,
                'invalid_count': invalid_count,
                'success_rate': round(valid_count/len(resources)*100, 2),
                'results': validated
            }, f, indent=2)
        
        print(f"📄 Detailed report saved to: {report_path}")
        
    except FileNotFoundError:
        print(f"❌ Error: File not found: {file_path}")
    except json.JSONDecodeError:
        print(f"❌ Error: Invalid JSON file: {file_path}")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


async def validate_single_url(url: str):
    """Validate a single URL."""
    print(f"\n{'='*60}")
    print(f"🔍 Validating URL")
    print(f"{'='*60}\n")
    
    validator = ResourceValidator(cache_ttl_hours=0, max_retries=2)
    result = await validator.validate_url(url)
    
    print(f"URL: {url}")
    print(f"Valid: {'✅ Yes' if result.get('valid') else '❌ No'}")
    print(f"Status Code: {result.get('status_code', 'N/A')}")
    print(f"Platform: {result.get('platform', 'unknown')}")
    print(f"Confidence: {result.get('confidence', 0):.2f}")
    
    if not result.get('valid'):
        print(f"Error: {result.get('error', 'Unknown error')}")
    
    if result.get('title'):
        print(f"Title: {result.get('title')}")
    if result.get('author'):
        print(f"Author: {result.get('author')}")
    
    print(f"\n{'='*60}\n")


async def validate_batch(file_path: str):
    """Validate URLs from a text file (one URL per line)."""
    print(f"\n{'='*60}")
    print(f"🔍 Batch Validation: {file_path}")
    print(f"{'='*60}\n")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            urls = [line.strip() for line in f if line.strip()]
        
        if not urls:
            print("❌ No URLs found in the file.")
            return
        
        print(f"📊 Found {len(urls)} URLs to validate\n")
        
        resources = [{'url': url, 'title': url} for url in urls]
        validator = ResourceValidator(cache_ttl_hours=0, max_retries=2)
        validated = await validator.validate_resources(resources)
        
        valid_count = 0
        invalid_count = 0
        
        for item in validated:
            validation = item.get('validation', {})
            is_valid = validation.get('valid', False)
            
            if is_valid:
                valid_count += 1
                print(f"✅ {item.get('url')}")
            else:
                invalid_count += 1
                print(f"❌ {item.get('url')}")
                print(f"   Error: {validation.get('error', 'Unknown')}")
        
        print(f"\n{'='*60}")
        print(f"📊 SUMMARY")
        print(f"{'='*60}")
        print(f"Total: {len(urls)}")
        print(f"✅ Valid: {valid_count}")
        print(f"❌ Invalid: {invalid_count}")
        print(f"Success Rate: {(valid_count/len(urls)*100):.1f}%")
        print(f"{'='*60}\n")
        
    except FileNotFoundError:
        print(f"❌ Error: File not found: {file_path}")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Validate resources in learning paths',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Validate a learning path JSON file
  python -m tools.validate_resources path/to/learning_path.json
  
  # Validate a single URL
  python -m tools.validate_resources --url https://www.youtube.com/watch?v=abc123
  
  # Validate URLs from a text file
  python -m tools.validate_resources --batch urls.txt
        """
    )
    
    parser.add_argument('file', nargs='?', help='Path to learning path JSON file')
    parser.add_argument('--url', help='Validate a single URL')
    parser.add_argument('--batch', help='Validate URLs from a text file (one per line)')
    
    args = parser.parse_args()
    
    if args.url:
        asyncio.run(validate_single_url(args.url))
    elif args.batch:
        asyncio.run(validate_batch(args.batch))
    elif args.file:
        asyncio.run(validate_learning_path(args.file))
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()
