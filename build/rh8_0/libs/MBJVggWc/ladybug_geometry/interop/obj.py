# coding=utf-8
"""A class that supports the import and export of OBJ data to/from ladybug_geometry.
"""
import os

try:
    from itertools import izip as zip  # python 2
    writemode = 'wb'
except ImportError:
    writemode = 'w'  # python 3

from ladybug_geometry.geometry2d.pointvector import Point2D
from ladybug_geometry.geometry3d.pointvector import Vector3D, Point3D


class OBJ(object):
    """A class that supports the import and export of OBJ data to/from ladybug_geometry.

    Note that ladybug_geometry Mesh3D can be easily created from this OBJ by
    taking the vertices and normals.

    Args:
        vertices: A list or tuple of Point3D objects for vertices.
        faces: A list of tuples with each tuple having either 3 or 4 integers.
            These integers correspond to indices within the list of vertices.
        vertex_texture_map: An optional list or tuple of Point2D that align with the
            vertices input. All coordinate values of the Point2D should be between
            0 and 1 and are intended to map to the XY system of images to be mapped
            onto the OBJ mesh. If None, the OBJ file is written without
            textures. (Default: None).
        vertex_normals: An optional list or tuple of Vector3D that align with the
            vertices input and describe the normal vector to be used at each vertex.
            If None, the OBJ file is written without normals. (Default: None).
        vertex_colors: An optional list of colors that align with the vertices input.
            Note that these are written into the OBJ alongside the vertex
            coordinates separately from the texture map. Not all programs support
            importing OBJs with this color information but Rhino does. (Default: None).

    Properties:
        * vertices
        * faces
        * vertex_texture_map
        * vertex_normals
        * vertex_colors
    """

    __slots__ = ('_vertices', '_faces', '_vertex_texture_map',
                 '_vertex_normals', '_vertex_colors')

    def __init__(self, vertices, faces, vertex_texture_map=None,
                 vertex_normals=None, vertex_colors=None):
        self._vertices = self._check_vertices_input(vertices)
        self._faces = self._check_faces_input(faces)
        self.vertex_texture_map = vertex_texture_map
        self.vertex_normals = vertex_normals
        self.vertex_colors = vertex_colors

    @classmethod
    def from_file(cls, file_path):
        """Create an OBJ object from a .obj file.

        Args:
            file_path: Path to an OBJ file as a text string. Note that, if the file
                includes texture mapping coordinates or vertex normals, the number
                of texture coordinates and normals must align with the number of
                vertices to be importable. NEarly all OBJ files follow this standard.
                If any of the OBJ mesh faces contain more than 4 vertices, only
                the first 4 vertices will be counted.
        """
        vertices, faces, vertex_texture_map, vertex_normals, vertex_colors = \
            [], [], [], [], []
        with open(file_path, 'r') as fp:
            for line in fp:
                if line.startswith('#'):
                    continue
                words = line.split()
                if len(words) > 0:
                    first_word = words[0]
                    if first_word == 'v':  # start of a new face
                        pass
        return cls(vertices, faces, vertex_texture_map, vertex_normals, vertex_colors)

    @classmethod
    def from_meh3d(cls, mesh, include_normals=False):
        """Create an OBJ object from a ladybug_geometry Mesh3D.
        
        If colors are specified on the Mesh3D, they will be correctly transferred
        to the resulting OBJ object.

        Args:
            mesh: A ladybug_geometry Mesh3D object to be converted to an OBJ object.
            include_normals: Boolean to note whether the vertex normals should be
                included in the resulting OBJ object. (Default: False).
        """
        if mesh.is_color_by_face:  # we need to duplicate vertices to preserve colors
            vertices, faces, colors = [], [], []
            v_ct = 0
            for face_verts, col in zip(mesh.face_vertices, mesh.colors):
                vertices.extend(face_verts)
                if len(face_verts) == 4:
                    faces.append((v_ct, v_ct + 1, v_ct + 2, v_ct + 3))
                    colors.extend([col] * 4)
                    v_ct += 4
                else:
                    faces.append((v_ct, v_ct + 1, v_ct + 2))
                    colors.extend([col] * 3)
                    v_ct += 3
            if include_normals:
                msh_norms = mesh.vertex_normals
                vert_normals = []
                for face in mesh.faces:
                    for fi in face:
                        vert_normals.append(msh_norms[fi])
                return cls(vertices, faces, vertex_normals=msh_norms,
                           vertex_colors=colors)
            return cls(vertices, faces, vertex_colors=colors)
        if include_normals:
            return cls(mesh.vertices, mesh.faces, vertex_normals=mesh.vertex_normals,
                       vertex_colors=mesh.colors)
        return cls(mesh.vertices, mesh.faces, vertex_colors=mesh.colors)

    @property
    def vertices(self):
        """Tuple of Point3D for all vertices in the OBJ."""
        return self._vertices

    @property
    def faces(self):
        """Tuple of tuples for all faces in the OBJ."""
        return self._faces

    @property
    def vertex_texture_map(self):
        """Get or set a tuple of Point2D for texture image coordinates for each vertex.

        Will be None if no texture map is assigned.
        """
        return self._vertex_texture_map

    @vertex_texture_map.setter
    def vertex_texture_map(self, value):
        if value is not None:
            assert isinstance(value, (list, tuple)), 'vertex_texture_map should be ' \
                'a list or tuple. Got {}'.format(type(value))
            if isinstance(value, list):
                value = tuple(value)
            if len(value) == 0:
                value = None
            elif len(value) != len(self.vertices):
                raise ValueError(
                    'Number of items in vertex_texture_map ({}) does not match number'
                    'of OBJ vertices ({}).'.format(len(value), len(self.vertices)))
            else:
                for vert in value:
                    assert isinstance(vert, Point2D), 'Expected Point2D for OBJ ' \
                        'vertex texture. Got {}.'.format(type(vert))
        self._vertex_texture_map = value

    @property
    def vertex_normals(self):
        """Get or set a tuple of Vector3D for vertex normals.

        Will be None if no vertex normals are assigned.
        """
        return self._vertex_normals

    @vertex_normals.setter
    def vertex_normals(self, value):
        if value is not None:
            assert isinstance(value, (list, tuple)), \
                'vertex_normals should be a list or tuple. Got {}'.format(type(value))
            if isinstance(value, list):
                value = tuple(value)
            if len(value) == 0:
                value = None
            elif len(value) != len(self.vertices):
                raise ValueError(
                    'Number of OBJ vertex_normals ({}) does not match the number of'
                    ' OBJ vertices ({}).'.format(len(value), len(self.vertices)))
            else:
                for norm in value:
                    assert isinstance(norm, Vector3D), 'Expected Vector3D for OBJ ' \
                        'vertex normal. Got {}.'.format(type(norm))
        self._vertex_normals = value

    @property
    def vertex_colors(self):
        """Get or set a list of colors for the OBJ. Will be None if no colors assigned.
        """
        return self._vertex_colors

    @vertex_colors.setter
    def vertex_colors(self, value):
        if value is not None:
            assert isinstance(value, (list, tuple)), \
                'vertex_normals should be a list or tuple. Got {}'.format(type(value))
            if isinstance(value, list):
                value = tuple(value)
            if len(value) == 0:
                value = None
            elif len(value) != len(self.vertices):
                raise ValueError(
                    'Number of OBJ vertex_normals ({}) does not match the number of'
                    ' OBJ vertices ({}).'.format(len(value), len(self.vertices)))
            else:
                for norm in value:
                    assert isinstance(norm, Vector3D), 'Expected Vector3D for OBJ ' \
                        'vertex normal. Got {}.'.format(type(norm))
        self._vertex_colors = value

    def to_file(self, folder, name, material_name='diffuse_0', include_mtl=True):
        """Write the OBJ object to an ASCII text file.

        Args:
            folder: A text string for the directory where the OBJ will be written.
            name: A text string for the name of the OBJ file. Note that, if an image
                texture is meant to be assigned to this OBJ, the image should have
                the same name as the one input here except with the .mtl extension
                instead of the .obj extension.
            material_name: A name to be used for the material assigned to the OBJ mesh.
                When using this method for Radiance simulation, this should be the
                name of the modifier assigned to the mesh. (Default: diffuse_0)
            include_mtl: Boolean to note whether the .mtl file should be written
                next to the .obj file in the output folder. (Default: True).
        """
        # set up a name and folder
        file_name = name if name.lower().endswith('.obj') else '{}.obj'.format(name)
        obj_file = os.path.join(folder, file_name)
        mtl_file = '{}.mtl'.format(name) if not name.lower().endswith('.obj') else \
            '{}.mtl'.format(name[:-4])

        # write everything into the OBJ file
        with open(obj_file, writemode) as outfile:
            # add a comment at the top to note where the OBJ is written from
            outfile.write('# OBJ file written by ladybug geometry\n\n')

            # add material file name if include_mtl is true
            if include_mtl:
                outfile.write('mtllib ' + mtl_file + '\n')
            outfile.write('usemtl {}\n'.format(material_name))

            # loop through the vertices and add them to the file
            if self.vertex_colors is None:
                for v in self.vertices:
                    outfile.write('v {} {} {}\n'.format(v.x, v.y, v.z))
            else:  # write the vertex colors alongside the vertices
                for v, c in zip(self.vertices, self.vertex_colors):
                    outfile.write(
                        'v {} {} {} {} {} {}\n'.format(v.x, v.y, v.z, c.r, c.g, c.b)
                    )

            # loop through the texture vertices, if present, and add them to the file
            if self.vertex_texture_map is not None:
                for vt in self.vertex_texture_map:
                    outfile.write('vt {} {}\n'.format(vt.x, vt.y))

            # loop through the normals, if present, and add them to the file
            if self.vertex_normals is not None:
                for vn in self.vertex_normals:
                    outfile.write('vn {} {} {}\n'.format(vn.x, vn.y, vn.z))

            # loop through the faces and add them to the file
            if self.vertex_texture_map is None and self.vertex_normals is None:
                for f in self.faces:
                    outfile.write('f ' + ' '.join(str(fi) for fi in f) + '\n')
            else:
                if self.vertex_texture_map is not None and self.vertex_normals is not None:
                    f_map = '{0}/{0}/{0}'
                elif self.vertex_texture_map is None and self.vertex_normals is not None:
                    f_map = '{0}//{0}'
                else:
                    f_map = '{0}/{0}'
                for f in self.faces:
                    outfile.write('f ' + ' '.join(f_map.format(fi) for fi in f) + '\n')

        # write the MTL file if requested
        if include_mtl:
            with open(mtl_file, writemode) as mtl_f:
                mtl_str = '# Ladybug Geometry\n' \
                    'newmtl {}\n' \
                    'Ka 0.0000 0.0000 0.0000\n' \
                    'Kd 0.0000 0.0000 0.0000\n' \
                    'Ks 1.0000 1.0000 1.0000\n' \
                    'Tf 0.0000 0.0000 0.0000\n' \
                    'd 1.0000\n' \
                    'Ns 0.0000\n'.format(material_name)
                mtl_f.write(mtl_str)

        return obj_file

    def _check_vertices_input(self, vertices):
        """Check the input vertices."""
        if not isinstance(vertices, tuple):
            vertices = tuple(vertices)
        for vert in vertices:
            assert isinstance(vert, Point3D), \
                'Expected Point3D for OBJ vertex. Got {}.'.format(type(vert))
        return vertices

    def _check_faces_input(self, faces):
        """Check input faces for correct formatting."""
        if not isinstance(faces, tuple):
            faces = tuple(faces)
        assert len(faces) > 0, 'OBJ mesh must have at least one face.'
        for f in faces:
            assert isinstance(f, tuple), \
                'Expected tuple for Mesh face. Got {}.'.format(type(f))
            assert len(f) >= 3, \
                'OBJ mesh face must have 3 or more vertices. Got {}.'.format(len(f))
            for ind in f:
                try:
                    self._vertices[ind]
                except IndexError:
                    raise IndexError(
                        'mesh face index {} does not correspond to any vertex. There '
                        'are {} vertices in the mesh.'.format(ind, len(self._vertices)))
                except TypeError:
                    raise TypeError(
                        'Mesh face must use integers to reference vertices. '
                        'Got {}.'.format(type(ind)))
        return faces

    def __len__(self):
        return len(self._vertices)

    def __getitem__(self, key):
        return self._vertices[key]

    def __iter__(self):
        return iter(self._vertices)

    def __repr__(self):
        return 'OBJ ({} vertices) ({} faces)'.format(
            len(self._vertices), len(self._faces))
