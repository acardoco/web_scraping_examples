'''

** Este crawler saca la temperatura HORARIA PASADA en el mes y año deseados

'''

import calendar
import datetime
from bs4 import BeautifulSoup

import numpy as np
import pandas as pd
import os

import utils.common_utilities as utiles
import utils.variables_globales as var

from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver import DesiredCapabilities
from selenium.webdriver.chrome.options import Options
import time

#//*[@id="wt-his"]/tbody/tr[44]/th
#//*[@id="wt-his"]/tbody/tr[48]/th
#//*[@id="wt-his"]/tbody/tr[47]/th

#//*[@id="wt-his"]/tbody/tr[1]/th
#//*[@id="wt-his"]/tbody/tr[47]/th
#//*[@id="wt-his"]/tbody/tr[24]/th
# temps
#//*[@id="wt-his"]/tbody/tr[1]/td[2]
#//*[@id="wt-his"]/tbody/tr[2]/td[2]
base_url = 'https://www.timeanddate.com/weather/'

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
def get_previsiones_by_distrito(distrito, month, year):

    distrito = distrito.lower()
    if distrito == 'lisboa':
        distrito = 'lisbon'

    # construimos la url
    pagina_web = base_url + 'portugal/' + distrito + '/historic?month=' + str(month) + '&year=' + str(year)

    # quitar notificaciones
    options = Options()
    options.add_argument("--disable-notifications")

    # no cargar imagenes y usar cache para cargar mas rapido las paginas
    prefs = {"profile.managed_default_content_settings.images": 2, 'disk-cache-size': 4096}
    options.add_experimental_option('prefs', prefs)

    # empezar a currar sin esperar a que cargue toda la pagina
    caps = DesiredCapabilities().CHROME
    caps["pageLoadStrategy"] = "none"  # complete

    # Selenium driver
    driver = webdriver.Chrome(var.CHROME_DRIVER, chrome_options=options, desired_capabilities=caps)
    driver.get(pagina_web)
    driver.maximize_window()

    espera = 2
    time.sleep(espera)

    lista_temp = []
    base_dia_url = '/html/body/div[1]/div[7]/section[2]/div[5]/div[3]/a['

    num_dias_del_mes = calendar.monthrange(year, month)[1]
    for dia in range(1, num_dias_del_mes + 1, 1):

        lista_temp_dia = []

        fecha = str(year) + utiles.check_fecha(month) + utiles.check_fecha(dia)

        # nos metemos en el dia
        dia_url = driver.find_element_by_xpath(base_dia_url + str(dia) +']')
        dia_url.click()

        time.sleep(espera)

        # y empezamos a preparar el surfeo por el cuerpo de horas
        num_horas_disponibles = len(driver.find_elements_by_xpath('//*[@id="wt-his"]/tbody/tr'))
        base_hora_url = '//*[@id="wt-his"]/tbody/tr['
        end_hora_url = ']/th'

        hora_actual = 0 # Como hay veces que aparece "12:00" y su media hora "12:30"
        acumulador_hora_actual = 0 # acumulo las veces que pase eso (maximo dos)
        acumulador_temp_actual = 0 # y de la temp acumulado saco la media (div entre maximo dos)

        for hora in range(1, num_horas_disponibles + 1, 1):

            am_pm = '-'
            # la hora puede venir "12:00 am" o simplemente "0:00"
            ruta_hora = base_hora_url + str(hora) + end_hora_url
            texto_hora = driver.find_element_by_xpath(ruta_hora).text
            hora_original = texto_hora.split(' ')[0]
            if len(texto_hora.split(' ')) > 1:
                am_pm = texto_hora.split(' ')[1]
                am_pm = am_pm[:2]
            hora_sin_minutos = int(hora_original.split(':')[0])

            # control am/pm
            if am_pm == 'am' and hora_sin_minutos == 12:
                hora_sin_minutos = 0
            if am_pm == 'pm' and hora_sin_minutos < 12:
                hora_sin_minutos += 12

            ruta_temp = '//*[@id="wt-his"]/tbody/tr[' + str(hora) + ']/td[2]'
            temp = driver.find_element_by_xpath(ruta_temp).text
            temp_sin_signo = int(temp.split(' ')[0])

            if hora_actual == hora_sin_minutos:
                acumulador_temp_actual += temp_sin_signo
                acumulador_hora_actual += 1

            # se almacena lo que tenga esa hora (se hace la media si venia con xx:30)
            if hora_actual != hora_sin_minutos or hora == num_horas_disponibles:
                temp_media = acumulador_temp_actual/ acumulador_hora_actual
                fila_actual = [fecha + ':' + utiles.check_fecha(hora_actual), temp_media]

                # guardamos
                lista_temp_dia.append(fila_actual)

                if hora < num_horas_disponibles:
                    # actualizamos contadores
                    hora_actual = hora_sin_minutos
                    acumulador_hora_actual = 1
                    acumulador_temp_actual = temp_sin_signo

        # CHECK de las horas que FALTEN
        lista_temp_dia_controlada = utiles.add_horas_quefalten(lista_temp_dia)

        # añadimos las horas del dia
        for ele in lista_temp_dia_controlada:
            lista_temp.append(ele)


    time.sleep(espera)

    driver.close()

    return lista_temp
#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
def get_temp_horarias_pasadas(month, year):


    for distrito in var.DISTRITOS_PARA_TEMP_HORARIA_PASADA:
        # *****************************************************************************************************************
        # *****************************************************************************************************************
        # 1- se crea/accede el DIRECTORIO donde estarian las temperaturas del distrito
        mydate = datetime.datetime(year, month, 1)
        mes = mydate.strftime("%B")

        directory = 'excel/temp_horarias_pasadas/' + str(year) + '/' + str(mes) + '/'

        # si el directorio no existe, se crea
        if not os.path.exists(directory):
            os.makedirs(directory)

        excel_name = directory + distrito + '.xlsx'

        # si el fichero no existe, se crea
        if not os.path.exists(excel_name):
            file = open(excel_name, 'w+')
            file.close()

        # *****************************************************************************************************************
        # *****************************************************************************************************************
        # 2- se traen las temperaturas  horarias pasadas
        lista_temp_horarias = np.asarray(get_previsiones_by_distrito(distrito, month, year))

        # y se guardan en excel
        df_lista_temp_horarias = pd.DataFrame(lista_temp_horarias, columns=['hora', 'temp'])
        df_lista_temp_horarias['temp'] = pd.to_numeric(df_lista_temp_horarias["temp"])

        df_lista_temp_horarias.to_excel(excel_name, index=False)

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
'''get_temp_horarias_pasadas(3, 2018)
get_temp_horarias_pasadas(4, 2018)
get_temp_horarias_pasadas(5, 2018)'''
#get_temp_horarias_pasadas(12, 2017)