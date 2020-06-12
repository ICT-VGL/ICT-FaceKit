# June 12, 2020

import time  # time functionality
from copy import deepcopy  # deep copy functionality

import numpy as np  # numpy library
import openmesh as om  # openmesh library

from face_x_model import face_x_model as fxm


# FaceModel class to represent an instance of a FaceXModel
class FaceModel(object):
    """
    An instance of the FaceModel represents a specific face in using the FaxeXModel
    parameterization. This class allows one to construct a new FaceModel with
    identity and expression weights initialized to zero, sample a random identity,
    deform the mesh according to the identity and expression weights, write the mesh,
    reset the mesh, and some additional helper procedures.
    """

    def __init__(self):
        """
        Constructs a new FaceModel object. Each FaceModel stores a reference to
        the generic neutral mesh, a deep copy of the generic neutral mesh that
        will be deformed called the deformed mesh, and references to the identity
        and expression shape modes. The identity weights and expression weights
        are initialized to all zeros.
        """
        super(FaceModel, self).__init__()

        # store a reference to the generic neutral mesh
        self.generic_neutral_mesh = fxm["generic_neutral_mesh"]
        self.generic_neutral_points = self.generic_neutral_mesh.points()
        self.num_vertices = self.generic_neutral_mesh.n_vertices()

        # create a deep clone for the deformed mesh
        self.deformed_mesh = deepcopy(fxm["generic_neutral_mesh"])
        self.deformed_points = self.deformed_mesh.points()

        # store references to the identity and expression shape modes
        # shape modes are K * N * 3 dimension numpy arrays where K is the
        # number of shape modes and N is the number of vertices
        self.identity_shape_modes = fxm["identity_deltas"]
        self.num_identities = len(self.identity_shape_modes)
        self.identity_weights = np.zeros((self.num_identities))

        self.expression_shape_modes = fxm["expression_deltas"]
        self.num_expressions = len(self.expression_shape_modes)
        self.expression_weights = np.zeros((self.num_expressions))

        # the file writing path
        self.write_path = "./"

    def write_mesh(self):
        """
        Writes the current deformed_mesh to the current directory. The filename
        of the written deformed_mesh is determined by the current time.
        """
        timestr = str(time.time()).replace('.', '')
        write_path = self.write_path + "face_model_" + timestr + ".obj"
        om.write_mesh(write_path, self.deformed_mesh)

    def reset_mesh(self):
        """
        Resets the deformed mesh to that of the generic neutral mesh.
        """
        self.deformed_points[:] = self.generic_neutral_points

    def deform_mesh(self):
        """
        Deforms the generic neutral mesh by adding the product of each identity
        weight by identity shape mode and expression wieght by expression shape
        mode.
        """
        # reset to generic mesh
        self.reset_mesh()

        # deform the deformed mesh according to the identity and expression weights
        self._deform_mesh_helper(self.identity_weights, self.identity_shape_modes)
        self._deform_mesh_helper(self.expression_weights, self.expression_shape_modes)

    def _deform_mesh_helper(self, weights, shape_modes):
        """
        Given a scalar list of weights and a list of shape modes, loops over
        the weights and shape modes and adds the contribution of each current
        weight * shape mode to the deformed mesh.
        """
        # loop over the weights and shape modes
        for weight, shape_mode in zip(weights, shape_modes):
            # add the contribution of the current weight * shape mode
            self.deformed_points += weight * shape_mode

    def sample_random_identity(self):
        """
        Randomly samples the gaussian distribution to make a new face. Does not
        deform the deformed_mesh, but instead updated the identity and
        exprssion weights.
        """
        self.identity_weights = np.random.normal(size=self.num_identities)

    def write_random_identity(self):
        """
        Samples a random identity, deforms the mesh, and writes the mesh.
        """
        self.sample_random_identity()
        self.deform_mesh()
        self.write_mesh()
