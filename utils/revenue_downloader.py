#!/usr/bin/env python
# coding: utf-8

''' Downloads revenue data via Selenium.

Usage: revenue_downloader [options] [<year>...]

Options:
-h, --help                        Show this message.
-o, --outfolder <outfolder>       Folder where to place files.
                                  I think it MUST be full path to folder.
                                  [default: current folder]
-f, --firefox-binary <firefox>    Firefox binary.
                                  [default: /bin/firefox]
'''

import os
import time

from docopt import docopt

from selenium import webdriver
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary


class RevenueDownloader(object):

    def __init__(self, firefox, out_filename, out_folder):
        """
        :param firefox: path to the firefox binary
        :param out_filename: name of the downloaded file
        :param out_folder: path to the output folder
        """
        self.firefox = firefox
        self.out_filename = out_filename
        self.out_folder = out_folder
        self.browser = None

    def start_browser(self):
        """Starts the browser
        """
        print("Starting browser")
        fp = webdriver.FirefoxProfile()
        fp.set_preference("browser.download.folderList", 2)
        fp.set_preference("browser.download.manager.showWhenStarting", False)
        fp.set_preference("browser.download.dir", self.out_folder)
        fp.set_preference("browser.helperApps.neverAsk.saveToDisk",
                          "text/csv,application/vnd.ms-excel")
        binary = FirefoxBinary(self.firefox)
        self.browser = webdriver.Firefox(
            firefox_binary=binary,
            firefox_profile=fp
        )
        self.browser.implicitly_wait(20)

    def click(self, element_id):
        """Clicks an element by id
        """
        self.browser.find_element_by_id(element_id).click()

    def perseverant_run(self, function, max_tries):
        """Tries to run a function again if it raises an exception.
        :param function: function to be run
        :param max_tries: max number of times it will run the function
        """
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
        """Waits the 'loading' banner disapear.
        """
        print("    waiting...")

        def dangerous_block():
            while self.browser.find_element_by_id(
                    "ReportViewer1_AsyncWait").is_displayed():
                time.sleep(1)
        self.perseverant_run(dangerous_block, 5)
        print("    done waiting")

    def setup_page(self):
        """Enter page and setup basic stuff.
        """
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

    def create_year_button_dict(self):
        """Clear year selection and return dict year->button
        """
        time.sleep(1)
        year_window_id = "ReportViewer1_ctl04_ctl05_divDropDown"
        year_window_button_id = "ReportViewer1_ctl04_ctl05_ddDropDownButton"
        year_window = self.browser.find_element_by_id(year_window_id)
        # If the year selection window is not open, opens
        if not year_window.is_displayed():
            self.click(year_window_button_id)
            time.sleep(2)
        # Year buttons
        buttons = year_window.find_elements_by_tag_name("input")
        select_all_button = buttons[0]
        # Year buttons (excludes "selecionar todos" and "todos")
        years_buttons = buttons[2:]
        year_dict = {}
        for year_button in years_buttons:
            yearname = year_button.find_elements_by_xpath("..")[0].text.strip()
            year_dict[yearname] = year_button
        # Clear selection
        select_all_button.click()
        time.sleep(1)
        select_all_button.click()
        time.sleep(1)
        return year_dict

    def get_data_by_year(self, year_list):
        """Gets the data by each year.
        :param year_list: list of years to download, if empty, downloads all"""
        # def first_dangerous_block():
        #     # Opens year window
        #     self.click("ReportViewer1_ctl04_ctl05_ddDropDownButton")
        # self.perseverant_run(first_dangerous_block, 5)
        if not year_list:
            year_list = sorted(self.create_year_button_dict().keys())

        for year_name in year_list:
            year_dict = self.create_year_button_dict()
            print("Picking year %s" % year_name)
            # Pick the year
            year_dict[year_name].click()
            time.sleep(1)
            self.wait_load()
            self.generate_report()
            self.download_file(year_name)
            print("    Done!")

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
            # test = element.find_elements_by_tag_name("a")
            # if not test:
            if not element.text:
                print("    Failed to generate report...")
                print("    But I'll try to the death!")
            else:
                break
        print("    Done!")

    def download_file(self, year_name):
        """Downloads the CSV, waiting it to finish and renaming it in the end.
        :param year_name: name of the final file (without '.csv')
        """
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
        # Waits while there is still a Firefox temp file
        while self.out_filename + ".part" in os.listdir(self.out_folder):
            time.sleep(1)
        time.sleep(1)
        tmp = os.path.join(self.out_folder, self.out_filename)
        final = os.path.join(self.out_folder, year_name + ".csv")
        os.rename(tmp, final)
        print("    Done!")

    def download(self, year_list):
        """Gets the data.
        :param year_list: list of years to download"""
        # Create out folder
        try:
            os.makedirs(self.out_folder)
        except OSError as erro:
            # Ignore if already exists
            if erro.errno != 17:
                raise
        # Removes, if exists, the previous downloaded temp file
        filepath = os.path.join(self.out_folder, self.out_filename)
        try:
            os.remove(filepath)
        except OSError as erro:
            # Ignore if doesn't exists
            if erro.errno != 2:
                raise
        try:
            self.start_browser()
            self.setup_page()
            self.get_data_by_year(year_list)
            self.browser.quit()
            return filepath
        except:
            self.browser.quit()
            raise


if __name__ == '__main__':
    arguments = docopt(__doc__)
    firefox = arguments['--firefox-binary']
    out_filename = "rpt921ConsultaLivre.csv"
    out_folder = arguments['--outfolder']
    if out_folder == "current folder":
        out_folder = os.getcwd()
    extractor = RevenueDownloader(firefox, out_filename, out_folder)
    extractor.download(arguments['<year>'])
