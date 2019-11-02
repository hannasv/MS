import cdsapi
import glob

c = cdsapi.Client()

c.retrieve(
'reanalysis-era5-pressure-levels', # reanalysis-era5-single-levels
{
    #'class'='ea', # era5 data
    #'expver' = '1', # ??
	'area'    : "75/-15/57/42", # retrieving subarea :Europe
	"type" : "an", # analysis
    'product_type':'reanalysis',
    'format':'grib',
    'day':[
        '01','02','03',
        '04','05','06',
        '07','08','09',
        '10','11','12',
        '13','14','15',
        '16','17','18',
        '19','20','21',
        '22','23','24',
        '25','26','27',
        '28','29','30',
        '31'
    ],
    'month':["12","01","02"],
    'year': ['1979','1980','1981','1982','1983','1984','1985','1986','1987'],

    'pressure_level':['0','250','600','850','1000'],
    'variable':'relative_humidity',
    'time':[
        '00:00','01:00','02:00','03:00',
        '04:00','05:00','06:00',
        '07:00','08:00','09:00',
        '10:00','11:00','12:00',
        '13:00','14:00','15:00',
        '16:00','17:00','18:00',
        '19:00','20:00','21:00',
        '22:00','23:00'],
"stream": "oper", # sub-daily data
},
'./negative_rh.grib')
