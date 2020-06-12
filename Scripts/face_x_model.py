# June 11, 2020

import os  # access files in directory
import shutil  # high level file operations
import inspect  # get path to current file
from pathlib import Path  # parse windows paths
import json  # .json file reader
from copy import deepcopy  # deepcopy

import openmesh as om  # openmesh library
import numpy as np  # numpy library


# initialize face_x_model as empty dictionary
face_x_model = {}

# find path to file and FaceXModel directory
filename = inspect.getframeinfo(inspect.currentframe()).filename
path = Path(os.path.dirname(os.path.abspath(filename)))
face_x_model_path = path.parent / 'FaceXModel'

# first read and store the vertex indices json
with open(face_x_model_path / 'vertex_indices.json') as input_file:
    vertex_indices = json.load(input_file)
    face_x_model['vertex_indices'] = vertex_indices

# second read and store the generic neutral mesh
generic_neutral_mesh_path = str(face_x_model_path / 'generic_neutral_mesh.obj')
generic_neutral_mesh = om.read_polymesh(generic_neutral_mesh_path)
face_x_model['generic_neutral_mesh'] = generic_neutral_mesh

# alert user of script status
print('Started loading FaceXModel.')
print('Loading identity and expression meshes...')

# read in every identity and expression in the FaceXModel
identity_meshes = []
identity_names = []
expression_meshes = []
expression_names = []
filenames = os.listdir(face_x_model_path)
for filename in filenames:
    name, ext = os.path.splitext(filename)
    # if .obj file and not generic neutral mesh
    if ext == ".obj" and name != 'generic_neutral_mesh':
        file_path = os.path.join(face_x_model_path, filename)  # full file path
        mesh = om.read_polymesh(file_path)  # read in .obj with openmesh
        # add identity or expression mesh to corresponding list
        if name.startswith('identity'):
            identity_meshes.append(mesh)
            identity_names.append(name)
        else:
            expression_meshes.append(mesh)
            expression_names.append(name)

# alert user of script status
print("Computing identity and expression shape modes...")

# initialize the identity and expression  deltas (shape modes) as K * N * 3
# numpy arrays, where K is the number of shape modes, N is the number of
# vertices, and 3 represents the number of components per-vertex (xyz)
num_vertices = generic_neutral_mesh.n_vertices()
num_identities = len(identity_meshes)
num_expressions = len(expression_meshes)
identity_deltas = np.zeros((num_identities, num_vertices, 3))
expression_deltas = np.zeros((num_identities, num_vertices, 3))


# helper function to compute vertex deltas
def _compute_vertex_deltas(basis_mesh, offset_mesh, shape_mode):
    """
    Computes the vertex deltas from a base_mesh to an offset_mesh (with the
    same topology) and stores the resulting deltas in a shape_mode. The
    basis and offset mesh are assumed to be openmesh.PolyMesh objects, and
    the shape_mode is assumed to be a numpy array of dimension num_vertices
    by 3.
    """
    # Get a numpy array representation of the vertices of each mesh
    basis_vertices = basis_mesh.points()
    offset_vertices = offset_mesh.points()
    # for each basis and offset vertex compute and store the vertex delta
    for i in range(num_vertices):
        basis_vertex = basis_vertices[i]
        offset_vertex = offset_vertices[i]
        shape_mode[i] = offset_vertex - basis_vertex


# compute the identity and expression deltas
for i, id_mesh in enumerate(identity_meshes):
    id_delta = identity_deltas[i]
    _compute_vertex_deltas(generic_neutral_mesh, id_mesh, id_delta)

for i, ex_mesh in enumerate(expression_meshes):
    ex_delta = expression_deltas[i]
    _compute_vertex_deltas(generic_neutral_mesh, ex_mesh, ex_delta)

# store the deltas in the face_x_model
face_x_model['identity_deltas'] = identity_deltas
face_x_model['expression_deltas'] = expression_deltas

# alert user of script status
print("Finished loading FaceXModel.")


# helper function that allows the user to verify the computed shape modes
def verify_shape_modes():
    """
    Allows the user to verify that the shape modes were computed correctly by
    applying each shape mode to the generic_neutral_mesh and saving the
    resulting mesh. The user can verify that the shape modes were computed
    correctly by running this helper function, and then manually comparing the
    output .obj files to the original identity and expression .obj files by
    opening them up in an applicaton like Blender.
    """
    # make a directory if it does not exist
    dir_path = path / 'verify_shape_modes'
    if not os.path.exists(dir_path):
        try:
            os.mkdir(dir_path)
        except OSError:
            print("ERROR: creation of the directory %s failed." % dir_path)
            return
        else:
            pass

    # write verification meshes for identity and expression shape modes
    basis_points = generic_neutral_mesh.points()

    print("Writing identity shape mode verification meshes...")
    _verify_shape_modes_helper(dir_path, basis_points, identity_names,
                               identity_deltas)

    print("Writing expression shape mode verification meshes...")
    _verify_shape_modes_helper(dir_path, basis_points, expression_names,
                               expression_deltas)

    # alert user to status of script
    print("Completed writing verification meshes and ready for inspection.")


# helper function that writes the shape mode verification meshes
def _verify_shape_modes_helper(dir_path, basis_points, mode_names,
                               mode_deltas):
    """
    Helper procedure that writes the shape mode verification meshes given the
    shape mode verificaton path dir_path, the basis_points determined by the
    generic_neutral_mesh, the shape mode names mod_names, and the shape mode
    deltas themselves mode_deltas.
    """
    # loop over each shape mode deltas and their corresponding names
    for i, (name, deltas) in enumerate(zip(mode_names, mode_deltas)):

        # the mesh and points we will write to
        write_mesh = deepcopy(generic_neutral_mesh)
        write_points = write_mesh.points()

        # we want to traverse the basis points, deltas, and write points
        # all of these are N * 3 dimensional numpy arrays
        for i in range(num_vertices):
            # do the reverse of the vertex delta computation
            write_points[i] = basis_points[i] + deltas[i]

        # write the meshes to be verified
        write_path = dir_path / (name + '.obj')
        om.write_mesh(str(write_path), write_mesh)


# cleans the folder and verification meshes produced by verify_shapes_modes
def clean_verify_shape_modes():
    """
    If the directory './verify_shape_modes' exists, recursively delete it.
    """
    dir_path = path / 'verify_shape_modes'
    if os.path.exists(dir_path):
        shutil.rmtree(dir_path)


# sources
# https://www.programiz.com/python-programming/json
# https://stackoverflow.com/questions/10377998/how-can-i-iterate-over-files-in-a-given-directory
# https://stackoverflow.com/questions/541390/extracting-extension-from-filename-in-python
# https://kite.com/python/examples/4286/os-get-the-path-of-all-files-in-a-directory
# https://stackoverflow.com/questions/1274405/how-to-create-new-folder
# https://stackabuse.com/creating-and-deleting-directories-with-python/
