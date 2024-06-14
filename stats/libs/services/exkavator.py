import os
import urllib.request
import xml.etree.ElementTree as ET

from applications.autoconverter.converter import save_on_ftp


def modify_exkavator_xml():
    """
    Таск для изменений фида FNGROUP для exkavator.ru
    :return:
    """
    url_feed = 'https://fngroup.ru/exkavator.xml'
    new_phone = '(495) 9754242'
    new_email = 'fngroup.volga@mail.ru'

    # Скачиваю фид
    response = urllib.request.urlopen(url_feed)
    xml_data = response.read()
    root = ET.fromstring(xml_data)

    # Меняю телефон и почту в контактах
    contacts = root.findall('Contacts/Contact')
    for contact in contacts:
        phone = contact.find('Phone')
        phone.set('Text', new_phone)

        email = contact.find('Email')
        email.set('Text', new_email)

    # Меняю почту в объявлениях
    in_ad_contacts = root.findall('OffersData/Entry/RegionList/RegionItem/Contact')
    for ad_contact in in_ad_contacts:
        ad_contact.set('Value', new_email)

    # Ensure the directory exists
    directory = 'Autoload/FNGroup'
    if not os.path.exists(directory):
        os.makedirs(directory)

    file_path = os.path.join(directory, 'exkavator_modified.xml')
    with open(file_path, 'wb') as f:
        ET.ElementTree(root).write(f, encoding='UTF-8')

    # file_path = 'temp/exkavator_modified.xml'
    # with open(file_path, 'wb') as f:
    #     ET.ElementTree(root).write(f, encoding='UTF-8')

    with open(file_path, 'rb') as file:
        file_content = file.read()
        save_on_ftp(file_path, file_content)
