def get_data():
    """
    get_data() is a function which automatically goes into the soccom.ucsd.edu website, and accesses the 
    past trajectory data (and also the WMOID of that float) then creates a pickle within the directory you are in
    with the following variables: [index, WMOID, Latitude, Longitude, SOCCOM].
    SOCCOM is a list that is simply true or false to demonstrate if that ARGO float is part of those dropped by
    SOCCOM.
    """
    
    #import necessary modules:
    import os
    import pandas as pd
    from ftplib import FTP 
    import argparse
    import folium
    import folium.plugins
    import numpy as np
    from itertools import cycle
    import requests
    
    url = 'http://soccom.ucsd.edu/floats/SOCCOM_float_stats.html'
    #this is the website from which we can get the information we want about the floats
    online = requests.get(url).content  
    #requests is used to go to the url and get the info
    df_list = pd.read_html(online)  
    #data_list uses the online to go to the url using pd.read_html instead of something like pd.read_Csv
    wmoID_list = df_list[-1]['TrajdataWMOID'].values
    wmoID_list = [str(dummy) for dummy in wmoID_list]
    #adds the wmoid list to the dataframe - necessary to loop through later
    
    #gets the information from the ar_index_global_prof.txt by accessing the website that comes from 
    link = 'usgodae.org'
    ftp = FTP(link) 
    ftp.login()
    ftp.cwd('pub/outgoing/argo')
    filename = 'ar_index_global_prof.txt'
    file = open(filename, 'wb')
    ftp.retrbinary('RETR %s' % filename,file.write,8*1024)
    file.close()
    ftp.close()
    #creates a new pandas dataframe from the usgodae database
    df_ = pd.read_csv(filename,skiprows=8)
    df_['FLOAT'] = [dummy.split('/')[1] for dummy in df_['file'].values]
    #creates columns within the pandas dataframe: float, longitude, latitude
    df_ = df_[['FLOAT','latitude','longitude']]
    #get ride of some bad longitudes within the dataframe
    df_ = df_[df_.longitude!=99999]
    df_ = df_[df_.longitude!=-999]
    df_ = df_[df_.longitude<=180]
    #create the soccom true or false bit
    df_['SOCCOM'] = df_.FLOAT.isin(wmoID_list)
    #use assert to make sure it's reasonable values for lon/lat
    assert df_.longitude.min()>-180
    assert df_.longitude.max()<=180
    assert df_.latitude.min()>-90
    assert df_.latitude.max()<90
    #make the pickle!
    df_.to_pickle('traj_data.pickle')
    return df_

def get_Lon():
    """
    get_Lon() is a function which pops up a gui window into which a longitude can be entered, and then
    it is stored as a global variable.
    """
    
    import tkinter as tk
    
    HEIGHT = 300 #set heigh and width for ease
    WIDTH = 600
    
    #GET THE LATITUDE:
    def get_Lon(entry):
        global Lon #need to make it global so we can use it once it's made within the function
        Lon = float(entry) #need it to be a float value
        print("Longitude Entered: ", entry)
        root.destroy() #gets rid of the window once you click enter
    
    root = tk.Tk() #begins the process to add to
    root.wm_attributes("-topmost", 1)

    canvas = tk.Canvas(root, height=HEIGHT, width=WIDTH) #creates the canvas
    canvas.pack()

    background_image = tk.PhotoImage(file='SOCCOM_logo.png') #make a cool background using soccom logo
    background_label = tk.Label(root, image=background_image)
    background_label.place(relwidth=1, relheight=1)

    frame = tk.Frame(root, bd=5)# bg='#80c1ff', bd=5) #make a frame around the entry
    frame.place(relx=0.5, rely=0.5, relwidth=0.55, relheight=0.3, anchor='n')

    entry = tk.Entry(frame, font=40) #make the entry
    entry.place(relwidth=1, relheight=1)

    button = tk.Button(frame, text="Enter Lon", font=40, command=lambda: get_Lon(entry.get())) #make the button
    #using a lambda function so you can re-define each time
    button.place(relx=0.7, relheight=1, relwidth=0.3)

    root.mainloop()
    
    return(Lon)

def get_Lat():
    """
    get_Lat() is a function which pops up a gui window into which a latitude can be entered, and then
    it is stored as a global variable.
    """
    import tkinter as tk
    
    HEIGHT = 300 #set heigh and width for ease
    WIDTH = 600
    
    #GET THE LATITUDE:
    def get_Lat(entry):
        global Lat #need to make it global so we can use it once it's made within the function
        Lat = float(entry) #need it to be a float value
        print("Longitude Entered: ", entry)
        root.destroy() #gets rid of the window once you click enter
    
    root = tk.Tk() #begins the process to add to
    root.wm_attributes("-topmost", 1)

    canvas = tk.Canvas(root, height=HEIGHT, width=WIDTH) #creates the canvas
    canvas.pack()

    background_image = tk.PhotoImage(file='SOCCOM_logo.png') #make a cool background using soccom logo
    background_label = tk.Label(root, image=background_image)
    background_label.place(relwidth=1, relheight=1)

    frame = tk.Frame(root, bd=5)# bg='#80c1ff', bd=5) #make a frame around the entry
    frame.place(relx=0.5, rely=0.5, relwidth=0.55, relheight=0.3, anchor='n')

    entry = tk.Entry(frame, font=40) #make the entry
    entry.place(relwidth=1, relheight=1)

    button = tk.Button(frame, text="Enter Lat", font=40, command=lambda: get_Lat(entry.get())) #make the button
    #using a lambda function so you can re-define each time
    button.place(relx=0.7, relheight=1, relwidth=0.3)

    root.mainloop()
    
    return(Lat)

def plot_the_floats(lon,lat):
    """
    plot_the_floats() is a function which takes a (lon,lat) entry, and then creates a 20 by 30 degree
    mercator map with the past ARGO trajectories plotted as differently colored lines. 
    In order to run this function, you must have the 'traj_data.pickle' which is a pickle of the past ARGO 
    trajectories.
    """
    
    #import all necessary modules
    import pandas as pd
    #import oceans
    import matplotlib.pyplot as plt
    from IPython.display import Image
    import numpy as np
    import cartopy
    import cartopy.crs as ccrs
    from cartopy import config
    from cartopy.mpl.ticker import LongitudeFormatter, LatitudeFormatter
    from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER
    from cartopy import feature as cfeature
    from cartopy.feature import NaturalEarthFeature, LAND, COASTLINE, OCEAN, LAKES, BORDERS
    import matplotlib.ticker as mticker
    
    #read in the data set
    data = pd.read_pickle('traj_data.pickle')
    #make the general max and min for the map
    lllat = lat- 20;
    urlat = lat+20;
    lllon = lon-30;
    urlon = lon+30;
    #find midlon for the cartopy map
    midlon = (urlon-lllon)/2;
    #you will use this to limit the trajectories 
    degree_size=0.5;
    
    #create the figure, mercator projection, with coastlines
    plt.figure()
    ax = plt.axes(projection=ccrs.Mercator(
        central_longitude=midlon, min_latitude= lllat, max_latitude= urlat, globe=None))
    ax.coastlines()
    
    #label axes and make title
    ax.set_xlabel('Lat (degrees)')
    ax.set_ylabel('Lon (degrees)')
    ax.set_title('ARGO Trajectories for a float at '+str(lon)+', '+str(lat))
    
    #make the Lon/Lat labels
    ylabels=np.arange(-90,91,10)
    xlabels=np.arange(-180.,181,10.)
    g1=ax.gridlines(xlocs=xlabels,ylocs=ylabels, crs=ccrs.PlateCarree(),linewidth=2,linestyle='dotted',draw_labels=False)
    glabels = ax.gridlines(xlocs=xlabels,
                   ylocs=ylabels,
                   draw_labels=True, alpha=0)
    glabels.xlabels_top = False
    glabels.ylabels_right = False
    
    #THESE lat and lon max and min are for choosing the trajectories
    lat_min = lat- degree_size
    lat_max = lat+ degree_size
    lon_min = lon-degree_size
    lon_max = lon+degree_size
    data_cut = data[((data.longitude<lon_max)&(data.longitude>lon_min))&\
                    ((data.latitude<lat_max)&(data.latitude>lat_min))]
    
    #stock image for making it look good and also basic basic bathymetry
    ax.stock_img()

    #loops through the floats within the data file, creates new variable token of the right trajectories, then
    #plots the token trajectories
    for Float in data_cut.FLOAT.unique():
        token = data[(data.FLOAT == Float)]
        if len(token)<=2:
               continue 
        else:
            ax.plot(token['longitude'],token['latitude'],marker='.',markersize=2,transform=ccrs.Geodetic())
    
    #now plot the original latitude and longitude so you can see where they're all coming from
    ax.plot(lon,lat,marker='*',color='gold',markersize=10,transform=ccrs.Geodetic(),\
        markeredgecolor='black',markeredgewidth=2)
    #set the extent so it doesnt go crazy and show way too much
    ax.set_extent((lllon,urlon,lllat,urlat), crs=None)
    
    #save the figure to your directory
    plt.savefig('ARGO_Traj_'+str(lon)+'_'+str(lat)+'.png')
    
        
def get_Plot():
    """
    get_Plot() is a function which uses the functions get_Lon(), get_Lat(), and plot_the_floats() in order to 
    effortlessly plot an ARGO trajectory plot.
    """
    
    # get the file name
    Lon=get_Lon()
    # read in the data and make the mesh
    # make the map
    Lat=get_Lat()
    plot_the_floats(Lon,Lat)
    #Show_Plot(Lon,Lat)

get_Plot()
