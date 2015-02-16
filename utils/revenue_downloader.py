#!/usr/bin/env python
# coding: utf-8

import os
import time

from selenium import webdriver
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary


class RevenueExtractor(object):

    def __init__(self, firefox, out_filename, out_folder):
        """'firefox' é o caminho para o binário do Firefox a ser usado.
        'pasta' é o caminho para a pasta onde salvar os downloads."""
        self.firefox = firefox
        self.out_filename = out_filename
        self.out_folder = out_folder
        self.browser = None

    def start_browser(self):
        """Retorna um browser firefox configurado para salvar arquivos
        baixados em 'pasta'."""
        print("Starting browser")
        fp = webdriver.FirefoxProfile()
        fp.set_preference("browser.download.folderList", 2)
        fp.set_preference("browser.download.manager.showWhenStarting", False)
        fp.set_preference("browser.download.dir", self.out_folder)
        fp.set_preference("browser.helperApps.neverAsk.saveToDisk",
                          "text/csv,application/vnd.ms-excel")
        # O binário do browser deve estar na pasta firefox
        binary = FirefoxBinary(self.firefox)
        self.browser = webdriver.Firefox(
            firefox_binary=binary,
            firefox_profile=fp
        )
        self.browser.implicitly_wait(20)

    def click(self, element_id):
        self.browser.find_element_by_id(element_id).click()

    def perseverant_run(self, function, max_tries):
        tries = 0
        while True:
            try:
                function()
                break
            except:
                if tries < max_tries:
                    print("Failed, trying again...")
                    tries += 1
                    pass
                else:
                    raise

    def wait_load(self):
        print("    waiting...")
        while self.browser.find_element_by_id(
                "ReportViewer1_AsyncWait").is_displayed():
            time.sleep(1)

    def setup_page(self):
        """Navega no site do Senado até o 'lindo' sistema de consulta de dados.
        O nome passado é usado para escolher a base que será analisada"""
        print("Entering website")
        a = """
        http://rsv.prefeitura.sp.gov.br/default.aspx?rsview=rpt921ConsultaLivre&Prj=SF8426
        """.strip()
        self.browser.get(a)
        time.sleep(1)
        self.wait_load()

        month_window_id = "ReportViewer1_ctl04_ctl09_ddDropDownButton"

        # def dangerous_block():
        #     print("Selecting base options")
        #     # Open month window
        #     self.click(month_window_id)
        #     time.sleep(1)
        #     # Select all months
        #     self.click("ReportViewer1_ctl04_ctl09_divDropDown_ctl00")
        # self.perseverant_run(dangerous_block, 5)
        print("Selecting base options")
        # Open month window
        self.click(month_window_id)
        time.sleep(1)
        # Select all months
        self.click("ReportViewer1_ctl04_ctl09_divDropDown_ctl00")
        # Deselect 'todos'
        time.sleep(1)
        self.click("ReportViewer1_ctl04_ctl09_divDropDown_ctl01")
        time.sleep(1)
        self.click(month_window_id)
        time.sleep(2)
        self.wait_load()
        print("    Done!")

    def get_data_by_year(self):
        """Adiciona os dados passados para serem consultados e executa a
        consulta"""
        # def first_dangerous_block():
        #     # Opens year window
        #     self.click("ReportViewer1_ctl04_ctl05_ddDropDownButton")
        # self.perseverant_run(first_dangerous_block, 5)
        index = 0
        while True:
            # Open year window
            time.sleep(1)
            year_window_id = "ReportViewer1_ctl04_ctl05_ddDropDownButton"
            self.click(year_window_id)
            time.sleep(1)
            year_window = self.browser.find_element_by_id(
                "ReportViewer1_ctl04_ctl05_divDropDown")
            # Year buttons
            buttons = year_window.find_elements_by_tag_name("input")
            select_all_button = buttons[0]
            # Year buttons (excludes "selecionar todos" and "todos")
            years_buttons = buttons[2:]
            year = years_buttons[index]
            year_name = year.find_elements_by_xpath("..")[0].text.strip()

            print("Picking year %s" % year_name)
            # Clear selection
            select_all_button.click()
            time.sleep(1)
            select_all_button.click()
            time.sleep(1)
            # Pick the year
            year.click()
            time.sleep(1)
            self.wait_load()
            self.generate_report()
            self.download_file(year_name)
            print("    Done!")

            index += 1
            if len(years_buttons) <= index:
                break

    def generate_report(self):
        while True:
            # Get report
            print("Generate Report")
            self.click("ReportViewer1_ctl04_ctl00")
            time.sleep(2)
            self.wait_load()
            time.sleep(2)

            element = self.browser.find_element_by_id(
                "VisibleReportContentReportViewer1_ctl10")
            print("ISSO!!!!: ", element.text)
            # test = element.find_elements_by_tag_name("a")
            # if not test:
            if not element.text:
                print("    Failed to generate report...")
                print("    But I'll try to the death!")
            else:
                break
        print("    Done!")

    def download_file(self, year_name):
        """Inicia o download do CSV e aguarda ele terminar"""
        # def dangerous_block():
        #     # Open the export menu
        #     self.click("ReportViewer1_ctl06_ctl04_ctl00_ButtonImgDown")
        #     # Get export links
        #     export_menu = self.browser.find_element_by_id(
        #         "ReportViewer1_ctl06_ctl04_ctl00_Menu")
        #     links = export_menu.find_elements_by_tag_name("a")
        #     # Download the CSV
        #     links[1].click()
        # self.perseverant_run(dangerous_block, 5)

        # Open the export menu
        self.click("ReportViewer1_ctl06_ctl04_ctl00_ButtonImgDown")
        time.sleep(1)
        # Get export links
        export_menu = self.browser.find_element_by_id(
            "ReportViewer1_ctl06_ctl04_ctl00_Menu")
        links = export_menu.find_elements_by_tag_name("a")
        # Download the CSV
        links[1].click()
        print("Downloading...")
        time.sleep(5)
        # Enquanto ainda existir um arquivo temporário do firefox, esperar
        while self.out_filename + ".part" in os.listdir(self.out_folder):
            time.sleep(1)
        time.sleep(1)
        tmp = os.path.join(self.out_folder, self.out_filename)
        final = os.path.join(self.out_folder, year_name + ".csv")
        os.rename(tmp, final)
        print("    Done!")

    def get_all_data(self):
        """Obtem dados de base salvando em pasta. Retorna o caminho para o
        arquivo baixado."""
        # Create out folder
        try:
            os.makedirs(self.out_folder)
        except OSError as erro:
            # Ignore if already exists
            if erro.errno != 17:
                raise
        # Remove possível arquivo baixado anteriormente
        caminho_arquivo = os.path.join(self.out_folder, self.out_filename)
        try:
            os.remove(caminho_arquivo)
        except OSError as erro:
            # Ignora se arquivo não existe
            if erro.errno != 2:
                raise
        self.start_browser()
        self.setup_page()
        self.get_data_by_year()
        # self.browser.quit()
        return caminho_arquivo


if __name__ == '__main__':
    firefox = os.path.join("/", "bin", "firefox")
    out_filename = "rpt921ConsultaLivre.csv"
    out_folder = os.getcwd()
    extractor = RevenueExtractor(firefox, out_filename, out_folder)
    extractor.get_all_data()
