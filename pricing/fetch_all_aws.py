import requests
import pandas as pd
import json
import os

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
        print("Fetching raw EC2 pricing JSON data...")
        response = requests.get(base_url)
        data = response.json()
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)
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
        print("Fetching raw Aurora pricing JSON data...")
        response = requests.get(base_url)
        data = response.json()
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)
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
        with open(json_file, 'r') as f:
            pricing_data = json.load(f)
        instances_info = []
        # Get the OnDemand pricing terms indexed by SKU.
        on_demand_terms = pricing_data.get('terms', {}).get('OnDemand', {})
        sku_index = 0
        for sku, product in pricing_data.get('products', {}).items():
            #if sku_index >= 20:
            #    break
            if product.get('productFamily', '') == 'Compute Instance':
                attributes = product.get('attributes', {})
                instance_type = attributes.get('instanceType', '')
                if instance_type:
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
                    sku_index += 1
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
        with open(json_file, 'r') as f:
            pricing_data = json.load(f)
        aurora_info = []
        # Prepare lookup for OnDemand pricing by SKU.
        on_demand_terms = pricing_data.get('terms', {}).get('OnDemand', {})
        for sku, product in pricing_data.get('products', {}).items():
            if product.get('productFamily', '') == 'Database Instance':
                attributes = product.get('attributes', {})
                # Filter only for Aurora PostgreSQL instances.
                if attributes.get('databaseEngine', '').strip() == "Aurora PostgreSQL":
                    instance_type = attributes.get('instanceType', '')
                    if instance_type:
                        price_per_hour = "N/A"
                        if sku in on_demand_terms:
                            term = list(on_demand_terms[sku].values())[0]  # take first term available
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
    # First download raw JSON files
    fetch_ec2_pricing_json()
    fetch_aurora_pricing_json()
    # Then process the JSON files into CSV files
    fetch_ec2_pricing()
    fetch_aurora_pricing()

