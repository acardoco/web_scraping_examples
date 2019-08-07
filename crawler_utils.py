import calendar
import datetime
import os
import time
from random import randint

import numpy as np
import pandas as pd
from bs4 import BeautifulSoup
from pandas.io.common import EmptyDataError
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

import utils.variables_globales as var

import utils.db as db



estaciones = ['ABRANTES', 'ALBUFEIRA DO CAIA', 'ALBUFEIRA DO MARANHÃO', 'ALBUFEIRA DO ROXO',
            'BARCELOS', 'BARRAGEM DE CASTELO BURGÃES', 'BARRAGEM DE MAGOS',  'CELA',
            'FOLGARES', 'GRÂNDOLA', 'HERDADE DE VALADA', 'MARTIM LONGO', 'MOINHOLA', 'MONCHIQUE', 'PONTE DA BARCA',
            'RIO TORTO', 'SÃO BRÁS DE ALPORTEL', 'SÃO JULIÃO DO TOJAL', 'VIANA DO ALENTEJO', 'VIDIGAL']
concellos_con_2017_completo = ['beja', 'albufeira', 'loule', 'amadora', 'cascais', 'lisboa', 'oeiras',
                                              'ponta-delgada', 'elvas', 'maia', 'matosinhos', 'paredes', 'porto',
                                              'povoa-de-varzim', 'santo-tirso', 'trofa', 'valongo', 'vila-do-conde',
                                              'vila-nova-de-gaia', 'abrantes', 'tomar', 'torres-novas', 'almada']
concellos_sin_2017_completo = ['espinho', 'oliveira-de-azemeis', 'ovar', 'santa-maria-da-feira', 'vale-de-cambra',
                               'leiria', 'marinha-grande', 'nazare', 'pombal', 'mafra', 'sintra', 'torres-vedras',
                               'barreiro', 'setubal']

concellos_con_historico = ['beja', 'albufeira', 'loule', 'amadora', 'cascais', 'lisboa', 'oeiras',
                                              'ponta-delgada', 'elvas', 'maia', 'matosinhos', 'paredes', 'porto',
                                              'povoa-de-varzim', 'santo-tirso', 'trofa', 'valongo', 'vila-do-conde',
                                              'vila-nova-de-gaia', 'abrantes', 'tomar', 'torres-novas', 'almada',
                           'espinho', 'oliveira-de-azemeis', 'ovar', 'santa-maria-da-feira', 'vale-de-cambra',
                           'leiria', 'marinha-grande', 'nazare', 'pombal', 'mafra', 'sintra', 'torres-vedras',
                           'barreiro', 'setubal'
                           ]
#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
# cuando son dias o meses < que 10 no se pone el 0 delante (ejemplo 1/1/2018).
# Esta funcion solventa esa problematica
def check_fecha(numero):

    if numero < 10:
        return '0' + str(numero)
    else:
        return str(numero)
#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
# devuelve un calendario con los 365 dias
def get_calendario(year):

    return pd.date_range(start='1/1/' + year, end='31/12/' + year, periods=365) #TODO ojito años bisiestos
#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
# devuelve un calendario con los dias del mes
def get_calendario_by_mes(year, mes, dias_que_tiene_el_mes):

    return pd.date_range(start='1/'+ str(mes) + '/' + year, end=str(dias_que_tiene_el_mes) + '/'+ str(mes) + '/' + year, periods=dias_que_tiene_el_mes)
#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
def filter_word(word):

    filtered = word.lower()
    filtered = filtered.replace('á', 'a')\
        .replace('é', 'e')\
        .replace('í', 'i')\
        .replace('ó', 'o')\
        .replace('ú', 'u')\
        .replace('â', 'a')\
        .replace('ê', 'e')\
        .replace('î', 'i')\
        .replace('ô', 'o')\
        .replace('û', 'u')\
        .replace('ã', 'a')\
        .replace('à', 'a')\
        .replace(' ', '-')\
        .rstrip()

    return filtered
#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
def filter_concellos(concellos):
    concellos_factura = [x.lower() for x in concellos]
    concellos_factura = [x.replace('á', 'a')
                             .replace('é', 'e')
                             .replace('í', 'i')
                             .replace('ó', 'o')
                             .replace('ú', 'u')
                             .replace('â', 'a')
                             .replace('ê', 'e')
                             .replace('î', 'i')
                             .replace('ô', 'o')
                             .replace('û', 'u')
                             .replace('ã', 'a')
                             .replace('à', 'a')  # e.g. Freixo Espada à Cinta
                             .replace(' ', '-')
                             .rstrip() for x in concellos_factura]

    return concellos_factura
#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
def ruido_temp_concellos_2017(txt_file, txt_out):

    rango_maximo_diferencia = 3

    print(txt_file)
    temperaturas = np.genfromtxt(txt_file, dtype={'names': ('concello', 'fecha', 'temp'),
                                               'formats': ('U20', 'i4', 'i4')},
                                 delimiter="\t",
                              encoding="latin-1")

    # Desde el 1 de Enero hasta el 8 de Mayo, inclusives
    anterior = temperaturas[0][2]
    for i in range(0, 128):
        ruido = randint(- 3, 3)
        temp_actual = temperaturas[i][2]
        temp_aplicar_ruido = temp_actual + ruido

        diferencia_con_anterior = abs(temp_aplicar_ruido - anterior)

        if abs(temp_actual - anterior) <= rango_maximo_diferencia: # para evitar bucles infinitos
            # control para que no se diferencien demasiado las temperaturas de un dia para otro
            while (diferencia_con_anterior > rango_maximo_diferencia):
                ruido = randint(- 3, 3)
                temp_aplicar_ruido = temp_actual + ruido

                diferencia_con_anterior = abs(temp_aplicar_ruido - anterior)

        anterior = temp_aplicar_ruido
        temperaturas[i][2] = temp_aplicar_ruido

    np.savetxt(txt_out,
               temperaturas,
               fmt='%s\t%s\t%s',
               encoding="latin-1",
               newline="\n")
#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
# en la pagina web de https://meteo.isep.ipp.pt el rango de años para escoger viene dado por estos numeros
def get_year_from_meteoisep(year):

    base = 1992
    web_year = int(year) - base

    return web_year
#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
# funcion para guardar temperaturas diarias a partir de la ultima fecha que se tenga
def get_temp_concello_for_historic_prevision(url, year, month):

    # quitar notificaciones
    options = Options()
    options.add_argument("--disable-notifications")
    options.add_argument('--ignore-certificate-errors')

    # no cargar imagenes y usar cache para cargar mas rapido las paginas
    prefs = {"profile.managed_default_content_settings.images": 2, 'disk-cache-size': 4096}
    options.add_experimental_option('prefs', prefs)

    # empezar a currar sin esperar a que cargue toda la pagina
    # [normal (cargar toda la pagina) | eager (interactivo) | none (no espera)] -> eager sigue en desarrollo
    '''caps = DesiredCapabilities().CHROME
    caps["pageLoadStrategy"] = var.Chrome_pageLoadStrategyMode'''

    # Selenium driver
    driver = webdriver.Chrome(var.CHROME_DRIVER, chrome_options=options)
    driver.get(url)
    driver.maximize_window()
    wait = WebDriverWait(driver, 20)

    espera = 4
    time.sleep(espera)

    # cerrar cookies
    cookies = wait.until(
        EC.presence_of_element_located((By.ID, "sendOpGdpr")))
    cookies.click()


    fechas = []

    if (driver.title == 'Error 404 Not Found. - tempo.pt'):  # si no  tiene histórico

        print('Sin histórico: ' + url)

    else:
        time.sleep(espera)

        # pestaña del resumen mensual
        elem = wait.until(
            EC.presence_of_element_located((By.ID, "tipoResumen_1")))
        elem.click()
        time.sleep(espera)

        if month != datetime.datetime.today().month:

            # se clickea en el icono de calendario
            elem_icon_calendario = wait.until(
                EC.presence_of_element_located((By.ID, "datos_calendario_month")))
            elem_icon_calendario.click()
            time.sleep(espera)

            # mes que toque
            mes = 'month' + str(month)
            elemento_mes = wait.until(
                EC.presence_of_element_located((By.ID, mes)))
            elemento_mes.click()

            time.sleep(espera)

        # crawler
        soup = BeautifulSoup(driver.page_source, 'lxml')

        # como hay dias en los que no hay datos, se pone la temperatura media en tales casos
        temp_media = driver.find_element_by_id('mes_temp_media').text

        table = soup.find('table', attrs={'class': 'h-pred d1'})
        table_body = table.find('tbody')

        rows = table_body.find_all('tr')
        dias_fin_crawlear = len(rows)

        # se coje las temperaturas medias de cada DIA
        for j in range(1, dias_fin_crawlear + 1):

            dia = 'd' + str(j) + '_ini'
            tr = soup.find('tr', {"class": dia})

            # si no hay registro de ese dia, se rellena con la temperatura media del mes
            if tr == None:
                temp = (temp_media.replace('°C', '')).strip()
            else:
                td_list = tr.find_all("td")
                temp = td_list[1].text
                temp = (temp.replace('°C', '')).strip()

            # ---------------------------------------
            fecha = str(year) + \
                    check_fecha(month) + \
                    check_fecha(j)

            fechas.append([fecha, temp])
            # ---------------------------------------

    driver.close()

    return fechas

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
# Para cuando se caiga la BD, para seguir teniendo los concellos y distritos
def get_concellos_excel_distrito(filename, distrito):

    dataframe = pd.read_excel(filename)

    dataframe = dataframe.loc[
        (dataframe['distrito'] == distrito)]

    concellos_list = []

    for distrito, concello in zip(dataframe['distrito'], dataframe['concello']):

        elemento = [distrito, concello]
        concellos_list.append(elemento)

    return np.asarray(concellos_list)
#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
def read_temp(txt_name):

    try:
        temperaturas_provincia = pd.read_csv(txt_name,
                                             sep="\t",
                                             header=None)
    except EmptyDataError:
        temperaturas_provincia = pd.DataFrame()

    return temperaturas_provincia
#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
def filtered_to_normal_distrito(distrito_filtered):

    if distrito_filtered == 'lisboa':
        distrito = 'Lisboa'
    if distrito_filtered == 'generico':
        distrito = 'Genérico'
    if distrito_filtered == 'setubal':
        distrito = 'Setúbal'
    if distrito_filtered == 'aveiro':
        distrito = 'Aveiro'
    if distrito_filtered == 'porto':
        distrito = 'Porto'
    if distrito_filtered == 'leiria':
        distrito = 'Leiria'

    return distrito
#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
def get_fechas_by_month(year, month):

    num_dias_del_mes = calendar.monthrange(year, month)[1]

    fechas = []
    horas = []
    for dia in range(1, num_dias_del_mes + 1):

        horas_del_dia = 24
        fecha = str(year) + check_fecha(month) + check_fecha(dia)

        if fecha in var.lista_adelanto_horas:
            horas_del_dia -=1
        elif fecha in var.lista_retraso_horas:
            horas_del_dia +=1

        fecha = int(fecha)
        for hora in range(1, horas_del_dia + 1):
            fechas.append(fecha)
            horas.append(hora)

    return np.asarray(fechas), np.asarray(horas)

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
def columna_a_empezar_prevision_demanda_ren(driver, fecha_datetime):

    numero_de_columnas = len(driver.find_elements_by_xpath(
        '//*[@id="ctl00_ctl14_g_96459a04_7c84_4bf2_97a7_9ae2e9b5047f"]/div[2]/div/table/tbody/tr[2]/th'))

    celdita_columna = -1
    for dia_columna in range(2, numero_de_columnas):
        ruta_columna_dia_ren = '//*[@id="ctl00_ctl14_g_96459a04_7c84_4bf2_97a7_9ae2e9b5047f"]/div[2]/div/table/tbody/tr[2]/th[' \
                               + str(dia_columna) + ']'

        texto_columna = driver.find_element_by_xpath(ruta_columna_dia_ren).text
        dia_ren = texto_columna.split(' ')[0]
        if int(dia_ren) == fecha_datetime.day:
            celdita_columna = dia_columna
            break

    return celdita_columna
#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
def dias_a_traerse_prev_demanda(driver, today, tomorrow, dias_del_mes):

    numero_de_columnas = len(driver.find_elements_by_xpath(
        '//*[@id="ctl00_ctl14_g_96459a04_7c84_4bf2_97a7_9ae2e9b5047f"]/div[2]/div/table/tbody/tr[2]/th'))

    # check celdita maxima
    ruta_columna_dia_max_ren = '//*[@id="ctl00_ctl14_g_96459a04_7c84_4bf2_97a7_9ae2e9b5047f"]/div[2]/div/table/tbody/tr[2]/th[' +\
        str(numero_de_columnas) + ']'
    texto_columna_dia_max = driver.find_element_by_xpath(ruta_columna_dia_max_ren).text
    dia_max_ren = int(texto_columna_dia_max.split(' ')[0])

    num_dias_a_traerse = dia_max_ren - today

    # si se pasa del rango del mes
    if dia_max_ren < tomorrow.day:
        # buscamos por todas las columnas el ultimo dia del mes
        for dia_columna in range(2, numero_de_columnas):
            ruta_columna_dia_max_ren = '//*[@id="ctl00_ctl14_g_96459a04_7c84_4bf2_97a7_9ae2e9b5047f"]/div[2]/div/table/tbody/tr[2]/th[' \
                                   + str(dia_columna) + ']'

            texto_columna_dia_max = driver.find_element_by_xpath(ruta_columna_dia_max_ren).text
            dia_max_ren = int(texto_columna_dia_max.split(' ')[0])
            if dia_max_ren == dias_del_mes:
                num_dias_a_traerse = dia_max_ren - today
                break

    return num_dias_a_traerse
#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
def get_options_selenium_to_faster_download(path_absoluto):
    options = webdriver.ChromeOptions()
    # Fuente: https://cs.chromium.org/chromium/src/chrome/common/pref_names.cc
    options.add_experimental_option("prefs", {
        "download.default_directory": path_absoluto,  # fichero donde descargar las cosas
        "download.prompt_for_download": False,# con esto evitamos que salga la ventanita para pedir permiso de descarga al user
        "download.directory_upgrade": True,  # notificamos a chrome que se ha cambiado el directorio de descarga
        "safebrowsing.enabled": True  # Disable SafeBrowsing checks for files coming from trusted URLs when false
    })

    return options
#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
# empieza en 00
def get_calendario_by_cuartos(horas):

    array = []
    valores_cuarto =['00', '15', '30', '45']

    for hora in range(0, horas):

        for cuarto in valores_cuarto:

            array.append(check_fecha(hora) + ':' + cuarto)

    return array
#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
# para el crawler de temperaturas horarias
def add_horas_quefalten(lista):

    hora_que_deberia_tocar = 0
    nueva_lista = []

    for ele in lista:

        fecha = ele[0]
        hora = int(fecha.split(':')[1])

        # se han comido hora_que_deberia_tocar
        if hora > hora_que_deberia_tocar:

            temp_anterior = 0
            temp_siguiente = 0
            out_of_range = False

            # controles para que no se vaya del rango
            if hora_que_deberia_tocar - 1 >= 0:
                temp_anterior = int(lista[hora_que_deberia_tocar - 1][1])
            else:
                out_of_range = True
            if hora_que_deberia_tocar + 1 < len(lista):
                temp_siguiente = int(lista[hora_que_deberia_tocar + 1][1])
            else:
                out_of_range = True

            if out_of_range == True:
                division = 1
            else:
                division = 2

            # hacemos media entre la anterior y la siguiente
            temp_hora_que_falta = (temp_anterior + temp_siguiente)/division
            elemento_que_falta = [fecha[:-2] + check_fecha(hora_que_deberia_tocar), temp_hora_que_falta]
            nueva_lista.append(elemento_que_falta)
            hora_que_deberia_tocar += 2
        else:
            hora_que_deberia_tocar += 1

        nueva_lista.append(ele)

    return nueva_lista
#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
# datetime -> yyyymmdd
def get_fecha(now_datetime):

    return str(now_datetime.year) + check_fecha(now_datetime.month) + check_fecha(now_datetime.day)

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
# ------------ testing -----------
