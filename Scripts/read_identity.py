"""Example script that reads an identity and writes its mesh.
"""

import face_model_io


def main():
    """Reads an ICT FaceModel .json file and writes its mesh.
    """
    # Create a new FaceModel and load the model
    id_coeffs, ex_coeffs = face_model_io.read_coefficients('../sample_data/sample_identity_coeffs.json')
    face_model = face_model_io.load_face_model('../FaceXModel')
    face_model.from_coefficients(id_coeffs, ex_coeffs)

    # Deform the mesh
    face_model.deform_mesh()

    # Write the deformed mesh
    face_model_io.write_deformed_mesh('../sample_data/sample_identity.obj', face_model)

if __name__ == '__main__':
    main()
