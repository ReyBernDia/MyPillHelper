import os
from sys import argv
from pprint import pprint
import json
import requests

def query_fda_api(med_name):

  API_KEY = os.environ['API_KEY']
  url = ("https://api.fda.gov/drug/label.json?api_key="
         + API_KEY
         +"&search=openfda.generic_name:" 
         + med_name
         +"+openfda.brand_name:"
         + med_name)

  # print(url)
  r = requests.get(url)
  med_info = r.json()

  results = med_info.get('results', "")

  info_dict = (med_info['results'][0])
  openfda_dict = (med_info['results'][0]['openfda'])

  indications = info_dict.get('indications_and_usage', "")
  dosing_info = info_dict.get('dosage_and_administration', "")
  info_for_patients = info_dict.get('information_for_patients', "")
  contraindications = info_dict.get('contraindications', "")
  brand_name = openfda_dict.get('brand_name', med_name)
  pharm_class = openfda_dict.get('pharm_class_moa', "")

  return [indications, 
          dosing_info, 
          info_for_patients, 
          contraindications, 
          brand_name, 
          pharm_class
          ]