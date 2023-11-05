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
    from ladybug.epw import EPW
    from ladybug.sunpath import Sunpath
except ImportError as e:
    raise ImportError('\nFailed to import ladybug:\n\t{}'.format(e))

try:
    from ladybug_rhino.download import download_file
    from ladybug_rhino.config import conversion_to_meters
    from ladybug_rhino.preview import VisualizationSetConduit
    from ladybug_rhino.togeometry import to_point3d
    from ladybug_rhino.fromgeometry import from_point3d
    from ladybug_rhino.bakeobjects import bake_visualization_set
except ImportError as e:
    raise ImportError('\nFailed to import ladybug_rhino:\n\t{}'.format(e))

import Rhino
import rhinoscriptsyntax as rs
import scriptcontext as sc


def run_sunpath_command():
    # get the EPW from command line
    gepw = Rhino.Input.Custom.GetString()
    gepw.SetCommandPrompt('Select an EPW file path or URL')
    epw_path = None
    if 'lbt_epw' in sc.sticky:
        epw_path = sc.sticky['lbt_epw']
        gepw.SetDefaultString(epw_path)

    # add all of the options to the command
    north_ = sc.sticky['lbt_north'] if 'lbt_north' in sc.sticky else 0
    north_option = Rhino.Input.Custom.OptionDouble(north_, 0, 360)
    gepw.AddOptionDouble('North', north_option)

    scale_ = sc.sticky['lbt_sunpath_scale'] if 'lbt_sunpath_scale' in sc.sticky else 1
    scale_option = Rhino.Input.Custom.OptionDouble(scale_, True, 0)
    gepw.AddOptionDouble('Scale', scale_option)

    projection_i_ = sc.sticky['lbt_sunpath_projection'] \
        if 'lbt_sunpath_projection' in sc.sticky else 0
    projections = ('3D', 'StereoGraphic', 'Orthographic')
    proj_list = gepw.AddOptionList('Projection', projections, projection_i_)

    solar_time_ = sc.sticky['lbt_sunpath_solar_time'] \
        if 'lbt_sunpath_solar_time' in sc.sticky else False
    solar_time_option = Rhino.Input.Custom.OptionToggle(solar_time_, 'No', 'Yes')
    gepw.AddOptionToggle('SolarTime', solar_time_option)

    epw_data_i_ = sc.sticky['lbt_sunpath_data'] \
        if 'lbt_sunpath_data' in sc.sticky else 0
    epw_data_sets = (
        'None', 'dry_bulb_temperature', 'dew_point_temperature', 'relative_humidity',
        'wind_speed', 'wind_direction', 'direct_normal_radiation',
        'diffuse_horizontal_radiation', 'global_horizontal_radiation'
    )
    epw_data_list = gepw.AddOptionList('Data', epw_data_sets, epw_data_i_)

    # get the weather file and all options
    while True:
        # This will prompt the user to input an EPW and visualization options
        get_epw = gepw.Get()
        if get_epw == Rhino.Input.GetResult.String:
            epw_path = gepw.StringResult()
            north_ = north_option.CurrentValue
            scale_ = scale_option.CurrentValue
            solar_time_ = solar_time_option.CurrentValue
        elif get_epw == Rhino.Input.GetResult.Option:
            if gepw.OptionIndex() == proj_list:
                projection_i_ = gepw.Option().CurrentListOptionIndex
            if gepw.OptionIndex() == epw_data_list:
                epw_data_i_ = gepw.Option().CurrentListOptionIndex
            continue
        break

    # save all of the options to sticky
    sc.sticky['lbt_north'] = north_
    sc.sticky['lbt_sunpath_scale'] = scale_
    sc.sticky['lbt_sunpath_projection'] = projection_i_
    sc.sticky['lbt_sunpath_solar_time'] = solar_time_
    sc.sticky['lbt_sunpath_data'] = epw_data_i_

    # process the EPW file path or URL
    if not epw_path:
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

    # process all of the global inputs for the sunpath
    center_pt3d = sc.sticky['lbt_origin'] if 'lbt_origin' in sc.sticky else Point3D()
    radius = (100 * scale_) / conversion_to_meters()
    daily_ = False
    projection_ = projections[projection_i_] if projection_i_ != 0 else None

    # get the location from the EPW
    epw_obj = EPW(epw_path)
    _location = epw_obj.location

    # process the EPW data to be plotted on the chart if it was requested
    hoys_, data_ = [], []
    if epw_data_i_ != 0:
        data_.append(getattr(epw_obj, epw_data_sets[epw_data_i_]))
        for month in range(1, 13):
            for day in range(1, 29, 7):
                for hour in range(24):
                    hoys_.append(DateTime(month, day, hour).hoy)

    # make the sunpath visualization set
    sp = Sunpath.from_location(_location, north_)
    vis_set_args = [hoys_, data_, None, radius, center_pt3d, solar_time_, daily_, projection_]
    vis_set = sp.to_vis_set(*vis_set_args)

    # preview the visualization set and ask if the origin should be changed
    conduit = VisualizationSetConduit(vis_set, render_3d_legend=True, render_2d_legend=False)
    conduit.Enabled = True
    sc.doc.Views.Redraw()
    gp = Rhino.Input.Custom.GetPoint()
    gp.SetCommandPrompt('Select a Point for the origin or press ENTER to keep the current one.')
    gp.SetDefaultPoint(from_point3d(center_pt3d))
    gp.Get()
    if gp.CommandResult() == Rhino.Commands.Result.Success:
        point = gp.Point()
        origin = to_point3d(point)
        vis_set_args[4] = origin
        sc.sticky['lbt_origin'] = origin
        vis_set = sp.to_vis_set(*vis_set_args)
        conduit.Enabled = False
        conduit = VisualizationSetConduit(vis_set, render_3d_legend=True, render_2d_legend=False)
        conduit.Enabled = True
        sc.doc.Views.Redraw()

    # finally, let people decide what they want to do with the result
    gres = Rhino.Input.Custom.GetString()
    gres.SetCommandPrompt('Would you like to add the Sunpath Geometry to the Document? Hit ENTER when done.')
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


run_sunpath_command()
