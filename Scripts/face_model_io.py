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

"""Defines functionality to read ICT face models and write them as meshes.
"""

import os
import copy
import json
import numpy as np

import openmesh as om

import ict_face_model


def read_coefficients(file_path):
    """Reads coefficients representing identity and expression
    Args:
        file_path: The file path of the .json file we are reading the
            identity and expression coefficents from.
    Returns:
        identity and expression shape coefficients
    """
    with open(file_path) as file:
        # Read the identity and expression weights
        face_model_json = json.load(file)
        id_coeffs = np.array(face_model_json['identity_coefficients'])
        ex_coeffs = np.array(face_model_json['expression_coefficients'])

        return id_coeffs, ex_coeffs

def write_deformed_mesh(file_path, face_model):
    """Writes the deformed mesh to the specified file path.

    Args:
        file_path: The file_path we write to.
        face_model: Face model with deformabl mesh.
    """
    print("Writing: " + file_path)
    om.write_mesh(file_path, face_model._deformed_mesh, halfedge_tex_coord = True)

def load_face_model(model_directory):
    """Loads the ICT Face Model.

    Returns:
        An initialized face model.
    """
    loader = _DirectoryModelLoader(model_directory)
    return loader.load_model()

class _DirectoryModelLoader:
    def __init__(self, model_path):
        super(_DirectoryModelLoader, self).__init__()
        self._model_path = model_path
    
    def load_model(self):
        """Loads the ICT Face Model.

        Reads the ICT Face Model configuration file, generic neutral mesh,
        expressions, and identity shapes. Stores the contents of the model
        configuration file and the generic neutral mesh as a openmesh.PolyMesh
        object. Initializes the deformed mesh as a deep copy of the generic
        neutral mesh. Computes and stores the expression and identity shape
        modes from the read expressions and identities. Initializes the
        expression and identity weights to all zero lists.

        Returns:
            An initialized face model.
        """

        print("Loading face model...")
        face_model = ict_face_model.FaceModel()
        face_model._model_path = self._model_path

        # Read the model config and generic neutral mesh
        face_model._model_config = self._read_model_config()
        face_model._generic_neutral_mesh = self._read_generic_neutral_mesh()

        # Initialize deformed mesh
        face_model._deformed_mesh = copy.deepcopy(face_model._generic_neutral_mesh)
        face_model._deformed_vertices = face_model._deformed_mesh.points()

        # Read the expressions and the identities
        print("Reading expression morph targets...")
        ex_names, ex_meshes = self._read_expression_morph_targets(face_model._model_config['expressions'])
        print("Reading identity morph targets...")
        id_names, id_meshes = self._read_identity_morph_targets()
        face_model._expression_names = np.array(ex_names, dtype=object)
        face_model._identity_names = np.array(id_names, dtype=object)
        face_model._num_expression_shapes = len(face_model._expression_names)
        face_model._num_identity_shapes = len(face_model._identity_names)

        # Initialize expression and identity weights
        face_model._expression_weights = np.zeros((face_model._num_expression_shapes))
        face_model._identity_weights = np.zeros((face_model._num_identity_shapes))

        # Compute the expression and identity shape modes
        face_model._expression_shape_modes = self._compute_shape_mode_deltas(face_model._generic_neutral_mesh, ex_meshes)
        face_model._identity_shape_modes = self._compute_shape_mode_deltas(face_model._generic_neutral_mesh, id_meshes)

        face_model._model_initialized = True
        print("Finished loading face model.")
        return face_model

    def _compute_shape_mode_deltas(self, generic_neutral_mesh, morph_target_meshes):
        """Computes and returns shape modes determined by the specifed morph_target_meshes.

        Computes the shape modes determined by the specified morph_target_meshes in relation
        to the generic_neutral_mesh. Each individual shape mode is a numpy
        array of dimension N * 3, where N is equal to the number of vertices
        in the generic neutral mesh. The list of shape modes is a numpy array
        of dimension K * N * 3, where K is the total number of shape modes.

        Args:
            morph_target_meshes: A list of openmesh PolyMesh objects to compute the shape
                modes for. This will either be the identity morph_target_meshes or the
                expression morph_target_meshes.

        Returns:
            The K * N * 3 numpy array representing the list of shape modes
            determined by the specified morph_target_meshes in relation to the
            generic neutral mesh.
        """

        # Initialize the shape modes
        num_modes = len(morph_target_meshes)
        num_vertices = generic_neutral_mesh.n_vertices()
        shape_modes = np.zeros((num_modes, num_vertices, 3))

        # Compute each shape mode
        for mesh, shape_mode in zip(morph_target_meshes, shape_modes):
            shape_mode[:] = mesh.points() - generic_neutral_mesh.points()

        return shape_modes

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
        generic_neutral_mesh = om.read_polymesh(file_path, halfedge_tex_coord = True)
        return generic_neutral_mesh

    def _read_expression_morph_targets(self, expression_names):
        """Reads and returns the expressions in the face model.

        Returns:
            A tuple whose first element is a list of expression names and whose
            second element is a list of openmesh.PolyMesh expression meshes.
        """
        ex_names = []
        ex_meshes = []
        for ex_name in expression_names:
            print("Reading expression morph target: " + ex_name)
            file_name = ex_name + '.obj'
            file_path = os.path.join(self._model_path, file_name)
            mesh = om.read_polymesh(file_path)
            ex_names.append(ex_name)
            ex_meshes.append(mesh)
        return ex_names, ex_meshes

    def _read_identity_morph_targets(self):
        """Reads and returns the identities in the face model.

        Returns:
            A tuple whose first element is a list of identity names and whose
            second element is a list of openmesh.PolyMesh identity meshes.
        """
        id_names = []
        id_meshes = []

        identityNum = 0
        while True:
            id_name = 'identity{:03d}'.format(identityNum)
            file_name = id_name + ".obj"
            file_path = os.path.join(self._model_path, file_name)
            mesh = None
            try:
                print("Reading identity morph target: " + id_name)
                mesh = om.read_polymesh(file_path)
                id_names.append(id_name)
                id_meshes.append(mesh)
                identityNum = identityNum + 1
            except Exception as e:
                print("Unable to read identity morph target. Continuing...")
                break
            else:
                continue
            finally:
                pass

        return id_names, id_meshes
