"""Defines functionality to verify the loading of the ICT Face Model.
"""

import copy
import os
import openmesh as om

import face_model_io


def main():
    """Verifies that the FaceModel class loads the ICT Face Model properly.
    """
    face_model = face_model_io.load_face_model('../FaceXModel')
    verify_model_loaded('./verfication_files', face_model)


def verify_model_loaded(dir_path, face_model):
    """Writes meshes to verify that the ICT Face Model was loaded correctly.

    Allows the user to verify that the ICT Face Model was loaded correctly.
    Does this by recreating the original expression and identity meshes from
    the expression shape modes, identity shape modes, and generic neutral mesh.
    Saves these meshes as .obj files to a specified directory. Creates the
    specified directory if it does not already exist. These verification files
    can be inspected in an application like Blender.
    """

    # Check if ICT face model loaded
    if not face_model._model_initialized:  # pylint:disable=protected-access
        print("The FaceModel has not loaded the ICT Face Model.")
        return

    # Make the directory if it doesn't exist
    if not os.path.exists(dir_path):
        os.mkdir(dir_path)

    # In line comments ignore protected access and line too long linter errors
    gn_mesh = face_model._generic_neutral_mesh  # noqa: E501 pylint:disable=protected-access
    ex_names = face_model._expression_names  # pylint:disable=protected-access
    ex_shape_modes = face_model._expression_shape_modes  # noqa: E501 pylint:disable=protected-access
    id_names = face_model._identity_names  # pylint:disable=protected-access
    id_shape_modes = face_model._identity_shape_modes  # noqa: E501 pylint:disable=protected-access

    # Write expression verification meshes
    print("Writing expression meshes...")
    _verify_model_loaded_helper(dir_path, gn_mesh, ex_names, ex_shape_modes)

    # Write identity verification meshes
    print("Writing identity meshes...")
    _verify_model_loaded_helper(dir_path, gn_mesh, id_names, id_shape_modes)

    # Alert user to status of script
    print("Completed writing verification meshes.")


def _verify_model_loaded_helper(dir_path, generic_neutral_mesh, file_names,
                                shape_modes):
    """Helper procedure to write the verification meshes.
    """
    for file_name, shape_mode in zip(file_names, shape_modes):
        # Initialize the verification mesh
        write_mesh = copy.deepcopy(generic_neutral_mesh)
        write_points = write_mesh.points()

        # Create the verification mesh
        write_points[:] = generic_neutral_mesh.points() + shape_mode

        # Write the meshes to be verified
        write_path = os.path.join(dir_path, file_name + '.obj')
        om.write_mesh(write_path, write_mesh)


if __name__ == '__main__':
    main()
