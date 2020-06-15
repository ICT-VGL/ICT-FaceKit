"""A module that reads and loads the FaceXModel morphable face model.""

  Typical usage example:

  face_x_model = FaceXModel()
  [Now the FaceXModel is loaded and can be used.]
"""

import inspect
import json
import os
from pathlib import Path
import shutil

from copy import deepcopy

import numpy as np
import openmesh as om


class FaceXModel:  # pylint: disable=too-many-instance-attributes
    """Reads and loads the FaceXModel morphable face model.

    This class allows one to load the read and load the contents of the
    FaceXModel. Creating a FaceXModel object consists of reads every .obj file
    in the FaceXModel directory using openmesh. Then, the identity and
    expression mode per vertex deltas are computed. Each FaceXModel object only
    stores the vertex_indices.json, the generic_neutral_mesh.obj, and the
    computed identity and expression mode per vertex deltas.

    Attributes:
        path: The absolute path to this file.

        model_path: The absolute path to the FaceXModel directory.

        vertex_indices: A dictionary of the vertex indices specifed by the
            vertex_indices.json file.

        generic_neutral_mesh:  A reference to the generic neutral mesh object
            read in using openmesh.

        num_vertices: The number of vertices of the generic neutral mesh; N.

        identity_names: A list of the filenames of the identity meshes read in.

        expression_names: A list of the filenames of the expression meshes read
            in.

        identity_shape_modes: A reference to the list of identity shape modes
            read in using openmesh. This list of shape modes is represented as
            a numpy array of dimension K * N * 3 where K is the number of shape
            modes.

        expression_shape_modes: A reference to the list of expression shape
            modes read in using openmesh. This list of shape modes is
            represented as a numpy array of dimension K * N * 3 where K is the
            number of shape modes.
    """

    def __init__(self):
        """Constructs a FaceXModel object by loading the FaceXModel.

        Each FaceXModel object stores the vertex indices, the generic neutral
        mesh, and the identity and expression modes computed as per vertex
        deltas. This constructor explicitly reads and stores the
        vertex_indices.json and generic_neutral_mesh.obj files, and then
        computes and stores the identity and expression modes.

        Returns:
            A FaceXModel object keeping track of the vertex indices, the
            generic neutral mesh, and the identity and expression shape modes.
        """

        # Find path to file and FaceXModel directory
        filename = inspect.getframeinfo(inspect.currentframe()).filename
        self.path = Path(os.path.dirname(os.path.abspath(filename)))
        self.model_path = self.path.parent / 'FaceXModel'

        # Read and store the vertex indices .json and generic neutral mesh .obj
        self.vertex_indices = self._read_vertex_indices()
        self.generic_neutral_mesh = self._read_generic_neutral_mesh()
        self.num_vertices = self.generic_neutral_mesh.n_vertices()

        # Alert user of procedure status
        print('Started loading FaceXModel.')
        print('Loading identity and expression meshes...')

        # Read in every identity .obj and expression .obj
        id_meshes, id_names, ex_meshes, ex_names = self._read_ids_and_exs()

        # Store a list of the identity names and expression names
        self.identity_names = id_names
        self.expression_names = ex_names

        # Alert user of procedure status
        print("Computing identity and expression shape modes...")

        # Compute and store the identity and shape modes
        self.identity_shape_modes = self._compute_shape_modes(id_meshes)
        self.expression_shape_modes = self._compute_shape_modes(ex_meshes)

        # alert user of procedure status
        print("Finished loading FaceXModel.")

    def _read_vertex_indices(self):
        """Reads and returns the FaceXModel vertex_indices.json.

        Returns:
            Returns the json object created by reading the vertex_indices.json
            file.
        """
        with open(self.model_path / 'vertex_indices.json') as input_file:
            vertex_indices = json.load(input_file)
            return vertex_indices

    def _read_generic_neutral_mesh(self):
        """Reads and returns the FaceXModel generic neutral mesh.

        Returns:
            Returns the PolyMesh object created by reading the
            generic_neutral_mesh.obj file using openmesh.
        """
        generic_neutral_mesh_path = str(self.model_path /
                                        'generic_neutral_mesh.obj')
        generic_neutral_mesh = om.read_polymesh(generic_neutral_mesh_path)
        return generic_neutral_mesh

    def _read_ids_and_exs(self):
        """Reads and returns the FaceXModel identity and expression data.

        Reads and stores the FaceXModel identity and expression meshes and
        names in lists. Reads the mesh .obj files using openmesh.

        Returns:
            A tuple of four lists, where the first item is a list of identity
            meshes, the second item is a list of identity mesh names, the third
            item is a list of expression meshes, and the fourth item is a list
            of expression mesh names.
        """

        # Initialize our lists of identity and expression data
        identity_meshes = []
        identity_names = []
        expression_meshes = []
        expression_names = []

        # For each file in the directory
        filenames = os.listdir(self.model_path)
        for filename in filenames:
            name, ext = os.path.splitext(filename)
            # If .obj file and not generic neutral mesh
            if ext == ".obj" and name != 'generic_neutral_mesh':
                # Get full file path
                file_path = os.path.join(self.model_path, filename)
                # Read in .obj with openmesh
                mesh = om.read_polymesh(file_path)
                # Add identity or expression mesh to corresponding list
                if name.startswith('identity'):
                    identity_meshes.append(mesh)
                    identity_names.append(name)
                else:
                    expression_meshes.append(mesh)
                    expression_names.append(name)

        # Return a tuple of the identity and expression data
        return (identity_meshes, identity_names, expression_meshes,
                expression_names)

    def _compute_shape_modes(self, meshes):
        """Computes and returns shape modes determined by the specifed meshes.

        Computes the shape modes determined by the specified meshes in relation
        to the generic_neutral_mesh. Each individual shape mode is a numpy
        array of dimension N * 3, where N is equal to the number of vertices
        in the generic neutral mesh. The list of shape modes is a numpy array
        of dimension K * N * 3, where K is the total number of shape modes.

        Args:
            meshes: A list of openmesh PolyMesh objects to compute the shape
                modes for. This will either be the identity meshes or the
                expression meshes.

        Returns:
            The K * N * 3 numpy array encoding the list of shape modes
            determined by the specified meshes in relation to the
            generic_neutral_mesh.
        """

        # Initialize the shape modes
        num_modes = len(meshes)
        shape_modes = np.zeros((num_modes, self.num_vertices, 3))

        # Compute each shape mode
        for mesh, shape_mode in zip(meshes, shape_modes):
            shape_mode[:] = mesh.points() - self.generic_neutral_mesh.points()

        return shape_modes

    def verify_shape_modes(self):
        """Writes meshes to verify the shape modes were computed correctly.

        Allows the user to verify that the shape modes were computed correctly
        by applying each shape mode to the generic neutral mesh and saving the
        resulting mesh. The user can verify that the shape modes were computed
        correctly by running this helper function, and then manually comparing
        the output .obj files to the original identity and expression .obj
        files by opening them up in an applicaton like Blender.
        """

        # Make a directory if it does not exist
        dir_path = self.path / 'verify_shape_modes'
        if not os.path.exists(dir_path):
            os.mkdir(dir_path)

        # Write verification meshes for identity and expression shape modes
        print("Writing identity shape mode verification meshes...")
        self._verify_shape_modes_helper(dir_path, self.identity_shape_modes,
                                        self.identity_names)

        print("Writing expression shape mode verification meshes...")
        self._verify_shape_modes_helper(dir_path, self.expression_shape_modes,
                                        self.expression_names)

        # Alert user to status of script
        print("Completed writing verification meshes.")

    def _verify_shape_modes_helper(self, dir_path, shape_modes, filenames):
        """Helper procedure to write the shape mode verification meshes.
        """
        for shape_mode, filename in zip(shape_modes, filenames):
            # Initialize the verification mesh
            write_mesh = deepcopy(self.generic_neutral_mesh)
            write_points = write_mesh.points()

            # Create the verification mesh
            write_points[:] = self.generic_neutral_mesh.points() + shape_mode

            # Write the meshes to be verified
            write_path = dir_path / (filename + '.obj')
            om.write_mesh(str(write_path), write_mesh)

    def clean_verify_shape_modes(self):
        """Cleans the folder and verification meshes made by verify_shapes_mode.

        If the directory './verify_shape_modes' exists, recursively delete it
        and its contents.
        """
        dir_path = self.path / 'verify_shape_modes'
        if os.path.exists(dir_path):
            shutil.rmtree(dir_path)
