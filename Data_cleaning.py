import streamlit as st
import plotly.express as px
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
import os
import warnings


#file uploading 
def load_files(folder_path):

    df_list = []

    for file in os.listdir(folder_path):

        file_path = os.path.join(r"E:\PRODUCT_CARNIBALIZATION_DASHBOARD\PRODUCT_CARNIBALIZATION_DASHBOARD\raw_data", file)

        try:

            if file.endswith(".csv"):
                df = pd.read_csv(file_path)

            elif file.endswith(".xlsx"):
                df = pd.read_excel(file_path)
            elif file.endswith('.js'):
                df=pd.read_json(file_path)
            elif file.endswith('.txt'):
                df=pd.read_table(file_path)

            else:
                continue

            df['source_file'] = file
            df_list.append(df)

            print(f"{file} loaded successfully")

        except Exception as e:
            print(f"Error loading {file}: {e}")

    return pd.concat(df_list, ignore_index=True)

#reading of file 
df = load_files(r"E:\PRODUCT_CARNIBALIZATION_DASHBOARD\PRODUCT_CARNIBALIZATION_DASHBOARD\raw_data")


#data cleaning and preprocessing
df['START_DATE'] = pd.to_datetime(df['START_DATE'], errors='coerce')
df['END_DATE'] = pd.to_datetime(df['END_DATE'], errors='coerce')


#feature engineering

def add_promotion_features(df):
    # Promotion Duration
    df['Promo_Duration'] = (df['END_DATE'] - df['START_DATE']).dt.days

    # Discount Percentage
    df['Calculated_Discount'] = (df['Price with VAT'] - df['Promo Price with VAT']) / df['Price with VAT'] * 100

    # Price Reduction
    df['Price_Reduction'] = df['Price with VAT'] - df['Promo Price with VAT']

    # Discount Depth
    df['Discount_Depth'] = df['Saving'] / df['Price with VAT'] 

    # Price Category
    df['Price_Category'] = pd.qcut(df['Price with VAT'], q=4, labels=['Low', 'Medium', 'High', 'Premium'])

    # Calculated Discount Category
    df['Calculated_Discount_catrgory'] = pd.qcut(df['Calculated_Discount'], q=3, labels=['Low', 'High', 'Premium'])

    # Promotion Month
    df['Promo_Month'] = df['START_DATE'].dt.month

    return df

df = add_promotion_features(df)

#corrected depth and labels
def add_depth_and_labels(df):
    offer_mapping = {
        'BUY 2 GET 1 FREE ': 0.33,
        'BUY 1 GET 1 FREE ': 0.50,
        'BUY 2 GET 2 FREE ': 0.50,
        'BUY 1 GET 1 WITH PERCENT OFF 30': 0.15,
        'BUY 1 GET 1 WITH PERCENT OFF 40': 0.20,
        'BUY 1 GET 1 WITH PERCENT OFF 50': 0.25,
        'BUY 1 GET 1 WITH PERCENT OFF 60': 0.30,
        'BUY 1 GET 1 WITH PERCENT OFF 70': 0.35,
        'BUY 1 GET 2 FREE ': 0.67,
        '(B/G) BUY 2 GET 1 FREE ': 0.33
    }

    brand_mapping = {
        'Accez': 'PL', 'Active Go': 'PL', 'Alfoshan': 'PL', 'ALmisan': 'PL', 'AURI': 'PL',
        'Babygee': 'PL', 'Babywell': 'PL', 'Beatswell': 'PL', 'Bibi': 'PL', 'Bio-Synergy': 'PL',
        'Blade': 'PL', 'Body Spa': 'PL', 'BODYLICIOUS': 'PL', 'Boutique': 'PL', 'Citizen': 'PL',
        'Clary': 'PL', 'Clevie': 'PL', 'Clevie Derma': 'PL', 'Connect': 'PL', 'COXIR': 'PL',
        'Creigtons': 'PL', 'Davids': 'PL', 'Emotion': 'PL', 'Eric Favre': 'PL', 'Febella': 'PL',
        'First Aids Kit': 'PL', 'Footness': 'PL', 'Fragrances For Her': 'PL', 'Fruit Works': 'PL',
        'Gamar': 'PL', 'Grit': 'PL', 'I Kuzma': 'PL', 'Kaiyang': 'PL', 'Keller': 'PL', 'Killys': 'PL',
        'Mades': 'PL', 'Martini': 'PL', 'Medex': 'PL', 'Molfix': 'PL', 'Movera': 'PL', 'Movera Ortho': 'PL',
        'Movera Sport': 'PL', 'MUVU': 'PL', 'Nahdi': 'PL', 'NUTSHELL': 'PL', 'OE': 'PL', 'OnCall': 'PL',
        'Orex': 'PL', 'Parsa': 'PL', 'Parsa Beauty': 'PL', 'Qure': 'PL', 'Rosal': 'PL', 'Sanotact': 'PL',
        'Shadez': 'PL', 'True Honey': 'PL', 'Velveta': 'PL', 'Viora': 'PL', 'Yunmai': 'PL', 'Yuwell': 'PL', 'ZAK': 'PL'
    }

    # Vectorized mapping (faster and cleaner than df.apply)
    df["corrected_Depth%"] = df["OFFER TYPE"].map(offer_mapping).fillna(df["Depth%"])
    df['Promo_Risk_Score'] = df['corrected_Depth%'] * df['Promo_Duration']
    df["LABELS"] = df["Item Brand"].map(brand_mapping).fillna('OTHERS')

    return df

df = add_depth_and_labels(df)

# 1. Save the file to CSV
df.to_csv(r"processed_data.csv", index=False)

# 2. Keep your working dataframe as df (or assign a new name if needed)
df_cleaned_data = df.copy()
