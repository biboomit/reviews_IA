# Resumen del Sistema
# El código implementa un sistema automatizado de monitoreo de estrategias publicitarias que:
# Funcionalidades Principales:

# 🔍 Extracción Automática: Usa Selenium para extraer anuncios de Facebook Ad Library
# 🤖 Análisis con IA: Emplea GPT-4 para analizar estrategias publicitarias y colores dominantes
# 📊 Almacenamiento Estructurado: Guarda todo en BigQuery para análisis histórico
# 📈 Detección de Cambios: Identifica cambios significativos en estrategias publicitarias
# 📋 Reportes Automáticos: Genera reportes detallados de cambios estratégicos

# Flujo de Trabajo:

# Primera ejecución: Procesa todos los anuncios encontrados
# Ejecuciones posteriores: Solo procesa anuncios nuevos y compara con históricos
# Análisis diferencial: Detecta cambios en tono, colores, estrategias y audiencias objetivo

# Casos de Uso:

# Monitoreo competitivo: Seguimiento de estrategias de competidores
# Análisis de tendencias: Evolución de estrategias publicitarias en el tiempo
# Business Intelligence: Datos estructurados para dashboards y análisis predictivo

# DIAGRAMA DE FLUJO https://www.mermaidchart.com/raw/badef755-bb79-458f-99eb-57b677d4eab0?theme=light&version=v0.1&format=svg

import os
import time
import json
import pandas as pd
from datetime import datetime
import re
import streamlit as st
from google.cloud import bigquery
from google.oauth2 import service_account
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from openai import OpenAI
import shutil
import requests
from io import BytesIO
from PIL import Image
import numpy as np

# ---------- CONFIGURATION ----------
PAGE_ID = os.getenv("PAGE_ID", "105145991960464")
COUNTRY_CODE = "MX"
OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
ASSISTANT_ID = st.secrets["ASSISTANT_ID"]
BQ_PROJECT = "dimensiones"
BQ_DATASET = "boomt_ia"
BQ_TABLE = "ads_facebook"
CHECK_INTERVAL_HOURS = 48
SLACK_TOKEN = os.getenv("SLACK_TOKEN", "")  # Bot token de Slack
SLACK_CHANNEL = "#test-bi"  # Canal donde enviar alertas

# Initialize clients
credentials = service_account.Credentials.from_service_account_file(
    'key.json',
    scopes=["https://www.googleapis.com/auth/cloud-platform", 
            "https://www.googleapis.com/auth/drive", 
            "https://www.googleapis.com/auth/bigquery"]
)
bq_client = bigquery.Client(credentials=credentials, project=credentials.project_id)
openai_client = OpenAI(api_key=OPENAI_API_KEY)

# Setup paths
CHROMEDRIVER_PATH = shutil.which('chromedriver')
TEMP_IMG_DIR = os.getenv("TEMP_IMG_DIR", "/tmp/ads_images")
temp_dir = "temp_images"
os.makedirs(TEMP_IMG_DIR, exist_ok=True)
os.makedirs(temp_dir, exist_ok=True)

def get_bigquery_data(query):
    """Execute BigQuery query and return results as DataFrame"""
    try:
        return bq_client.query(query).to_dataframe()
    except Exception as e:
        print(f"BigQuery error: {e}")
        return pd.DataFrame()


def get_all_historical_ads(page_id):
    """Get all historical ads from BigQuery for a given page_id"""
    table_ref = f"{BQ_PROJECT}.{BQ_DATASET}.{BQ_TABLE}"
    query = f"""
        SELECT *
        FROM `{table_ref}`
        WHERE page_id = '{page_id}'
        ORDER BY start_date DESC
    """
    return get_bigquery_data(query)

def check_table_exists():
    """Check if the BigQuery table exists and has data"""
    table_ref = f"{BQ_PROJECT}.{BQ_DATASET}.{BQ_TABLE}"
    query = f"SELECT COUNT(*) as count FROM `{table_ref}`"
    result = get_bigquery_data(query)
    return False if result.empty else result['count'].iloc[0] > 0

def format_value_for_bigquery(value, target_type='TIMESTAMP'):
    """Format values to match BigQuery's expected types"""
    if isinstance(value, (datetime, pd.Timestamp)):
        if target_type == 'DATE':
            return value.strftime('%Y-%m-%d')
        elif target_type == 'TIMESTAMP':
            return value.isoformat(sep=' ')
    return value

def save_ads_to_bigquery(df_ads):
    """Save ads data to BigQuery"""
    if df_ads.empty:
        print("No data to save.")
        return

    # Ensure all required columns exist with proper values
    required_columns = {
        'ad_id': '',
        'page_id': PAGE_ID,
        'ad_text': '',
        'image_url': '',
        'start_date': None,
        'end_date': None,
        'is_active': True,
        'created_at': datetime.now(),
        'strategy_summary': None,
        'strategy_version': None,
        'gpt_analysis_date': None,
        'overall_strategy': None,
        'dominant_colors': None
    }

    for col, default_val in required_columns.items():
        if col not in df_ads.columns:
            df_ads[col] = default_val

    df_ads['page_id'] = PAGE_ID

    # Convert dates properly
    date_columns = {
        'start_date': 'DATE',
        'end_date': 'DATE',
        'created_at': 'TIMESTAMP',
        'gpt_analysis_date': 'TIMESTAMP'
    }
    
    for col, col_type in date_columns.items():
        if col in df_ads.columns:
            df_ads[col] = pd.to_datetime(df_ads[col], errors='coerce')
            df_ads[col] = df_ads[col].apply(lambda x: format_value_for_bigquery(x, col_type) if pd.notna(x) else None)

    # Convert 'dominant_colors' to string if it's a list
    if 'dominant_colors' in df_ads.columns:
        df_ads['dominant_colors'] = df_ads['dominant_colors'].apply(
            lambda x: ", ".join(x) if isinstance(x, list) else x
        )

    table_ref = f"{BQ_PROJECT}.{BQ_DATASET}.{BQ_TABLE}"
    records = df_ads.to_dict(orient='records')

    try:
        errors = bq_client.insert_rows_json(table_ref, records)
        if errors:
            print(f"Errors saving ads: {errors}")
        else:
            print(f"{len(records)} records successfully saved to BigQuery.")
    except Exception as e:
        print(f"Error saving to BigQuery: {e}")


def clear_temp_images():
    """Clear all temporary image files"""
    for file in os.listdir(temp_dir):
        try:
            file_path = os.path.join(temp_dir, file)
            if os.path.isfile(file_path):
                os.remove(file_path)
        except Exception as e:
            print(f"Error deleting {file_path}: {e}")

def extract_ads(country_code, page_id):
    """Extract ads from Facebook Ad Library using Selenium"""
    clear_temp_images()
    options = webdriver.ChromeOptions()
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_argument("--lang=en-US")

    driver = webdriver.Chrome(service=Service(CHROMEDRIVER_PATH), options=options)
    url = f"https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country={country_code}&view_all_page_id={page_id}&media_type=all"
    driver.get(url)
    WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.TAG_NAME, "body")))

    print("Loading ads (scrolling)...")
    # Scroll to load all ads with limit
    last_height = driver.execute_script("return document.body.scrollHeight")
    for attempt in range(20):  # Max 20 scroll attempts
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

    print("Extracting ad data...")
    ads = driver.find_elements(By.XPATH, "//div[contains(@class, 'x1plvlek')]")
    print(f"Found {len(ads)} ads to process")
    
    ads_list = []
    for index, ad in enumerate(ads):
        if index % 10 == 0:
            print(f"Processing ad {index+1}/{len(ads)}")
            
        # Extract ad details with error handling
        try:
            ad_id = ad.find_element(By.XPATH, ".//span[contains(text(), 'Library ID')]").text.split(':')[-1].strip()
        except:
            ad_id = f"unknown_{index}_{int(time.time())}"
            
        try:
            start_text = ad.find_element(By.XPATH, ".//span[contains(text(), 'Started running')]").text
            match = re.search(r"Started running on (.+)", start_text)
            start_date = datetime.strptime(match.group(1), "%b %d, %Y") if match else None
            start_date_str = start_date.strftime('%Y-%m-%d %H:%M:%S') if start_date else None
        except:
            start_date_str = None
            
        try:
            end_text = ad.find_element(By.XPATH, ".//span[contains(text(), 'Ended on')]").text
            match = re.search(r"Ended on (.+)", end_text)
            end_date = datetime.strptime(match.group(1), "%b %d, %Y") if match else None
            end_date_str = end_date.strftime('%Y-%m-%d %H:%M:%S') if end_date else None
        except:
            end_date_str = None
            
        is_active = end_date_str is None
            
        try:
            ad_text = ad.find_element(By.XPATH, ".//div[@style='white-space: pre-wrap;']/span").text.strip()
        except:
            try:
                ad_text = ad.find_element(By.XPATH, ".//div[contains(@class, 'x1iorvi4')]//span").text.strip()
            except:
                ad_text = None
            
        try:
            img_url = ad.find_element(By.XPATH, ".//img").get_attribute("src")
        except:
            img_url = None

        ads_list.append({
            "page_id": page_id,
            "ad_id": ad_id,
            "ad_text": ad_text,
            "image_url": img_url,
            "start_date": start_date_str,
            "end_date": end_date_str,
            "is_active": is_active,
            "created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "strategy_summary": None,
            "strategy_version": None,
            "gpt_analysis_date": None,
            "overall_strategy": None,  # Keeping overall_strategy without clustering
            "dominant_colors": None  # New field for color analysis
        })
    driver.quit()
    
    # Filter ads without text or image
    valid_ads = [ad for ad in ads_list if ad['ad_text'] or ad['image_url']]
    print(f"Of {len(ads_list)} extracted ads, {len(valid_ads)} have valid text or image")
    
    return pd.DataFrame(valid_ads)

def generate_ad_analysis_prompt(ad_text, image_url=None, overall_strategy=None):
    """Generate prompt for OpenAI to analyze an ad with overall strategy context and extract dominant colors."""
    text_content = ad_text if ad_text else "No text available"
    
    color_context = ""
    if image_url:
        color_context = f"\nAnalyze the dominant colors in the image at: {image_url}"
    
    strategy_context = ""
    if overall_strategy:
        strategy_context = f"\nOverall advertiser strategy context: {overall_strategy}"

    return f"""
Analyze this ad as an expert ad analyst.

Return ONLY a valid JSON object with these keys:
- "strategy_summary": brief phrase describing the ad's primary advertising strategy
- "strategy_version": a category or numerical identifier representing the strategy type/evolution
- "dominant_colors": dominant colors extracted from the ad's image URL

Example response:
{{
  "strategy_summary": "Generate urgency through time-limited benefits",
  "strategy_version": "v3-urgency",
  "dominant_colors": ["#FF5733", "#C70039", "#900C3F"]
}}

Ad text:
{text_content}

Image URL (description): {image_url if image_url else "Not available"}{color_context}{strategy_context}

Respond only with the JSON object. No additional text, titles, explanations or comments.
"""

def generate_overall_strategy(df_ads):
    """Generate overall strategy for all ads"""
    if df_ads.empty or 'ad_text' not in df_ads.columns:
        return df_ads
        
    # Prepare ad content for analysis
    ads_content = []
    for idx, ad in df_ads.iterrows():
        if pd.notna(ad['ad_text']) and ad['ad_text'].strip():
            ads_content.append(f"Ad {idx+1}: {ad['ad_text'][:300]}")
    
    if not ads_content:
        return df_ads
        
    all_ads_text = "\n\n".join(ads_content)
    
    prompt = f"""
    You are a marketing strategist analyzing Facebook ads. Analyze these ads and provide a concise 
    overall strategy summary that captures the advertiser's general approach.
    
    Ads to analyze:
    {all_ads_text}
    
    Provide ONLY a brief summary of the advertiser's general strategy across all ads in 1-2 sentences.
    """
    
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a marketing strategy expert."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=150
        )
        
        overall_strategy = response.choices[0].message.content.strip()
        
        # Apply overall strategy to all ads
        df_ads['overall_strategy'] = overall_strategy
        
        print(f"Generated overall strategy: {overall_strategy}")
        return df_ads
        
    except Exception as e:
        print(f"Error generating overall strategy: {e}")
        return df_ads


def analyze_ads_with_openai(df_ads):
    """Analyze ads with OpenAI and return enhanced dataframe"""
    if df_ads.empty:
        return df_ads

    df = df_ads.copy()
    df['page_id'] = PAGE_ID

    # First generate overall strategy
    df = generate_overall_strategy(df)
    
    total_ads = len(df)
    ads_with_text = df['ad_text'].notna().sum()

    print(f"Analyzing {ads_with_text} ads with text out of {total_ads} total...")

    for index, row in df.iterrows():
        ad_text = row['ad_text']
        image_url = row['image_url']
        ad_id = row['ad_id']
        overall_strategy = row.get('overall_strategy')

        if pd.isna(ad_text) or not ad_text.strip():
            df.at[index, 'strategy_summary'] = "No text to analyze"
            df.at[index, 'strategy_version'] = "n/a"
            df.at[index, 'dominant_colors'] = None
            df.at[index, 'gpt_analysis_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            continue

        if index % 5 == 0:
            print(f"Analyzing ad {index+1}/{total_ads} (ID: {ad_id})")

        prompt = generate_ad_analysis_prompt(ad_text, image_url, overall_strategy)

        for retry in range(3):  # Max 3 retries
            try:
                resp = openai_client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{
                        "role": "system", "content": "You are an expert in visual and strategic advertising analysis."
                    }, {
                        "role": "user", "content": prompt
                    }],
                    max_tokens=500
                )

                content = resp.choices[0].message.content
                if not content or not content.strip():
                    raise ValueError("Empty response from OpenAI.")
                    
                # Extract JSON from response
                match = re.search(r'\{.*\}', content, re.DOTALL)
                if not match:
                    raise ValueError("No JSON found in response.")
                    
                json_text = match.group(0)
                analysis = json.loads(json_text)

                # Update dataframe with analysis
                df.at[index, 'strategy_summary'] = analysis.get('strategy_summary')
                df.at[index, 'strategy_version'] = analysis.get('strategy_version')
                df.at[index, 'dominant_colors'] = analysis.get('dominant_colors')
                df.at[index, 'gpt_analysis_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                # Add any additional fields returned by the API
                for key, value in analysis.items():
                    if key not in df.columns:
                        df[key] = None
                    df.at[index, key] = value

                break  # Successful analysis
                
            except (json.JSONDecodeError, ValueError) as err:
                if retry == 2:  # Last retry
                    df.at[index, 'strategy_summary'] = f"Error: {str(err)[:100]}"
                    df.at[index, 'strategy_version'] = None
                    df.at[index, 'dominant_colors'] = None
                    df.at[index, 'gpt_analysis_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                time.sleep(2)
                
            except Exception as e:
                df.at[index, 'strategy_summary'] = f"Error: {str(e)[:100]}"
                df.at[index, 'strategy_version'] = None
                df.at[index, 'dominant_colors'] = None
                df.at[index, 'gpt_analysis_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                break

        # Rate limit prevention
        time.sleep(1)

    analyzed_count = df[df['strategy_summary'].notna()].shape[0]
    print(f"Analysis completed: {analyzed_count}/{total_ads} ads successfully analyzed")

    return df

def detect_strategy_shift(new_ads_df, historical_ads_df):
    """Detect if there's a significant shift in advertising strategy"""
    if new_ads_df.empty or historical_ads_df.empty:
        return {
            "has_significant_change": False,
            "report": "Insufficient data for comparison.",
            "change_level": "none"
        }
        
    # Prepare text samples for comparison
    old_texts = " ".join(historical_ads_df['ad_text'].dropna().astype(str).tolist())[:3000]
    new_texts = " ".join(new_ads_df['ad_text'].dropna().astype(str).tolist())[:3000]
    
    # Use strategies and analysis from both datasets
    old_strategies = ", ".join(historical_ads_df['strategy_summary'].dropna().astype(str).unique().tolist())
    new_strategies = ", ".join(new_ads_df['strategy_summary'].dropna().astype(str).unique().tolist())
    
    # Get color data from both datasets
    old_colors = [color for colors in historical_ads_df['dominant_colors'].dropna() for color in colors if colors]
    new_colors = [color for colors in new_ads_df['dominant_colors'].dropna() for color in colors if colors]
    
    # Prepare color information
    color_context = ""
    if old_colors and new_colors:
        old_colors_str = ", ".join(old_colors[:10])
        new_colors_str = ", ".join(new_colors[:10])
        color_context = f"""
Previous ad dominant colors:
{old_colors_str}

New ad dominant colors:
{new_colors_str}
        """
    
    # Include overall strategy data if available
    old_overall = historical_ads_df['overall_strategy'].dropna().astype(str).unique().tolist()
    new_overall = new_ads_df['overall_strategy'].dropna().astype(str).unique().tolist()
    
    overall_context = ""
    if old_overall and new_overall:
        overall_context = f"""
Previous overall strategy: 
{old_overall[0]}

New overall strategy:
{new_overall[0]}
        """
    
    prompt = f"""
You are an expert marketing analyst.

Previous ads - Identified strategies:
---
{old_strategies}

Previous ad text samples:
---
{old_texts}

New ads - Identified strategies:
---
{new_strategies}

New ad text samples:
---
{new_texts}

{color_context}
{overall_context}

Analyze for significant changes in communication strategy, examining:
1. Communication tone
2. Visual elements and color palette
3. Value proposition
4. Call-to-action approaches
5. Target audience indicators

IMPORTANT: Start your response with exactly one of these classifications:
- CHANGE_LEVEL: SIGNIFICANT (for major strategic shifts)
- CHANGE_LEVEL: MODERATE (for noticeable but not major changes)
- CHANGE_LEVEL: MINOR (for small variations)

Then provide your detailed analysis explaining the changes found and their potential strategic impact.
"""
    
    try:
        # Create a thread and run it with the OpenAI assistant
        thread = openai_client.beta.threads.create()
        openai_client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=prompt
        )
        
        run = openai_client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=ASSISTANT_ID
        )
        
        # Wait for completion (max 5 minutes)
        start_time = time.time()
        while run.status not in ["completed", "failed", "cancelled"]:
            if time.time() - start_time > 300:
                return {
                    "has_significant_change": False,
                    "report": "Timeout exceeded for strategy shift analysis.",
                    "change_level": "error"
                }
            time.sleep(5)
            run = openai_client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
            
        if run.status != "completed":
            return {
                "has_significant_change": False,
                "report": f"Strategy shift analysis error: {run.status}",
                "change_level": "error"
            }
        
        # Get the response
        messages = openai_client.beta.threads.messages.list(thread_id=thread.id)
        if not messages.data:
            return {
                "has_significant_change": False,
                "report": "No response received from strategy shift analysis.",
                "change_level": "error"
            }
            
        full_report = messages.data[0].content[0].text.value
        
        # Extract change level from the response
        change_level = "minor"
        has_significant_change = False
        
        if "CHANGE_LEVEL: SIGNIFICANT" in full_report:
            change_level = "significant"
            has_significant_change = True
        elif "CHANGE_LEVEL: MODERATE" in full_report:
            change_level = "moderate"
            has_significant_change = True
        elif "CHANGE_LEVEL: MINOR" in full_report:
            change_level = "minor"
            has_significant_change = False
            
        return {
            "has_significant_change": has_significant_change,
            "report": full_report,
            "change_level": change_level
        }
        
    except Exception as e:
        return {
            "has_significant_change": False,
            "report": f"Error in strategy shift analysis: {str(e)}",
            "change_level": "error"
        }
def send_slack_alert(strategy_report, new_ads_count, page_id):
    """Send Slack alert using Slack Bot Token when significant strategy change is detected"""
    if not SLACK_TOKEN:
        print("Warning: SLACK_TOKEN not configured. Skipping Slack notification.")
        return False
    
    # Prepare the message
    change_level = strategy_report.get("change_level", "unknown")
    report_text = strategy_report.get("report", "No report available")
    
    # Truncate report if too long for Slack
    if len(report_text) > 2800:
        report_text = report_text[:2750] + "...\n[Reporte truncado]"
    
    # Create Slack message payload using blocks
    slack_message = {
        "channel": SLACK_CHANNEL,
        "text": f"🚨 Cambio de Estrategia Publicitaria Detectado - Nivel: {change_level.upper()}",
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "🚨 Alerta: Cambio de Estrategia Publicitaria"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Página ID:*\n{page_id}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Nivel de Cambio:*\n{change_level.upper()}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Nuevos Anuncios:*\n{new_ads_count}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Fecha:*\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                    }
                ]
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Análisis Detallado:*\n```{report_text}```"
                }
            },
            {
                "type": "divider"
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": "Sistema de Monitoreo de Estrategias Publicitarias | Facebook Ad Library"
                    }
                ]
            }
        ]
    }
    
    # Slack API endpoint
    url = "https://slack.com/api/chat.postMessage"
    
    # Headers with Bearer token
    headers = {
        "Authorization": f"Bearer {SLACK_TOKEN}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(
            url,
            data=json.dumps(slack_message),
            headers=headers,
            timeout=10
        )
        
        response_data = response.json()
        
        if response.status_code == 200 and response_data.get("ok"):
            print("✅ Alerta enviada exitosamente a Slack")
            return True
        else:
            error_msg = response_data.get("error", "Unknown error")
            print(f"❌ Error enviando alerta a Slack: {error_msg}")
            return False
            
    except Exception as e:
        print(f"❌ Error enviando alerta a Slack: {str(e)}")
        return False
    
def main():
    print("Starting Facebook Ad Strategy Monitor...")

    # 1. Extract ads from Facebook Ad Library
    print(f"Extracting ads for page ID: {PAGE_ID}")
    scraped_ads = extract_ads(COUNTRY_CODE, PAGE_ID)
    
    if scraped_ads.empty:
        print("No ads found in Facebook Ad Library.")
        return
    
    # 2. Check if table exists with data
    table_has_data = check_table_exists()
    
    # 3. Process different scenarios based on existing data
    if not table_has_data:
        print("No data in BigQuery table. Processing all ads as new.")
        
        # Analyze all ads without clustering
        enhanced_ads = analyze_ads_with_openai(scraped_ads)
        
        # Save all analyzed ads
        save_ads_to_bigquery(enhanced_ads)
        print(f"Analyzed and saved {len(enhanced_ads)} new ads.")
        return
    
    # 4. Get historical ads from BigQuery
    historical_ads = get_all_historical_ads(PAGE_ID)
    
    if historical_ads.empty:
        print("No historical data for specified page. Processing all ads as new.")
        
        # Analyze all ads without clustering
        enhanced_ads = analyze_ads_with_openai(scraped_ads)
        
        # Save all analyzed ads
        save_ads_to_bigquery(enhanced_ads)
        print(f"Analyzed and saved {len(enhanced_ads)} new ads.")
        return
    
    # 5. Convert dates for comparison if needed
    if 'start_date' in historical_ads.columns and 'start_date' in scraped_ads.columns:
        for df in [historical_ads, scraped_ads]:
            if not pd.api.types.is_datetime64_any_dtype(df['start_date']):
                df['start_date'] = pd.to_datetime(df['start_date'], errors='coerce')
    
    # 6. Identify new ads using ad_id
    existing_ad_ids = set(historical_ads['ad_id'].dropna().astype(str).unique())
    new_ads = scraped_ads[~scraped_ads['ad_id'].astype(str).isin(existing_ad_ids)]
    
    if new_ads.empty:
        print("No new ads found.")
        return
    
    print(f"Found {len(new_ads)} new ads.")
    
    # 7. Analyze new ads with overall strategy generation
    enhanced_new_ads = analyze_ads_with_openai(new_ads)
    
    # 8. Save new ads with analysis to BigQuery
    save_ads_to_bigquery(enhanced_new_ads)
    print(f"Saved {len(enhanced_new_ads)} new ads to BigQuery.")
    
   # 9. Detect strategy shifts between historical and new ads
    print("Analyzing changes in advertising strategy...")
    strategy_shift_result = detect_strategy_shift(enhanced_new_ads, historical_ads)
    
    print("\n===== STRATEGY SHIFT REPORT =====")
    print(f"Change Level: {strategy_shift_result['change_level'].upper()}")
    print(f"Significant Change Detected: {strategy_shift_result['has_significant_change']}")
    print("\nDetailed Report:")
    print(strategy_shift_result['report'])
    print("=================================\n")
    
    # 10. Send Slack alert if significant change detected
    if strategy_shift_result['has_significant_change']:
        print("🚨 Significant strategy change detected! Sending Slack alert...")
        alert_sent = send_slack_alert(
            strategy_shift_result, 
            len(enhanced_new_ads), 
            PAGE_ID
        )
        
        if alert_sent:
            print("✅ Slack alert sent successfully")
        else:
            print("❌ Failed to send Slack alert")
    else:
        print("ℹ️  No significant strategy change detected. No alert sent.")
    
    print("Process completed successfully.")

if __name__ == "__main__":
    main()
