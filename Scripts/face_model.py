"""A module defining functionality to use the FaceXModel morphable face model.

This module defines the FaceModel class which allows one work with faces
parameterized by the FaceXModel morphable face model. In the following typical
usage example, one samples a random face from the distribution, computes the
corresponding deformed mesh, and write the corresponding deformed mesh as a
.obj file.

  Typical usage example:

  FaceModel.load_face_x_model()  # Load the FaceXModel
  my_face = FaceModel()  # Make a new face
  my_face.write_random_identity() # Sample a random face and write it
"""

from copy import deepcopy
import time

import json
import numpy as np
import openmesh as om

import face_x_model


class FaceModel():  # pylint: disable=too-many-instance-attributes
    """Represents faces parameterized by the FaceXModel morphable face model.

    This class allows one to construct a FaceModel parameterized by a list of
    identity and expression weights. Each FaceModel uses identity and
    expression weights to compute a deformed mesh in terms of the generic
    neutral mesh, the identity shape modes, and the expression shape modes.
    This class allows one to set the identity and expression weights, compute
    the deformed mesh, write the deformed mesh, and sample a random identity
    from the distribution.

    Keeps track of a static variable face_x_model that is either explititly
    initialized to a FaceXModel object or intialized the first time the
    FaceModel constructor is called.

    Attributes:
        generic_neutral_mesh: A reference to the generic neutral mesh object
            read in using openmesh.

        generic_neutral_points: A reference to the numpy array of dimension N *
            3 representing the vertices of the generic neutral mesh.

        num_vertices: The number of vertices of the generic neutral mesh; N.

        deformed_mesh: A reference to a deep copy of the generic neutral mesh
            object that we will deform using the identity and expression shape
            modes.

        identity_shape_modes: A reference to the list of identity shape modes
            read in using openmesh. This list of shape modes is represented as
            a numpy array of dimension K * N * 3 where K is the number of shape
            modes.

        num_identities: The number of identity shape modes.

        identity_weights: A numpy array of dimension K representing the weights
            corresponding to each identity shape mode.

        expression_shape_modes: A reference to the list of expression shape
            modes read in using openmesh. This list of shape modes is
            represented as a numpy array of dimension K * N * 3 where K is the
            number of shape modes.

        num_expressions: the number of expression shape modes.

        expression_weights: A numpy array of dimension K representing the
            weights corresponding to each identity shape mode.

        write_path: The file path to write the resulting deformed mesh.

        filename: The filename used when writing the resulting deformed mesh.
    """

    # A static variable to store a FaceXModel object
    face_x_model = None

    @staticmethod
    def load_face_x_model():
        """Loads the FaceXModel into the face_x_model static variable.
        """
        FaceModel.face_x_model = face_x_model.FaceXModel()

    def __init__(self, id_weights=None, ex_weights=None, write_path=None,
                 filename=None):
        """Constructs a new FaceModel object.

        Each FaceModel stores a reference to the generic neutral mesh and
        references to the identity and expression shape modes. The deformed
        mesh is intialized to a deep copy of the generic neutral mesh and the
        identity and expression weights are initialized to lists of all zeros.
        If specified, the identity weights are intialized to id_weights, the
        expression weights are initialized to ex_weights, and the write_path
        and filename properties are set.

        If the static variable FaceModel.face_x_model is None, then this
        constructor calls the FaceModel.load_face_x_model to load the
        FaceXModel.

        Args:
            id_weights: An optional numpy array to intialize the identity
                weights.
            ex_weights: An optional numpy array to initialze the expression
                weights.
            write_path: An optional string representing the file path to write
                to when writing the mesh.
            filename: An optional string to overwrite the default timestamp
                based filename used when writing the mesh.

        Returns:
            If no parameters are passed, returns a  new FaceModel object
            parameterizing the generic neutral mesh. Otherwise, returns a new
            FaceModel object parameterized by the specified identity and
            expression weights, with write_path and filename properties set.
        """

        # If we have not loaded the FaceXModel, load it
        if FaceModel.face_x_model is None:
            FaceModel.load_face_x_model()
        fxm = FaceModel.face_x_model

        # We keep track of the generic neutral mesh
        self.generic_neutral_mesh = fxm.generic_neutral_mesh
        self.generic_neutral_points = self.generic_neutral_mesh.points()
        self.num_vertices = self.generic_neutral_mesh.n_vertices()

        # We initialize the deformed mesh to the generic neutral mesh
        self.deformed_mesh = deepcopy(self.generic_neutral_mesh)
        self.deformed_points = self.deformed_mesh.points()

        # We store references to the identity shape modes
        self.identity_shape_modes = fxm.identity_shape_modes
        self.num_identities = len(self.identity_shape_modes)
        self.identity_weights = np.zeros((self.num_identities))

        # Set the iddentity weights if specified
        if id_weights:
            self.identity_weights[:] = id_weights

        # We store references to the expression shape modes
        self.expression_shape_modes = fxm.expression_shape_modes
        self.num_expressions = len(self.expression_shape_modes)
        self.expression_weights = np.zeros((self.num_expressions))

        # Set the expression weights if specified
        if ex_weights:
            self.expression_weights[:] = ex_weights

        # We store the write path and filename
        if write_path:
            self.write_path = write_path
        else:
            self.write_path = "./"
        self.filename = filename

    def write_mesh(self, write_path=None, filename=None):
        """Writes the current deformed mesh to the working directory.

        Writes the current deformed_mesh to the working directory as an .obj
        file with the specified filename. If a filename was not previously set,
        a filename is created from the current timestamp. If a new write_path
        or filename is specified, updates the specified properties before
        writing.

        Args:
            write_path: An optional string representing the file path to write
                to when writing the mesh.
            filename: An optional string to overwrite the default timestamp
                based filename used when writing the mesh.
        """
        # Update specifed properties
        if write_path:
            self.write_path = write_path
        if filename:
            self.filename = filename

        # Construct path based on filename or timestamp
        if self.filename:
            path = self.write_path + "/" + self.filename + ".obj"
        else:
            timestr = str(time.time()).replace('.', '')
            path = self.write_path + "/face_model_" + timestr + ".obj"

        om.write_mesh(path, self.deformed_mesh)

    def reset_mesh(self):
        """Resets the deformed mesh to the generic neutral mesh.

        Resets the deformed mesh to the generic neutral mesh by setting the
        vertices of the deformed mesh to a copy of the vertices of the generic
        neutral mesh.
        """
        self.deformed_points[:] = self.generic_neutral_points

    def deform_mesh(self):
        """Computes the deformed mesh based on the shape mode weights.

        Computes the vertices of the deformed mesh by adding the product of
        each identity weight by identity shape mode and each expression weight
        by expression shape mode to the vertices of the generic neutral mesh.
        """
        # reset to generic mesh
        self.reset_mesh()

        # compute the contribution of the identity shape modes
        self._deform_mesh_helper(self.identity_weights,
                                 self.identity_shape_modes)

        # compute the contribution of the expression shape modes
        self._deform_mesh_helper(self.expression_weights,
                                 self.expression_shape_modes)

    def _deform_mesh_helper(self, weights, shape_modes):
        """Adds the specified shape modes to the deformed mesh.

        Given a scalar list of weights and a list of shape modes, loops over
        the weights and shape modes and adds the contribution of each current
        weight * shape mode to the deformed mesh.
        """
        # Loop over the weights and shape modes
        for weight, shape_mode in zip(weights, shape_modes):
            # Add the contribution of the current weight * shape mode
            self.deformed_points += weight * shape_mode

    def sample_random_identity(self):
        """Sample a random identity from the distribution.

        Randomly samples the gaussian distribution to make a new face. Does not
        deform the deformed mesh, but instead updates the identity and
        expression weights.
        """
        self.identity_weights = np.random.normal(size=self.num_identities)

    def write_random_identity(self):
        """Samples a random identity, deforms the mesh, and writes the mesh.
        """
        self.sample_random_identity()
        self.deform_mesh()
        self.write_mesh()

    def read_face_model(self, file_path):
        """Reads a face model parameterization from a .json file.

        Reads in and stores the identity weights and expression weights
        encoded in a .json file. After reading in and storing the weights,
        updates the deformed mesh.

        Args:
            file_path: The file path of the .json file we are reading the
                identity and expression coefficents from.
        """
        with open(file_path) as input_file:
            # Read the identity and expression weights
            face_model_json = json.load(input_file)
            id_weights = np.array(face_model_json['identity_coefficients'])
            ex_weights = np.array(face_model_json['expression_coefficients'])

            # Set the identity and expression weights and update the mesh
            self.identity_weights = id_weights
            self.expression_weights = ex_weights
            self.deform_mesh()
