# E-Commerce Medallion Data Pipeline

Built an end-to-end data pipeline to process raw e-commerce sales data and turn it into clean, analysis-ready datasets.

The project follows the Medallion Architecture (Bronze → Silver → Gold), using PostgreSQL for raw data storage, PySpark for data cleaning, and DuckDB for analytical processing.

### What I Worked On

- Loaded raw e-commerce sales data into PostgreSQL.
- Used PySpark to remove duplicate records, filter invalid quantities, and standardize data types.
- Stored cleaned data in DuckDB for further analysis.
- Created Gold-layer datasets for daily sales and product category performance using SQL.
- Built an interactive dashboard using Streamlit and Plotly.
- Worked with Apache Airflow and Docker for pipeline orchestration.

### Data Processing Results

| Dataset | Records |
|---|---:|
| Raw sales data | 12,180 |
| Cleaned sales data | 11,814 |
| Daily sales aggregates | 829 |
| Category performance | 8 |

### Tech Stack

`Python` `PostgreSQL` `PySpark` `Pandas` `DuckDB` `SQL` `Apache Airflow` `Docker` `Streamlit` `Plotly`

### Dashboard Preview
<img width="1917" height="1000" alt="image" src="https://github.com/user-attachments/assets/7986e643-48cc-4dce-ad25-b854c155bcb8" />

