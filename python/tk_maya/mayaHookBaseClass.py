
import glob
import os
import maya.cmds as cmds
import sgtk

from tank_vendor import six

HookBaseClass = sgtk.get_hook_baseclass()

class MayaHookBaseClass(HookBaseClass):

    def __init__(self, parent):
        super(MayaHookBaseClass, self).__init__(parent)

    def checkPublishTemplate(self, template_name):
        ''' Check if the publish template is defined and valid.

        Args:
            template_name (str): The publish template.

        Returns:
            bool: True is valid, otherwise False.
        '''
        publisher = self.parent
        # ensure the publish template is defined and valid and that we also have
        publish_template = publisher.get_template_by_name(template_name)
        if not publish_template:
            self.logger.debug(
                "The valid publish template could not be determined for the "
                "session geometry item. Not accepting the item."
            )
            return False, None
        
        return True, publish_template

    def getCurrentSessionPath(self):
        """
        Return the path to the current session
        :return:
        """
        path = cmds.file(query=True, sn=True)

        if path is not None:
            path = six.ensure_str(path)

        if not path:
            # the session still requires saving. provide a save button.
            # validation fails.
            error_msg = "The Maya session has not been saved."
            self.logger.error(error_msg)
            raise Exception(error_msg)

        # get the normalized path
        path = sgtk.util.ShotgunPath.normalize(path)
        self.logger.info("Path : %s" % path)

        return path

    def getWorkTemplateFieldsFromPath(self, workTemplate, path, addFields=None):

        # get the current scene path and extract fields from it using the work
        # template:
        work_fields = workTemplate.get_fields(path)
        self.logger.info("Work Fields : %s" % work_fields)

        # Add Custom fields.
        if(addFields):
            work_fields.append(addFields)

        # ensure the fields work for the publish template
        missing_keys = workTemplate.missing_keys(work_fields)
        if missing_keys:
            error_msg = (
                "Work file '%s' missing keys required for the "
                "publish template: %s" % (path, missing_keys)
            )
            self.logger.error(error_msg)
            raise Exception(error_msg)
        
        return work_fields
               
    def addPublishDatasToPublishItem(self, item, publishTemplateName):

        # Get the session path.
        sessionPath = self.getCurrentSessionPath()

        # Use the working template to extract fields from sessionPath to solve the template path.
        workTemplate = item.properties.get("work_template")

        workFields = self.getWorkTemplateFieldsFromPath(workTemplate, sessionPath)

        # Get the template path.
        publishTemplate = item.properties.get(publishTemplateName)

        # create the publish path by applying the fields. store it in the item's
        # properties. This is the path we'll create and then publish in the base
        # publish plugin. Also set the publish_path to be explicit.
        item.properties["path"]         = publishTemplate.apply_fields(workFields)
        item.properties["publish_path"] = item.properties["path"]

        # use the work file's version number when publishing
        if "version" in workFields:
            item.properties["publish_version"] = workFields["version"]

        return item