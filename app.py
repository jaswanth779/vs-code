from flask import Flask, render_template, request, jsonify, send_file
import pandas as pd

app = Flask(__name__)

# Load Excel data
file_path = 'ASSEMBLY INVOICE STATUS.xlsx'
df = pd.read_excel(file_path)

# Debugging: Print the columns in the loaded DataFrame
print("Available columns in DataFrame:", df.columns)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/invoices')
def invoices():
    discoms = df['Discom'].dropna().unique().tolist()
    assemblers = df['Assembler'].dropna().unique().tolist()
    statuses = df['Status'].dropna().unique().tolist()  # Get unique statuses
    columns = [col for col in df.columns if col != 'S.No']  # Exclude 'S.No' from columns
    return render_template('invoices.html', discoms=discoms, assemblers=assemblers, statuses=statuses, columns=columns, active_page='invoices')

@app.route('/filter_data', methods=['POST'])
def filter_data():
    # Retrieve selected filter values from the request
    selected_discom = request.json.get('discom')
    selected_assembler = request.json.get('assembler')
    selected_status = request.json.get('status')  

    # Filter the data based on selections
    filtered_df = df
    if selected_discom:
        filtered_df = filtered_df[filtered_df['Discom'] == selected_discom]
    if selected_assembler:
        filtered_df = filtered_df[filtered_df['Assembler'] == selected_assembler]
    if selected_status: 
        filtered_df = filtered_df[filtered_df['Status'] == selected_status]
        
    # Drop the 'S.No' column if it exists
    if 'S.No' in filtered_df.columns:
        filtered_df = filtered_df.drop(columns=['S.No'])    

    # Convert the filtered data to JSON for the frontend, and add an auto-generated 'S.No' column
    filtered_data = filtered_df.to_dict(orient='records')
    for idx, item in enumerate(filtered_data, start=1):
        item['S.No'] = idx  # Auto-generate 'S.No' starting from 1

    return jsonify(filtered_data)

@app.route('/invoice_pdfs')
def invoice_pdfs():
    assemblers = df['Assembler'].dropna().unique().tolist()
    return render_template('invoice_pdfs.html', assemblers=assemblers, active_page='invoice_pdfs')

@app.route('/filter_invoices', methods=['POST'])
def filter_invoices():
    selected_assembler = request.json.get('assembler')
    print("Selected assembler:", selected_assembler)

    try:
        # Filter the DataFrame based on assembler and get invoice numbers
        filtered_df = df[df['Assembler'] == selected_assembler] if selected_assembler else df
        invoice_numbers = filtered_df['Invoice no'].dropna().tolist()
        print("Filtered invoice numbers:", invoice_numbers)

        return jsonify(invoice_numbers)
    except Exception as e:
        print("Error in filter_invoices:", e)
        return jsonify({"error": str(e)}), 500

@app.route('/download_invoice/<invoice_no>')
def download_invoice(invoice_no):
    filename = f'static/images/{invoice_no}.pdf'
    try:
        return send_file(filename)
    except FileNotFoundError:
        print(f"File not found: {filename}")
        return "File not found", 404
    except Exception as e:
        print("Error in download_invoice:", e)
        return "Internal server error", 500

@app.route('/download_table', methods=['POST'])
def download_table():
    selected_discom = request.json.get('discom')
    selected_assembler = request.json.get('assembler')

    # Filter the DataFrame based on the selected filters
    filtered_df = df
    if selected_discom:
        filtered_df = filtered_df[filtered_df['Discom'] == selected_discom]
    if selected_assembler:
        filtered_df = filtered_df[filtered_df['Assembler'] == selected_assembler]

    # Drop the 'S.No' column if it exists, as it's auto-generated on the frontend
    if 'S.No' in filtered_df.columns:
        filtered_df = filtered_df.drop(columns=['S.No'])

    # Create a CSV file from the filtered DataFrame
    output_file = 'filtered_invoices.csv'
    filtered_df.to_csv(output_file, index=False)

    return send_file(output_file, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
