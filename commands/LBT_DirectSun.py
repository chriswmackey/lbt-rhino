#! python 2
import os
import math

try:
    from ladybug_geometry.geometry2d import Point2D
    from ladybug_geometry.geometry3d import Point3D, Vector3D
except ImportError as e:
    raise ImportError('\nFailed to import ladybug_geometry:\n\t{}'.format(e))

try:
    from ladybug.futil import unzip_file
    from ladybug.config import folders
    from ladybug.dt import DateTime
    from ladybug.color import Colorset
    from ladybug.legend import LegendParameters
    from ladybug.epw import EPW
    from ladybug.sunpath import Sunpath
    from ladybug.datatype.time import Time
except ImportError as e:
    raise ImportError('\nFailed to import ladybug:\n\t{}'.format(e))

try:
    from ladybug_display.visualization import VisualizationSet, AnalysisGeometry, \
        VisualizationData, ContextGeometry
except ImportError as e:
    raise ImportError('\nFailed to import ladybug_geometry:\n\t{}'.format(e))

try:
    from ladybug_rhino.download import download_file
    from ladybug_rhino.config import conversion_to_meters, rhino_version
    from ladybug_rhino.togeometry import to_joined_gridded_mesh3d, to_vector3d
    from ladybug_rhino.fromgeometry import from_point3d, from_vector3d
    from ladybug_rhino.intersect import join_geometry_to_mesh, intersect_mesh_rays
    from ladybug_rhino.preview import VisualizationSetConduit
    from ladybug_rhino.bakeobjects import bake_visualization_set
except ImportError as e:
    raise ImportError('\nFailed to import ladybug_rhino:\n\t{}'.format(e))

import Rhino
import scriptcontext as sc


from System import Environment

def local_processor_count():
    """Get an integer for the number of processors on this machine.

    If, for whatever reason, the number of processors could not be sensed,
    None will be returned.
    """
    return Environment.ProcessorCount


def recommended_processor_count():
    """Get an integer for the recommended number of processors for parallel calculation.

    This should be one less than the number of processors available on this machine
    unless the machine has only one processor, in which case 1 will be returned.
    If, for whatever reason, the number of processors could not be sensed, a value
    of 1 will be returned.
    """
    cpu_count = local_processor_count()
    return 1 if cpu_count is None or cpu_count <= 1 else cpu_count - 1


def run_direct_sun_command():
    # get the EPW from command line
    gepw = Rhino.Input.Custom.GetString()
    gepw.SetCommandPrompt('Select an EPW file path or URL')
    epw_path = None
    if 'lbt_epw' in sc.sticky:
        epw_path = sc.sticky['lbt_epw']
        gepw.SetDefaultString(epw_path)

    # add all of the options to the command
    month_i_ = sc.sticky['lbt_sunpath_month'] if 'lbt_sunpath_month' in sc.sticky else 12
    avail_months = ('All', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                    'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec')
    month_list = gepw.AddOptionList('Month', avail_months, month_i_)

    day_ = sc.sticky['lbt_sunpath_day'] if 'lbt_sunpath_day' in sc.sticky else 21
    day_option = Rhino.Input.Custom.OptionInteger(day_, 0, 31)
    gepw.AddOptionInteger('Day', day_option)

    hour_ =  sc.sticky['lbt_sunpath_hour'] if 'lbt_sunpath_hour' in sc.sticky else 24
    hour_option = Rhino.Input.Custom.OptionInteger(hour_, 0, 24)
    gepw.AddOptionInteger('Hour', hour_option)

    north_ = sc.sticky['lbt_north'] if 'lbt_north' in sc.sticky else 0
    north_option = Rhino.Input.Custom.OptionDouble(north_, 0, 360)
    gepw.AddOptionDouble('North', north_option)

    # get the weather file and all options
    while True:
        # This will prompt the user to input an EPW and visualization options
        get_epw = gepw.Get()
        if get_epw == Rhino.Input.GetResult.String:
            epw_path = gepw.StringResult()
            north_ = north_option.CurrentValue
            day_ = day_option.CurrentValue
            hour_ = hour_option.CurrentValue
        elif get_epw == Rhino.Input.GetResult.Option:
            if gepw.OptionIndex() == month_list:
                month_i_ = gepw.Option().CurrentListOptionIndex
        break

    # save all of the options to sticky
    sc.sticky['lbt_sunpath_month'] = month_i_
    sc.sticky['lbt_sunpath_day'] = day_
    sc.sticky['lbt_sunpath_hour'] = hour_
    sc.sticky['lbt_north'] = north_

    # process the EPW file path or URL
    if not epw_path:
        print('No EPW file selected.')
        return
    _def_folder = folders.default_epw_folder
    if epw_path.startswith('http'):  # download the EPW file
        _weather_URL = epw_path
        if _weather_URL.lower().endswith('.zip'):  # onebuilding URL type
            _folder_name = _weather_URL.split('/')[-1][:-4]
        else:  # dept of energy URL type
            _folder_name = _weather_URL.split('/')[-2]
        epw_path = os.path.join(_def_folder, _folder_name, _folder_name + '.epw')
        if not os.path.isfile(epw_path):
            zip_file_path = os.path.join(_def_folder, _folder_name, _folder_name + '.zip')
            download_file(_weather_URL, zip_file_path, True)
            unzip_file(zip_file_path)
        sc.sticky['lbt_epw'] = os.path.basename(epw_path)
    elif not os.path.isfile(epw_path):
        possible_file = os.path.basename(epw_path)[:-4] \
            if epw_path.lower().endswith('.epw') else epw_path
        epw_path = os.path.join(_def_folder, possible_file, possible_file + '.epw')
        if not os.path.isfile(epw_path):
            print('Selected EPW file at does not exist at: {}'.format(epw_path))
            return
        sc.sticky['lbt_epw'] = possible_file + '.epw'
    else:
        sc.sticky['lbt_epw'] = epw_path

    # compute the sun vectors to be used in the study
    epw_obj = EPW(epw_path)
    _location = epw_obj.location
    sp = Sunpath.from_location(_location, north_)
    months = [month_i_] if month_i_ != 0 else list(range(1, 13))
    days = [day_] if day_ != 0 else list(range(1, 32))
    hours = [hour_] if hour_ != 24 else list(range(0, 24))
    _vectors, _hoys = [], []
    for month in months:
        for day in days:
            for hour in hours:
                date_obj = DateTime(month, day, hour)
                hoy = date_obj.hoy
                sun = sp.calculate_sun_from_hoy(hoy, False)
                if sun.is_during_day:
                    _vectors.append(from_vector3d(sun.sun_vector))
                    _hoys.append(hoy)

    # make a preview of the suns on the sunpath
    center_pt3d = sc.sticky['lbt_origin'] if 'lbt_origin' in sc.sticky else Point3D()
    scale_ = sc.sticky['lbt_sunpath_scale'] if 'lbt_sunpath_scale' in sc.sticky else 1
    radius = (100 * scale_) / conversion_to_meters()
    vis_set_args = [_hoys, [], None, radius, center_pt3d]
    vis_set = sp.to_vis_set(*vis_set_args)
    conduit = VisualizationSetConduit(vis_set)
    conduit.Enabled = True
    sc.doc.Views.Redraw()

    # get the analysis geometry from the scene
    geo_filter = Rhino.DocObjects.ObjectType.Surface | Rhino.DocObjects.ObjectType.PolysrfFilter | \
        Rhino.DocObjects.ObjectType.Mesh
    go = Rhino.Input.Custom.GetObject()
    go.SetCommandPrompt('Select surfaces, polysurfaces, or meshes on which Direct Sun will be studied.')
    go.GeometryFilter = geo_filter

    # add all of the options for the geometry
    grid_size_ = sc.sticky['lbt_study_grid_size'] if 'lbt_study_grid_size' in sc.sticky \
        else int(1 / conversion_to_meters())
    gs_option = Rhino.Input.Custom.OptionDouble(grid_size_, True, 0)
    go.AddOptionDouble('GridSize', gs_option)

    offset_dist_ = sc.sticky['lbt_study_offset'] if 'lbt_study_offset' in sc.sticky \
        else round((0.1 / conversion_to_meters()), 2)
    off_option = Rhino.Input.Custom.OptionDouble(offset_dist_, True, 0)
    go.AddOptionDouble('Offset', off_option)

    # add more attributes related to selection
    go.GroupSelect = True
    go.SubObjectSelect = False
    go.EnableClearObjectsOnEntry(False)
    go.EnableUnselectObjectsOnExit(False)
    go.DeselectAllBeforePostSelect = False

    # get the analysis geometries from the scene
    have_preselected_objects = False
    while True:
        res = go.GetMultiple(1, 0)
        if res == Rhino.Input.GetResult.Option:
            go.EnablePreSelect(False, True)
            continue
        elif res != Rhino.Input.GetResult.Object:
            return Rhino.Commands.Result.Cancel
        if go.ObjectsWerePreselected:
            have_preselected_objects = True
            go.EnablePreSelect(False, True)
            continue
        grid_size_ = gs_option.CurrentValue
        offset_dist_ = off_option.CurrentValue
        break
    if have_preselected_objects:
        for i in range(0, go.ObjectCount):
            rhino_obj = go.Object(i).Object()
            if not rhino_obj is None:
                rhino_obj.Select(False)
        sc.doc.Views.Redraw()

    # turn off the preview of the sunpath
    conduit.Enabled = False
    sc.doc.Views.Redraw()

    # get the actual geometry from the selection
    obj_table = Rhino.RhinoDoc.ActiveDoc.Objects
    geometry_ = []
    for get_obj in go.Objects():
        geometry_.append(obj_table.Find(get_obj.ObjectId).Geometry)
    if len(geometry_) == 0:
        return

    # save all of the options to sticky
    sc.sticky['lbt_study_grid_size'] = grid_size_
    sc.sticky['lbt_study_offset'] = offset_dist_

    # create the gridded mesh from the geometry
    study_mesh = to_joined_gridded_mesh3d(geometry_, grid_size_)
    lb_points = [pt.move(vec * offset_dist_) for pt, vec in
                 zip(study_mesh.face_centroids, study_mesh.face_normals)]
    points = [from_point3d(pt) for pt in lb_points]

    # display the analysis points in the scene
    points_context = ContextGeometry('Analysis_Points', lb_points)
    vis_set = VisualizationSet('Analysis_Preview', [points_context])
    conduit = VisualizationSetConduit(vis_set)
    conduit.Enabled = True
    sc.doc.Views.Redraw()

    # get any context geometry
    gcon = Rhino.Input.Custom.GetObject()
    gcon.SetCommandPrompt('Select context surfaces, polysurfaces, or meshes on which block the sun.')
    gcon.GeometryFilter = geo_filter
    gcon.GroupSelect = True
    gcon.SubObjectSelect = False
    gcon.EnableClearObjectsOnEntry(False)
    gcon.EnableUnselectObjectsOnExit(False)
    gcon.DeselectAllBeforePostSelect = False

    # get the analysis geometries from the scene
    have_preselected_objects = False
    while True:
        res = gcon.GetMultiple(1, 0)
        if res == Rhino.Input.GetResult.Option:
            gcon.EnablePreSelect(False, True)
            continue
        if gcon.ObjectsWerePreselected:
            have_preselected_objects = True
            gcon.EnablePreSelect(False, True)
            continue
        break
    if have_preselected_objects:
        for i in range(0, gcon.ObjectCount):
            rhino_obj = gcon.Object(i).Object()
            if not rhino_obj is None:
                rhino_obj.Select(False)
        sc.doc.Views.Redraw()
    
    # get the actual geometry from the selection
    obj_table = Rhino.RhinoDoc.ActiveDoc.Objects
    context_ = []
    for get_obj in gcon.Objects():
        context_.append(obj_table.Find(get_obj.ObjectId).Geometry)

    # turn off the preview of the analysis points
    conduit.Enabled = False
    sc.doc.Views.Redraw()

    # merge all of the context meshes together
    shade_mesh = join_geometry_to_mesh(geometry_ + context_)

    # get the study points and reverse the sun vectors (for backward ray-tracting)
    rev_vec = [from_vector3d(to_vector3d(vec).reverse()) for vec in _vectors]
    normals = [from_vector3d(vec) for vec in study_mesh.face_normals]

    # intersect the rays with the mesh
    cpu_count = recommended_processor_count()
    int_matrix, _ = intersect_mesh_rays(
        shade_mesh, points, rev_vec, normals, cpu_count=cpu_count)
    results = [sum(int_list) for int_list in int_matrix]

    # create an result visualization set and display it in the scene
    vis_set = VisualizationSet('DirectSunStudy', ())
    vis_set.display_name = 'Direct Sun Study'
    d_type, unit = Time(), 'hr'

    # create the AnalysisGeometry
    l_par = LegendParameters()
    l_par.colors = Colorset.ecotect()
    vis_data = VisualizationData(results, l_par, d_type, unit)
    mesh_geo = AnalysisGeometry('Direct_Sun_Data', [study_mesh], [vis_data])
    mesh_geo.display_name = 'Direct Sun Data'
    mesh_geo.display_mode = 'Surface'
    vis_set.add_geometry(mesh_geo)

    # preview the visualization set
    render_2d_legend = True if rhino_version < (8, 0) else False
    render_3d_legend = False if rhino_version < (8, 0) else True
    conduit = VisualizationSetConduit(
        vis_set, render_2d_legend=render_2d_legend, render_3d_legend=render_3d_legend)
    conduit.Enabled = True
    sc.doc.Views.Redraw()

    # finally, let people decide what they want to do with the result
    gres = Rhino.Input.Custom.GetString()
    gres.SetCommandPrompt('Would you like to add the Study Geometry to the Document? Hit ENTER when done.')
    gres.SetDefaultString('Add?')
    bake_result = False
    result_option = Rhino.Input.Custom.OptionToggle(False, 'No', 'Yes')
    gres.AddOptionToggle('AddToDoc', result_option)
    while True:
        # This will prompt the user to input an EPW and visualization options
        get_res = gres.Get()
        if get_res == Rhino.Input.GetResult.String:
            bake_result = result_option.CurrentValue
        else:
            continue
        break
    conduit.Enabled = False
    sc.doc.Views.Redraw()

    # add the visualization set to the document
    if bake_result:
        bake_visualization_set(vis_set, bake_3d_legend=True)


run_direct_sun_command()
