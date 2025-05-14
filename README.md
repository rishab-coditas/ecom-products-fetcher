# Amazon Product Search API

This is a Flask-based REST API that allows you to search for products on Amazon using the Rainforest API and download the results in both JSON and CSV formats.

## Prerequisites

- Python 3.7 or higher
- pip (Python package installer)
- A Rainforest API key (Get it from [Rainforest API](https://www.rainforestapi.com/))

## Installation

1. Clone the repository or download the source code:
```bash
git clone <repository-url>
# or download and unzip the project
```

2. Navigate to the project directory:
```bash
cd products+search
```

3. Install the required dependencies:
```bash
pip install -r requirements.txt
```

## Configuration

Before running the application, make sure you have your Rainforest API key ready. You'll need to include this in your API requests.

## Running the Application

1. Start the Flask server:
```bash
python product+search.py
```

2. The server will start running on `http://localhost:5000`

## API Endpoints

### 1. Search Products (JSON Response)

**Endpoint:** `/api/search`
**Method:** POST
**Content-Type:** application/json

**Request Body:**
```json
{
    "product_name": "Your product name",
    "api_key": "your_rainforest_api_key",
    "num_results": 10  // optional, defaults to 50
}
```

**Example using curl:**
```bash
curl -X POST http://localhost:5000/api/search \
-H "Content-Type: application/json" \
-d '{"product_name": "Blender", "api_key": "your_api_key_here", "num_results": 10}'
```

### 2. Search Products (CSV Download)

**Endpoint:** `/api/search/csv`
**Method:** POST
**Content-Type:** application/json

**Request Body:**
```json
{
    "product_name": "Your product name",
    "api_key": "your_rainforest_api_key",
    "num_results": 10  // optional, defaults to 50
}
```

**Example using curl:**
```bash
curl -X POST http://localhost:5000/api/search/csv \
-H "Content-Type: application/json" \
-d '{"product_name": "Blender", "api_key": "your_api_key_here", "num_results": 10}' \
--output "search_results.csv"
```

## Using with Postman

1. Create a new POST request
2. Enter the URL: `http://localhost:5000/api/search` (for JSON) or `http://localhost:5000/api/search/csv` (for CSV)
3. Set the header:
   - Key: `Content-Type`
   - Value: `application/json`
4. In the Body tab:
   - Select "raw"
   - Select "JSON" from the dropdown
   - Enter your request body:
```json
{
    "product_name": "Blender",
    "api_key": "your_api_key_here",
    "num_results": 10
}
```
5. Click Send

## Response Format

### JSON Response (`/api/search`)
```json
{
    "success": true,
    "product_name": "Blender",
    "num_results": 10,
    "products": [
        {
            "title": "Product Title",
            "price": "Product Price",
            "rating": "Product Rating",
            // ... other product details
        }
        // ... more products
    ]
}
```

### CSV Response (`/api/search/csv`)
Downloads a CSV file with all product details in tabular format.

## Error Handling

The API returns appropriate error messages with corresponding HTTP status codes:

- 400: Bad Request (missing required parameters)
- 404: Not Found (no products found)
- 500: Internal Server Error (API errors or other issues)

## Limitations

- Maximum number of results per request: 50
- Rate limiting depends on your Rainforest API plan
- Requires active internet connection

## Troubleshooting

1. If you get a "ModuleNotFoundError":
   - Make sure you've installed all requirements: `pip install -r requirements.txt`

2. If you get an API key error:
   - Verify your Rainforest API key is correct
   - Make sure you're including it in the request body

3. If the server won't start:
   - Check if port 5000 is available
   - Try running with a different port: `app.run(port=5001)`

## License

[Your License Here]

## Support

For support, please [create an issue](your-repository-issues-url) or contact [your contact information]. 