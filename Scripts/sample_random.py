"""Example script that samples and writes random identities.
"""

import face_model_io


def main():
    """Loads the ICT Face Mode and samples and writes 10 random identities.
    """
    # Create a new FaceModel and load the model
    face_model = face_model_io.load_face_model('../FaceXModel')

    print("Writing 10 random identities...")
    for i in range(10):
        # Randomize the identity and deform the mesh
        face_model.randomize_identity()
        face_model.deform_mesh()

        # Write the deformed mesh
        write_path = '../sample_data/random_identity{:02d}.obj'.format(i)
        face_model_io.write_deformed_mesh(write_path, face_model)

    print("Finished writing meshes.")


if __name__ == '__main__':
    main()
