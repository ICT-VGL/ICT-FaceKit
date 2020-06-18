"""Defines functionality to use the ICT face model.

This module defines the FaceModel class which allows one work with faces
parameterized by the ICT morphable face model.
"""

import copy
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
        _model_loaded: A boolean representing whether or not the ICT Face Model
            has been loaded.

        _model_path: The path to the ICT face model directory.

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

        _num_expressions: The number of face model expressions.

        _num_identities: The number of face model identities.

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
        self._model_loaded = False
        self._model_path = None
        self._model_config = None
        self._generic_neutral_mesh = None
        self._deformed_mesh = None
        self._deformed_vertices = None
        self._expression_names = None
        self._identity_names = None
        self._num_expressions = None
        self._num_identities = None
        self._expression_weights = None
        self._identity_weights = None
        self._expression_shape_modes = None
        self._identity_shape_modes = None

    def load_model(self, model_path):
        """Loads the ICT Face Model.

        Reads the ICT Face Model configuration file, generic neutral mesh,
        expressions, and identities. Stores the contents of the model
        configuration file and the generic neutral mesh as a openmesh.PolyMesh
        object. Initializes the deformed mesh as a deep copy of the generic
        neutral mesh. Computes and stores the expression and identity shape
        modes from the read expressions and identities. Initializes the
        expression and identity weights to all zero lists.

        Args:
            model_path: The file path of the folder containing the ICT Face
                Model.
        """

        print("Loading face model...")
        self._model_path = model_path

        # Read the model config and generic neutral mesh
        self._model_config = self._read_model_config()
        self._generic_neutral_mesh = self._read_generic_neutral_mesh()

        # Initialize deformed mesh
        self._deformed_mesh = copy.deepcopy(self._generic_neutral_mesh)
        self._deformed_vertices = self._deformed_mesh.points()

        # Read the expressions and the identities
        ex_names, ex_meshes = self._read_expressions()
        id_names, id_meshes = self._read_identities()
        self._expression_names = np.array(ex_names, dtype=object)
        self._identity_names = np.array(id_names, dtype=object)
        self._num_expressions = len(self._expression_names)
        self._num_identities = len(self._identity_names)

        # Initialize expression and identity weights
        ex_weights = np.zeros((self._num_expressions))
        id_weights = np.zeros((self._num_identities))

        # If the expression weights were set before the model was loaded
        if self._expression_weights is not None:
            # Make sure that self._expression_weights is the right dimension
            ex_weights[:] = self._expression_weights[:self._num_expressions]
        self._expression_weights = ex_weights

        # If the identity weights were set before the model was loaded
        if self._identity_weights is not None:
            # Make sure self._identity_weights is the right dimension
            id_weights[:] = self._identity_weights[:self._num_identities]
        self._identity_weights = id_weights

        # Compute the expression and identity shape modes
        self._expression_shape_modes = self._compute_shape_modes(ex_meshes)
        self._identity_shape_modes = self._compute_shape_modes(id_meshes)

        self._model_loaded = True
        print("Finished loading face model.")

    def _read_model_config(self):
        """Reads and returns the face model config json file.

        Returns:
            A dictionary representation of the model config json file.
        """
        file_path = os.path.join(self._model_path, 'vertex_indices.json')
        with open(file_path) as file:
            model_config = json.load(file)
            return model_config

    def _read_generic_neutral_mesh(self):
        """Reads and returns the face model generic neutral mesh.

        Returns:
            A openmesh.PolyMesh representation of the generic neutral mesh.
        """
        file_path = os.path.join(self._model_path, 'generic_neutral_mesh.obj')
        generic_neutral_mesh = om.read_polymesh(file_path)
        return generic_neutral_mesh

    def _read_expressions(self):
        """Reads and returns the expressions in the face model.

        Returns:
            A tuple whose first element is a list of expression names and whose
            second element is a list of openmesh.PolyMesh expression meshes.
        """
        ex_names = []
        ex_meshes = []
        for ex_name in self._model_config['expressions']:
            file_name = ex_name + '.obj'
            file_path = os.path.join(self._model_path, file_name)
            mesh = om.read_polymesh(file_path)
            ex_names.append(ex_name)
            ex_meshes.append(mesh)
        return ex_names, ex_meshes

    def _read_identities(self):
        """Reads and returns the identities in the face model.

        Returns:
            A tuple whose first element is a list of identity names and whose
            second element is a list of openmesh.PolyMesh identity meshes.
        """
        id_names = []
        id_meshes = []
        for file_name in os.listdir(self._model_path):
            name, ext = os.path.splitext(file_name)
            if name.startswith('identity') and ext == '.obj':
                file_path = os.path.join(self._model_path, file_name)
                mesh = om.read_polymesh(file_path)
                id_names.append(name)
                id_meshes.append(mesh)
        return id_names, id_meshes

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
            The K * N * 3 numpy array representing the list of shape modes
            determined by the specified meshes in relation to the
            generic neutral mesh.
        """

        # Initialize the shape modes
        num_modes = len(meshes)
        num_vertices = self._generic_neutral_mesh.n_vertices()
        shape_modes = np.zeros((num_modes, num_vertices, 3))

        # Compute each shape mode
        for mesh, shape_mode in zip(meshes, shape_modes):
            shape_mode[:] = mesh.points() - self._generic_neutral_mesh.points()

        return shape_modes

    def set_identity(self, identity_weights):
        """Sets the identity weights.

        If the ICT Face Model has been loaded, overwrites the identity weights.
        If the ICT Face Modle has not been loaded, assigns the identity weights
        to the input identity weights so that they can be processed when the
        ICT Face Model is loaded.

        Args:
            identity_weights: the new list of identity_weights
        """
        if self._model_loaded:
            # Make sure that identity_weights is the right dimension
            num_ids = self._num_identities
            self._identity_weights[:] = identity_weights[:num_ids]
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
        if self._model_loaded:
            # Make sure that expression_weights is the right dimension
            num_exs = self._num_expressions
            self._expression_weights[:] = expression_weights[num_exs:]
        else:
            self._expression_weights = expression_weights

    def randomize_identity(self):
        """Sample a random identity from the normal distribution.

        Randomly samples the normal distribution to make a new face. Does not
        deform the deformed mesh, but instead updates the identity weights.

        As a precondition the ICT Face Model must be loaded. Raises an
        exception if the ICT Face Model was not loaded.
        """
        if not self._model_loaded:
            raise Exception("Face Model not loaded but required.")

        self._identity_weights = np.random.normal(size=self._num_identities)

    def reset_mesh(self):
        """Resets the deformed mesh to the generic neutral mesh.

        Resets the deformed mesh to the generic neutral mesh by setting the
        vertices of the deformed mesh to a copy of the vertices of the generic
        neutral mesh.

        As a precondition the ICT Face Model must be loaded. Raises an
        exception if the ICT Face Model was not loaded.
        """
        if not self._model_loaded:
            raise Exception("Face Model not loaded but required.")

        self._deformed_vertices[:] = self._generic_neutral_mesh.points()

    def deform_mesh(self):
        """Updates the deformed mesh based on the shape mode weights.

        Updates the vertices of the deformed mesh by adding the product of
        each identity weight by identity shape mode and each expression weight
        by expression shape mode to the vertices of the generic neutral mesh.

        As a precondition the ICT Face Model must be loaded. Raises an
        exception if the ICT Face Model was not loaded.
        """
        if not self._model_loaded:
            raise Exception("Face Model not loaded but required.")

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
        if not self._model_loaded:
            raise Exception("Face Model not loaded but required.")

        return self._deformed_mesh
