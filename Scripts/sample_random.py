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
        write_path = '../sample_data_out/random_identity{:02d}.obj'.format(i)
        face_model_io.write_deformed_mesh(write_path, face_model)

    print("Finished writing meshes.")


if __name__ == '__main__':
    main()
