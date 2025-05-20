from flask import Flask, request, jsonify, send_file
import requests
import json
import pandas as pd 
import logging
import sys
from io import StringIO, BytesIO
import time
from datetime import datetime
import os

# Configure logging to output to console
logging.basicConfig(
    stream=sys.stdout,  # Ensure logs go to stdout
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add a console handler to make sure logs are printed
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.DEBUG)
logger.addHandler(console_handler)

app = Flask(__name__)

def get_amazon_data(product_name, api_key, num_results=50):
    print(f"\n=== Starting API Request ===")  # Direct print statement
    print(f"Searching for: {product_name}")
    print(f"Number of results requested: {num_results}")
    
    if not api_key:
        print("Error: API key is missing")
        raise Exception("api_key is required")

    url = 'https://api.rainforestapi.com/request'

    params = {
        'api_key': api_key,
        'type': 'search',
        'amazon_domain': 'amazon.com',
        # 'number_of_results': num_results,
        'search_term': product_name,
        'sort_by': 'featured',
        'max_page': 3
    }
    
    try:
        print(f"\nMaking request to Rainforest API...")
        response = requests.get(url, params=params)
        print(f"Response Status Code: {response.status_code}")
        
        if response.status_code != 200:
            print(f"Error Response: {response.text}")
            response.raise_for_status()
            
        data = response.json()
        products = data.get('search_results', [])
        print(f"Number of products found: {len(products)}")
        
        if not products:
            print("No products found in search results")
            return []
            
        asins = [product.get('asin') for product in products]
        print(f"Found {len(asins)} product ASINs")
        all_products_data = []

        for idx, asin in enumerate(asins, 1):
            print(f"\nFetching details for product {idx}/{len(asins)} - ASIN: {asin}")
            product_params = {
                'api_key': api_key,
                'type': 'product',
                'output': 'json',
                'amazon_domain': 'amazon.com',
                'asin': asin,
            }   
            
            product_response = requests.get(url, params=product_params)
            print(f"Product API Response Status: {product_response.status_code}")
            
            if product_response.status_code == 200:
                product_data = product_response.json()
                if 'product' in product_data:
                    all_products_data.append(product_data['product'])
                    print(f"Successfully added product data")
                else:
                    print(f"No product data found for ASIN: {asin}")
            else:
                print(f"Error fetching product details: {product_response.text}")

        print(f"\nTotal products retrieved: {len(all_products_data)}")
        return all_products_data
        
    except Exception as e:
        print(f"Error occurred: {str(e)}")
        raise

@app.route('/api/search', methods=['POST'])
def search_products():
    print("\n=== Received New Request ===")  # Direct print statement
    
    if not request.is_json:
        print("Error: Request is not JSON")
        return jsonify({"error": "Request must be JSON"}), 400
        
    data = request.get_json()
    print(f"Request data received: {json.dumps(data, indent=2)}")
    
    # Check for required parameters
    if 'product_name' not in data:
        print("Error: Missing product_name")
        return jsonify({"error": "product_name is required"}), 400
    if 'api_key' not in data:
        print("Error: Missing api_key")
        return jsonify({"error": "api_key is required"}), 400
        
    product_name = data['product_name']
    api_key = data['api_key']
    num_results = data.get('num_results', 50)
    
    print(f"\nProcessing request:")
    print(f"Product Name: {product_name}")
    print(f"Number of Results: {num_results}")
    
    try:
        products = get_amazon_data(product_name, api_key, num_results)
        
        response_data = {
            "success": True,
            "product_name": product_name,
            "num_results": len(products),
            "products": products
        }
        
        if data.get('save_to_csv', False):
            print("\nSaving results to CSV...")
            df = pd.DataFrame(products)
            csv_file = f'search_results_{product_name}.csv'
            df.to_csv(csv_file, index=False)
            response_data["csv_file"] = csv_file
            print(f"Data saved to {csv_file}")
            
        print(f"\nRequest completed successfully")
        return jsonify(response_data)
        
    except Exception as e:
        print(f"\nError processing request: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/search/csv', methods=['POST'])
def search_products_csv():
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400
        
    data = request.get_json()
    
    if 'product_name' not in data:
        return jsonify({"error": "product_name is required"}), 400
    if 'api_key' not in data:
        return jsonify({"error": "api_key is required"}), 400
        
    product_name = data['product_name']
    api_key = data['api_key']
    num_results = data.get('num_results', 100)
    
    try:
        products = get_amazon_data(product_name, api_key, num_results)
        
        if not products:
            return jsonify({"error": "No products found"}), 404
            
        # Create DataFrame and convert to CSV in memory
        df = pd.DataFrame(products)
        csv_buffer = BytesIO()
        df.to_csv(csv_buffer, index=False)
        csv_buffer.seek(0)
        
        # Return the CSV file as a downloadable attachment
        return send_file(
            csv_buffer,
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'search_results_{product_name}.csv'
        )
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def get_amazon_data_in_batches(product_name, api_key, file_name, total_results=200, batch_size=20):
    """
    Fetches Amazon product data in batches
    
    Parameters:
    - product_name: Name of the product to search
    - api_key: Rainforest API key
    - file_name: Custom name for the output CSV file
    - total_results: Total number of products to fetch (default: 200)
    - batch_size: Number of products to fetch in each API call (default: 20)
                 Recommended to keep between 10-20 to avoid API timeouts
    """
    print(f"\nStarting batch processing for {product_name}")
    print(f"Total results requested: {total_results}")
    print(f"Batch size: {batch_size}")
    
    url = 'https://api.rainforestapi.com/request'
    all_products = []
    batch_number = 1
    
    # Create a directory for temporary files if it doesn't exist
    temp_dir = 'temp_batches'
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
    
    # Ensure filename ends with .csv
    if not file_name.endswith('.csv'):
        file_name += '.csv'
    
    try:
        for offset in range(0, total_results, batch_size):
            current_batch_size = min(batch_size, total_results - offset)
            print(f"\nProcessing batch {batch_number}")
            print(f"Fetching products {offset+1} to {offset + current_batch_size}")
            
            params = {
                'api_key': api_key,
                'type': 'search',
                'amazon_domain': 'amazon.com',
                'number_of_results': current_batch_size,
                'search_term': product_name,
                'sort_by': 'featured',
                'offset': offset
            }
            
            # Make the search request
            print(f"Making search request for batch {batch_number}...")
            response = requests.get(url, params=params)
            print(f"Search response status: {response.status_code}")
            
            if response.status_code != 200:
                print(f"Error in batch {batch_number}: {response.text}")
                continue
                
            data = response.json()
            products = data.get('search_results', [])
            
            if not products:
                print(f"No products found in batch {batch_number}")
                break
                
            print(f"Found {len(products)} products in batch {batch_number}")
            
            # Process each product in the batch
            batch_products = []
            for idx, product in enumerate(products, 1):
                asin = product.get('asin')
                if not asin:
                    continue
                    
                print(f"Fetching details for product {idx}/{len(products)} in batch {batch_number}")
                product_params = {
                    'api_key': api_key,
                    'type': 'product',
                    'amazon_domain': 'amazon.com',
                    'asin': asin
                }
                
                try:
                    product_response = requests.get(url, params=product_params)
                    if product_response.status_code == 200:
                        product_data = product_response.json()
                        if 'product' in product_data:
                            batch_products.append(product_data['product'])
                            print(f"Successfully added product {idx}")
                    else:
                        print(f"Failed to fetch product {idx} details")
                        
                except Exception as e:
                    print(f"Error processing product {idx}: {str(e)}")
                
                # Add a small delay between product requests
                time.sleep(1)
            
            # Save batch to temporary CSV
            if batch_products:
                batch_df = pd.DataFrame(batch_products)
                batch_file = os.path.join(temp_dir, f'batch_{batch_number}.csv')
                batch_df.to_csv(batch_file, index=False)
                print(f"Saved batch {batch_number} to temporary file")
                
                all_products.extend(batch_products)
                
            print(f"Completed batch {batch_number}")
            batch_number += 1
            
            # Add a delay between batches
            time.sleep(2)
        
        # Combine all batches into final CSV
        if all_products:
            final_df = pd.DataFrame(all_products)
            final_df.to_csv(file_name, index=False)
            print(f"\nAll batches completed. Total products: {len(all_products)}")
            print(f"Final CSV saved to: {file_name}")
            
            # Cleanup temporary files
            for file in os.listdir(temp_dir):
                os.remove(os.path.join(temp_dir, file))
            os.rmdir(temp_dir)
            
            return file_name, len(all_products)
        else:
            print("No products found across all batches")
            return None, 0
            
    except Exception as e:
        print(f"Error in batch processing: {str(e)}")
        return None, 0

@app.route('/api/search/batch', methods=['POST'])
def search_products_batch():
    print("\nReceived batch search request")
    
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400
        
    data = request.get_json()
    
    # Validate required fields
    if 'product_name' not in data:
        return jsonify({"error": "product_name is required"}), 400
    if 'api_key' not in data:
        return jsonify({"error": "api_key is required"}), 400
    if 'file_name' not in data:
        return jsonify({"error": "file_name is required"}), 400
        
    product_name = data['product_name']
    api_key = data['api_key']
    file_name = data['file_name']
    total_results = data.get('total_results', 200)
    batch_size = data.get('batch_size', 20)
    
    try:
        csv_path, total_products = get_amazon_data_in_batches(
            product_name, 
            api_key,
            file_name,
            total_results, 
            batch_size
        )
        
        if csv_path:
            return jsonify({
                "success": True,
                "message": f"Successfully retrieved {total_products} products",
                "csv_file_path": csv_path
            })
        else:
            return jsonify({
                "success": False,
                "message": "No products found or error occurred"
            }), 404
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("\n=== Starting Flask Server ===")
    print("Server will be available at http://localhost:5000")
    app.run(debug=True, port=5000)
