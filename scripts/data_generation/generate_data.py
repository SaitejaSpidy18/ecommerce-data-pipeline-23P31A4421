# scripts/data_generation/generate_data.py

import os
import json
import csv
from datetime import datetime, timedelta
from faker import Faker
import random
import yaml
from pathlib import Path

fake = Faker()

def load_config():
    """Load configuration from config/config.yaml"""
    config_path = "config/config.yaml"
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def create_output_dirs(config):
    """Create output directories if they don't exist"""
    output_dir = config['paths']['data_raw']
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    return output_dir

def generate_customers(num_customers, output_dir):
    """Generate customer data"""
    print(f"Generating {num_customers} customers...")
    customers = []
    
    for i in range(1, num_customers + 1):
        customer = {
            'customer_id': i,
            'first_name': fake.first_name(),
            'last_name': fake.last_name(),
            'email': fake.email(),
            'phone': fake.phone_number(),
            'address': fake.address().replace('\n', ', '),
            'city': fake.city(),
            'state': fake.state(),
            'postal_code': fake.postcode(),
            'country': 'India',
            'signup_date': fake.date_between(start_date='-2y').isoformat(),
            'is_active': random.choice([True, True, True, False]),  # 75% active
        }
        customers.append(customer)
    
    # Write to CSV
    output_file = os.path.join(output_dir, 'customers.csv')
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=customers[0].keys())
        writer.writeheader()
        writer.writerows(customers)
    
    print(f"✓ Generated {len(customers)} customers -> {output_file}")
    return customers

def generate_products(num_products, output_dir):
    """Generate product data"""
    print(f"Generating {num_products} products...")
    products = []
    
    categories = ['Electronics', 'Clothing', 'Home & Garden', 'Sports', 'Books', 'Toys', 'Food', 'Beauty']
    
    for i in range(1, num_products + 1):
        cost = round(random.uniform(50, 5000), 2)
        markup = random.uniform(1.2, 3.0)
        price = round(cost * markup, 2)
        
        product = {
            'product_id': i,
            'product_name': fake.word() + ' ' + fake.word(),
            'category': random.choice(categories),
            'cost': cost,
            'price': price,
            'stock_quantity': random.randint(0, 1000),
            'is_active': random.choice([True, True, True, True, False]),  # 80% active
            'created_date': fake.date_between(start_date='-3y').isoformat(),
        }
        products.append(product)
    
    # Write to CSV
    output_file = os.path.join(output_dir, 'products.csv')
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=products[0].keys())
        writer.writeheader()
        writer.writerows(products)
    
    print(f"✓ Generated {len(products)} products -> {output_file}")
    return products

def generate_transactions(num_transactions, customers, products, start_date, end_date, output_dir):
    """Generate transaction data"""
    print(f"Generating {num_transactions} transactions...")
    transactions = []
    
    payment_methods = ['Credit Card', 'Debit Card', 'UPI', 'Net Banking', 'Cash']
    
    start = datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.strptime(end_date, '%Y-%m-%d')
    date_range = (end - start).days
    
    for i in range(1, num_transactions + 1):
        trans_date = start + timedelta(days=random.randint(0, date_range))
        
        transaction = {
            'transaction_id': i,
            'customer_id': random.choice(customers)['customer_id'],
            'transaction_date': trans_date.isoformat(),
            'payment_method': random.choice(payment_methods),
            'total_amount': round(random.uniform(100, 50000), 2),
            'transaction_status': random.choice(['Completed', 'Completed', 'Completed', 'Pending', 'Failed']),
        }
        transactions.append(transaction)
    
    # Write to CSV
    output_file = os.path.join(output_dir, 'transactions.csv')
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=transactions[0].keys())
        writer.writeheader()
        writer.writerows(transactions)
    
    print(f"✓ Generated {len(transactions)} transactions -> {output_file}")
    return transactions

def generate_transaction_items(transactions, products, min_items, max_items, output_dir):
    """Generate transaction items (line items)"""
    print(f"Generating transaction items ({min_items}-{max_items} total)...")
    transaction_items = []
    
    item_id = 1
    for transaction in transactions:
        num_items = random.randint(1, 5)  # 1-5 items per transaction
        
        for line in range(num_items):
            product = random.choice(products)
            quantity = random.randint(1, 10)
            unit_price = product['price']
            line_total = round(quantity * unit_price, 2)
            
            item = {
                'item_id': item_id,
                'transaction_id': transaction['transaction_id'],
                'product_id': product['product_id'],
                'quantity': quantity,
                'unit_price': unit_price,
                'line_total': line_total,
            }
            transaction_items.append(item)
            item_id += 1
    
    # Write to CSV
    output_file = os.path.join(output_dir, 'transaction_items.csv')
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=transaction_items[0].keys())
        writer.writeheader()
        writer.writerows(transaction_items)
    
    print(f"✓ Generated {len(transaction_items)} transaction items -> {output_file}")
    return transaction_items

def generate_metadata(output_dir, customers, products, transactions, transaction_items):
    """Generate metadata JSON file"""
    metadata = {
        'generated_at': datetime.now().isoformat(),
        'generation_summary': {
            'num_customers': len(customers),
            'num_products': len(products),
            'num_transactions': len(transactions),
            'num_transaction_items': len(transaction_items),
        },
        'data_quality_notes': {
            'referential_integrity': 'All customer_ids and product_ids are valid references',
            'date_range': f"Transactions span from {min([t['transaction_date'] for t in transactions])} to {max([t['transaction_date'] for t in transactions])}",
        }
    }
    
    output_file = os.path.join(output_dir, 'generation_metadata.json')
    with open(output_file, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"✓ Generated metadata -> {output_file}")
    return metadata

def main():
    """Main execution"""
    print("\n" + "="*60)
    print("E-Commerce Data Generation Pipeline")
    print("="*60 + "\n")
    
    try:
        # Load config
        config = load_config()
        print("✓ Configuration loaded from config/config.yaml\n")
        
        # Create output directories
        output_dir = create_output_dirs(config)
        print(f"✓ Output directory ready: {output_dir}\n")
        
        # Extract generation parameters
        num_customers = config['data_generation']['num_customers']
        num_products = config['data_generation']['num_products']
        num_transactions = config['data_generation']['num_transactions']
        start_date = config['data_generation']['start_date']
        end_date = config['data_generation']['end_date']
        
        # Generate data
        customers = generate_customers(num_customers, output_dir)
        products = generate_products(num_products, output_dir)
        transactions = generate_transactions(num_transactions, customers, products, start_date, end_date, output_dir)
        transaction_items = generate_transaction_items(transactions, products, 
                                                       config['data_generation']['min_transaction_items'],
                                                       config['data_generation']['max_transaction_items'],
                                                       output_dir)
        metadata = generate_metadata(output_dir, customers, products, transactions, transaction_items)
        
        # Summary
        print("\n" + "="*60)
        print("Data Generation Complete")
        print("="*60)
        print(f"Customers:          {metadata['generation_summary']['num_customers']}")
        print(f"Products:           {metadata['generation_summary']['num_products']}")
        print(f"Transactions:       {metadata['generation_summary']['num_transactions']}")
        print(f"Transaction Items:  {metadata['generation_summary']['num_transaction_items']}")
        print("="*60 + "\n")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Error during data generation: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
