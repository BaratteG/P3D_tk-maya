
from maya import cmds

class MayaAsset(object):

    def __init__(self, assetRoot=""):

        self._root = assetRoot

    def getGroup(self, parent, groupName):
        ''' Get a group from the parent object.
        The group need to be direclty under the asset root in the hierarchy.

        Args:
            parent      (str):  The parent of the group.
            groupName   (str): The group name

        Returns:
            str: The group full path.
        '''
        subGroups = cmds.listRelatives(parent, allDescendents=False, type="transform", fullPath=True)

        for group in subGroups:
            if(group.find(groupName) != -1):
                return group
        
        return None

    def isValid(self):
        ''' Check if the current asset root is a valide production asset.

        Returns:
            bool: True if valid, otherwise False.
        '''
        return self.groupMeshes is not None and \
        self.groupBones is not None and \
        self.groupRig is not None and \
        self.groupMeshesHI is not None and \
        self.groupMeshesMI is not None and \
        self.groupMeshesLO is not None and \
        self.groupMeshesTechnical is not None

    @property
    def name(self):
        return self._root
    
    @name.setter
    def name(self, value):
        cmds.rename(self._root, value)

    @property
    def groupMeshes(self):
        return self.getGroup(self._root, "meshes_GRP")

    @property
    def groupRig(self):
        return self.getGroup(self._root, "rig_GRP")

    @property
    def groupBones(self):
        return self.getGroup(self._root, "bones_GRP")

    @property
    def groupMeshesHI(self):
        return self.getGroup(self.groupMeshes, "HI_GRP")

    @property
    def groupMeshesMI(self):
        return self.getGroup(self.groupMeshes, "MI_GRP")

    @property
    def groupMeshesLO(self):
        return self.getGroup(self.groupMeshes, "LO_GRP")

    @property
    def groupMeshesTechnical(self):
        return self.getGroup(self.groupMeshes, "Technical_GRP")

    @property
    def meshesHI(self):
        return cmds.listRelatives(self.groupMeshesHI, children=True, fullPath=True, type="transform")

    @property
    def meshesMI(self):
        return cmds.listRelatives(self.groupMeshesMI, children=True, fullPath=True, type="transform")

    @property
    def meshesLO(self):
        return cmds.listRelatives(self.groupMeshesLO, children=True, fullPath=True, type="transform")

    @property
    def meshesTechnical(self):
        return cmds.listRelatives(self.groupMeshesTechnical, children=True, fullPath=True, type="transform")
