import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder

path = r"C:\Users\lmutu\Downloads\911.csv\911.csv"
df = pd.read_csv(path)

def parse_timestamp(ts):
    if pd.isna(ts):
        return pd.NaT
    try:
        return pd.to_datetime(ts, format='%Y-%m-%d @ %H:%M:%S')
    except:
        pass
    try:
        return pd.to_datetime(ts, format='%Y-%m-%d %H:%M:%S')
    except:
        return pd.NaT

if 'timeStamp' in df.columns:
    df['incident_datetime'] = df['timeStamp'].apply(parse_timestamp)
else:
    raise SystemExit('timeStamp missing')

if 'zip' in df.columns:
    df['zip'] = df['zip'].fillna('').astype(str).str.strip().replace(['', 'nan', 'NaN', 'none'], np.nan)
if 'twp' in df.columns:
    df['twp'] = df['twp'].fillna('').astype(str).str.strip().str.upper().replace(['', 'NAN', 'NONE'], np.nan)

if 'lat' in df.columns and 'lng' in df.columns:
    df['lat_clean'] = df['lat'].clip(df['lat'].quantile(0.01), df['lat'].quantile(0.99))
    df['lng_clean'] = df['lng'].clip(df['lng'].quantile(0.01), df['lng'].quantile(0.99))
    coords = df[['lat_clean', 'lng_clean']].dropna()
    from sklearn.cluster import KMeans, DBSCAN
    kmeans = KMeans(n_clusters=20, random_state=42, n_init=10)
    df.loc[coords.index, 'location_cluster'] = kmeans.fit_predict(coords[['lat_clean', 'lng_clean']].values)
    dbscan = DBSCAN(eps=0.01, min_samples=10)
    df.loc[coords.index, 'density_cluster'] = dbscan.fit_predict(coords[['lat_clean', 'lng_clean']].values)
    df['distance_from_center'] = np.sqrt((df['lat_clean'] - df['lat_clean'].median())**2 + (df['lng_clean'] - df['lng_clean'].median())**2)

if 'twp' in df.columns:
    le_township = LabelEncoder()
    df['township_code'] = le_township.fit_transform(df['twp'].fillna('UNKNOWN'))
    township_counts = df['twp'].value_counts()
    high_risk_townships = township_counts[township_counts >= township_counts.quantile(0.8)].index
    df['is_high_risk_township'] = df['twp'].isin(high_risk_townships).astype(int)
if 'zip' in df.columns and df['zip'].notna().any():
    le_zip = LabelEncoder()
    df['zip_code'] = le_zip.fit_transform(df['zip'].fillna('UNKNOWN').astype(str))

for col in ['hour', 'day_of_week', 'month', 'quarter', 'week_of_year']:
    df[col] = getattr(df['incident_datetime'].dt, col)

if 'hour' in df.columns:
    df['is_weekend'] = df['day_of_week'].isin([5,6]).astype(int)
    df['is_rush_hour'] = df['hour'].isin([7,8,9,16,17,18]).astype(int)
    df['is_night'] = df['hour'].isin([22,23,0,1,2,3,4,5]).astype(int)
    df['is_morning_peak'] = df['hour'].isin([6,7,8,9]).astype(int)
    df['is_evening_peak'] = df['hour'].isin([16,17,18,19]).astype(int)
    df['is_lunch_hour'] = df['hour'].isin([12,13]).astype(int)
    df['is_holiday_season'] = df['month'].isin([11,12]).astype(int)
    df['weekend_rush_hour'] = df['is_weekend'] * df['is_rush_hour']
    df['night_weekend'] = df['is_night'] * df['is_weekend']
    df['month_hour'] = df['month'] * df['hour'] / 12
    df['cluster_hour'] = df['location_cluster'] * df['hour'] / 23

for col in ['hourly_incident_rate', 'township_incident_rate', 'hour_township_rate']:
    df[col] = 0.0

feature_cols = ['lat_clean','lng_clean','hour','day_of_week','month','quarter','week_of_year','is_weekend','is_rush_hour','is_night','is_morning_peak','is_evening_peak','is_lunch_hour','is_holiday_season','location_cluster','density_cluster','distance_from_center','township_code','is_high_risk_township','zip_code','hourly_incident_rate','township_incident_rate','hour_township_rate','weekend_rush_hour','night_weekend','month_hour','cluster_hour']
print(df[feature_cols].dtypes)
print(df[feature_cols].isna().sum())
