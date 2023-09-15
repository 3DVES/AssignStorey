import uuid
import ifcopenshell
import ifcopenshell.geom
import numpy as np
try:
    from ..BIMEP3DVESUtils.GeometryUtils import moveElement
except:
    from BIMEP3DVESUtils.GeometryUtils import moveElement

def globalCoordenate(objectPlacement):
    x = 0
    y = 0
    z = 0
    if objectPlacement == None:
        return [x, y, z]
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


def assign_storey(ifc_base, ifc_geometry, element_types=['IfcBuildingElementProxy']):
    settings = ifcopenshell.geom.settings()
    settings.set(settings.USE_WORLD_COORDS, True)
    settings.set(settings.CONVERT_BACK_UNITS, True)
    locations = {}
    def create_guid(): return ifcopenshell.guid.compress(uuid.uuid1().hex)

    #ifc_base = ifcopenshell.open(ifc_base_path)
    base_storeys = []
    if hasattr(ifc_base, 'by_type'):
        base_storeys = ifc_base.by_type('IfcBuildingStorey')
    #ifc_geometry = ifcopenshell.open(ifc_geometry_path)
    geometry_elements = []
    for kind in element_types:
        if hasattr(ifc_geometry, 'by_type'):
            geometry_elements.extend(ifc_geometry.by_type(kind))
    levels = []
    storeys = []
    for index in range(len(base_storeys)):
        z_level = round(globalCoordenate(
            base_storeys[index].ObjectPlacement)[2], 1)
        globals()["container_"+str(z_level).replace('.', '_')] = []
        if z_level not in levels:
            levels.append(z_level)
            storeys.append(base_storeys[index])
    levels = np.array(levels)
    globcoord = {i.GlobalId:globalCoordenate(i.ObjectPlacement) if globalCoordenate(i.ObjectPlacement) != None else [0,0,0] for i in geometry_elements}
    print(levels)
    for element in geometry_elements:
        try:
            shape = ifcopenshell.geom.create_shape(settings, element)
            verts = shape.geometry.verts
            z_coords = [verts[j+2] for j in range(0, len(verts), 3)]
            z_level = round(min(list(set(z_coords))), 1)
        except:
            try:
                z_level = round(element.Representation.Representations[0].Items[0].MappingSource.MappedRepresentation.Items[
                    0].Outer.CfsFaces[0].Bounds[0].Bound.Polygon[0].Coordinates[-1], 1)
                if element.Representation.Representations[0].Items[0].MappingTarget.LocalOrigin:
                    z_level += element.Representation.Representations[0].Items[0].MappingTarget.LocalOrigin.Coordinates[2]
            except:
                z_level = round(
                    element.ObjectPlacement.RelativePlacement.Location.Coordinates[-1], 1)
        try:
            # find_nearest(levels, z_level)
            z_level_f = levels[(levels - z_level) <= 0][-1]
        except:
            z_level_f = levels[-1]
        element = ifc_base.add(element)
        if not(element.ObjectPlacement):
            altitude = levels - z_level
            try:
                altitude = np.where(altitude<0)[-1][-1]
            except:
                altitude = 0
            if z_level not in locations.keys():
                location = ifc_base.create_entity(**{'type': 'IfcCartesianPoint','Coordinates': (0.0, 0.0, -float(levels[altitude]))})
                IfcAxis2Placement3D = ifc_base.create_entity(**{'type': 'IfcAxis2Placement3D','Location': location})
                locations[z_level] = IfcAxis2Placement3D
            else:
                IfcAxis2Placement3D = locations[z_level]
            buildingLoc = base_storeys[altitude].ObjectPlacement
            loc = ifc_base.create_entity(**{'type': 'IfcLocalPlacement', 'PlacementRelTo': buildingLoc, 'RelativePlacement': IfcAxis2Placement3D})
            element.ObjectPlacement = loc
        globals()["container_"+str(z_level_f).replace('.', '_')].append(element)
    for index in range(len(base_storeys)):
        z_level = round(globalCoordenate(
            base_storeys[index].ObjectPlacement)[2], 1)
        owner_history = base_storeys[index].OwnerHistory
        container_SpatialStructure = ifc_base.createIfcRelContainedInSpatialStructure(
            create_guid(), owner_history)
        container_SpatialStructure.RelatingStructure = base_storeys[index]
        container_SpatialStructure.RelatedElements = globals()["container_"+str(z_level).replace('.', '_')]
        ifc_base.create_entity('IfcRelAggregates', ifcopenshell.guid.new(
        ), owner_history, '', '', base_storeys[index], globals()["container_"+str(z_level).replace('.', '_')])
    # Avoid modification of position
    for element in geometry_elements:
        if globalCoordenate(element.ObjectPlacement) != globcoord[element.GlobalId]:
            displ = np.array(globcoord[element.GlobalId]).reshape(3) - np.array(globalCoordenate(element.ObjectPlacement)).reshape(3)
            moveElement(element, float(displ[0]), float(displ[1]), float(displ[2]))
    return (ifc_base)
    # ifc_base.write(output_path)
