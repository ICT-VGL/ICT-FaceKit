##########################################################################################
#                                                                                        #
# ICT FaceKit                                                                            #
#                                                                                        #
# Copyright (c) 2020 USC Institute for Creative Technologies                             #
#                                                                                        #
# Permission is hereby granted, free of charge, to any person obtaining a copy           #
# of this software and associated documentation files (the "Software"), to deal          #
# in the Software without restriction, including without limitation the rights           #
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell              #
# copies of the Software, and to permit persons to whom the Software is                  #
# furnished to do so, subject to the following conditions:                               #
#                                                                                        #
# The above copyright notice and this permission notice shall be included in all         #
# copies or substantial portions of the Software.                                        #
#                                                                                        #
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR             #
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,               #
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE            #
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER                 #
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,          #
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE          #
# SOFTWARE.                                                                              #
##########################################################################################

"""Defines functionality to use the ICT face model.

This module defines the FaceModel class which allows one work with faces
parameterized by the ICT morphable face model.
"""

import json
import os

import numpy as np
import openmesh as om


class FaceModel:  # pylint: disable=too-many-instance-attributes
    """A class that parameterizes faces with the ICT face model.

    This class represents faces parameterized by the ICT face model. Each
    FaceModel object uses a list of identity and expression weights to compute
    a deformed mesh in terms of the generic neutral mesh, the identity shape
    modes, and the expression shape modes.

    Attributes:
        _model_initialized: A boolean representing whether or not the ICT Face Model
            has been loaded.

        _model_config: The ICT face model configuration data.

        _generic_neutral_mesh: The generic neutral mesh represented as an
            openmesh.PolyMesh object.

        _deformed_mesh: A deep copy of the generic neutral mesh that we will
            deform using the identity and expression shape modes.

        _deformed_vertices: A numpy array of dimension N * 3 where N is the
            number of vertices of the generic neutral mesh. Represents the
            vertices of the deformed mesh.

        _expression_names: A numpy array of strings representing the names of
            the face model expressions.

        _expression_names: A numpy array of strings representing the names of
            the face model identities.

        _num_expression_shapes: The number of face model expressions.

        _num_identity_shapes: The number of face model identities.

        _expression_weights: A numpy array of dimension K representing the
            weights corresponding to each expression shape mode.

        _identity_weights: A numpy array of dimension K representing the
            weights corresponding to each identity shape mode.

        _expression_shape_modes: A numpy array of dimension K * N * 3 where K
            is the number of shape modes and N is the number of vertices.
            Represents the list of expression shape modes computed from the
            expression meshes read in with openmesh.

        _identity_shape_modes: A numpy array of dimension K * N * 3 where K
            is the number of shape modes and N is the number of vertices.
            Represents the list of identity shape modes computed from the
            identity meshes read in with openmesh.
    """
    def __init__(self):
        """Creates a new FaceModel object.

        Creates a new FaceModel object by initializing each of its attributes
        to None and initializing the model loaded attribute to False.
        """
        self._model_initialized = False
        self._model_config = None
        self._generic_neutral_mesh = None
        self._deformed_mesh = None
        self._deformed_vertices = None
        self._expression_names = None
        self._identity_names = None
        self._num_expression_shapes = None
        self._num_identity_shapes = None
        self._expression_weights = None
        self._identity_weights = None
        self._expression_shape_modes = None
        self._identity_shape_modes = None

    def set_identity(self, identity_weights):
        """Sets the identity weights.

        If the ICT Face Model has been loaded, overwrites the identity weights.
        If the ICT Face Modle has not been loaded, assigns the identity weights
        to the input identity weights so that they can be processed when the
        ICT Face Model is loaded.

        Args:
            identity_weights: the new list of identity_weights
        """
        if self._model_initialized:
            # Make sure that identity_weights is the right dimension
            min_num_ids = min(self._num_identity_shapes, len(identity_weights))
            self._identity_weights[:min_num_ids] = identity_weights[:min_num_ids]
        else:
            self._identity_weights = identity_weights

    def set_expression(self, expression_weights):
        """Sets the expression weights.

        If the ICT Face Model has been loaded, overwrites the expression
        weights. If the ICT Face Modle has not been loaded, assigns the
        expression weights to the input expression weights so that they can be
        processed when the ICT Face Model is loaded.

        Args:
            expression_weights: the new list of expression_weights
        """
        if self._model_initialized:
            # Make sure that expression_weights is the right dimension
            min_num_exs = min(self._num_expression_shapes, len(expression_weights))
            self._expression_weights[:min_num_exs] = expression_weights[:min_num_exs]
        else:
            self._expression_weights = expression_weights

    def randomize_identity(self):
        """Sample a random identity from the normal distribution.

        Randomly samples the normal distribution to make a new face. Does not
        deform the deformed mesh, but instead updates the identity weights.

        As a precondition the ICT Face Model must be loaded. Raises an
        exception if the ICT Face Model was not loaded.
        """
        assert self._model_initialized, "Face Model not loaded but required"

        self._identity_weights = np.random.normal(size=self._num_identity_shapes)

    def from_coefficients(self, id_coeffs, ex_coeffs):
        self.set_identity(id_coeffs)
        self.set_expression(ex_coeffs)

    def reset_mesh(self):
        """Resets the deformed mesh to the generic neutral mesh.

        Resets the deformed mesh to the generic neutral mesh by setting the
        vertices of the deformed mesh to a copy of the vertices of the generic
        neutral mesh.

        As a precondition the ICT Face Model must be loaded. Raises an
        exception if the ICT Face Model was not loaded.
        """
        assert self._model_initialized, "Face Model not loaded but required"

        self._deformed_vertices[:] = self._generic_neutral_mesh.points()

    def deform_mesh(self):
        """Updates the deformed mesh based on the shape mode weights.

        Updates the vertices of the deformed mesh by adding the product of
        each identity weight by identity shape mode and each expression weight
        by expression shape mode to the vertices of the generic neutral mesh.

        As a precondition the ICT Face Model must be loaded. Raises an
        exception if the ICT Face Model was not loaded.
        """
        assert self._model_initialized, "Face Model not loaded but required"

        # reset to generic mesh
        self.reset_mesh()

        # compute the contribution of the identity shape modes
        self._deform_mesh_helper(self._identity_weights,
                                 self._identity_shape_modes)

        # compute the contribution of the expression shape modes
        self._deform_mesh_helper(self._expression_weights,
                                 self._expression_shape_modes)

    def _deform_mesh_helper(self, weights, shape_modes):
        """Adds the specified shape modes to the deformed mesh.

        Given a scalar list of weights and a list of shape modes, loops over
        the weights and shape modes and adds the contribution of each current
        weight * shape mode to the deformed mesh.
        """
        # Loop over the weights and shape modes
        for weight, shape_mode in zip(weights, shape_modes):
            # Add the contribution of the current weight * shape mode
            self._deformed_vertices += weight * shape_mode

    def get_deformed_mesh(self):
        """Returns the deformed mesh.

        As a precondition the ICT Face Model must be loaded. Raises an
        exception if the ICT Face Model was not loaded.

        Returns:
            Returns a reference to the openmesh.PolyMesh deformed mesh object.
        """
        assert self._model_initialized, "Face Model not loaded but required"

        return self._deformed_mesh
