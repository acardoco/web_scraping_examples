import time
import numpy as np
import pandas as pd
import datetime
from datetime import timedelta
import os
import calendar

import utils.common_utilities as utiles
import utils.variables_globales as var

from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException

base_url = 'http://www.centrodeinformacao.ren.pt/userControls/GetExcel.aspx?T=CRG&P='
end_url = '&variation=PT'

future_url = 'http://www.mercado.ren.pt/PT/Electr/InfoMercado/Consumo/PrevConsumo/Paginas/PrevConsDia.aspx'
verificada_url = 'http://www.mercado.ren.pt/PT/Electr/InfoMercado/Consumo/Paginas/Verif.aspx'

path_previsiones_iniciales_2019= "excel/perfiles_consumo_2019.xlsx"
path_previsiones_iniciales_2018= "excel/perfiles_consumo_2018.xlsx"

directory_to_download = 'temporales/'

celdita_hora_maxima = 26

lista_adelanto_horas = ['20150329', '20160327', '20170326', '20180325', '20190331']
lista_retraso_horas = ['20151025', '20161030', '20171029', '20181028', '20191027']

celdita_a_empezar_prevision_hoy = 3 #puede ser 4, a veces REN quita y pone la columna de la izquierda del toodo

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
def guardar_en_txt(dia,year, month, array_a_guardar):

    mydate = datetime.datetime(year, month, dia)
    mes = mydate.strftime("%B")

    directory = 'txt/demanda/' + str(year) + '/' + str(mes) + '/'

    # si el directorio no existe, se crea
    if not os.path.exists(directory):
        os.makedirs(directory)

    fecha = str(year) + utiles.check_fecha(month) + utiles.check_fecha(dia)
    txt_name = directory + fecha + '.txt'

    # si el fichero no existe, se crea
    if not os.path.exists(txt_name):
        file = open(txt_name, 'w+')
        file.close()

    # *****************************************************************************************************************
    # *****************************************************************************************************************
    # 3 - se guarda el fichero
    np.savetxt(txt_name, array_a_guardar,
               fmt='%s\t%s',
               delimiter='\n')

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
def save_prevision_a_futuro(year, month, dia_a_empezar):

    actual_year = datetime.date.today().year
    actual_month = datetime.date.today().month
    today = datetime.date.today().day
    num_dias_del_mes = calendar.monthrange(year, month)[1]

    if actual_year == year and actual_month >= month:
        tomorrow = datetime.datetime(actual_year, actual_month, today) + timedelta(days=1)
    else: # esto es para traerse meses siguientes
        tomorrow = datetime.datetime(year, month, dia_a_empezar)
        today = dia_a_empezar - 1
    # *****************************************************************************************************************
    # *****************************************************************************************************************
    # 1- Se cogen los consumos previstos de REN
    pagina_web = future_url

    # Selenium driver
    driver = webdriver.Chrome(var.CHROME_DRIVER)
    driver.get(pagina_web)
    driver.maximize_window()
    espera = 1
    time.sleep(espera)

    # surfeo por el html
    # check celdita columna a empezar (empieza en manhana incluido)
    celdita_columna = utiles.columna_a_empezar_prevision_demanda_ren(driver, tomorrow)

    if celdita_columna == -1:

        driver.close()

    else:
        # numero maximo de dias a traerse
        num_dias_a_traerse = utiles.dias_a_traerse_prev_demanda(driver, today, tomorrow, num_dias_del_mes)

        # seguimos surfeando
        ruta_base = '//*[@id="ctl00_ctl14_g_96459a04_7c84_4bf2_97a7_9ae2e9b5047f"]/div[2]/div/table/tbody/tr['
        ruta_intermedia = ']/td['
        ruta_final = ']'

        # el dia
        dia_a_guarda_en_txt = tomorrow.day
        for dia in range(celdita_columna, celdita_columna + num_dias_a_traerse):

            # dia dividido en cuartos
            calendario_dia = utiles.get_calendario_by_cuartos(24)
            contador_calendario_dia = 0

            #check cambio de hora
            hora_maxima = celdita_hora_maxima
            fecha = str(year) + utiles.check_fecha(month) + utiles.check_fecha(dia_a_guarda_en_txt)
            if fecha in lista_retraso_horas:
                hora_maxima = 27
                calendario_dia = utiles.get_calendario_by_cuartos(25)
            if fecha in lista_adelanto_horas:
                hora_maxima = 25
                calendario_dia = utiles.get_calendario_by_cuartos(23)

            consumos_cuartohorarios = []
            # la hora
            for hora in range(3, hora_maxima + 1):
                ruta_celdita_hora = ruta_base + str(hora) + ruta_intermedia + str(dia) + ruta_final
                consumo_celdita_hora = driver.find_element_by_xpath(ruta_celdita_hora).text

                # el cuarto
                for cuarto in range(0, 4):
                    cuarto_hora = calendario_dia[contador_calendario_dia + cuarto]
                    consumos_cuartohorarios.append((cuarto_hora, consumo_celdita_hora))

                contador_calendario_dia += 4

            # se GUARDA
            guardar_en_txt(dia_a_guarda_en_txt, year, month, consumos_cuartohorarios)

            dia_a_guarda_en_txt += 1

        driver.close()
#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
# BUSCA todos los dias hasta ayer incluido
def save_prevision_a_pasado_by_verificado(year, month, dia_a_empezar, dia_a_acabar):
    # *****************************************************************************************************************
    # *****************************************************************************************************************
    # 1- Se cogen los consumos previstos de REN para ayer
    pagina_web = verificada_url

    # Selenium driver
    driver = webdriver.Chrome(var.CHROME_DRIVER)
    driver.get(pagina_web)
    driver.maximize_window()
    wait = WebDriverWait(driver, 15)
    espera = 2
    time.sleep(espera)

    # se buscan todos los dias hasta ayer
    for dia in range(dia_a_empezar, dia_a_acabar): # excluye hoy

        # surfeo por el html
        # se cubre el campo
        campo_fecha = driver.find_element_by_id("ctl00_ctl14_g_5ee12aa8_2064_4404_b94d_7b6b4057473f_ctl04_foo")
        campo_fecha.clear()

        fecha_a_cubrir = str(year) + '-' + utiles.check_fecha(month) + '-' + utiles.check_fecha(dia)
        campo_fecha.send_keys(fecha_a_cubrir)

        # se clickea en la flecha
        xpath_flechita = '//*[@id="ctl00_ctl14_g_5ee12aa8_2064_4404_b94d_7b6b4057473f"]/div[1]/table/tbody/tr/td[1]/input[3]'
        elem = wait.until(
            EC.presence_of_element_located((By.XPATH, xpath_flechita)))
        elem.click()
        time.sleep(espera)

        # y leemos
        ruta_base = '//*[@id="ctl00_ctl14_g_5ee12aa8_2064_4404_b94d_7b6b4057473f_ctl15"]/tbody/tr['
        ruta_final = ']/td[2]'

        consumos_cuartohorarios = []
        # dia dividido en cuartos
        calendario_dia = utiles.get_calendario_by_cuartos(24)
        contador_calendario_dia = 0

        # check cambio de hora
        hora_maxima = celdita_hora_maxima
        fecha = str(year) + utiles.check_fecha(month) + utiles.check_fecha(dia)
        if fecha in lista_retraso_horas:
            hora_maxima = 27
            calendario_dia =utiles.get_calendario_by_cuartos(25)
        if fecha in lista_adelanto_horas:
            hora_maxima = 25
            calendario_dia = utiles.get_calendario_by_cuartos(23)

        # la hora
        for hora in range(3, hora_maxima + 1):
            ruta_celdita_hora = ruta_base + str(hora) + ruta_final

            # control de cambio de hora
            try:
                consumo_celdita_hora = driver.find_element_by_xpath(ruta_celdita_hora)
            except NoSuchElementException:
                break
            consumo_celdita_hora = consumo_celdita_hora.text
            consumo_celdita_hora = consumo_celdita_hora.replace(',', '.')

            # el cuarto
            for cuarto in range(0, 4):
                cuarto_hora = calendario_dia[contador_calendario_dia + cuarto]
                consumos_cuartohorarios.append((cuarto_hora, consumo_celdita_hora))

            contador_calendario_dia += 4

        # se GUARDA
        guardar_en_txt(dia, year, month, consumos_cuartohorarios)

    driver.close()
#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
def save_prevision_de_hoy():

    year = datetime.date.today().year
    month = datetime.date.today().month
    today = datetime.date.today().day
    hora_actual = datetime.datetime.now().hour
    fecha_hoy = datetime.datetime(year, month, today)

    consumos_cuartohorarios = []
    # dia dividido en cuartos
    calendario_dia = utiles.get_calendario_by_cuartos(24)
    contador_calendario_dia = 0
    # *****************************************************************************************************************
    # *****************************************************************************************************************
    # 1- Se cogen los consumos previstos de REN para hoy
    pagina_web = verificada_url

    # Selenium driver
    driver = webdriver.Chrome(var.CHROME_DRIVER)
    driver.get(pagina_web)
    driver.maximize_window()
    wait = WebDriverWait(driver, 15)
    espera = 2
    time.sleep(espera)

    # surfeo por el html
    # se clickea en la flecha
    xpath_flechita = '//*[@id="ctl00_ctl14_g_5ee12aa8_2064_4404_b94d_7b6b4057473f"]/div[1]/table/tbody/tr/td[1]/input[3]'
    elem = wait.until(
        EC.presence_of_element_located((By.XPATH, xpath_flechita)))
    elem.click()
    time.sleep(espera)

    # y leemos
    ruta_base = '//*[@id="ctl00_ctl14_g_5ee12aa8_2064_4404_b94d_7b6b4057473f_ctl15"]/tbody/tr['
    ruta_final = ']/td[2]'

    # la hora
    for hora in range(3, hora_actual + 3):
        ruta_celdita_hora = ruta_base + str(hora) + ruta_final

        # control de cambio de hora
        try:
            consumo_celdita_hora = driver.find_element_by_xpath(ruta_celdita_hora)
        except NoSuchElementException:
            break
        consumo_celdita_hora = consumo_celdita_hora.text
        consumo_celdita_hora = consumo_celdita_hora.replace(',', '.')

        # el cuarto
        for cuarto in range(0, 4):
            cuarto_hora = calendario_dia[contador_calendario_dia + cuarto]
            consumos_cuartohorarios.append((cuarto_hora, consumo_celdita_hora))

        contador_calendario_dia += 4

    driver.close()

    # *****************************************************************************************************************
    # *****************************************************************************************************************
    # 2- Ahora se cogen los previstos para hoy
    pagina_web = future_url

    # Selenium driver
    driver = webdriver.Chrome(var.CHROME_DRIVER)
    driver.get(pagina_web)
    driver.maximize_window()
    espera = 1
    time.sleep(espera)

    # check celdita columna a empezar
    celdita_columna = utiles.columna_a_empezar_prevision_demanda_ren(driver, fecha_hoy)

    # surfeo por el html
    ruta_base = '//*[@id="ctl00_ctl14_g_96459a04_7c84_4bf2_97a7_9ae2e9b5047f"]/div[2]/div/table/tbody/tr['
    ruta_final = ']/td[' + str(celdita_columna) + ']'

    hora_a_empezar = hora_actual + 3

    # check cambio de hora
    hora_maxima = celdita_hora_maxima
    fecha = str(year) + utiles.check_fecha(month) + utiles.check_fecha(today)
    if fecha in lista_retraso_horas:
        hora_maxima = 27
        calendario_dia = utiles.get_calendario_by_cuartos(25)
    if fecha in lista_adelanto_horas:
        hora_maxima = 25
        calendario_dia = utiles.get_calendario_by_cuartos(23)

    # la hora
    for hora in range(hora_a_empezar, hora_maxima + 1):
        ruta_celdita_hora = ruta_base + str(hora) + ruta_final
        consumo_celdita_hora = driver.find_element_by_xpath(ruta_celdita_hora).text

        # el cuarto
        for cuarto in range(0, 4):
            cuarto_hora = calendario_dia[contador_calendario_dia + cuarto]
            consumos_cuartohorarios.append((cuarto_hora, consumo_celdita_hora))

        contador_calendario_dia += 4

    # se GUARDA
    guardar_en_txt(datetime.date.today().day, year, month, consumos_cuartohorarios)

    driver.close()

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
def save_consumos_iniciales(year, month, dia_a_empezar):

    num_dias_del_mes = calendar.monthrange(year, month)[1]

    xlsx = pd.read_excel('excel/perfiles_consumo_' + str(year) + '.xlsx')

    # checking de rango de mes
    for dia in range(dia_a_empezar, num_dias_del_mes + 1):

        # dia del rango
        fecha_en_dataframe = utiles.check_fecha(dia) + '/' + utiles.check_fecha(month) + '/' + str(year)
        #dataframe_dia = xlsx[ (xlsx['Data'] == fecha_en_dataframe) & (xlsx['Hora']!='24:00')]
        dataframe_dia = xlsx[xlsx['Data'] == fecha_en_dataframe]

        horas = dataframe_dia['Hora']
        consumos = dataframe_dia['RESP']

        # se GUARDA
        guardar_en_txt(dia, year, month, np.column_stack((horas, consumos)))

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
def get_demanda_mensual(year, month, dia_a_empezar):

    actual_year = datetime.date.today().year
    actual_month = datetime.date.today().month
    today = datetime.date.today().day

    fecha_actual = str(actual_year) + utiles.check_fecha(actual_month) + utiles.check_fecha(today)
    fecha_actual = int(fecha_actual)
    fecha_a_traerse = str(year) + utiles.check_fecha(month) + utiles.check_fecha(dia_a_empezar)
    fecha_a_traerse = int(fecha_a_traerse)

    # ******************************************* INICIALES  *******************************************************
    print('Cargando demanda inicial desde la fecha ' + str(dia_a_empezar) + '-' + str(month) + '-' + str(year))
    save_consumos_iniciales(year, month, dia_a_empezar)
    print('Fin.')

    # ******************************************* PASADAS *******************************************************
    if fecha_a_traerse < fecha_actual:

        if actual_month == month and actual_year == year:
            dia_a_acabar = today
        else:
            dia_a_acabar = calendar.monthrange(year, month)[1] + 1 # numero dias del mes que se quiere traer

        print('Buscando demanda pasada...')
        save_prevision_a_pasado_by_verificado(year, month, dia_a_empezar, dia_a_acabar) # el dia_a_cabar sustiyue a today que habia ntes
        print('Fin.')

    # ******************************************* PREVISTAS y HOY *******************************************************
    if month >= actual_month and year >= actual_year:

        print('Buscando demanda prevista...')
        save_prevision_a_futuro(year, month, dia_a_empezar)
        print('Fin.')

        # el de hoy
        if dia_a_empezar <= today and month == actual_month and year == actual_year:
            print('Buscando demanda de hoy...')
            save_prevision_de_hoy()
            print('Fin.')


#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
#get_demanda_mensual(2019, 3, 1)
'''get_demanda_mensual(2018, 3, 1)
get_demanda_mensual(2018, 4, 1)
get_demanda_mensual(2018, 5, 1)'''