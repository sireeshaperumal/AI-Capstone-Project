** AI Capstone Project**

This repository contains the full workflow for the AI Capstone assessment:  
- SQL schema, seed, and reporting queries on raw data  - CSV files provided
- Python scripts for cleaning, EDA (Exploratory Data Analysis), and visualization  
- Narrative generation (online via Gemini API or offline fallback)

---

## 📋 **Prerequisites**

- **Software**
  - Python 3.10+  
  - MySQL (Workbench or CLI)  or equvalent SQL engine)
  - Git (optional, for version control)

- **Python packages**
  Install required libraries:

  ```bash
  pip install pandas matplotlib google-genai

Data

data/customers.csv

data/products.csv

data/orders.csv

🗄️ SQL Setup

HOW TO - Create schema

After creating a database <database_name> run the below to:

1. Create schema

mysql -u <user> -p < database_name > < sql/schema.sql

2. Load Seed Data

mysql -u <user> -p < database_name > < sql/seed_data.sql

3. Run Reports

mysql -u <user> -p < database_name > < sql/reports.sql

📊 Python Analysis

1. Clean and EDA

How to run (Command Prompt) : python analysis/clean_and_eda.py

What It Does:

Cleans the raw data

Performs exploratory analysis

Writes narrator/findings.json (Task 5, Part 2)

2. Visualize

How to run (Command Prompt): python analysis/visualize.py

What it Does: Generates plots in the visualizations folder

📝 **Narrative Generation**

The narrative is produced from narrator/findings.json.

Option 1: Online (Gemini API)

Set your API key as an environment variable:

Linux/macOS

export GOOGLE_API_KEY="your_api_key_here"

Windows (cmd)

set GOOGLE_API_KEY=your_api_key_here

**How to run (cmd line)**

python narrator/generate_narrative.py

Parameters are programmatically set - temperature=0.0, max_output_tokens=5000, timeout=15

Returns a structured dict with "status": "success" and the narrative text

You may have to change the model in the code if it isn't supported at your end

Option 2: Offline Fallback
If no API key is set or the API call fails:

How to run (cmd line): 
python narrator/generate_narrative.py

Runs a deterministic template generator

Produces the same SCR structure with all required figures

Guarantees reproducibility with zero configuration

✅ Reproducibility

By following the steps above top to bottom, a reader can:

Recreate the schema and seed data

Run the raw reports

Clean and analyze the data

Generate visualizations

Produce narrator/findings.json

Generate the SCR narrative (online or offline)

Every number in the brief is reproducible from this workflow.





   


