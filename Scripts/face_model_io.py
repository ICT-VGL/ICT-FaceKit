"""Defines functionality to read ICT face models and write them as meshes.
"""

import json
import numpy as np

import openmesh as om

import ict_face_model


def read_face_model(file_path):
    """Creates a FaceModel object encoded by a .json file.

    Args:
        file_path: The file path of the .json file we are reading the
            identity and expression coefficents from.
    """
    with open(file_path) as file:
        # Create a new FaceModel object
        face_model = ict_face_model.FaceModel()

        # Read the identity and expression weights
        face_model_json = json.load(file)
        id_weights = np.array(face_model_json['identity_coefficients'])
        ex_weights = np.array(face_model_json['expression_coefficients'])

        # Set the identity and expression weights and update the mesh
        face_model.set_identity(id_weights)
        face_model.set_expression(ex_weights)

        return face_model


def write_mesh(file_path, mesh):
    """Writes the mesh to the specified file path.

    Args:
        mesh: The openmesh.PolyMesh object we are writing.
        file_path: The file_path we write to.
    """
    om.write_mesh(file_path, mesh)
