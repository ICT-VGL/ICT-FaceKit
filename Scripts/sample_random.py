"""Example script that samples and writes random identities.
"""

import face_model_io
import ict_face_model


def main():
    """Loads the ICT Face Mode and samples and writes 10 random identities.
    """
    # Create a new FaceModel and load the model
    face_model = ict_face_model.FaceModel()
    face_model.load_model('../FaceXModel')

    print("Writing 10 random identities...")
    for i in range(10):
        # Randomize the identity and deform the mesh
        face_model.randomize_identity()
        face_model.deform_mesh()

        # Write the deformed mesh
        mesh = face_model.get_deformed_mesh()
        write_path = './random_identity' + str(i) + '.obj'
        face_model_io.write_mesh(write_path, mesh)

    print("Finished writing meshes.")


if __name__ == '__main__':
    main()
