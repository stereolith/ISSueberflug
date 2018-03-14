def run_script(iface):
    import math
    from qgis.core import QgsMapLayerRegistry

#Importiere Vektorlayer zur verarbeitung hier im Skript
    layerSatellit = None
    layerUserStandort = None
    for lyr in QgsMapLayerRegistry.instance().mapLayers().values():
        if lyr.name() == "UserStandort":
            layerUserStandort = lyr
        if lyr.name() == "ISS":
            layerSatellit = lyr

 #uebergibt Wert des Attributes "attName" des ersten Features im Layer "layer"
    def getFirstAttributeValue(layer, attName):
        iter = layer.getFeatures()
        for feature in iter:
            return feature[attName]

#   ---
#   Hauptfunktion zum Aktualisieren der Distanz, der Elevation und des Azimuth
#   ---
    def calculate():
        #Extrahiere Positionsdaten aus den Attributen des ISS-Layer (Bei nicht aktiviertem TimeManager wird nur das erste feature extrahiert)
        coordSat = {'lat': getFirstAttributeValue(layerSatellit, 'latitude'), 'lon': getFirstAttributeValue(layerSatellit, 'longitude'), 'elv': getFirstAttributeValue(layerSatellit, 'altitude')*1000}
        satPoint = locationToPoint(coordSat)
        
        #iteriert die Features (hier: Punkte) im Vektorlayer UserStandort
        iter = layerUserStandort.getFeatures()
        for feature in iter:
            #extrahiert die positionsdaten von Punkt
            geom = feature.geometry()
            pointErde = geom.asPoint()
            coordErde = {'lat': pointErde.y(), 'lon': pointErde.x(), 'elv': 0.0}
            erdePoint = locationToPoint(coordErde)
            
            #Berechnet Distanz, Azimuth und Elevation zu Satellit
            distMeter = distancePoints(erdePoint, satPoint)
            distKM = distMeter * 0.001
            az = cAzimuth(coordErde, coordSat)
            elevation = cElevation(erdePoint, satPoint)
            
            #Ergebnisse in die Attribute von dem aktuellen feature speichern, damit Label Daten beziehen koennen
            layerUserStandort.startEditing()
            
            feature['distance'] = distKM
            feature['azimuth'] = az
            feature['elevation'] = elevation
            
            layerUserStandort.updateFeature(feature) #Aenderungen updaten/ speichern
            layerUserStandort.commitChanges()
            
            print "Distanz, Azimuth und Elevation erfolgreich fuer Punkt " + str(feature.id()) +" aktualisiert."
            
#Folgende Funktion: jeromer @ https://gist.github.com/jeromer/2005586
    def cAzimuth(a, b):
        lat1 = math.radians(a['lat'])
        lat2 = math.radians(b['lat'])
        diffLong = math.radians(b['lon'] - a['lon'])

        x = math.sin(diffLong) * math.cos(lat2)
        y = math.cos(lat1) * math.sin(lat2) - (math.sin(lat1) * math.cos(lat2) * math.cos(diffLong))

        initial_bearing = math.atan2(x, y)
        initial_bearing = math.degrees(initial_bearing)
        compass_bearing = (initial_bearing + 360) % 360

        return compass_bearing
    
# Folgende Funktion: whuber @ https://gis.stackexchange.com/a/58926
    def cElevation(ap, bp):
        #Vektor (dx, dy, dz) ap zu bp berechnen
        d = {'x': bp['x'] - ap['x'], 'y': bp['y'] - ap['y'], 'z': bp['z'] - ap['z']}
        cosElv = (ap['x']*d['x'] + ap['y']*d['y'] + ap['z']*d['z']) / math.sqrt((ap['x']*ap['x'] + ap['y']*ap['y'] + ap['z']*ap['z'])*(d['x']*d['x'] + d['y']*d['y'] + d['z']*d['z']))
        elv = 90 - math.degrees(math.acos(cosElv))
        return elv
        
# Folgende drei Funktionen: Don Cross @ http://cosinekitty.com/compass.html
    def distancePoints(ap, bp):
        dx = ap['x'] - bp['x']
        dy = ap['y'] - bp['y']
        dz = ap['z'] - bp['z']
        return (math.sqrt(dx*dx + dy*dy + dz*dz))
    
    def locationToPoint( c ):
        lat = c['lat'] * math.pi / 180.0
        lon = c['lon'] * math.pi / 180.0
        radius = earthRadiusInMeters(lat)
        clat = geocentricLatitude(lat)

        cosLon = math.cos(lon)
        sinLon = math.sin(lon)
        cosLat = math.cos(clat)
        sinLat = math.sin(clat)
        x = radius * cosLon * cosLat
        y = radius * sinLon * cosLat
        z = radius * sinLat;
        #Normalenvektor berechnen, um altitude mit einzubeziehen
        cosGlat = math.cos(lat)
        sinGlat = math.sin(lat)

        nx = cosGlat * cosLon
        ny = cosGlat * sinLon
        nz = sinGlat

        x += c['elv'] * nx;
        y += c['elv'] * ny
        z += c['elv'] * nz
        return ({'x':x, 'y':y, 'z':z, 'radius':radius, 'nx':nx, 'ny':ny, 'nz':nz})
    
    def earthRadiusInMeters(latitude):
        a = 6378137.0
        b = 6356752.3
        cos = math.cos(latitude)
        sin = math.sin(latitude)
        t1 = a * a * cos
        t2 = b * b * sin
        t3 = a * cos
        t4 = b * sin
        return (math.sqrt ((t1*t1 + t2*t2) / (t3*t3 + t4*t4)))
    
    def geocentricLatitude(lat):
        e2 = 0.00669437999014;
        clat = math.atan((1.0 - e2) * math.tan(lat))
        return clat;


#Laden der Layer, Ausfuehren der Aktualisierungsfunktion
    calculate()