"""
Module 3 — Crowd Risk — DATASET COLLECTION
===========================================
Collects the two raw signals train_module3.py fuses into a Destination
Interest Index: weekly Google Trends search interest (via pytrends) and
monthly Wikipedia page views (via the Wikimedia REST pageviews API), for
~300 named attractions and landmarks across Sri Lanka.

This is a slow, network-dependent, rate-limited scrape (Google Trends in
particular throttles aggressively) — it is not meant to be run casually,
and can take well over an hour. The CSVs it produces are already checked
into backend/data/module3/ (trends_master.csv, wiki_master.csv); only run
this again to refresh them with newer data.
"""
import time
import random
from pathlib import Path

import pandas as pd
import requests
from pytrends.request import TrendReq

BASE_DIR = Path(__file__).resolve().parent.parent  # backend/
DATA_DIR = BASE_DIR / "data" / "module3"
CACHE_DIR = DATA_DIR / "trends_cache"
DATA_DIR.mkdir(parents=True, exist_ok=True)
CACHE_DIR.mkdir(parents=True, exist_ok=True)

TRENDS_GEO = "LK"
TRENDS_TIMEFRAME = "today 5-y"
WIKI_START = "20190101"
WIKI_END = "20261231"

# Keyword variants to search on Google Trends, and the Wikipedia article slug
# to pull page views for, per tracked place.
DESTINATIONS = {
    "Attidiya Bird Sanctuary": {"trends_kw": ["Attidiya Bird Sanctuary", "Attidiya Bird Sanctuary Colombo"], "wiki": "Attidiya_Bird_Sanctuary"},
    "Beddagana Wetland Park": {"trends_kw": ["Beddagana Wetland Park", "Beddagana Wetland Park Colombo"], "wiki": "Beddagana_Wetland_Park"},
    "Bellagio Colombo": {"trends_kw": ["Bellagio Colombo"], "wiki": "Bellagio_Colombo"},
    "Casino Marina Colombo": {"trends_kw": ["Casino Marina Colombo"], "wiki": "Casino_Marina_Colombo"},
    "Colombo Natational Museum": {"trends_kw": ["Colombo Natational Museum"], "wiki": "Colombo_Natational_Museum"},
    "Colombo Port Maritime Museum": {"trends_kw": ["Colombo Port Maritime Museum"], "wiki": "Colombo_Port_Maritime_Museum"},
    "Colombo Port Old Lighthouse": {"trends_kw": ["Colombo Port Old Lighthouse"], "wiki": "Colombo_Port_Old_Lighthouse"},
    "Crow Island Beach Park": {"trends_kw": ["Crow Island Beach Park", "Crow Island Beach Park Colombo"], "wiki": "Crow_Island_Beach_Park"},
    "Dehiwala Zoological Gardens": {"trends_kw": ["Dehiwala Zoological Gardens", "Dehiwala Zoological Gardens Colombo"], "wiki": "Dehiwala_Zoological_Gardens"},
    "Diyatha Uyana": {"trends_kw": ["Diyatha Uyana", "Diyatha Uyana Colombo"], "wiki": "Diyatha_Uyana"},
    "Dutch Museum": {"trends_kw": ["Dutch Museum", "Dutch Museum Colombo"], "wiki": "Dutch_Museum"},
    "Excel World Entertainment Park": {"trends_kw": ["Excel World Entertainment Park", "Excel World Entertainment Park Colombo"], "wiki": "Excel_World_Entertainment_Park"},
    "Galle Face Green": {"trends_kw": ["Galle Face Green", "Galle Face Green Colombo"], "wiki": "Galle_Face_Green"},
    "Galle Face Park & Beach": {"trends_kw": ["Galle Face Park & Beach", "Galle Face Park & Beach Colombo"], "wiki": "Galle_Face_Park__Beach"},
    "Gangarama Sima Malaka": {"trends_kw": ["Gangarama Sima Malaka", "Gangarama Sima Malaka Colombo"], "wiki": "Gangarama_Sima_Malaka"},
    "Gangarama Temple": {"trends_kw": ["Gangarama Temple", "Gangarama Temple Colombo"], "wiki": "Gangarama_Temple"},
    "Hamilton Canal Park": {"trends_kw": ["Hamilton Canal Park", "Hamilton Canal Park Colombo"], "wiki": "Hamilton_Canal_Park"},
    "Independence Square": {"trends_kw": ["Independence Square", "Independence Square Colombo"], "wiki": "Independence_Square"},
    "Kathiresan Pillayar Kovil": {"trends_kw": ["Kathiresan Pillayar Kovil", "Kathiresan Pillayar Kovil Colombo"], "wiki": "Kathiresan_Pillayar_Kovil"},
    "Kayman'S Gate": {"trends_kw": ["Kayman'S Gate", "Kayman'S Gate Colombo"], "wiki": "Kaymans_Gate"},
    "Kelaniya Raja Maha Viharaya": {"trends_kw": ["Kelaniya Raja Maha Viharaya", "Kelaniya Raja Maha Viharaya Colombo"], "wiki": "Kelaniya_Raja_Maha_Viharaya"},
    "Mount Lavania Beach": {"trends_kw": ["Mount Lavania Beach", "Mount Lavania Beach Colombo"], "wiki": "Mount_Lavania_Beach"},
    "National Art Gallery": {"trends_kw": ["National Art Gallery", "National Art Gallery Colombo"], "wiki": "National_Art_Gallery"},
    "Old Parliament Building": {"trends_kw": ["Old Parliament Building", "Old Parliament Building Colombo"], "wiki": "Old_Parliament_Building"},
    "Pettah Floating Market": {"trends_kw": ["Pettah Floating Market", "Pettah Floating Market Colombo"], "wiki": "Pettah_Floating_Market"},
    "Queen Viharamahadevi Statue": {"trends_kw": ["Queen Viharamahadevi Statue", "Queen Viharamahadevi Statue Colombo"], "wiki": "Queen_Viharamahadevi_Statue"},
    "Sambodhi Pagoda": {"trends_kw": ["Sambodhi Pagoda", "Sambodhi Pagoda Colombo"], "wiki": "Sambodhi_Pagoda"},
    "Sathutu Uyana": {"trends_kw": ["Sathutu Uyana", "Sathutu Uyana Colombo"], "wiki": "Sathutu_Uyana"},
    "Sri Kailawasanathan Swami Devasthanam Kovil": {"trends_kw": ["Sri Kailawasanathan Swami Devasthanam Kovil", "Sri Kailawasanathan Swami Devasthanam Kovil Colombo"], "wiki": "Sri_Kailawasanathan_Swami_Devasthanam_Kovil"},
    "Sri Lanka Planetarium": {"trends_kw": ["Sri Lanka Planetarium", "Sri Lanka Planetarium Colombo"], "wiki": "Sri_Lanka_Planetarium"},
    "St. Anthony'S Shrine, Kochchikade": {"trends_kw": ["St. Anthony'S Shrine, Kochchikade", "St. Anthony'S Shrine, Kochchikade Colombo"], "wiki": "St_Anthonys_Shrine,_Kochchikade"},
    "St. Lucia'S Cathedral": {"trends_kw": ["St. Lucia'S Cathedral", "St. Lucia'S Cathedral Colombo"], "wiki": "St_Lucias_Cathedral"},
    "Thalangama Lake": {"trends_kw": ["Thalangama Lake", "Thalangama Lake Colombo"], "wiki": "Thalangama_Lake"},
    "Torington Park": {"trends_kw": ["Torington Park", "Torington Park Colombo"], "wiki": "Torington_Park"},
    "Viharamahadevi Park": {"trends_kw": ["Viharamahadevi Park", "Viharamahadevi Park Colombo"], "wiki": "Viharamahadevi_Park"},
    "Asgiriya Raja Maha Viharaya": {"trends_kw": ["Asgiriya Raja Maha Viharaya", "Asgiriya Raja Maha Viharaya Gampaha"], "wiki": "Asgiriya_Raja_Maha_Viharaya"},
    "Bopagama Ella": {"trends_kw": ["Bopagama Ella", "Bopagama Ella Gampaha"], "wiki": "Bopagama_Ella"},
    "Gampaha Botanical Garden": {"trends_kw": ["Gampaha Botanical Garden", "Gampaha Botanical Garden Gampaha"], "wiki": "Gampaha_Botanical_Garden"},
    "Goraka Ella": {"trends_kw": ["Goraka Ella", "Goraka Ella Gampaha"], "wiki": "Goraka_Ella"},
    "Guruge Park": {"trends_kw": ["Guruge Park", "Guruge Park Gampaha"], "wiki": "Guruge_Park"},
    "Horagolla National Park": {"trends_kw": ["Horagolla National Park", "Horagolla National Park Gampaha", "Horagolla National Park Safari"], "wiki": "Horagolla_National_Park"},
    "Mayan Water Park": {"trends_kw": ["Mayan Water Park", "Mayan Water Park Gampaha"], "wiki": "Mayan_Water_Park"},
    "Rukmani Devi Park": {"trends_kw": ["Rukmani Devi Park", "Rukmani Devi Park Gampaha"], "wiki": "Rukmani_Devi_Park"},
    "Saniro Dream Paradise": {"trends_kw": ["Saniro Dream Paradise", "Saniro Dream Paradise Gampaha"], "wiki": "Saniro_Dream_Paradise"},
    "Udammita Ambalama": {"trends_kw": ["Udammita Ambalama", "Udammita Ambalama Gampaha"], "wiki": "Udammita_Ambalama"},
    "Black Galle Fort": {"trends_kw": ["Black Galle Fort", "Black Galle Fort Galle"], "wiki": "Black_Galle_Fort"},
    "Dutch Reformed Church": {"trends_kw": ["Dutch Reformed Church", "Dutch Reformed Church Galle"], "wiki": "Dutch_Reformed_Church"},
    "Galle Dutch Fort": {"trends_kw": ["Galle Dutch Fort", "Galle Dutch Fort Galle"], "wiki": "Galle_Dutch_Fort"},
    "Galle Fort Attractions And Jumpers Sri Lanka": {"trends_kw": ["Galle Fort Attractions And Jumpers Sri Lanka", "Galle Fort Attractions And Jumpers Sri Lanka Galle"], "wiki": "Galle_Fort_Attractions_And_Jumpers_Sri_Lanka"},
    "Galle Fort Clock Tower": {"trends_kw": ["Galle Fort Clock Tower", "Galle Fort Clock Tower Galle"], "wiki": "Galle_Fort_Clock_Tower"},
    "Galle Fort Ramparts": {"trends_kw": ["Galle Fort Ramparts", "Galle Fort Ramparts Galle"], "wiki": "Galle_Fort_Ramparts"},
    "Galle Fort View Point": {"trends_kw": ["Galle Fort View Point", "Galle Fort View Point Galle"], "wiki": "Galle_Fort_View_Point"},
    "Historical Mansion Museum": {"trends_kw": ["Historical Mansion Museum", "Historical Mansion Museum Galle"], "wiki": "Historical_Mansion_Museum"},
    "Japanese Peace Pagoda - Rumassala": {"trends_kw": ["Japanese Peace Pagoda - Rumassala", "Japanese Peace Pagoda", "Japanese Peace Pagoda Galle"], "wiki": "Japanese_Peace_Pagoda"},
    "Koggala Beach": {"trends_kw": ["Koggala Beach", "Koggala Beach Galle"], "wiki": "Koggala_Beach"},
    "Koggala Lake": {"trends_kw": ["Koggala Lake", "Koggala Lake Galle"], "wiki": "Koggala_Lake"},
    "Lighthouse - Galle": {"trends_kw": ["Lighthouse - Galle", "Lighthouse", "Lighthouse Galle"], "wiki": "Lighthouse"},
    "Lover'S Leap Galle Fort": {"trends_kw": ["Lover'S Leap Galle Fort", "Lover'S Leap Galle Fort Galle"], "wiki": "Lovers_Leap_Galle_Fort"},
    "Mahamodara Beach Park & Marine Walk": {"trends_kw": ["Mahamodara Beach Park & Marine Walk", "Mahamodara Beach Park & Marine Walk Galle"], "wiki": "Mahamodara_Beach_Park__Marine_Walk"},
    "Martin Wickramasinghe Folk Museum": {"trends_kw": ["Martin Wickramasinghe Folk Museum", "Martin Wickramasinghe Folk Museum Galle"], "wiki": "Martin_Wickramasinghe_Folk_Museum"},
    "National Maritime Museum": {"trends_kw": ["National Maritime Museum", "National Maritime Museum Galle"], "wiki": "National_Maritime_Museum"},
    "National Museum Of Galle": {"trends_kw": ["National Museum Of Galle"], "wiki": "National_Museum_Of_Galle"},
    "Old Dutch Hospital Galle": {"trends_kw": ["Old Dutch Hospital Galle"], "wiki": "Old_Dutch_Hospital_Galle"},
    "Old Gate Galle Fort": {"trends_kw": ["Old Gate Galle Fort"], "wiki": "Old_Gate_Galle_Fort"},
    "Rumassala Sanctuary": {"trends_kw": ["Rumassala Sanctuary", "Rumassala Sanctuary Galle"], "wiki": "Rumassala_Sanctuary"},
    "Sri Sudharmalaya Buddhistst Temple": {"trends_kw": ["Sri Sudharmalaya Buddhistst Temple", "Sri Sudharmalaya Buddhistst Temple Galle"], "wiki": "Sri_Sudharmalaya_Buddhistst_Temple"},
    "Unawatuna Beach": {"trends_kw": ["Unawatuna Beach", "Unawatuna Beach Galle"], "wiki": "Unawatuna_Beach"},
    "All Saints Church Galle": {"trends_kw": ["All Saints Church Galle"], "wiki": "All_Saints_Church_Galle"},
    "Ambalangoda Mask Museum": {"trends_kw": ["Ambalangoda Mask Museum", "Ambalangoda Mask Museum Galle"], "wiki": "Ambalangoda_Mask_Museum"},
    "Dutch Fort Light House Galle": {"trends_kw": ["Dutch Fort Light House Galle"], "wiki": "Dutch_Fort_Light_House_Galle"},
    "Galle Fort Wall": {"trends_kw": ["Galle Fort Wall", "Galle Fort Wall Galle"], "wiki": "Galle_Fort_Wall"},
    "Galle Fort Wall End": {"trends_kw": ["Galle Fort Wall End", "Galle Fort Wall End Galle"], "wiki": "Galle_Fort_Wall_End"},
    "Galle Lighthouse Point": {"trends_kw": ["Galle Lighthouse Point", "Galle Lighthouse Point Galle"], "wiki": "Galle_Lighthouse_Point"},
    "Galle Marine Walk Park": {"trends_kw": ["Galle Marine Walk Park", "Galle Marine Walk Park Galle"], "wiki": "Galle_Marine_Walk_Park"},
    "Jungle Beach": {"trends_kw": ["Jungle Beach", "Jungle Beach Galle"], "wiki": "Jungle_Beach"},
    "Sea Turtle Hatchery Mahamodara": {"trends_kw": ["Sea Turtle Hatchery Mahamodara", "Sea Turtle Hatchery Mahamodara Galle"], "wiki": "Sea_Turtle_Hatchery_Mahamodara"},
    "Tsunami Photo Museum": {"trends_kw": ["Tsunami Photo Museum", "Tsunami Photo Museum Galle"], "wiki": "Tsunami_Photo_Museum"},
    "Blow Hole (Hummanaya)": {"trends_kw": ["Blow Hole (Hummanaya)", "Blow Hole", "Blow Hole Matara"], "wiki": "Blow_Hole"},
    "Dondra Head Lighthouse": {"trends_kw": ["Dondra Head Lighthouse", "Dondra Head Lighthouse Matara"], "wiki": "Dondra_Head_Lighthouse"},
    "Hiriketiya Beach": {"trends_kw": ["Hiriketiya Beach", "Hiriketiya Beach Matara"], "wiki": "Hiriketiya_Beach"},
    "Kabinagala Waterfall": {"trends_kw": ["Kabinagala Waterfall", "Kabinagala Waterfall Matara"], "wiki": "Kabinagala_Waterfall"},
    "Matara Bodhiya": {"trends_kw": ["Matara Bodhiya", "Matara Bodhiya Matara"], "wiki": "Matara_Bodhiya"},
    "Matara Paravi Duwa Temple": {"trends_kw": ["Matara Paravi Duwa Temple", "Matara Paravi Duwa Temple Matara"], "wiki": "Matara_Paravi_Duwa_Temple"},
    "Mirissa Beach": {"trends_kw": ["Mirissa Beach", "Mirissa Beach Matara"], "wiki": "Mirissa_Beach"},
    "Nilwella Beach": {"trends_kw": ["Nilwella Beach", "Nilwella Beach Matara"], "wiki": "Nilwella_Beach"},
    "Parrot Rock": {"trends_kw": ["Parrot Rock", "Parrot Rock Matara"], "wiki": "Parrot_Rock"},
    "Raja & The Whales": {"trends_kw": ["Raja & The Whales", "Raja & The Whales Matara"], "wiki": "Raja__The_Whales"},
    "Snake Farm Weligama (Traditional Farm)": {"trends_kw": ["Snake Farm Weligama (Traditional Farm)", "Snake Farm Weligama", "Snake Farm Weligama Matara"], "wiki": "Snake_Farm_Weligama"},
    "Star Fort Matara": {"trends_kw": ["Star Fort Matara"], "wiki": "Star_Fort_Matara"},
    "Talalla Beach": {"trends_kw": ["Talalla Beach", "Talalla Beach Matara"], "wiki": "Talalla_Beach"},
    "Weherahena Poorwarama Rajamaha Viharaya": {"trends_kw": ["Weherahena Poorwarama Rajamaha Viharaya", "Weherahena Poorwarama Rajamaha Viharaya Matara"], "wiki": "Weherahena_Poorwarama_Rajamaha_Viharaya"},
    "Weligama Beach (Surf Spot)": {"trends_kw": ["Weligama Beach (Surf Spot)", "Weligama Beach", "Weligama Beach Matara"], "wiki": "Weligama_Beach"},
    "Wewurukannala Buduraja Maha Viharaya": {"trends_kw": ["Wewurukannala Buduraja Maha Viharaya", "Wewurukannala Buduraja Maha Viharaya Matara"], "wiki": "Wewurukannala_Buduraja_Maha_Viharaya"},
    "Aradunu Falls": {"trends_kw": ["Aradunu Falls", "Aradunu Falls Badulla"], "wiki": "Aradunu_Falls"},
    "Badulla Alugolla Samadhi Buddha": {"trends_kw": ["Badulla Alugolla Samadhi Buddha"], "wiki": "Badulla_Alugolla_Samadhi_Buddha"},
    "Badulla Dutch Fort": {"trends_kw": ["Badulla Dutch Fort"], "wiki": "Badulla_Dutch_Fort"},
    "Badulla Katharagama Devalaya": {"trends_kw": ["Badulla Katharagama Devalaya"], "wiki": "Badulla_Katharagama_Devalaya"},
    "Blackpool": {"trends_kw": ["Blackpool", "Blackpool Badulla"], "wiki": "Blackpool"},
    "Bogoda Wooden Bridge": {"trends_kw": ["Bogoda Wooden Bridge", "Bogoda Wooden Bridge Badulla"], "wiki": "Bogoda_Wooden_Bridge"},
    "Bogoda Raja Maha Viharaya": {"trends_kw": ["Bogoda Raja Maha Viharaya", "Bogoda Raja Maha Viharaya Badulla"], "wiki": "Bogoda_Raja_Maha_Viharaya"},
    "Bomburu Ella Waterfall": {"trends_kw": ["Bomburu Ella Waterfall", "Bomburu Ella Waterfall Badulla"], "wiki": "Bomburu_Ella_Waterfall"},
    "Diyaluma Falls": {"trends_kw": ["Diyaluma Falls", "Diyaluma Falls Badulla"], "wiki": "Diyaluma_Falls"},
    "Dunhida Waterfall Access Point": {"trends_kw": ["Dunhida Waterfall Access Point", "Dunhida Waterfall Access Point Badulla"], "wiki": "Dunhida_Waterfall_Access_Point"},
    "Dunhinda Waterfall": {"trends_kw": ["Dunhinda Waterfall", "Dunhinda Waterfall Badulla"], "wiki": "Dunhinda_Waterfall"},
    "Kombukara Nature Pool And Secre": {"trends_kw": ["Kombukara Nature Pool And Secre", "Kombukara Nature Pool And Secre Badulla"], "wiki": "Kombukara_Nature_Pool_And_Secre"},
    "Kurundu Oya Ella Falls": {"trends_kw": ["Kurundu Oya Ella Falls", "Kurundu Oya Ella Falls Badulla"], "wiki": "Kurundu_Oya_Ella_Falls"},
    "Lanka Ella - Waterfall": {"trends_kw": ["Lanka Ella - Waterfall", "Lanka Ella", "Lanka Ella Badulla"], "wiki": "Lanka_Ella"},
    "Muthiyangana Raja Maha Vihara": {"trends_kw": ["Muthiyangana Raja Maha Vihara", "Muthiyangana Raja Maha Vihara Badulla"], "wiki": "Muthiyangana_Raja_Maha_Vihara"},
    "Narangala Hill": {"trends_kw": ["Narangala Hill", "Narangala Hill Badulla"], "wiki": "Narangala_Hill"},
    "Narangala Mountain": {"trends_kw": ["Narangala Mountain", "Narangala Mountain Badulla"], "wiki": "Narangala_Mountain"},
    "Pallewela Waterfall": {"trends_kw": ["Pallewela Waterfall", "Pallewela Waterfall Badulla"], "wiki": "Pallewela_Waterfall"},
    "Pareiyan Ella Falls": {"trends_kw": ["Pareiyan Ella Falls", "Pareiyan Ella Falls Badulla"], "wiki": "Pareiyan_Ella_Falls"},
    "Porawagala Viewpoint": {"trends_kw": ["Porawagala Viewpoint", "Porawagala Viewpoint Badulla"], "wiki": "Porawagala_Viewpoint"},
    "Prabhawa Mountain Day Viewpoint": {"trends_kw": ["Prabhawa Mountain Day Viewpoint", "Prabhawa Mountain Day Viewpoint Badulla"], "wiki": "Prabhawa_Mountain_Day_Viewpoint"},
    "Rahangala Mountain View Point": {"trends_kw": ["Rahangala Mountain View Point", "Rahangala Mountain View Point Badulla"], "wiki": "Rahangala_Mountain_View_Point"},
    "Sorabora Wewa": {"trends_kw": ["Sorabora Wewa", "Sorabora Wewa Badulla"], "wiki": "Sorabora_Wewa"},
    "Wawuliyadda Falls": {"trends_kw": ["Wawuliyadda Falls", "Wawuliyadda Falls Badulla"], "wiki": "Wawuliyadda_Falls"},
    "Calido Beach Kalutara": {"trends_kw": ["Calido Beach Kalutara"], "wiki": "Calido_Beach_Kalutara"},
    "Kalido Beach Kalutara": {"trends_kw": ["Kalido Beach Kalutara"], "wiki": "Kalido_Beach_Kalutara"},
    "Kalutara Bodhiya": {"trends_kw": ["Kalutara Bodhiya", "Kalutara Bodhiya Kalutara"], "wiki": "Kalutara_Bodhiya"},
    "Richmond Castle": {"trends_kw": ["Richmond Castle", "Richmond Castle Kalutara"], "wiki": "Richmond_Castle"},
    "Christ Church Warleigh, Dickoya": {"trends_kw": ["Christ Church Warleigh, Dickoya", "Christ Church Warleigh, Dickoya Hatton"], "wiki": "Christ_Church_Warleigh,_Dickoya"},
    "Devon Falls": {"trends_kw": ["Devon Falls", "Devon Falls Hatton"], "wiki": "Devon_Falls"},
    "Devon Waterfall View Point": {"trends_kw": ["Devon Waterfall View Point", "Devon Waterfall View Point Hatton"], "wiki": "Devon_Waterfall_View_Point"},
    "Galpotha Natural Water Slide": {"trends_kw": ["Galpotha Natural Water Slide", "Galpotha Natural Water Slide Hatton"], "wiki": "Galpotha_Natural_Water_Slide"},
    "Gartmore Falls": {"trends_kw": ["Gartmore Falls", "Gartmore Falls Hatton"], "wiki": "Gartmore_Falls"},
    "Kithulgala Waterfall View": {"trends_kw": ["Kithulgala Waterfall View", "Kithulgala Waterfall View Hatton"], "wiki": "Kithulgala_Waterfall_View"},
    "Laxapana Falls": {"trends_kw": ["Laxapana Falls", "Laxapana Falls Hatton"], "wiki": "Laxapana_Falls"},
    "Mahi Ella Falls": {"trends_kw": ["Mahi Ella Falls", "Mahi Ella Falls Hatton"], "wiki": "Mahi_Ella_Falls"},
    "Mapalana Falls": {"trends_kw": ["Mapalana Falls", "Mapalana Falls Hatton"], "wiki": "Mapalana_Falls"},
    "Mohini Waterfall": {"trends_kw": ["Mohini Waterfall", "Mohini Waterfall Hatton"], "wiki": "Mohini_Waterfall"},
    "Moray Falls": {"trends_kw": ["Moray Falls", "Moray Falls Hatton"], "wiki": "Moray_Falls"},
    "Nalagana Ella Waterfall": {"trends_kw": ["Nalagana Ella Waterfall", "Nalagana Ella Waterfall Hatton"], "wiki": "Nalagana_Ella_Waterfall"},
    "Peace Pagoda Sri Pada": {"trends_kw": ["Peace Pagoda Sri Pada", "Peace Pagoda Sri Pada Hatton"], "wiki": "Peace_Pagoda_Sri_Pada"},
    "Ramboda Falls": {"trends_kw": ["Ramboda Falls", "Ramboda Falls Hatton"], "wiki": "Ramboda_Falls"},
    "Single Tree Hill": {"trends_kw": ["Single Tree Hill", "Single Tree Hill Hatton"], "wiki": "Single_Tree_Hill"},
    "Sri Pada (Adam'S Peak)": {"trends_kw": ["Sri Pada (Adam'S Peak)", "Sri Pada", "Sri Pada Hatton"], "wiki": "Sri_Pada"},
    "Sri Pada (Adam'S Peak) Trailhead": {"trends_kw": ["Sri Pada (Adam'S Peak) Trailhead", "Sri Pada", "Sri Pada Hatton"], "wiki": "Sri_Pada"},
    "St. Clair'S Falls": {"trends_kw": ["St. Clair'S Falls", "St. Clair'S Falls Hatton"], "wiki": "St_Clairs_Falls"},
    "Surathali Waterfall View Point": {"trends_kw": ["Surathali Waterfall View Point", "Surathali Waterfall View Point Hatton"], "wiki": "Surathali_Waterfall_View_Point"},
    "Batadobalena": {"trends_kw": ["Batadobalena", "Batadobalena Rathnapura"], "wiki": "Batadobalena"},
    "Bopath Falls": {"trends_kw": ["Bopath Falls", "Bopath Falls Rathnapura"], "wiki": "Bopath_Falls"},
    "Dehena Ella": {"trends_kw": ["Dehena Ella", "Dehena Ella Rathnapura"], "wiki": "Dehena_Ella"},
    "Delgamuwa Rajamaha Viharaya": {"trends_kw": ["Delgamuwa Rajamaha Viharaya", "Delgamuwa Rajamaha Viharaya Rathnapura"], "wiki": "Delgamuwa_Rajamaha_Viharaya"},
    "Diva Guhawa": {"trends_kw": ["Diva Guhawa", "Diva Guhawa Rathnapura"], "wiki": "Diva_Guhawa"},
    "Katugas Ella": {"trends_kw": ["Katugas Ella", "Katugas Ella Rathnapura"], "wiki": "Katugas_Ella"},
    "Kirindi Ella": {"trends_kw": ["Kirindi Ella", "Kirindi Ella Rathnapura"], "wiki": "Kirindi_Ella"},
    "Minee Ella": {"trends_kw": ["Minee Ella", "Minee Ella Rathnapura"], "wiki": "Minee_Ella"},
    "Puna Ella": {"trends_kw": ["Puna Ella", "Puna Ella Rathnapura"], "wiki": "Puna_Ella"},
    "Rathnapura National Museum": {"trends_kw": ["Rathnapura National Museum"], "wiki": "Rathnapura_National_Museum"},
    "Sri Sumana Saman Devalaya": {"trends_kw": ["Sri Sumana Saman Devalaya", "Sri Sumana Saman Devalaya Rathnapura"], "wiki": "Sri_Sumana_Saman_Devalaya"},
    "Arugam Bay Beach": {"trends_kw": ["Arugam Bay Beach", "Arugam Bay Beach Kalmunai"], "wiki": "Arugam_Bay_Beach"},
    "Kalmunai Beach Park": {"trends_kw": ["Kalmunai Beach Park", "Kalmunai Beach Park Kalmunai"], "wiki": "Kalmunai_Beach_Park"},
    "Maruthamunai Beach": {"trends_kw": ["Maruthamunai Beach", "Maruthamunai Beach Kalmunai"], "wiki": "Maruthamunai_Beach"},
    "Arankele Archaeological Site": {"trends_kw": ["Arankele Archaeological Site", "Arankele Archaeological Site Kurunagela"], "wiki": "Arankele_Archaeological_Site"},
    "Athkanda Raja Maha Viharaya": {"trends_kw": ["Athkanda Raja Maha Viharaya", "Athkanda Raja Maha Viharaya Kurunagela"], "wiki": "Athkanda_Raja_Maha_Viharaya"},
    "Athugala Viharaya": {"trends_kw": ["Athugala Viharaya", "Athugala Viharaya Kurunagela"], "wiki": "Athugala_Viharaya"},
    "Cathedral Church Of Christ The King": {"trends_kw": ["Cathedral Church Of Christ The King", "Cathedral Church Of Christ The King Kurunagela"], "wiki": "Cathedral_Church_Of_Christ_The_King"},
    "Children Park - Lakeround": {"trends_kw": ["Children Park - Lakeround", "Children Park", "Children Park Kurunagela"], "wiki": "Children_Park"},
    "Elephant Rock Viewpoint Kurunegala": {"trends_kw": ["Elephant Rock Viewpoint Kurunegala"], "wiki": "Elephant_Rock_Viewpoint_Kurunegala"},
    "Kurunagela Lake Jogging Path": {"trends_kw": ["Kurunagela Lake Jogging Path"], "wiki": "Kurunagela_Lake_Jogging_Path"},
    "Kurunegala Clock Tower": {"trends_kw": ["Kurunegala Clock Tower", "Kurunegala Clock Tower Kurunagela"], "wiki": "Kurunegala_Clock_Tower"},
    "Kurunegala Lake Round Park": {"trends_kw": ["Kurunegala Lake Round Park", "Kurunegala Lake Round Park Kurunagela"], "wiki": "Kurunegala_Lake_Round_Park"},
    "Kurunegala Lakaround Walkway": {"trends_kw": ["Kurunegala Lakaround Walkway", "Kurunegala Lakaround Walkway Kurunagela"], "wiki": "Kurunegala_Lakaround_Walkway"},
    "Kurunegala View Point": {"trends_kw": ["Kurunegala View Point", "Kurunegala View Point Kurunagela"], "wiki": "Kurunegala_View_Point"},
    "Lord Buddha Statue Athugala": {"trends_kw": ["Lord Buddha Statue Athugala", "Lord Buddha Statue Athugala Kurunagela"], "wiki": "Lord_Buddha_Statue_Athugala"},
    "Padeniya Raja Maha Viharaya": {"trends_kw": ["Padeniya Raja Maha Viharaya", "Padeniya Raja Maha Viharaya Kurunagela"], "wiki": "Padeniya_Raja_Maha_Viharaya"},
    "Panduwasnuwara Kingdom": {"trends_kw": ["Panduwasnuwara Kingdom", "Panduwasnuwara Kingdom Kurunagela"], "wiki": "Panduwasnuwara_Kingdom"},
    "Ridi Viharaya": {"trends_kw": ["Ridi Viharaya", "Ridi Viharaya Kurunagela"], "wiki": "Ridi_Viharaya"},
    "Sirigala Rock": {"trends_kw": ["Sirigala Rock", "Sirigala Rock Kurunagela"], "wiki": "Sirigala_Rock"},
    "Balakaduwa Ella Waterfall": {"trends_kw": ["Balakaduwa Ella Waterfall", "Balakaduwa Ella Waterfall Matale"], "wiki": "Balakaduwa_Ella_Waterfall"},
    "Bambarakiri Ella": {"trends_kw": ["Bambarakiri Ella", "Bambarakiri Ella Matale"], "wiki": "Bambarakiri_Ella"},
    "Dumbara Ella Waterfalls": {"trends_kw": ["Dumbara Ella Waterfalls", "Dumbara Ella Waterfalls Matale"], "wiki": "Dumbara_Ella_Waterfalls"},
    "Hulangala Mini World'S End View": {"trends_kw": ["Hulangala Mini World'S End View", "Hulangala Mini World'S End View Matale"], "wiki": "Hulangala_Mini_Worlds_End_View"},
    "Hunnasgiriya Water Falls": {"trends_kw": ["Hunnasgiriya Water Falls", "Hunnasgiriya Water Falls Matale"], "wiki": "Hunnasgiriya_Water_Falls"},
    "Kalu Ganga Reservoir Dam View Point": {"trends_kw": ["Kalu Ganga Reservoir Dam View Point", "Kalu Ganga Reservoir Dam View Point Matale"], "wiki": "Kalu_Ganga_Reservoir_Dam_View_Point"},
    "Kawanthissa Raja Maha Viharaya": {"trends_kw": ["Kawanthissa Raja Maha Viharaya", "Kawanthissa Raja Maha Viharaya Matale"], "wiki": "Kawanthissa_Raja_Maha_Viharaya"},
    "Matale Heritage Museum": {"trends_kw": ["Matale Heritage Museum"], "wiki": "Matale_Heritage_Museum"},
    "Matale Heritage Spice Garden": {"trends_kw": ["Matale Heritage Spice Garden"], "wiki": "Matale_Heritage_Spice_Garden"},
    "Matale Heritage Spice Villa": {"trends_kw": ["Matale Heritage Spice Villa"], "wiki": "Matale_Heritage_Spice_Villa"},
    "Matale Spice Garden": {"trends_kw": ["Matale Spice Garden"], "wiki": "Matale_Spice_Garden"},
    "Matale Spice Garden No 15": {"trends_kw": ["Matale Spice Garden No 15"], "wiki": "Matale_Spice_Garden_No_15"},
    "Matale Spice Villa": {"trends_kw": ["Matale Spice Villa"], "wiki": "Matale_Spice_Villa"},
    "Matale Town -  View Point": {"trends_kw": ["Matale Town -  View Point", "Matale Town", "Matale Town Matale"], "wiki": "Matale_Town"},
    "Abarana Ella": {"trends_kw": ["Abarana Ella", "Abarana Ella Hambantota"], "wiki": "Abarana_Ella"},
    "Bataatha Agro Technology And Tourism Park": {"trends_kw": ["Bataatha Agro Technology And Tourism Park", "Bataatha Agro Technology And Tourism Park Hambantota"], "wiki": "Bataatha_Agro_Technology_And_Tourism_Park"},
    "Birds Research Center Hambantota": {"trends_kw": ["Birds Research Center Hambantota"], "wiki": "Birds_Research_Center_Hambantota"},
    "Bundala National Park": {"trends_kw": ["Bundala National Park", "Bundala National Park Hambantota", "Bundala National Park Safari"], "wiki": "Bundala_National_Park"},
    "Bundala Safari With Srimal": {"trends_kw": ["Bundala Safari With Srimal", "Bundala Safari With Srimal Hambantota"], "wiki": "Bundala_Safari_With_Srimal"},
    "Dry Zone Botanic Gardens, Hambantota": {"trends_kw": ["Dry Zone Botanic Gardens, Hambantota", "Dry Zone Botanic Gardens, Hambantota Hambantota"], "wiki": "Dry_Zone_Botanic_Gardens,_Hambantota"},
    "Flamingos Safari Tours": {"trends_kw": ["Flamingos Safari Tours", "Flamingos Safari Tours Hambantota"], "wiki": "Flamingos_Safari_Tours"},
    "Hambantota Beach": {"trends_kw": ["Hambantota Beach", "Hambantota Beach Hambantota"], "wiki": "Hambantota_Beach"},
    "Hambantota Beach Park": {"trends_kw": ["Hambantota Beach Park", "Hambantota Beach Park Hambantota"], "wiki": "Hambantota_Beach_Park"},
    "Hambantota Birds Park": {"trends_kw": ["Hambantota Birds Park", "Hambantota Birds Park Hambantota"], "wiki": "Hambantota_Birds_Park"},
    "Hambantota Botanical Garden": {"trends_kw": ["Hambantota Botanical Garden", "Hambantota Botanical Garden Hambantota"], "wiki": "Hambantota_Botanical_Garden"},
    "Hambantota Fort": {"trends_kw": ["Hambantota Fort", "Hambantota Fort Hambantota"], "wiki": "Hambantota_Fort"},
    "Hambantota Heritage Museum": {"trends_kw": ["Hambantota Heritage Museum"], "wiki": "Hambantota_Heritage_Museum"},
    "Hambantota Light House Point": {"trends_kw": ["Hambantota Light House Point", "Hambantota Light House Point Hambantota"], "wiki": "Hambantota_Light_House_Point"},
    "Hambantota Salterns View Point": {"trends_kw": ["Hambantota Salterns View Point", "Hambantota Salterns View Point Hambantota"], "wiki": "Hambantota_Salterns_View_Point"},
    "Lagoon Boat Tour And Bird Watching With The Beautiful Nature": {"trends_kw": ["Lagoon Boat Tour And Bird Watching With The Beautiful Nature", "Lagoon Boat Tour And Bird Watching With The Beautiful Nature Hambantota"], "wiki": "Lagoon_Boat_Tour_And_Bird_Watching_With_The_Beautiful_Nature"},
    "Lighthouse - Hambantota": {"trends_kw": ["Lighthouse - Hambantota", "Lighthouse", "Lighthouse Hambantota"], "wiki": "Lighthouse"},
    "Mirijjawila Botanical Gardens - South Gate": {"trends_kw": ["Mirijjawila Botanical Gardens - South Gate", "Mirijjawila Botanical Gardens", "Mirijjawila Botanical Gardens Hambantota"], "wiki": "Mirijjawila_Botanical_Gardens"},
    "Mirijjawila Botanical Garden": {"trends_kw": ["Mirijjawila Botanical Garden", "Mirijjawila Botanical Garden Hambantota"], "wiki": "Mirijjawila_Botanical_Garden"},
    "National Botanical Garden Hambantota": {"trends_kw": ["National Botanical Garden Hambantota"], "wiki": "National_Botanical_Garden_Hambantota"},
    "Bahirawakanda Buddha Statue": {"trends_kw": ["Bahirawakanda Buddha Statue", "Bahirawakanda Buddha Statue Kandy"], "wiki": "Bahirawakanda_Buddha_Statue"},
    "British Garrison Cemetery": {"trends_kw": ["British Garrison Cemetery", "British Garrison Cemetery Kandy"], "wiki": "British_Garrison_Cemetery"},
    "Ceylon Tea Museum": {"trends_kw": ["Ceylon Tea Museum", "Ceylon Tea Museum Kandy"], "wiki": "Ceylon_Tea_Museum"},
    "Degaldoruwa Raja Maha Viharaya": {"trends_kw": ["Degaldoruwa Raja Maha Viharaya", "Degaldoruwa Raja Maha Viharaya Kandy"], "wiki": "Degaldoruwa_Raja_Maha_Viharaya"},
    "Gadaladeniya Vihara": {"trends_kw": ["Gadaladeniya Vihara", "Gadaladeniya Vihara Kandy"], "wiki": "Gadaladeniya_Vihara"},
    "International Buddhist Museum": {"trends_kw": ["International Buddhist Museum", "International Buddhist Museum Kandy"], "wiki": "International_Buddhist_Museum"},
    "Kandy Garrison Cemetery": {"trends_kw": ["Kandy Garrison Cemetery", "Kandy Garrison Cemetery Kandy"], "wiki": "Kandy_Garrison_Cemetery"},
    "Kandy Lake": {"trends_kw": ["Kandy Lake", "Kandy Lake Kandy"], "wiki": "Kandy_Lake"},
    "Kandy Lake Round Walk": {"trends_kw": ["Kandy Lake Round Walk", "Kandy Lake Round Walk Kandy"], "wiki": "Kandy_Lake_Round_Walk"},
    "Kandy View Point": {"trends_kw": ["Kandy View Point", "Kandy View Point Kandy"], "wiki": "Kandy_View_Point"},
    "Lankatilaka Vihara": {"trends_kw": ["Lankatilaka Vihara", "Lankatilaka Vihara Kandy"], "wiki": "Lankatilaka_Vihara"},
    "National Museum Of Kandy": {"trends_kw": ["National Museum Of Kandy"], "wiki": "National_Museum_Of_Kandy"},
    "Natha Devale": {"trends_kw": ["Natha Devale", "Natha Devale Kandy"], "wiki": "Natha_Devale"},
    "Royal Botanical Gardens Peradeniya": {"trends_kw": ["Royal Botanical Gardens Peradeniya", "Royal Botanical Gardens Peradeniya Kandy"], "wiki": "Royal_Botanical_Gardens_Peradeniya"},
    "Temple Of The Sacred Tooth Relic": {"trends_kw": ["Temple Of The Sacred Tooth Relic", "Temple Of The Sacred Tooth Relic Kandy"], "wiki": "Temple_Of_The_Sacred_Tooth_Relic"},
    "Udawatta Kele Sanctuary": {"trends_kw": ["Udawatta Kele Sanctuary", "Udawatta Kele Sanctuary Kandy"], "wiki": "Udawatta_Kele_Sanctuary"},
    "Wales Park (Royal Palace Park)": {"trends_kw": ["Wales Park (Royal Palace Park)", "Wales Park", "Wales Park Kandy"], "wiki": "Wales_Park"},
    "Black Galle Fort": {"trends_kw": ["Black Galle Fort", "Black Galle Fort Galle"], "wiki": "Black_Galle_Fort"},
    "Clock Tower Galle Fort": {"trends_kw": ["Clock Tower Galle Fort", "Clock Tower Galle Fort Galle"], "wiki": "Clock_Tower_Galle_Fort"},
    "Dutch Reformed Church Galle": {"trends_kw": ["Dutch Reformed Church Galle"], "wiki": "Dutch_Reformed_Church_Galle"},
    "Fort Rampart Beach": {"trends_kw": ["Fort Rampart Beach", "Fort Rampart Beach Galle"], "wiki": "Fort_Rampart_Beach"},
    "Galle Fort Clock Tower": {"trends_kw": ["Galle Fort Clock Tower", "Galle Fort Clock Tower Galle"], "wiki": "Galle_Fort_Clock_Tower"},
    "Galle Fort Lighthouse": {"trends_kw": ["Galle Fort Lighthouse", "Galle Fort Lighthouse Galle"], "wiki": "Galle_Fort_Lighthouse"},
    "Galle Fort Rampart": {"trends_kw": ["Galle Fort Rampart", "Galle Fort Rampart Galle"], "wiki": "Galle_Fort_Rampart"},
    "Galle Lighthouse": {"trends_kw": ["Galle Lighthouse", "Galle Lighthouse Galle"], "wiki": "Galle_Lighthouse"},
    "Japanese Peace Pagoda Galle": {"trends_kw": ["Japanese Peace Pagoda Galle"], "wiki": "Japanese_Peace_Pagoda_Galle"},
    "National Museum Galle Fort": {"trends_kw": ["National Museum Galle Fort"], "wiki": "National_Museum_Galle_Fort"},
    "Old Dutch Hospital Galle": {"trends_kw": ["Old Dutch Hospital Galle"], "wiki": "Old_Dutch_Hospital_Galle"},
    "Old Gate Galle Fort": {"trends_kw": ["Old Gate Galle Fort"], "wiki": "Old_Gate_Galle_Fort"},
    "Unawatuna Beach": {"trends_kw": ["Unawatuna Beach", "Unawatuna Beach Galle"], "wiki": "Unawatuna_Beach"},
    "Amberrella Fall View Point": {"trends_kw": ["Amberrella Fall View Point", "Amberrella Fall View Point Nuwara Eliya"], "wiki": "Amberrella_Fall_View_Point"},
    "Ambewela Farm": {"trends_kw": ["Ambewela Farm", "Ambewela Farm Nuwara Eliya"], "wiki": "Ambewela_Farm"},
    "Ambewela Railway Station": {"trends_kw": ["Ambewela Railway Station", "Ambewela Railway Station Nuwara Eliya"], "wiki": "Ambewela_Railway_Station"},
    "Baker'S Falls": {"trends_kw": ["Baker'S Falls", "Baker'S Falls Nuwara Eliya"], "wiki": "Bakers_Falls"},
    "Bomburu Ella Waterfall": {"trends_kw": ["Bomburu Ella Waterfall", "Bomburu Ella Waterfall Nuwara Eliya"], "wiki": "Bomburu_Ella_Waterfall"},
    "Damro Labookellie Tea Centre": {"trends_kw": ["Damro Labookellie Tea Centre", "Damro Labookellie Tea Centre Nuwara Eliya"], "wiki": "Damro_Labookellie_Tea_Centre"},
    "Galway'S Land National Park": {"trends_kw": ["Galway'S Land National Park", "Galway'S Land National Park Nuwara Eliya", "Galway'S Land National Park Safari"], "wiki": "Galways_Land_National_Park"},
    "Gregory Lake": {"trends_kw": ["Gregory Lake", "Gregory Lake Nuwara Eliya"], "wiki": "Gregory_Lake"},
    "Gregory Park": {"trends_kw": ["Gregory Park", "Gregory Park Nuwara Eliya"], "wiki": "Gregory_Park"},
    "Hakgala Botanical Garden": {"trends_kw": ["Hakgala Botanical Garden", "Hakgala Botanical Garden Nuwara Eliya"], "wiki": "Hakgala_Botanical_Garden"},
    "Horton Plains National Park": {"trends_kw": ["Horton Plains National Park", "Horton Plains National Park Nuwara Eliya", "Horton Plains National Park Safari"], "wiki": "Horton_Plains_National_Park"},
    "Lover'S Leap Waterfall": {"trends_kw": ["Lover'S Leap Waterfall", "Lover'S Leap Waterfall Nuwara Eliya"], "wiki": "Lovers_Leap_Waterfall"},
    "Moon Plains": {"trends_kw": ["Moon Plains", "Moon Plains Nuwara Eliya"], "wiki": "Moon_Plains"},
    "Nanu Oya Railway Station": {"trends_kw": ["Nanu Oya Railway Station", "Nanu Oya Railway Station Nuwara Eliya"], "wiki": "Nanu_Oya_Railway_Station"},
    "Nuwara Eliya Golf Club": {"trends_kw": ["Nuwara Eliya Golf Club", "Nuwara Eliya Golf Club Nuwara Eliya"], "wiki": "Nuwara_Eliya_Golf_Club"},
    "Nuwara Eliya Post Office": {"trends_kw": ["Nuwara Eliya Post Office", "Nuwara Eliya Post Office Nuwara Eliya"], "wiki": "Nuwara_Eliya_Post_Office"},
    "Pedro Tea Estate": {"trends_kw": ["Pedro Tea Estate", "Pedro Tea Estate Nuwara Eliya"], "wiki": "Pedro_Tea_Estate"},
    "Pedro Tea Factory": {"trends_kw": ["Pedro Tea Factory", "Pedro Tea Factory Nuwara Eliya"], "wiki": "Pedro_Tea_Factory"},
    "Pundaluoya Falls": {"trends_kw": ["Pundaluoya Falls", "Pundaluoya Falls Nuwara Eliya"], "wiki": "Pundaluoya_Falls"},
    "Ramboda Falls": {"trends_kw": ["Ramboda Falls", "Ramboda Falls Nuwara Eliya"], "wiki": "Ramboda_Falls"},
    "Seetha Amman Temple": {"trends_kw": ["Seetha Amman Temple", "Seetha Amman Temple Nuwara Eliya"], "wiki": "Seetha_Amman_Temple"},
    "Single Tree Hill": {"trends_kw": ["Single Tree Hill", "Single Tree Hill Nuwara Eliya"], "wiki": "Single_Tree_Hill"},
    "St. Clair'S Falls": {"trends_kw": ["St. Clair'S Falls", "St. Clair'S Falls Nuwara Eliya"], "wiki": "St_Clairs_Falls"},
    "Victoria Park Nuwara Eliya": {"trends_kw": ["Victoria Park Nuwara Eliya"], "wiki": "Victoria_Park_Nuwara_Eliya"},
    "World'S End Nuwara Eliya": {"trends_kw": ["World'S End Nuwara Eliya"], "wiki": "Worlds_End_Nuwara_Eliya"},
    "Arcade Independence Square": {"trends_kw": ["Arcade Independence Square", "Arcade Independence Square Colombo"], "wiki": "Arcade_Independence_Square"},
    "Bandaranaike Memorial International Conference Hall": {"trends_kw": ["Bandaranaike Memorial International Conference Hall", "Bandaranaike Memorial International Conference Hall Colombo"], "wiki": "Bandaranaike_Memorial_International_Conference_Hall"},
    "Barefoot Gallery": {"trends_kw": ["Barefoot Gallery", "Barefoot Gallery Colombo"], "wiki": "Barefoot_Gallery"},
    "Beira Lake": {"trends_kw": ["Beira Lake", "Beira Lake Colombo"], "wiki": "Beira_Lake"},
    "Colombo City Center": {"trends_kw": ["Colombo City Center", "Colombo City Center Colombo"], "wiki": "Colombo_City_Center"},
    "Colombo Fort Railway Station": {"trends_kw": ["Colombo Fort Railway Station", "Colombo Fort Railway Station Colombo"], "wiki": "Colombo_Fort_Railway_Station"},
    "Colombo Lighthouse": {"trends_kw": ["Colombo Lighthouse", "Colombo Lighthouse Colombo"], "wiki": "Colombo_Lighthouse"},
    "Colombo National Museum": {"trends_kw": ["Colombo National Museum", "Colombo National Museum Colombo"], "wiki": "Colombo_National_Museum"},
    "Dutch Hospital Shopping Precinct": {"trends_kw": ["Dutch Hospital Shopping Precinct", "Dutch Hospital Shopping Precinct Colombo"], "wiki": "Dutch_Hospital_Shopping_Precinct"},
    "Lotus Tower": {"trends_kw": ["Lotus Tower", "Lotus Tower Colombo"], "wiki": "Lotus_Tower"},
    "National Zoological Gardens Of Sri Lanka": {"trends_kw": ["National Zoological Gardens Of Sri Lanka", "National Zoological Gardens Of Sri Lanka Colombo"], "wiki": "National_Zoological_Gardens_Of_Sri_Lanka"},
    "One Galle Face Mall": {"trends_kw": ["One Galle Face Mall", "One Galle Face Mall Colombo"], "wiki": "One_Galle_Face_Mall"},
    "Pettah Market": {"trends_kw": ["Pettah Market", "Pettah Market Colombo"], "wiki": "Pettah_Market"},
    "Red Mosque (Jami Ul-Alfar Mosque)": {"trends_kw": ["Red Mosque (Jami Ul-Alfar Mosque)", "Red Mosque", "Red Mosque Colombo"], "wiki": "Red_Mosque"},
    "Abhayagiri Vihara": {"trends_kw": ["Abhayagiri Vihara", "Abhayagiri Vihara Anuradhapura"], "wiki": "Abhayagiri_Vihara"},
    "Abhayagiri Dagaba": {"trends_kw": ["Abhayagiri Dagaba", "Abhayagiri Dagaba Anuradhapura"], "wiki": "Abhayagiri_Dagaba"},
    "Isurumuniya Temple": {"trends_kw": ["Isurumuniya Temple", "Isurumuniya Temple Anuradhapura"], "wiki": "Isurumuniya_Temple"},
    "Jetavanaramaya": {"trends_kw": ["Jetavanaramaya", "Jetavanaramaya Anuradhapura"], "wiki": "Jetavanaramaya"},
    "Kuttam Pokuna (Twin Ponds)": {"trends_kw": ["Kuttam Pokuna (Twin Ponds)", "Kuttam Pokuna", "Kuttam Pokuna Anuradhapura"], "wiki": "Kuttam_Pokuna"},
    "Lovamahapaya": {"trends_kw": ["Lovamahapaya", "Lovamahapaya Anuradhapura"], "wiki": "Lovamahapaya"},
    "Mihintale": {"trends_kw": ["Mihintale", "Mihintale Anuradhapura"], "wiki": "Mihintale"},
    "Mirisawetiya Stupa": {"trends_kw": ["Mirisawetiya Stupa", "Mirisawetiya Stupa Anuradhapura"], "wiki": "Mirisawetiya_Stupa"},
    "Ranmasu Uyana": {"trends_kw": ["Ranmasu Uyana", "Ranmasu Uyana Anuradhapura"], "wiki": "Ranmasu_Uyana"},
    "Ruwanwelisaya": {"trends_kw": ["Ruwanwelisaya", "Ruwanwelisaya Anuradhapura"], "wiki": "Ruwanwelisaya"},
    "Samadhi Statue": {"trends_kw": ["Samadhi Statue", "Samadhi Statue Anuradhapura"], "wiki": "Samadhi_Statue"},
    "Sri Maha Bodhi": {"trends_kw": ["Sri Maha Bodhi", "Sri Maha Bodhi Anuradhapura"], "wiki": "Sri_Maha_Bodhi"},
    "Thanthirimale Raja Maha Vihara": {"trends_kw": ["Thanthirimale Raja Maha Vihara", "Thanthirimale Raja Maha Vihara Anuradhapura"], "wiki": "Thanthirimale_Raja_Maha_Vihara"},
    "Thuparamaya": {"trends_kw": ["Thuparamaya", "Thuparamaya Anuradhapura"], "wiki": "Thuparamaya"},
    "Vessagiriya": {"trends_kw": ["Vessagiriya", "Vessagiriya Anuradhapura"], "wiki": "Vessagiriya"},
    "Alahena Pirivena": {"trends_kw": ["Alahena Pirivena", "Alahena Pirivena Polonnaruwa"], "wiki": "Alahena_Pirivena"},
    "Gal Vihara": {"trends_kw": ["Gal Vihara", "Gal Vihara Polonnaruwa"], "wiki": "Gal_Vihara"},
    "Lankatilaka Temple": {"trends_kw": ["Lankatilaka Temple", "Lankatilaka Temple Polonnaruwa"], "wiki": "Lankatilaka_Temple"},
    "Nissanka Latha Mandapaya": {"trends_kw": ["Nissanka Latha Mandapaya", "Nissanka Latha Mandapaya Polonnaruwa"], "wiki": "Nissanka_Latha_Mandapaya"},
    "Pabalu Vehera": {"trends_kw": ["Pabalu Vehera", "Pabalu Vehera Polonnaruwa"], "wiki": "Pabalu_Vehera"},
    "Parakrama Samudraya": {"trends_kw": ["Parakrama Samudraya", "Parakrama Samudraya Polonnaruwa"], "wiki": "Parakrama_Samudraya"},
    "Polonnaruwa Ancient City": {"trends_kw": ["Polonnaruwa Ancient City", "Polonnaruwa Ancient City Polonnaruwa"], "wiki": "Polonnaruwa_Ancient_City"},
    "Polonnaruwa Museum": {"trends_kw": ["Polonnaruwa Museum", "Polonnaruwa Museum Polonnaruwa"], "wiki": "Polonnaruwa_Museum"},
    "Polonnaruwa Vatadage": {"trends_kw": ["Polonnaruwa Vatadage", "Polonnaruwa Vatadage Polonnaruwa"], "wiki": "Polonnaruwa_Vatadage"},
    "Quadrangle (Dalada Malaluwa)": {"trends_kw": ["Quadrangle (Dalada Malaluwa)", "Quadrangle", "Quadrangle Polonnaruwa"], "wiki": "Quadrangle"},
    "Rankoth Vehera": {"trends_kw": ["Rankoth Vehera", "Rankoth Vehera Polonnaruwa"], "wiki": "Rankoth_Vehera"},
    "Royal Palace Of King Parakramabahu": {"trends_kw": ["Royal Palace Of King Parakramabahu", "Royal Palace Of King Parakramabahu Polonnaruwa"], "wiki": "Royal_Palace_Of_King_Parakramabahu"},
    "Siva Devale No 2": {"trends_kw": ["Siva Devale No 2", "Siva Devale No 2 Polonnaruwa"], "wiki": "Siva_Devale_No_2"},
    "Thuparama Gedige": {"trends_kw": ["Thuparama Gedige", "Thuparama Gedige Polonnaruwa"], "wiki": "Thuparama_Gedige"},
    "Tiwanka Image House": {"trends_kw": ["Tiwanka Image House", "Tiwanka Image House Polonnaruwa"], "wiki": "Tiwanka_Image_House"},
    "Casuarina Beach": {"trends_kw": ["Casuarina Beach", "Casuarina Beach Jaffna"], "wiki": "Casuarina_Beach"},
    "Charty Beach": {"trends_kw": ["Charty Beach", "Charty Beach Jaffna"], "wiki": "Charty_Beach"},
    "Dambakola Patuna": {"trends_kw": ["Dambakola Patuna", "Dambakola Patuna Jaffna"], "wiki": "Dambakola_Patuna"},
    "Delft Island (Neduntheevu)": {"trends_kw": ["Delft Island (Neduntheevu)", "Delft Island", "Delft Island Jaffna"], "wiki": "Delft_Island"},
    "Jaffna Fort": {"trends_kw": ["Jaffna Fort", "Jaffna Fort Jaffna"], "wiki": "Jaffna_Fort"},
    "Jaffna Public Library": {"trends_kw": ["Jaffna Public Library", "Jaffna Public Library Jaffna"], "wiki": "Jaffna_Public_Library"},
    "Keerimalai Hot Springs": {"trends_kw": ["Keerimalai Hot Springs", "Keerimalai Hot Springs Jaffna"], "wiki": "Keerimalai_Hot_Springs"},
    "Kadurugoda Temple": {"trends_kw": ["Kadurugoda Temple", "Kadurugoda Temple Jaffna"], "wiki": "Kadurugoda_Temple"},
    "Nagadeepa Purana Viharaya": {"trends_kw": ["Nagadeepa Purana Viharaya", "Nagadeepa Purana Viharaya Jaffna"], "wiki": "Nagadeepa_Purana_Viharaya"},
    "Nallur Kandaswamy Kovil": {"trends_kw": ["Nallur Kandaswamy Kovil", "Nallur Kandaswamy Kovil Jaffna"], "wiki": "Nallur_Kandaswamy_Kovil"},
    "Nallur Kandaswamy Temple": {"trends_kw": ["Nallur Kandaswamy Temple", "Nallur Kandaswamy Temple Jaffna"], "wiki": "Nallur_Kandaswamy_Temple"},
    "Point Pedro Lighthouse": {"trends_kw": ["Point Pedro Lighthouse", "Point Pedro Lighthouse Jaffna"], "wiki": "Point_Pedro_Lighthouse"},
    "Wild Horses Of Delft": {"trends_kw": ["Wild Horses Of Delft", "Wild Horses Of Delft Jaffna"], "wiki": "Wild_Horses_Of_Delft"},
    "Dambulla Cave Temple": {"trends_kw": ["Dambulla Cave Temple", "Dambulla Cave Temple Sigiriya"], "wiki": "Dambulla_Cave_Temple"},
    "Golden Temple Dambulla": {"trends_kw": ["Golden Temple Dambulla", "Golden Temple Dambulla Sigiriya"], "wiki": "Golden_Temple_Dambulla"},
    "Ibbankatuwa Megalithic Tombs": {"trends_kw": ["Ibbankatuwa Megalithic Tombs", "Ibbankatuwa Megalithic Tombs Sigiriya"], "wiki": "Ibbankatuwa_Megalithic_Tombs"},
    "Kandalama Dam View Point": {"trends_kw": ["Kandalama Dam View Point", "Kandalama Dam View Point Sigiriya"], "wiki": "Kandalama_Dam_View_Point"},
    "Mirror Wall Sigiriya": {"trends_kw": ["Mirror Wall Sigiriya"], "wiki": "Mirror_Wall_Sigiriya"},
    "Pidurangala Rock": {"trends_kw": ["Pidurangala Rock", "Pidurangala Rock Sigiriya"], "wiki": "Pidurangala_Rock"},
    "Popham'S Arboretum": {"trends_kw": ["Popham'S Arboretum", "Popham'S Arboretum Sigiriya"], "wiki": "Pophams_Arboretum"},
    "Sigiriya Archaeological Museum": {"trends_kw": ["Sigiriya Archaeological Museum"], "wiki": "Sigiriya_Archaeological_Museum"},
    "Sigiriya Frescoes": {"trends_kw": ["Sigiriya Frescoes", "Sigiriya Frescoes Sigiriya"], "wiki": "Sigiriya_Frescoes"},
    "Sigiriya Lion Paw": {"trends_kw": ["Sigiriya Lion Paw", "Sigiriya Lion Paw Sigiriya"], "wiki": "Sigiriya_Lion_Paw"},
    "Sigiriya Museum": {"trends_kw": ["Sigiriya Museum", "Sigiriya Museum Sigiriya"], "wiki": "Sigiriya_Museum"},
    "Sigiriya Rock Fortress": {"trends_kw": ["Sigiriya Rock Fortress", "Sigiriya Rock Fortress Sigiriya"], "wiki": "Sigiriya_Rock_Fortress"},
    "Sigiriya Water Gardens": {"trends_kw": ["Sigiriya Water Gardens", "Sigiriya Water Gardens Sigiriya"], "wiki": "Sigiriya_Water_Gardens"},
    "Kataragama Temple": {"trends_kw": ["Kataragama Temple", "Kataragama Temple Hambantota"], "wiki": "Kataragama_Temple"},
    "Kiri Vehera Kataragama": {"trends_kw": ["Kiri Vehera Kataragama", "Kiri Vehera Kataragama Hambantota"], "wiki": "Kiri_Vehera_Kataragama"},
    "Sellem Kataragama": {"trends_kw": ["Sellem Kataragama", "Sellem Kataragama Hambantota"], "wiki": "Sellem_Kataragama"},
    "Yala National Park Block 1 Entrance": {"trends_kw": ["Yala National Park Block 1 Entrance", "Yala National Park Block 1 Entrance Hambantota"], "wiki": "Yala_National_Park_Block_1_Entrance"},
    "Yala National Park Katagamuwa Entrance": {"trends_kw": ["Yala National Park Katagamuwa Entrance", "Yala National Park Katagamuwa Entrance Hambantota"], "wiki": "Yala_National_Park_Katagamuwa_Entrance"},
    "Yala Safari Center": {"trends_kw": ["Yala Safari Center", "Yala Safari Center Hambantota"], "wiki": "Yala_Safari_Center"},
    "Ayr Islet Fort Frederick": {"trends_kw": ["Ayr Islet Fort Frederick", "Ayr Islet Fort Frederick Trincomalee"], "wiki": "Ayr_Islet_Fort_Frederick"},
    "Fort Frederick Trincomalee": {"trends_kw": ["Fort Frederick Trincomalee"], "wiki": "Fort_Frederick_Trincomalee"},
    "Kanniya Hot Springs": {"trends_kw": ["Kanniya Hot Springs", "Kanniya Hot Springs Trincomalee"], "wiki": "Kanniya_Hot_Springs"},
    "Koneswaram Temple": {"trends_kw": ["Koneswaram Temple", "Koneswaram Temple Trincomalee"], "wiki": "Koneswaram_Temple"},
    "Marble Beach Trincomalee": {"trends_kw": ["Marble Beach Trincomalee"], "wiki": "Marble_Beach_Trincomalee"},
    "Nilaveli Beach": {"trends_kw": ["Nilaveli Beach", "Nilaveli Beach Trincomalee"], "wiki": "Nilaveli_Beach"},
    "Pigeon Island National Park": {"trends_kw": ["Pigeon Island National Park", "Pigeon Island National Park Trincomalee", "Pigeon Island National Park Safari"], "wiki": "Pigeon_Island_National_Park"},
    "Swami Rock": {"trends_kw": ["Swami Rock", "Swami Rock Trincomalee"], "wiki": "Swami_Rock"},
    "Trincomalee War Cemetery": {"trends_kw": ["Trincomalee War Cemetery", "Trincomalee War Cemetery Trincomalee"], "wiki": "Trincomalee_War_Cemetery"},
    "Uppuveli Beach": {"trends_kw": ["Uppuveli Beach", "Uppuveli Beach Trincomalee"], "wiki": "Uppuveli_Beach"},
    "Batticaloa Fort": {"trends_kw": ["Batticaloa Fort", "Batticaloa Fort Badulla"], "wiki": "Batticaloa_Fort"},
    "Batticaloa Gate": {"trends_kw": ["Batticaloa Gate", "Batticaloa Gate Badulla"], "wiki": "Batticaloa_Gate"},
    "Batticaloa Lighthouse": {"trends_kw": ["Batticaloa Lighthouse", "Batticaloa Lighthouse Badulla"], "wiki": "Batticaloa_Lighthouse"},
    "Bogoda Bridge": {"trends_kw": ["Bogoda Bridge", "Bogoda Bridge Badulla"], "wiki": "Bogoda_Bridge"},
    "Dambana Vedda Village": {"trends_kw": ["Dambana Vedda Village", "Dambana Vedda Village Badulla"], "wiki": "Dambana_Vedda_Village"},
    "Kallady Bridge": {"trends_kw": ["Kallady Bridge", "Kallady Bridge Badulla"], "wiki": "Kallady_Bridge"},
    "Mahiyanganaya Raja Maha Vihara": {"trends_kw": ["Mahiyanganaya Raja Maha Vihara", "Mahiyanganaya Raja Maha Vihara Badulla"], "wiki": "Mahiyanganaya_Raja_Maha_Vihara"},
    "Pasikudah Beach": {"trends_kw": ["Pasikudah Beach", "Pasikudah Beach Badulla"], "wiki": "Pasikudah_Beach"},
    "Belihuloya": {"trends_kw": ["Belihuloya", "Belihuloya Rathnapura"], "wiki": "Belihuloya"},
    "Belihuloya Bridge View Point": {"trends_kw": ["Belihuloya Bridge View Point", "Belihuloya Bridge View Point Rathnapura"], "wiki": "Belihuloya_Bridge_View_Point"},
    "Brampton Falls": {"trends_kw": ["Brampton Falls", "Brampton Falls Rathnapura"], "wiki": "Brampton_Falls"},
    "Chandrika Wewa": {"trends_kw": ["Chandrika Wewa", "Chandrika Wewa Rathnapura"], "wiki": "Chandrika_Wewa"},
    "Hawagala Mountain": {"trends_kw": ["Hawagala Mountain", "Hawagala Mountain Rathnapura"], "wiki": "Hawagala_Mountain"},
    "Kalthota Doowili Ella": {"trends_kw": ["Kalthota Doowili Ella", "Kalthota Doowili Ella Rathnapura"], "wiki": "Kalthota_Doowili_Ella"},
    "Kirikilla Ella": {"trends_kw": ["Kirikilla Ella", "Kirikilla Ella Rathnapura"], "wiki": "Kirikilla_Ella"},
    "Maduwanwela Walawwa": {"trends_kw": ["Maduwanwela Walawwa", "Maduwanwela Walawwa Rathnapura"], "wiki": "Maduwanwela_Walawwa"},
    "Nonpareil Estate Waterfall": {"trends_kw": ["Nonpareil Estate Waterfall", "Nonpareil Estate Waterfall Rathnapura"], "wiki": "Nonpareil_Estate_Waterfall"},
    "Pahanthudawa Waterfall": {"trends_kw": ["Pahanthudawa Waterfall", "Pahanthudawa Waterfall Rathnapura"], "wiki": "Pahanthudawa_Waterfall"},
    "Surathali Ella": {"trends_kw": ["Surathali Ella", "Surathali Ella Rathnapura"], "wiki": "Surathali_Ella"},
    "Wawulpane Limestone Cave": {"trends_kw": ["Wawulpane Limestone Cave", "Wawulpane Limestone Cave Rathnapura"], "wiki": "Wawulpane_Limestone_Cave"},
    "Badulla Railway Station": {"trends_kw": ["Badulla Railway Station", "Badulla Railway Station Badulla"], "wiki": "Badulla_Railway_Station"},
    "Demodara Nine Arch Bridge": {"trends_kw": ["Demodara Nine Arch Bridge", "Demodara Nine Arch Bridge Badulla"], "wiki": "Demodara_Nine_Arch_Bridge"},
    "Demodara Railway Loop": {"trends_kw": ["Demodara Railway Loop", "Demodara Railway Loop Badulla"], "wiki": "Demodara_Railway_Loop"},
    "Diyaluma Falls Viewpoint": {"trends_kw": ["Diyaluma Falls Viewpoint", "Diyaluma Falls Viewpoint Badulla"], "wiki": "Diyaluma_Falls_Viewpoint"},
    "Diyaluma Upper Falls Pool": {"trends_kw": ["Diyaluma Upper Falls Pool", "Diyaluma Upper Falls Pool Badulla"], "wiki": "Diyaluma_Upper_Falls_Pool"},
    "Haputale Gap": {"trends_kw": ["Haputale Gap", "Haputale Gap Badulla"], "wiki": "Haputale_Gap"},
    "Idalgashinna Railway Station": {"trends_kw": ["Idalgashinna Railway Station", "Idalgashinna Railway Station Badulla"], "wiki": "Idalgashinna_Railway_Station"},
    "Idalgashinna Ridge Trail": {"trends_kw": ["Idalgashinna Ridge Trail", "Idalgashinna Ridge Trail Badulla"], "wiki": "Idalgashinna_Ridge_Trail"},
    "Lipton'S Seat Haputale": {"trends_kw": ["Lipton'S Seat Haputale", "Lipton'S Seat Haputale Badulla"], "wiki": "Liptons_Seat_Haputale"},
    "Namunukula Mountain": {"trends_kw": ["Namunukula Mountain", "Namunukula Mountain Badulla"], "wiki": "Namunukula_Mountain"},
    "Ohiya Railway Station": {"trends_kw": ["Ohiya Railway Station", "Ohiya Railway Station Badulla"], "wiki": "Ohiya_Railway_Station"},
    "Ravana Falls": {"trends_kw": ["Ravana Falls", "Ravana Falls Badulla"], "wiki": "Ravana_Falls"},
    "Upper Diyaluma Falls": {"trends_kw": ["Upper Diyaluma Falls", "Upper Diyaluma Falls Badulla"], "wiki": "Upper_Diyaluma_Falls"},
    "Baker'S Fall Trail": {"trends_kw": ["Baker'S Fall Trail", "Baker'S Fall Trail Nuwara Eliya"], "wiki": "Bakers_Fall_Trail"},
    "Chimney Pool Horton Plains": {"trends_kw": ["Chimney Pool Horton Plains", "Chimney Pool Horton Plains Nuwara Eliya"], "wiki": "Chimney_Pool_Horton_Plains"},
    "Horton Plains Visitor Centre": {"trends_kw": ["Horton Plains Visitor Centre", "Horton Plains Visitor Centre Nuwara Eliya"], "wiki": "Horton_Plains_Visitor_Centre"},
    "New Zealand Farm Ambewela": {"trends_kw": ["New Zealand Farm Ambewela", "New Zealand Farm Ambewela Nuwara Eliya"], "wiki": "New_Zealand_Farm_Ambewela"},
    "Pattipola Agricultural Farm": {"trends_kw": ["Pattipola Agricultural Farm", "Pattipola Agricultural Farm Nuwara Eliya"], "wiki": "Pattipola_Agricultural_Farm"},
    "Pattipola Railway Station": {"trends_kw": ["Pattipola Railway Station", "Pattipola Railway Station Nuwara Eliya"], "wiki": "Pattipola_Railway_Station"},
    "Buduruwagala Rock Temple": {"trends_kw": ["Buduruwagala Rock Temple", "Buduruwagala Rock Temple Ella"], "wiki": "Buduruwagala_Rock_Temple"},
    "Ella Gap Viewpoint": {"trends_kw": ["Ella Gap Viewpoint", "Ella Gap Viewpoint Ella"], "wiki": "Ella_Gap_Viewpoint"},
    "Ella Rock": {"trends_kw": ["Ella Rock", "Ella Rock Ella"], "wiki": "Ella_Rock"},
    "Ella Spice Garden": {"trends_kw": ["Ella Spice Garden", "Ella Spice Garden Ella"], "wiki": "Ella_Spice_Garden"},
    "Ella Town Walkway": {"trends_kw": ["Ella Town Walkway", "Ella Town Walkway Ella"], "wiki": "Ella_Town_Walkway"},
    "Idalgashinna": {"trends_kw": ["Idalgashinna", "Idalgashinna Ella"], "wiki": "Idalgashinna"},
    "Kithal Ella Waterfall": {"trends_kw": ["Kithal Ella Waterfall", "Kithal Ella Waterfall Ella"], "wiki": "Kithal_Ella_Waterfall"},
    "Little Adam'S Peak Ella": {"trends_kw": ["Little Adam'S Peak Ella"], "wiki": "Little_Adams_Peak_Ella"},
    "Nine Arch Bridge Ella": {"trends_kw": ["Nine Arch Bridge Ella"], "wiki": "Nine_Arch_Bridge_Ella"},
    "Ravana Cave": {"trends_kw": ["Ravana Cave", "Ravana Cave Ella"], "wiki": "Ravana_Cave"},
    "Ravana Pool Club Ella": {"trends_kw": ["Ravana Pool Club Ella"], "wiki": "Ravana_Pool_Club_Ella"},
    "Ravana Temple": {"trends_kw": ["Ravana Temple", "Ravana Temple Ella"], "wiki": "Ravana_Temple"},
    "Secret Waterfall Ella": {"trends_kw": ["Secret Waterfall Ella"], "wiki": "Secret_Waterfall_Ella"},
}


def fetch_google_trends(name: str, keywords: list[str], geo: str = TRENDS_GEO,
                         timeframe: str = TRENDS_TIMEFRAME, max_retries: int = 3) -> pd.DataFrame:
    """Weekly Google Trends interest-over-time for one place, cached to disk
    so a re-run never re-hits already-fetched keywords."""
    cache_path = CACHE_DIR / f"{name}_{geo or 'WW'}.csv"
    if cache_path.exists():
        print(f"  [cache hit] {name} [{geo or 'worldwide'}]")
        return pd.read_csv(cache_path, index_col=0, parse_dates=True)

    pytrends = TrendReq(hl="en-US", tz=330)
    for attempt in range(1, max_retries + 1):
        try:
            pytrends.build_payload(keywords, timeframe=timeframe, geo=geo)
            df = pytrends.interest_over_time()
            if df.empty:
                return pd.DataFrame()
            df = df.drop(columns=["isPartial"], errors="ignore")
            df.to_csv(cache_path)
            return df
        except Exception as e:
            if "429" in str(e):
                wait = (2 ** attempt) * 15 + random.uniform(2, 5)
                print(f"  [rate limited] {name}, attempt {attempt}/{max_retries}, waiting {wait:.0f}s...")
                time.sleep(wait)
            else:
                print(f"  [failed] {name}: {e}")
                break
    return pd.DataFrame()


def fetch_wikipedia_pageviews(article: str, start: str = WIKI_START, end: str = WIKI_END) -> pd.DataFrame:
    """Monthly Wikipedia page views for one article, via the Wikimedia REST
    pageviews API (no API key required)."""
    url = (
        "https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/"
        f"en.wikipedia/all-access/all-agents/{article}/monthly/{start}/{end}"
    )
    resp = requests.get(url, headers={"User-Agent": "ceylon-tourism-ai/1.0"}, timeout=30)
    if resp.status_code != 200:
        return pd.DataFrame()
    items = resp.json().get("items", [])
    if not items:
        return pd.DataFrame()
    return pd.DataFrame([
        {"date": pd.to_datetime(it["timestamp"][:8]), "views": it["views"]}
        for it in items
    ])


def collect_trends(destinations: dict) -> pd.DataFrame:
    records = []
    consecutive_failures = 0
    for name, cfg in destinations.items():
        if consecutive_failures >= 3:
            print("\n3 consecutive live API failures — stopping to avoid a persistent IP block.")
            break
        print(f"Fetching Trends: {name}...")
        df = fetch_google_trends(name, cfg["trends_kw"])
        if df.empty:
            consecutive_failures += 1
            time.sleep(10)
            continue
        consecutive_failures = 0
        for kw in df.columns:
            for date, val in df[kw].items():
                records.append({"destination": name, "geo": TRENDS_GEO, "keyword": kw, "date": date, "trend_index": val})
        time.sleep(random.uniform(20, 35))  # stay well under Trends' rate limit
    return pd.DataFrame(records)


def collect_wikipedia(destinations: dict) -> pd.DataFrame:
    records = []
    for name, cfg in destinations.items():
        print(f"Fetching Wikipedia views: {name}...")
        df = fetch_wikipedia_pageviews(cfg["wiki"])
        if df.empty:
            continue
        df["destination"] = name
        records.append(df)
        time.sleep(1)  # Wikimedia's REST API is generous but still be polite
    return pd.concat(records, ignore_index=True) if records else pd.DataFrame(columns=["date", "views", "destination"])


if __name__ == "__main__":
    print(f"Collecting Trends + Wikipedia signal for {len(DESTINATIONS)} places...")

    trends_master = collect_trends(DESTINATIONS)
    trends_master.to_csv(DATA_DIR / "trends_master.csv", index=False)
    print(f"Saved trends_master.csv: {len(trends_master)} rows, {trends_master['destination'].nunique()} places")

    wiki_master = collect_wikipedia(DESTINATIONS)
    wiki_master.to_csv(DATA_DIR / "wiki_master.csv", index=False)
    print(f"Saved wiki_master.csv: {len(wiki_master)} rows, {wiki_master['destination'].nunique()} places")

    print("\nDone. Run train_module3.py next to rebuild the model from this data.")