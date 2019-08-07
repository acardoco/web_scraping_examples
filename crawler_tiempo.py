'''

Recupera de una pagina web llamada www.tempo.pt temperaturas y las guardas en txt por concello

'''
from bs4 import BeautifulSoup

import numpy as np
import pandas as pd

import utils.common_utilities as utiles
import utils.variables_globales as var

from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time


initial_year = 2019

concellos_file = 'excel\\concellos.xlsx'

mes_inicial = 1 # mes desde el que comenzar a mirar/crawlear: 1 es Enero (incluido)
meses_a_crawlear = 6 # 12 para el año completo, 1 para enero solo

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
# Comprueba qué concellos tienen el historial de 2017 completo para todos los meses (especialmente desde Enero a Abril, inclusive)
def has_complete_historic_for_2017(url):
    # quitar notificaciones
    options = Options()
    options.add_argument("--disable-notifications")

    # Selenium driver
    driver = webdriver.Chrome(var.CHROME_DRIVER, chrome_options=options)
    driver.get(url)
    driver.maximize_window()
    wait = WebDriverWait(driver, 10)

    # cerrar cookies
    cookies = wait.until(
        EC.presence_of_element_located((By.ID, "sendOpGdpr")))
    cookies.click()

    espera = 1
    time.sleep(espera)

    if (driver.title == 'Error 404 Not Found. - tempo.pt'):  # si no  tiene histórico

        print('Sin histórico: ' + url)
        # se cierra el driver
        driver.close()
        return -1

    else:
        time.sleep(5)

        # pestaña del resumen mensual
        elem = wait.until(
            EC.presence_of_element_located((By.ID, "tipoResumen_1")))
        elem.click()
        time.sleep(espera)

        # se clickea en el icono de calendario
        elem_icon_calendario = wait.until(
            EC.presence_of_element_located((By.ID, "datos_calendario_month")))
        elem_icon_calendario.click()
        time.sleep(espera)

        # se situa en el año 2017
        elem_pre_mes = wait.until(
            EC.presence_of_element_located((By.ID, "prev-mes")))
        elem_pre_mes.click()
        time.sleep(espera)
        elem_pre_mes.click()
        time.sleep(espera)

        # mes de ABRIL
        elemento_mes = wait.until(
            EC.presence_of_element_located((By.ID, 'month4')))

        # se mira si no tiene historico
        if elemento_mes.get_attribute("class") == 'month-td calendar-inactive':
            # se cierra el driver
            driver.close()
            return 0
        else:
            # se cierra el driver
            driver.close()
            return 1

    driver.close()

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
def get_concellos_sin_historico_completo_2017():

    concellos_distritos = get_concellos_excel(concellos_file)
    concellos_old = [x[1] for x in concellos_distritos]
    concellos = utiles.filter_concellos(concellos_old)

    lista_concellos_sin_historico_completo_2017 = []

    for i in range(0, len(concellos)):

        concello = concellos[i]

        if concello not in utiles.concellos_sin_historico:

            base_url = 'https://www.tempo.pt/'
            end_url = '-sactual.htm'
            url = base_url + concello + end_url

            resultado = has_complete_historic_for_2017(url)

            # si NO tiene historico completo en 2017
            if resultado == 0:
                lista_concellos_sin_historico_completo_2017.append(concello)

            time.sleep(5)
    print(lista_concellos_sin_historico_completo_2017)

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
# Para cuando se caiga la BD, para seguir teniendo los concellos y distritos
def get_concellos_excel(filename):

    dataframe = pd.read_excel(filename)

    concellos_list = []

    for distrito, concello in zip(dataframe['distrito'], dataframe['concello']):

        elemento = [distrito, concello]
        concellos_list.append(elemento)

    return np.asarray(concellos_list)

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
# ------------------- OBTIENE LA TEMP HISTORICA DE LOS MUNICIPIOS DE PORTUGAL----------------------
 # TODO despues de crawlear varios concellos, suele dar error de que no encuentre X elemento -> ir a
 # utilities -> concellos_con_historico Y borrar los concellos ya scrapeados
def navigate_web(concello, url, calendario, fDistrito):

    # quitar notificaciones
    options = Options()
    options.add_argument("--disable-notifications")

    # Selenium driver
    driver = webdriver.Chrome(var.CHROME_DRIVER, chrome_options=options)
    driver.get(url)
    driver.maximize_window()
    wait = WebDriverWait(driver, 100)

    # cerrar cookies
    cookies = wait.until(
        EC.presence_of_element_located((By.ID, "sendOpGdpr")))
    cookies.click()

    espera = 1
    time.sleep(espera)

    if (driver.title == 'Error 404 Not Found. - tempo.pt'): # si no  tiene histórico

        print('Sin histórico: ' + url)

    else:
        time.sleep(5)

        # pestaña del resumen mensual
        elem = wait.until(
            EC.presence_of_element_located((By.ID, "tipoResumen_1")))
        elem.click()
        time.sleep(espera)

        # variable para controlar si hay datos de un mes (caso primeros 4 meses 2017)
        has_no_month = False

        # ------inicializacion--------

        # se clickea en el icono de calendario
        elem_icon_calendario = wait.until(
            EC.presence_of_element_located((By.ID, "datos_calendario_month")))
        elem_icon_calendario.click()
        time.sleep(espera)

        #se situa en el año
        for veces in range(0, (initial_year - calendario[0].year)):
            elem_pre_mes = wait.until(
                EC.presence_of_element_located((By.ID, "prev-mes")))
            elem_pre_mes.click()
            time.sleep(espera)

        # MESES
        contador_dia_mes = 0
        for i in range(mes_inicial, meses_a_crawlear + 1):

            # mes que toque
            mes = 'month' + str(i)
            elemento_mes = wait.until(
                EC.presence_of_element_located((By.ID, mes)))

            time.sleep(espera)

            # para situarse en el año que se pida
            if has_no_month == True:
                time.sleep(espera)
                for veces in range(0, (2018 - calendario[0].year)):
                    elem_pre_mes.click()
                    time.sleep(espera)

            # si no hay datos del mes, se coge del 2018 (en este año siempre hay datos)
            if elemento_mes.get_attribute("class") == 'month-td calendar-inactive':
                for veces in range(0, (2018 - calendario[0].year)):
                    next_mes = wait.until(
                        EC.presence_of_element_located((By.ID, 'next-mes')))
                    next_mes.click()
                    time.sleep(espera)

                elemento_mes.click()
                has_no_month = True

            else:
                elemento_mes.click()
                has_no_month = False

            time.sleep(2)

            # crawler
            soup = BeautifulSoup(driver.page_source, 'lxml')

            # dias del mes
            #row_count = len(driver.find_elements_by_xpath("//table[@id='rmes']/tbody/tr"))
            dias_del_mes = calendario.days_in_month[contador_dia_mes] + 1

            # como hay dias en los que no hay datos, se pone la temperatura media en tales casos
            temp_media = driver.find_element_by_id('mes_temp_media').text

            #se coje las temperaturas medias de cada DIA
            for j in range(1, dias_del_mes):

                dia = 'd' + str(j) + '_ini'
                tr = soup.find('tr', {"class": dia})

                # si no hay registro de ese dia, se rellena con la temperatura media del mes
                if tr == None:
                    temp = (temp_media.replace('°C', '')).strip()
                else:
                    td_list = tr.find_all("td")
                    temp = td_list[1].text
                    temp = (temp.replace('°C', '')).strip()

                fecha = str(calendario[contador_dia_mes].year) +\
                        utiles.check_fecha(calendario[contador_dia_mes].month) + \
                        utiles.check_fecha(calendario[contador_dia_mes].day)

                fila = concello + '\t' +\
                    fecha + '\t' +\
                    temp + '\n'

                print(fila)
                fDistrito.write(fila)

                contador_dia_mes += 1

            # se clickea en el icono de calendario de nuevo
            elem_icon_calendario = wait.until(
                EC.presence_of_element_located((By.ID, "datos_calendario_month")))
            elem_icon_calendario.click()
            time.sleep(espera)

    driver.close()
#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
# Almacena por concello
def get_temp_offline(year):

    concellos_distritos = get_concellos_excel(concellos_file)
    concellos_old = [x[1] for x in concellos_distritos]
    concellos = utiles.filter_concellos(concellos_old)

    calendario = utiles.get_calendario(year)

    for i in range(0, len(concellos)):

        concello = concellos[i]

        if concello in utiles.concellos_con_historico:

            print('CONCELLO:' + concello)

            txt_name = 'txt/temperaturas/' + year + '/' + concellos[i] + '.txt'
            fDistrito = open(txt_name, "w+")


            base_url = 'https://www.tempo.pt/'
            end_url = '-sactual.htm'
            url = base_url + concello + end_url

            navigate_web(concellos_old[i], url, calendario, fDistrito)
            time.sleep(5)

            fDistrito.close()
#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
# Modifica las temperaturas entre enero y 8 de mayo de 2017 para los concellos que no tienen esos datos en la web
def add_ruido_2017():

    concellos_distritos = get_concellos_excel(concellos_file)
    concellos_old = [x[1] for x in concellos_distritos]
    concellos = utiles.filter_concellos(concellos_old)

    for i in range(0, len(concellos)):

        concello = concellos[i]

        if concello in utiles.concellos_sin_2017_completo:

            txt_name = 'txt/temperaturas/2017/' + concello + '.txt'
            # (input_txt, output_txt)
            utiles.ruido_temp_concellos_2017(txt_name, txt_name)
#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
def get_temp_porto(year):

    pagina_web = 'https://meteo.isep.ipp.pt/gauges'

    # Selenium driver
    driver = webdriver.Chrome(var.CHROME_DRIVER)
    driver.get(pagina_web)
    driver.maximize_window()
    wait = WebDriverWait(driver, 15)

    espera = 1
    time.sleep(espera)

    # pestaña del resumen mensual
    xpath_relatorios = '/html/body/app-root/div/div/mat-toolbar/mat-nav-list/a[6]'
    elem = wait.until(
        EC.presence_of_element_located((By.XPATH, xpath_relatorios)))
    elem.click()
    time.sleep(espera)

    # seleccionar anho
    xpath_box_year = '//*[@id="mat-select-2"]/div/div[1]/span/span'
    elem = wait.until(
        EC.presence_of_element_located((By.XPATH, xpath_box_year)))
    elem.click()
    time.sleep(espera)

    # AQUI SE PILLA EL AÑO
    web_year = utiles.get_year_from_meteoisep(year)
    xpath_year = '//*[@id="mat-option-'+ str(web_year) + '"]/span'
    elem = wait.until(
        EC.presence_of_element_located((By.XPATH, xpath_year)))
    elem.click()
    time.sleep(espera)

    # Ya leyendo las TEMPERATURAS
    calendario = utiles.get_calendario('2016')
    temperaturas_diarias = []
    for dia in calendario:
        row = dia.day
        celdita = dia.month + 1

        path_celdita = '/html/body/app-root/div/mat-sidenav-container/mat-sidenav-content/app-relat/div/mat-table[1]/mat-row[' +\
            str(row) + ']/mat-cell[' + str(celdita) + ']'

        # Se redondea la temperatura
        temp = driver.find_element_by_xpath(path_celdita).text
        temp = temp.replace(',', '.')
        temp = float(temp)
        temp = round(temp)

        fecha = str(dia.year) + utiles.check_fecha(dia.month) + utiles.check_fecha(dia.day)

        temperaturas_diarias.append((fecha, temp))

    # se guarda en txt
    np.savetxt('txt/temperaturas/distrito\\' + year + '\\' + 'porto' + '.txt',
               temperaturas_diarias,
               fmt='%s\t%s',
               encoding="latin-1",
               newline="\n")

    driver.close()
#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
# get_temp_offline('2018')
# get_temp_offline('2017')
# get_concellos_sin_historico_completo_2017()
# add_ruido_2017()
# ------------------- testing ----------
'''utiles.ruido_temp_concellos_2017('txt/temperaturas/2017/espinho.txt',
                                 'txt/temperaturas/2017/espinho-TEST.txt')'''

#get_temp_porto('2016')

# quitando el ruido
# get_temp_offline('2017')
#get_temp_offline('2019')