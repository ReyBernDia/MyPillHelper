import os
from sys import argv
from pprint import pprint
import json
import requests

def query_fda_api(med_name):

  API_KEY = os.environ['API_KEY']
  url = ("https://api.fda.gov/drug/label.json?api_key="
         + API_KEY
         +"&search=(openfda.generic_name:" 
         + med_name
         +"+openfda.brand_name:"
         + med_name 
         + ")"
         +"+AND+(route:ORAL+openfda.route:ORAL)"
         )

  r = requests.get(url)
  med_info = r.json()

  results = med_info.get('results', "")
  api_info = {}
  if len(results) != 0: 
    info_dict = (med_info['results'][0])
    openfda_dict = (med_info['results'][0]['openfda'])

    indications = info_dict.get('indications_and_usage', "")
    if indications != "":
      indications = " ".join(indications)
    dosing_info = info_dict.get('dosage_and_administration', "")
    if dosing_info != "":
      dosing_info = " ".join(dosing_info)
    info_for_patients = info_dict.get('information_for_patients', "")
    if info_for_patients != "":
      info_for_patients = " ".join(info_for_patients)
    contraindications = info_dict.get('contraindications', "")
    if contraindications != "":
      contraindications = " ".join(contraindications)
    brand_name = openfda_dict.get('brand_name', med_name)
    if (len(brand_name)>1) and (brand_name != ("" or med_name)):
      brand_name = ", ".join(brand_name)
    elif brand_name != ("" or med_name):
      brand_name = " ".join(brand_name)
    pharm_class = openfda_dict.get('pharm_class_moa', "")
    if pharm_class != "":
      pharm_class = " ".join(pharm_class)
  else: 
    indications = ""
    dosing_info = ""
    info_for_patients = ""
    contraindications = ""
    brand_name = ""
    pharm_class = ""

  api_info["indications"] = indications
  api_info["dosing_info"] = dosing_info
  api_info["info_for_patients"] = info_for_patients
  api_info["contraindications"] = contraindications
  api_info["brand_name"] = brand_name
  api_info["pharm_class"] = pharm_class

  return api_info

