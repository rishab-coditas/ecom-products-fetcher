import requests
import json
import pandas as pd 
import time
from datetime import datetime
import os
import argparse
import logging
from logging.handlers import RotatingFileHandler

# Hardcoded API key
API_KEY = "FB95857366114AC19C1C79E8A401B1AB"

def ensure_directory(directory):
    """Create directory if it doesn't exist"""
    if not os.path.exists(directory):
        os.makedirs(directory)
        print(f"Created directory: {directory}")

def get_amazon_data_paginated(category, product_name, output_dir, total_results=200, batch_size=20, max_page=5):
    """
    Fetches Amazon product data for a specific product within a category
    """
    # Create category directory
    category_dir = os.path.join(output_dir, category)
    ensure_directory(category_dir)
    
    # Create file name with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    file_name = os.path.join(category_dir, f'{product_name.replace(" ", "_")}_{timestamp}.csv')
    
    print(f"\n{'='*50}")
    print(f"Processing Category: {category}")
    print(f"Product: {product_name}")
    print(f"Target number of products: {total_results}")
    print(f"Output will be saved to: {file_name}")
    print(f"{'='*50}\n")
    
    url = 'https://api.rainforestapi.com/request'
    all_products = []
    processed_asins = set()
    batch_number = 1
    
    try:
        while len(all_products) < total_results:
            print(f"\nProcessing Batch {batch_number}")
            print(f"Products collected so far: {len(all_products)}/{total_results}")
            
            for page in range(1, max_page + 1):
                if len(all_products) >= total_results:
                    break
                    
                print(f"\nFetching page {page} of batch {batch_number}")
                
                params = {
                    'api_key': API_KEY,
                    'type': 'search',
                    'amazon_domain': 'amazon.com',
                    'search_term': product_name,
                    'page': page,
                    'max_page': max_page
                }
                
                print(f"Making search request...")
                response = requests.get(url, params=params)
                print(f"Search response status: {response.status_code}")
                
                if response.status_code != 200:
                    print(f"Error on page {page}: {response.text}")
                    break
                    
                data = response.json()
                products = data.get('search_results', [])
                
                if not products:
                    print(f"No products found on page {page}")
                    break
                    
                print(f"Found {len(products)} products on page {page}")
                
                new_products_count = 0
                products_remaining = total_results - len(all_products)
                products_to_process = min(batch_size, products_remaining, len(products))
                
                for idx, product in enumerate(products[:products_to_process], 1):
                    asin = product.get('asin')
                    if not asin or asin in processed_asins:
                        continue
                    
                    print(f"Fetching details for product {idx}/{products_to_process} on page {page} (ASIN: {asin})")
                    product_params = {
                        'api_key': API_KEY,
                        'type': 'product',
                        'amazon_domain': 'amazon.com',
                        'asin': asin
                    }
                    
                    try:
                        product_response = requests.get(url, params=product_params)
                        if product_response.status_code == 200:
                            product_data = product_response.json()
                            if 'product' in product_data:
                                # Add category to product data
                                product_data['product']['category'] = category
                                all_products.append(product_data['product'])
                                processed_asins.add(asin)
                                new_products_count += 1
                                print(f"Successfully added product {idx} (Total unique products: {len(all_products)})")
                                
                                # Save progress
                                df = pd.DataFrame(all_products)
                                df.to_csv(file_name, index=False)
                                print(f"Progress saved to {file_name}")
                                
                                if len(all_products) >= total_results:
                                    break
                        else:
                            print(f"Failed to fetch product {idx} details")
                            
                    except Exception as e:
                        print(f"Error processing product {idx}: {str(e)}")
                    
                    time.sleep(1)
                
                print(f"Added {new_products_count} new unique products from page {page}")
                
                if new_products_count == 0:
                    print("No new unique products found on this page")
                    break
                
                time.sleep(2)
            
            batch_number += 1
            
            if len(all_products) >= total_results or new_products_count == 0:
                break
        
        if all_products:
            # Final save and summary
            df = pd.DataFrame(all_products)
            df.to_csv(file_name, index=False)
            
            print(f"\nCategory '{category}' - Product '{product_name}' completed!")
            print(f"Total unique products collected: {len(all_products)}")
            print(f"Results saved to: {file_name}")
            
            return True, len(all_products), file_name
        else:
            print(f"No products found for {product_name} in {category}")
            return False, 0, None
            
    except Exception as e:
        print(f"Error in processing: {str(e)}")
        return False, 0, None

def process_categories(categories_data, output_dir, total_results=200, batch_size=20, max_page=5):
    """Process multiple categories and their products"""
    overall_results = []
    
    # Create main output directory
    ensure_directory(output_dir)
    
    for category, products in categories_data.items():
        print(f"\n{'#'*70}")
        print(f"Starting Category: {category}")
        print(f"Products to process: {', '.join(products)}")
        print(f"{'#'*70}\n")
        
        category_results = []
        
        for product in products:
            success, total_products, file_path = get_amazon_data_paginated(
                category,
                product,
                output_dir,
                total_results,
                batch_size,
                max_page
            )
            
            category_results.append({
                "category": category,
                "product": product,
                "success": success,
                "total_products": total_products,
                "file_path": file_path
            })
            
        overall_results.extend(category_results)
        
        # Save category summary
        category_summary = pd.DataFrame(category_results)
        summary_file = os.path.join(output_dir, category, f"{category}_summary.csv")
        category_summary.to_csv(summary_file, index=False)
        print(f"\nCategory summary saved to: {summary_file}")
    
    # Save overall summary
    overall_summary = pd.DataFrame(overall_results)
    summary_file = os.path.join(output_dir, "overall_summary.csv")
    overall_summary.to_csv(summary_file, index=False)
    print(f"\nOverall summary saved to: {summary_file}")
    
    return overall_results

# Set up logging
def setup_logging(output_dir):
    # Create logs directory
    logs_dir = os.path.join(output_dir, 'logs')
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)
    
    # Log file with timestamp
    log_file = os.path.join(logs_dir, f'scraper_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            RotatingFileHandler(log_file, maxBytes=10000000, backupCount=5),
            logging.StreamHandler()
        ]
    )
    
    return log_file

# Add status file function
def update_status(output_dir, status):
    status_file = os.path.join(output_dir, 'status.json')
    current_status = {
        'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'status': status
    }
    with open(status_file, 'w') as f:
        json.dump(current_status, f, indent=4)

# Modify main function to include status updates
def main():
    parser = argparse.ArgumentParser(description='Amazon Product Scraper for Multiple Categories')
    parser.add_argument('--categories_file', required=True, help='JSON file containing categories and products')
    parser.add_argument('--output_dir', required=True, help='Base output directory for results')
    parser.add_argument('--total_results', type=int, default=200, help='Products to fetch per item (default: 200)')
    parser.add_argument('--batch_size', type=int, default=20, help='Products per batch (default: 20)')
    parser.add_argument('--max_page', type=int, default=5, help='Maximum pages per batch (default: 5)')
    
    args = parser.parse_args()
    
    # Setup logging
    log_file = setup_logging(args.output_dir)
    logging.info("Script started")
    
    # Create PID file
    pid_file = os.path.join(args.output_dir, 'scraper.pid')
    with open(pid_file, 'w') as f:
        f.write(str(os.getpid()))
    
    try:
        update_status(args.output_dir, 'RUNNING')
        logging.info(f"Process ID: {os.getpid()}")
        
        # Read categories from JSON file
        with open(args.categories_file, 'r') as f:
            categories_data = json.load(f)
        
        # Process all categories
        results = process_categories(
            categories_data,
            args.output_dir,
            args.total_results,
            args.batch_size,
            args.max_page
        )
        
        update_status(args.output_dir, 'COMPLETED')
        logging.info("Script completed successfully!")
        logging.info(f"Results are organized in: {args.output_dir}")
        
    except Exception as e:
        update_status(args.output_dir, f'ERROR: {str(e)}')
        logging.error(f"Script failed: {str(e)}")
        raise
    
    finally:
        # Clean up PID file
        if os.path.exists(pid_file):
            os.remove(pid_file)

if __name__ == "__main__":
    main() 