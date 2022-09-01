import uuid
import ifcopenshell
import ifcopenshell.geom
import numpy as np

def globalCoordenate(objectPlacement):
    x = 0
    y = 0
    z = 0
    x, y, z = objectPlacement.RelativePlacement.Location.Coordinates
    if objectPlacement.PlacementRelTo != None:
        xx, yy, zz = globalCoordenate(objectPlacement.PlacementRelTo)
        x += xx
        y += yy
        z += zz
    return [x, y, z]

def find_nearest(array, value):
    array = np.asarray(array)
    idx = (np.abs(array - value)).argmin()
    return array[idx]

def assign_storey(ifc_base, ifc_geometry, output_path):
    settings = ifcopenshell.geom.settings()
    settings.set(settings.USE_WORLD_COORDS, True)
    settings.set(settings.CONVERT_BACK_UNITS, True)
    
    create_guid = lambda: ifcopenshell.guid.compress(uuid.uuid1().hex)
    
    #ifc_base = ifcopenshell.open(ifc_base_path)
    base_storeys = ifc_base.by_type('IfcBuildingStorey')
    #ifc_geometry = ifcopenshell.open(ifc_geometry_path)
    geometry_elements = ifc_geometry.by_type('IfcBuildingElementProxy')
    levels = []
    
    for index in range(len(base_storeys)):
        z_level = globalCoordenate(base_storeys[index].ObjectPlacement)[2]
        globals()["container_"+str(z_level).replace('.','_')] = []
        if z_level not in levels:
            levels.append(z_level)
    for element in geometry_elements:
        try:
            shape = ifcopenshell.geom.create_shape(settings, element)
            verts = shape.geometry.verts
            z_coords = [verts[j+2] for j in range(0,len(verts),3)]
            z_level = min(list(set(z_coords)))
        except:
            z_level = element.Representation.Representations[0].Items[0].MappingSource.MappedRepresentation.Items[0].Outer.CfsFaces[0].Bounds[0].Bound.Polygon[0].Coordinates[-1]
        z_level = find_nearest(levels, z_level)
        element = ifc_base.add(element)
        globals()["container_"+str(z_level).replace('.','_')].append(element)
    for index in range(len(base_storeys)):
        z_level = globalCoordenate(base_storeys[index].ObjectPlacement)[2]
        owner_history = base_storeys[index].OwnerHistory
        container_SpatialStructure = ifc_base.createIfcRelContainedInSpatialStructure(create_guid() , owner_history)
        container_SpatialStructure.RelatingStructure = base_storeys[index]
        container_SpatialStructure.RelatedElements = globals()["container_"+str(z_level).replace('.','_')]
    
    ifc_base.write(output_path)
