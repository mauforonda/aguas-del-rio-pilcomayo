#!/usr/bin/env python3

import requests
import pandas as pd
from bs4 import BeautifulSoup
import re
import argparse
import datetime as dt
from tqdm import tqdm

"""
run as:

run --cookie YOUR-OWN-AUTHENTICATED-PHPSSID-COOKIE
"""

def get_cookie() -> str:
    """
    Parses the PHPSESSID cookie from the --cookie command flag
    """
    
    parser = argparse.ArgumentParser(prog="miniminiflux")
    parser.add_argument(
        "--cookie",
        dest="cookie",
        help="The PHPSESSID cookie you get after authenticating on the portal",
        type=str,
        required=True
    )
    args = parser.parse_args()
    return args.cookie

def list_stations() -> pd.core.frame.DataFrame:
    """
    Retrieves the list of stations
    """
    
    def extract_station(ref:str) -> str:
        return re.findall('\'([^\']*)\'', ref)

    URL = 'https://www.pilcomayo.net/modulos/reportes/calidad_aguas/php/ver_calidad_aguas_preview_v2.php'
    COLUMNS = ['latitud', 'longitud', 'id_syscali01']
    cookies = {'PHPSESSID': cookie}
    # Any valid station IDs will work
    data = {
        'rela_syspubl01': '272',
        'id_syscali01': '364',
    }

    response = requests.post(URL, cookies=cookies, data=data)
    references = re.findall('mostrar_puntos_calidad_aguas\([^\)]*\)', response.text)
    stations = pd.DataFrame([extract_station(ref) for ref in references], columns=COLUMNS)
    print(f'{stations.shape[0]} stations')
    
    return stations

def get_station(id_syscali01:int):

    def parse_station(html:BeautifulSoup) -> dict:
        """
        Parses a station's records
        """
        
        station = parse_metadata(html)
        for table in html.select('table')[1:]:
            station.update(parse_measurements(table))
        return station

    def parse_metadata(html:BeautifulSoup) -> dict:
        """
        Extracts and parses station metadata
        """
        
        htmlTable = html.select('table')[0]
        table = extract_table(htmlTable)
        return {**parse_title(html), **parse_table(table)}

    def extract_table(table, columns=4):
        """
        Extract values from a table
        """

        return [
            [field.get_text() for field in row.select('td')] 
            for row in table.select('tr')[1:] 
            if len(row.select('td')) == columns]

    def parse_title(html:BeautifulSoup) -> dict:
        """
        Extract a station's name
        """
        
        return {'Nombre': html.select('h3')[0].get_text().strip().replace('Datos de ', '')}

    def parse_table(table:list) -> dict:
        """
        Format values from a table
        """
        
        data = {}
        for row in table:
            data[row[0].strip()] = row[1]
            data[row[2].strip()] = row[3]
        return data

    def parse_measurements_table(table:list) -> dict:
        """
        Parses a table of measurements
        """
        
        data = {}
        for row in table:
            data[f'{row[0].strip()} ({row[1].strip()})'] = row[2].strip()
        return data

    def parse_measurements(table):
        """
        Extracts and parses a table of measurements
        """
        
        return parse_measurements_table(extract_table(table)[1:])
    
    def fetch_station(id_syscali01:int) -> dict:

        URL = 'https://www.pilcomayo.net/modulos/reportes/calidad_aguas/php/ver_calidad_agua_reporte.php'
        cookies = {'PHPSESSID': cookie}
        params = {'id_syscali01': id_syscali01}

        response = requests.get(URL, params=params, cookies=cookies)
        html = BeautifulSoup(response.text, 'html.parser')
        return html

    station_html = fetch_station(id_syscali01)
    station_data = parse_station(station_html)
    return station_data

def save(df:pd.core.frame.DataFrame, filename:str):
    df.to_csv(f'data/{filename}', index=False)

def clean_data(df:pd.core.frame.DataFrame) -> pd.core.frame.DataFrame:
    """
    Formats most values, especially numerical ones, 
    and sets column order and names
    """

    def format_measurement(measurement) -> float:
        """
        Formats measurements
        """
        if type(measurement) == str:
            return float(re.sub('\<|\>', '', measurement))
        else:
            return measurement

    def format_datetime(row:pd.core.series.Series) -> dt.datetime:
        """
        Formats datetimes
        """
        
        return dt.datetime.strptime(f'{row["Fecha de Muestreo"]} {row["Hora de Muestreo"]}', '%d-%m-%Y %H:%M Hs')

    def format_feature(feature) -> float:
        """
        Formats station features
        """
        
        if type(feature) == str:
            if 'sin datos' in feature.lower():
                return None
            else:
                numbers = re.findall('[0-9\.]+', feature)
                if numbers:
                    return float(numbers[0])
                else:
                    return None
        else:
            return feature

    # Columns starting from the 14th are measurements
    for col in df.columns[14:]:
        df[col] = df[col].apply(format_measurement)

    # Make proper datetime objects
    timestamps = df[['Fecha de Muestreo', 'Hora de Muestreo']].apply(format_datetime, axis=1)
    df.insert(0, 'fecha', timestamps)

    # Format values in these metadata columns
    for col in ['Altura', 'Velocidad media', 'Caudal']:
        df[col] = df[col].apply(format_feature)

    # Fix column order and names
    metadata_columns = ['id_syscali01', 'Nombre', 'Responsable', 'Campaña','fecha', 'latitud', 'longitud', 'Río:', 'Altura', 'Velocidad media', 'Caudal']
    measurement_columns = df.columns[14:].tolist()
    selected_columns =  metadata_columns + measurement_columns
    column_names = ['id', 'nombre', 'responsable', 'campaña', 'fecha', 'latitud', 'longitud', 'rio', 'altura (msnm)', 'velocidad_media (m/s)', 'caudal (m3/s)'] + df.columns[14:].str.lower().str.strip().tolist()
    df = df[selected_columns]
    df.columns = column_names

    return df

if __name__ == "__main__":

    data = []
    cookie = get_cookie()
    stations = list_stations()
    for i, row in tqdm(stations.iterrows(), total=stations.shape[0]):
        station_data = get_station(row['id_syscali01'])
        data.append({**row.to_dict(), **station_data})

    df = pd.DataFrame(data)
    save(df, 'mediciones.csv')
    clean = clean_data(df)
    save(clean, 'mediciones_procesadas.csv')
