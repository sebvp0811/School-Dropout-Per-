# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np

# Calcular la edad al 30 de junio del año actual
def calcular_edad(month_born, year_born, current_year):
   if month_born <= 6:  # Nacidos entre enero y junio
       return current_year - year_born
   else:  # Nacidos entre julio y diciembre
       return current_year - year_born - 1

def dropout(M3, M4, df_icrp, data_ubigeo):
    
    data_ubigeo = data_ubigeo[["Ubigeo", "Departamento"]].rename(columns=
                                                                 {'Ubigeo': 'UBIGEO', 'Departamento': 'DEPARTAMENTO'})
    
    M4 = M4[["DOMINIO", "CONGLOME", "VIVIENDA", "HOGAR", "UBIGEO", "CODPERSO", "P400A1", "P400A2", "P400A3"]]

    M4['edadjuni'] = M4.apply(lambda row: calcular_edad(row['P400A2'], row['P400A3']), axis=1)

    M3 = M3[["DOMINIO", "CONGLOME", "VIVIENDA", "HOGAR", "UBIGEO", "CODPERSO", "P301A", "P306", "MES"]]

    df_d = pd.merge(M3, M4, on=("CODPERSO", "CONGLOME", "VIVIENDA", "HOGAR", "UBIGEO"), how="inner")

    # DESERCION PRIMARIA
    df_d["DESERCIÓN_PRIMARIA"] = np.where(((df_d['P301A'] == 3) &
                                           (df_d['MES'] >= 4) &
                                           (df_d['edadjuni'] >= 7) &
                                           (df_d['edadjuni'] <= 14)), 1, 0)

    # DESERCION SECUNDARIA
    df_d["DESERCIÓN_SECUNDARIA"] = np.where(((df_d['P301A'] == 5) &
                                             (df_d['MES'] >= 4) &
                                             (df_d['edadjuni'] >= 13) &
                                             (df_d['edadjuni'] <= 19)), 1, 0)

    df_d["Desercion_2023"] = df_d["DESERCIÓN_PRIMARIA"] + df_d["DESERCIÓN_SECUNDARIA"]

    data = pd.merge(df_d, data_ubigeo, on="UBIGEO", how="left")
    data = data.loc[:, ["Desercion_2023", "DEPARTAMENTO"]]

    # Realizar operaciones de resumen
    resumen_desercion = data.groupby("DEPARTAMENTO")["Desercion_2023"].sum().reset_index()
    conteo_dpto = data.groupby('DEPARTAMENTO').size().reset_index(name='Total')
    resumen_desercion["Total"] = conteo_dpto["Total"]

    # Sumar las filas correspondientes a "Callao" en la columna "Desercion"
    suma_desercion_callao = resumen_desercion.loc[resumen_desercion['DEPARTAMENTO'] == 'Callao', 'Desercion_2023'].sum()
    suma_total_callao = resumen_desercion.loc[resumen_desercion['DEPARTAMENTO'] == 'Callao', 'Total'].sum()

    # Crear una copia de las filas de "Lima" y asignarle la suma de deserción de "Callao"
    filas_lima = resumen_desercion.loc[resumen_desercion['DEPARTAMENTO'] == 'Lima'].copy()
    filas_lima['Desercion_2023'] += suma_desercion_callao
    filas_lima['Total'] += suma_total_callao

    # Concatenar las filas de "Lima" modificadas con las filas originales de "Callao" y "Lima"
    resumen_desercion = pd.concat([resumen_desercion.loc[resumen_desercion['DEPARTAMENTO'] != 'Callao'], filas_lima]).reset_index(drop=True)
    resumen_desercion = resumen_desercion.loc[:, ["Desercion_2023", "Total", "DEPARTAMENTO"]]

    # Calcular la proporción Deserción/Total para el año actual
    resumen_desercion["Proporción_2023"] = resumen_desercion["Desercion_2023"] / resumen_desercion["Total"]

    # Combina las bases de datos df_icrp y resumen_desercion usando la columna DEPARTAMENTO
    df_final = pd.merge(df_icrp, resumen_desercion, on="DEPARTAMENTO", how="inner", indicator=True)
   
    return df_final

    
