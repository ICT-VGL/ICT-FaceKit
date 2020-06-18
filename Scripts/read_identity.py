"""Example script that reads an identity and writes its mesh.
"""

import face_model_io


def main():
    """Reads an ICT FaceModel .json file and writes its mesh.
    """
    # Create a new FaceModel and load the model
    face_model = face_model_io.read_face_model('./testidentity.json')
    face_model.load_model('../FaceXModel')

    # Deform the mesh
    face_model.deform_mesh()

    # Write the deformed mesh
    mesh = face_model.get_deformed_mesh()
    face_model_io.write_mesh('./read_identity.obj', mesh)


if __name__ == '__main__':
    main()
