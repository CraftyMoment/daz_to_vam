# This file requires python 3.3.5 and the Adobe FBX python sdk

import json
import copy

from FbxCommon import *

# Match this to how long the animation is in DAZ.
SECS_TO_PROCESS = 4

# Rotates the feet when set to True
USE_HEELS = True

# Adds the same animation but backwards (reverses the animation)
REVERSE = False

# The file you want to inject the animation to
# For better results jack up the "Rotation Spring" under physics tab on all nodes
TARGET_FILE = 'I:\\VaM_Release1.13.0.1\\Saves\scene\\fbx_base'

# The name of the exported file from DAZ
ANIMATION_FILES = ['F:\\Users\\Public\\Desktop\\export.fbx']

# The name of the Atom to inject the animation to.
ATOM_NAME = 'Person'


SCALE_FACTOR_X = 120
SCALE_FACTOR_Y = 80
SCALE_FACTOR_Z = 120
Y_OFFSET = -2.0
FPS = 60

VAM_BONE_NAMES = {

    # Body
    'hip': 'hip',
    'pelvis': 'pelvis',
    'abdomen': 'abdomen',
    'abdomen2': 'abdomen2',
    'chest': 'chest',
    'neck': 'neck',
    'head': 'head',

    # Right arm
    'rCollar': 'rShoulder',
    'rShldr': 'rArm',
    'rForeArm': 'rElbow',
    'rHand': 'rHand',

    # Right leg
    'rThigh': 'rThigh',
    'rShin': 'rKnee',
    'rFoot': 'rFoot',
    'rToe': 'rToe',

    # Left arm
    'lCollar': 'lShoulder',
    'lShldr': 'lArm',
    'lForeArm': 'lElbow',
    'lHand': 'lHand',

    # Left leg
    'lThigh': 'lThigh',
    'lShin': 'lKnee',
    'lFoot': 'lFoot',
    'lToe': 'lToe',
}


class VamFile:

    def __init__(self, filename):
        with open(filename, 'r') as g:
            self.vam_json = json.load(g)

    def get_person_index(self):
        a_list = self.vam_json['atoms']
        i = 0
        for item in a_list:
            if item['id'] == ATOM_NAME:
                return i
            i = i + 1

    def insert_in_vam(self, steps, boneName):
        self.vam_json['atoms'][self.get_person_index()]['storables'].append({
            'id': boneName + 'Animation',
            'steps': steps
        })

    def insert_core_control(self, animation_length):
        a_list = self.vam_json['atoms']
        i = 0
        for item in a_list:
            if item['id'] == 'CoreControl':
                break
            else:
                i = i + 1
        j = 0
        for item in self.vam_json['atoms'][i]['storables']:
            if item['id'] == 'MotionAnimationMaster':
                break
            else:
                j = j + 1

        self.vam_json['atoms'][i]['storables'][j] = {
            'id': 'MotionAnimationMaster',
            'recordedLength': str(animation_length),
            'startTimestep': '0',
            'stopTimestep': str(animation_length),
            'loopbackTime': '0',
            'loop': 'false',
            'playbackSpeed': '1',
            'triggers': []
        }


class Converter:

    def __init__(self, vam_file):
        self.known_nodes = []
        self.vam_file = vam_file

    def show_structure(self, aNode, level):
        if aNode.GetName() in VAM_BONE_NAMES:
            print((' ' * (level - 1)) + '+' + aNode.GetName())
            self.known_nodes.append(aNode)
        else:
            print((' ' * (level - 1)) + '+' + aNode.GetName() + '(not mapped)')
        for k in range(aNode.GetChildCount()):
            self.show_structure(aNode.GetChild(k), level + 1)

    def process(self):

        for aFile in ANIMATION_FILES:
            print('Processing %s' % aFile)
            sdk, scene = InitializeSdkObjects()
            LoadScene(sdk, scene, aFile)

            root_node = scene.GetRootNode()

            print('Printing structure')
            self.show_structure(root_node, 0)
            secs_to_process = SECS_TO_PROCESS
            print('\nEvaluating...')
            for node in self.known_nodes:
                print('...' + node.GetName())
                eval = scene.GetAnimationEvaluator()
                time = FbxTime()
                steps = []

                for i in range(0, secs_to_process * FPS):
                    curr_time = i / FPS

                    time.SetSecondDouble(curr_time)

                    transform = eval.GetNodeGlobalTransform(node, time)
                    t = transform.GetT()
                    q = transform.GetQ()
                    animation = {
                        'timeStep': str(curr_time),
                        'rotationOn': 'true',
                        'rotation': {},
                        'position': {}
                    }
                    if VAM_BONE_NAMES[node.GetName()] in ['hip']:
                        animation['positionOn'] = 'true'
                        animation['position']['x'] = str(-t[0] / SCALE_FACTOR_X)
                        animation['position']['y'] = str((t[1] / SCALE_FACTOR_Y) + Y_OFFSET)
                        animation['position']['z'] = str(t[2] / SCALE_FACTOR_Z)
                    else:
                        animation['positionOn'] = 'false'

                    if VAM_BONE_NAMES[node.GetName()] in ['lFoot']:
                        if USE_HEELS:
                            q = q * FbxQuaternion(0.6, 0.2, 0, 0.98)
                        else:
                            q = q * FbxQuaternion(0.18, 0.2, 0, 0.98)
                    if VAM_BONE_NAMES[node.GetName()] in ['rFoot']:
                        if USE_HEELS:
                            q = q * FbxQuaternion(0.6, -0.2, 0, 0.98)
                        else:
                            q = q * FbxQuaternion(0.18, -0.2, 0, 0.98)
                    if VAM_BONE_NAMES[node.GetName()] in ['lToe']:
                        q = q * FbxQuaternion(0.18, 0.2, 0, 0.98)
                    if VAM_BONE_NAMES[node.GetName()] in ['rToe']:
                        q = q * FbxQuaternion(0.18, -0.2, 0, 0.98)
                    if VAM_BONE_NAMES[node.GetName()] in ['rShoulder']:
                        q = q * FbxQuaternion(0, -0.13, -0.13, 0.99)
                    if VAM_BONE_NAMES[node.GetName()] in ['lShoulder']:
                        q = q * FbxQuaternion(0, 0.13, 0.13, 0.99)
                    if VAM_BONE_NAMES[node.GetName()] in ['rElbow']:
                        q = q * FbxQuaternion(0, 0.34, 0, 0.93)
                    if VAM_BONE_NAMES[node.GetName()] in ['lElbow']:
                        q = q * FbxQuaternion(0, -0.34, 0, 0.93)
                    if VAM_BONE_NAMES[node.GetName()] in ['rThigh']:
                        q = q * FbxQuaternion(0, -0.043, -0.026, 0.999)
                    if VAM_BONE_NAMES[node.GetName()] in ['lThigh']:
                        q = q * FbxQuaternion(0, 0.043, 0.026, 0.999)
                    if VAM_BONE_NAMES[node.GetName()] in ['rKnee']:
                        q = q * FbxQuaternion(0, -0.043, 0, 0.999)
                    if VAM_BONE_NAMES[node.GetName()] in ['lKnee']:
                        q = q * FbxQuaternion(0, 0.043, 0, 0.999)
                    if VAM_BONE_NAMES[node.GetName()] in ['rarm']:
                        q = q * FbxQuaternion(0, 0, 0.02, 0.999)
                    if VAM_BONE_NAMES[node.GetName()] in ['lArm']:
                        q = q * FbxQuaternion(0, 0, -0.02, 0.999)
                    if VAM_BONE_NAMES[node.GetName()] in ['rHand']:
                        q = q * FbxQuaternion(0, 0.17, 0, 0.98)
                    if VAM_BONE_NAMES[node.GetName()] in ['lHand']:
                        q = q * FbxQuaternion(0, -0.17, 0, 0.98)
                    if VAM_BONE_NAMES[node.GetName()] in ['neck', 'head']:
                        q = q * FbxQuaternion(0.05, 0, 0, 0.98)

                    animation['rotation']['x'] = str(q.GetAt(0) * 1)
                    animation['rotation']['y'] = str(q.GetAt(1) * -1)
                    animation['rotation']['z'] = str(q.GetAt(2) * -1)
                    animation['rotation']['w'] = str(q.GetAt(3) * 1)

                    steps.append(animation)
                    if REVERSE:
                        rev_time = 2 * secs_to_process - (curr_time)
                        if rev_time != 0:
                            animation2 = copy.deepcopy(animation)
                            animation2['timeStep'] = str(rev_time)
                            steps.append(animation2)
                steps.sort(key=lambda x: float(x['timeStep']))
                self.vam_file.insert_in_vam(steps, VAM_BONE_NAMES[node.GetName()])
            if REVERSE:
                secs_to_process = secs_to_process * 2
            self.vam_file.insert_core_control(secs_to_process)
            output = TARGET_FILE + '_converted.json'
            with open(output, 'w') as g:
                print('\nSaving to %s' % output)
                json.dump(self.vam_file.vam_json, g, indent=3)


if __name__ == "__main__":
    vam_file = VamFile(TARGET_FILE + '.json')
    c = Converter(vam_file)
    c.process()
