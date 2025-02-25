import requests
import pandas as pd
import json

def get_aws_regions():
    # Get list of all AWS regions
    response = requests.get('https://ec2.amazonaws.com/pricing/regions')
    regions = [region['regionCode'] for region in response.json()['regions']]
    return regions

def fetch_ec2_pricing():
    # Base URL for AWS EC2 pricing API
    base_url = "https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonEC2/current/index.json"
    
    try:
        print("Fetching EC2 pricing data... This might take a few minutes...")
        response = requests.get(base_url)
        pricing_data = response.json()
        
        # Initialize list to store instance information
        instances_info = []
        
        # Extract product details
        for product_key, product in pricing_data['products'].items():
            if product['productFamily'] == 'Compute Instance':
                attributes = product['attributes']
                
                # Get pricing information
                instance_type = attributes.get('instanceType', '')
                if instance_type:
                    # Find corresponding price in USD
                    price_per_hour = None
                    for term in pricing_data['terms']['OnDemand'].values():
                        for price_dimension in term.values():
                            for price in price_dimension['priceDimensions'].values():
                                price_per_hour = price['pricePerUnit'].get('USD', 'N/A')
                                break
                            if price_per_hour:
                                break
                        if price_per_hour:
                            break
                    
                    instances_info.append({
                        'Instance Name': instance_type,
                        'vCPU': attributes.get('vcpu', 'N/A'),
                        'Memory (GiB)': attributes.get('memory', 'N/A').replace(' GiB', ''),
                        'Region': attributes.get('location', 'N/A'),
                        'Cost per Hour (USD)': price_per_hour
                    })
        
        # Convert to DataFrame and save to CSV
        df = pd.DataFrame(instances_info)
        output_file = 'ec2_pricing.csv'
        df.to_csv(output_file, index=False)
        print(f"Data has been saved to {output_file}")
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON data: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    fetch_ec2_pricing() 