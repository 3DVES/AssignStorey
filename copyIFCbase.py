import ifcopenshell
import ifcopenshell.api
import ifcopenshell.util.placement
def relation(file,element,parent):
    file.add(ifcopenshell.api.run('aggregate.assign_object',file,product=element,
    relating_object=parent))
def add_element(new_file,old_file,element):
    try:# Search if already is the element
        new_file.by_guide(element.GlobalId)
    except:# Add not existent element
        ifcopenshell.api.run('project.append_asset',new_file,
        library=old_file,element=element)
def Copy_base(ifcFile, schema='IFC2X3'):
    # Create empty file with IFC2x3 schema
    f=ifcopenshell.api.run("project.create_file",schema)
    # Copy and add of project and site
    main=ifcFile.by_type('IfcProject')
    main+=ifcFile.by_type('IfcSite')
    for val in main:
        f.add(val)
    # Relates site with project
    relation(f,f.by_type('IfcSite')[0],f.by_type('IfcProject')[0])
    #Add building and storeys with root info
    main=ifcFile.by_type('IfcBuilding')
    main+=ifcFile.by_type('IfcBuildingStorey')
    for val in main:
        add_element(f,ifcFile,val)
    # Relates building with site
    relation(f,f.by_type('IfcBuilding')[0],f.by_type('IfcSite')[0])
    # Relates every storey with the building
    for val in f.by_type('IfcBuildingStorey'):
        relation(f,val,f.by_type('IfcBuilding')[0])
    return(f)
