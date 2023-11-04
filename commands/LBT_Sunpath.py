#! python 2
import os
import math

try:
    from ladybug_geometry.geometry2d import Point2D
    from ladybug_geometry.geometry3d import Point3D, Vector3D
except ImportError as e:
    raise ImportError('\nFailed to import ladybug_geometry:\n\t{}'.format(e))

try:
    from ladybug.epw import EPW
    from ladybug.sunpath import Sunpath
except ImportError as e:
    raise ImportError('\nFailed to import ladybug:\n\t{}'.format(e))

try:
    from ladybug_rhino.config import conversion_to_meters
    from ladybug_rhino.bakeobjects import bake_visualization_set
except ImportError as e:
    raise ImportError('\nFailed to import ladybug_rhino:\n\t{}'.format(e))

import Rhino
import rhinoscriptsyntax as rs


def run_sunpath_command():
    # get the EPW
    gepw = Rhino.Input.Custom.GetString()
    gepw.SetCommandPrompt('Select an EPW file path')
    
    # add an option to set the north
    north_option = Rhino.Input.Custom.OptionDouble(0, 0, 360)
    gepw.AddOptionDouble('North', north_option)
    while True:
        # perform the get operation. This will prompt the user to
        # input a point, but also allow for command line options
        # defined above
        get_epw = gepw.Get()
        if get_epw == Rhino.Input.GetResult.String:
            epw_path = gepw.StringResult()
            north_ = north_option.CurrentValue
        elif get_epw == Rhino.Input.GetResult.Option:
            continue
        break


    if not epw_path:
        return
    if not os.path.isfile(epw_path):
        print('Selected EPW file at does not exist at: {}'.format(epw_path))
        return

    # process all of the global inputs for the sunpath
    center_pt, center_pt3d = Point2D(), Point3D()
    z = 0
    _scale_ = 1
    radius = (100 * _scale_) / conversion_to_meters()
    solar_time_ = False
    daily_ = False
    projection_ = None
    dl_saving_ = None
    l_par = None
    hoys_ = []
    data_ = []

    # get the location from the EPW
    epw_obj = EPW(epw_path)
    _location = epw_obj.location

    # make the sunpath
    sp = Sunpath.from_location(_location, north_, dl_saving_)
    vis_set_args = [hoys_, data_, l_par, radius, center_pt3d, solar_time_, daily_, projection_]
    vis_set = sp.to_vis_set(*vis_set_args)
    bake_visualization_set(vis_set)


run_sunpath_command()
