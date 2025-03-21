import requests
import pandas as pd
import json
import os
import ijson

def get_aws_regions():
    response = requests.get('https://ec2.amazonaws.com/pricing/regions')
    regions = [region['regionCode'] for region in response.json()['regions']]
    return regions

def fetch_ec2_pricing_json():
    output_file = 'ec2_pricing_raw.json'
    if os.path.exists(output_file):
        answer = input(f"{output_file} already exists. Overwrite? (y/n): ")
        if answer.lower() != 'y':
            print(f"Skipping writing {output_file}")
            return
    base_url = "https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonEC2/current/index.json"
    try:
        print("Downloading raw EC2 pricing JSON data...")
        with requests.get(base_url, stream=True) as response:
            response.raise_for_status()
            with open(output_file, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
        print(f"Raw EC2 pricing JSON data has been saved to {output_file}")
    except Exception as e:
        print(f"Error fetching raw EC2 pricing JSON data: {e}")

def fetch_aurora_pricing_json():
    output_file = 'aurora_pricing_raw.json'
    if os.path.exists(output_file):
        answer = input(f"{output_file} already exists. Overwrite? (y/n): ")
        if answer.lower() != 'y':
            print(f"Skipping writing {output_file}")
            return
    base_url = "https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonRDS/current/index.json"
    try:
        print("Downloading raw Aurora pricing JSON data...")
        with requests.get(base_url, stream=True) as response:
            response.raise_for_status()
            with open(output_file, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
        print(f"Raw Aurora pricing JSON data has been saved to {output_file}")
    except Exception as e:
        print(f"Error fetching raw Aurora pricing JSON data: {e}")

def fetch_ec2_pricing():
    output_file = 'ec2_pricing.csv'
    json_file = 'ec2_pricing_raw.json'
    if not os.path.exists(json_file):
        print(f"{json_file} not found. Please run fetch_ec2_pricing_json() first.")
        return
    if os.path.exists(output_file):
        answer = input(f"{output_file} already exists. Overwrite? (y/n): ")
        if answer.lower() != 'y':
            print(f"Skipping writing {output_file}")
            return
    try:
        # Build a dictionary for OnDemand terms using ijson streaming.
        on_demand_terms = {}
        with open(json_file, 'r') as f:
            for sku, term_data in ijson.kvitems(f, 'terms.OnDemand'):
                on_demand_terms[sku] = term_data

        instances_info = []
        # Process the products in a memory-efficient streaming fashion.
        with open(json_file, 'r') as f:
            for sku, product in ijson.kvitems(f, 'products'):
                if product.get('productFamily', '') == 'Compute Instance':
                    attributes = product.get('attributes', {})
                    instance_type = attributes.get('instanceType', '')
                    # Only process rows with an instance type and matching criteria.
                    if (instance_type and 
                        attributes.get('preInstalledSw', '') == "NA" and 
                        attributes.get('operatingSystem', '') == "Linux" and  
                        attributes.get('licenseModel', '') == "No License required" and 
                        attributes.get('tenancy', '') == "Shared" and  
                        attributes.get('capacitystatus', '') == "UnusedCapacityReservation"):
                        price_per_hour = "N/A"
                        if sku in on_demand_terms:
                            term = list(on_demand_terms[sku].values())[0]
                            price_dims = term.get('priceDimensions', {})
                            if price_dims:
                                price_per_hour = list(price_dims.values())[0]['pricePerUnit'].get('USD', 'N/A')
                        instances_info.append({
                            'SKU': sku,
                            'Instance Name': instance_type,
                            'vCPU': attributes.get('vcpu', 'N/A'),
                            'Memory (GiB)': attributes.get('memory', 'N/A').replace(' GiB', ''),
                            'Region': attributes.get('location', 'N/A'),
                            'Cost per Hour (USD)': price_per_hour
                        })
        df = pd.DataFrame(instances_info)
        df.to_csv(output_file, index=False)
        print(f"EC2 pricing data has been saved to {output_file}")
    except Exception as e:
        print(f"An unexpected error occurred while processing EC2 data: {e}")

def fetch_aurora_pricing():
    output_csv = 'aurora_pricing.csv'
    json_file = 'aurora_pricing_raw.json'
    if not os.path.exists(json_file):
        print(f"{json_file} not found. Please run fetch_aurora_pricing_json() first.")
        return
    if os.path.exists(output_csv):
        answer = input(f"{output_csv} already exists. Overwrite? (y/n): ")
        if answer.lower() != 'y':
            print(f"Skipping writing {output_csv}")
            return
    try:
        aurora_info = []
        on_demand_terms = {}
        with open(json_file, 'r') as f:
            for sku, term_data in ijson.kvitems(f, 'terms.OnDemand'):
                on_demand_terms[sku] = term_data

        with open(json_file, 'r') as f:
            for sku, product in ijson.kvitems(f, 'products'):
                if product.get('productFamily', '') == 'Database Instance':
                    attributes = product.get('attributes', {})
                    # Filter only for Aurora PostgreSQL instances.
                    if attributes.get('databaseEngine', '').strip() == "Aurora PostgreSQL":
                        instance_type = attributes.get('instanceType', '')
                        if instance_type:
                            price_per_hour = "N/A"
                            if sku in on_demand_terms:
                                term = list(on_demand_terms[sku].values())[0]
                                price_dims = term.get('priceDimensions', {})
                                if price_dims:
                                    price_per_hour = list(price_dims.values())[0]['pricePerUnit'].get('USD', 'N/A')
                            aurora_info.append({
                                'SKU': sku,
                                'Instance Name': instance_type,
                                'vCPU': attributes.get('vcpu', 'N/A'),
                                'Memory (GiB)': attributes.get('memory', 'N/A').replace(' GiB', ''),
                                'Region': attributes.get('location', 'N/A'),
                                'Cost per Hour (USD)': price_per_hour,
                                'Database Engine': attributes.get('databaseEngine', 'N/A'),
                                'Storage': attributes.get('storage', 'N/A')
                            })
        df_aurora = pd.DataFrame(aurora_info)
        df_aurora.to_csv(output_csv, index=False)
        print(f"Aurora pricing data has been saved to {output_csv} (loaded {len(aurora_info)} items)")
    except Exception as e:
        print(f"An unexpected error occurred while processing Aurora data: {e}")

if __name__ == "__main__":
    # First, download raw JSON files using streaming to limit memory usage.
    fetch_ec2_pricing_json()
    fetch_aurora_pricing_json()
    # Then, process the JSON files into CSV files using ijson for memory efficiency.
    fetch_ec2_pricing()
    fetch_aurora_pricing()

