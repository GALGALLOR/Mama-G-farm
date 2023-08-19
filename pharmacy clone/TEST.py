def calculate_monthly_category_totals(data_list):
    monthly_category_totals = {}

    for row in data_list[1:]:  # Skip the header row assuming it's in index 0
        month = row[6]
        category = row[7]
        profit = float(row[9])  # Assuming profit is in column 9
        loss = float(row[10])   # Assuming loss is in column 10

        key = (month, category)

        if key not in monthly_category_totals:
            monthly_category_totals[key] = {'profit': 0.0, 'loss': 0.0}

        monthly_category_totals[key]['profit'] += profit
        monthly_category_totals[key]['loss'] += loss

    return monthly_category_totals

# Example Bank_data list (replace this with your actual data)
Bank_data = [
    ['Header1', 'Header2', 'Header3', 'Header4', 'Header5', 'Header6', 'Month', 'Category', 'Header9', 'Profit', 'Loss'],
    ['Data1', 'Data2', 'Data3', 'Data4', 'Data5', 'Data6', 'Jan', 'Category1', 'Data9', '100.0', '20.0'],
    ['Data1', 'Data2', 'Data3', 'Data4', 'Data5', 'Data6', 'Jan', 'Category2', 'Data9', '150.0', '30.0'],
    ['Data1', 'Data2', 'Data3', 'Data4', 'Data5', 'Data6', 'Jan', 'Category1', 'Data9', '120.0', '25.0'],
    ['Data1', 'Data2', 'Data3', 'Data4', 'Data5', 'Data6', 'Feb', 'Category1', 'Data9', '120.0', '25.0'],
    ['Data1', 'Data2', 'Data3', 'Data4', 'Data5', 'Data6', 'Feb', 'Category1', 'Data9', '120.0', '25.0'],
    ['Data1', 'Data2', 'Data3', 'Data4', 'Data5', 'Data6', 'Feb', 'Category1', 'Data9', '120.0', '25.0'],
    # Add more data rows as needed
]

monthly_category_totals = calculate_monthly_category_totals(Bank_data)

# Display the monthly and category-wise totals
for key, totals in monthly_category_totals.items():
    month, category = key
    print(f"Month: {month}, Category: {category}")
    print(f"Total Profit: {totals['profit']:.2f}")
    print(f"Total Loss: {totals['loss']:.2f}")
    print("-" * 20)
